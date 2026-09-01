"""Dependency-free configuration loading and schema validation."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .environments import target_ids
from .models import Severity


class ConfigError(ValueError):
    """A user-actionable configuration or input error."""


DEFAULT_EXCLUDES: tuple[str, ...] = (
    ".git/**",
    ".hg/**",
    ".svn/**",
    "node_modules/**",
    "vendor/**",
    "dist/**",
    "build/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".tox/**",
    "coverage/**",
)

_KNOWN_KEYS = {
    "targets",
    "supported",
    "unsupported",
    "requirements",
    "exclude",
    "ignore",
    "minimum_score",
    "fail_on",
    "max_file_size",
    "verification",
}


@dataclass(frozen=True)
class Config:
    targets: tuple[str, ...] = field(default_factory=target_ids)
    exclude: tuple[str, ...] = DEFAULT_EXCLUDES
    ignore: tuple[str, ...] = ()
    minimum_score: int = 85
    fail_on: tuple[str, ...] = (Severity.BLOCKER.value, Severity.ERROR.value)
    supported: tuple[str, ...] = ()
    unsupported: tuple[str, ...] = ()
    requirements: dict[str, str] = field(default_factory=dict)
    max_file_size: int = 1_000_000
    verification: dict[str, Any] = field(default_factory=dict)
    config_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets": list(self.targets),
            "exclude": list(self.exclude),
            "ignore": list(self.ignore),
            "minimum_score": self.minimum_score,
            "fail_on": list(self.fail_on),
            "supported": list(self.supported),
            "unsupported": list(self.unsupported),
            "requirements": dict(self.requirements),
            "max_file_size": self.max_file_size,
            "verification": self.verification,
        }


def _strip_comment(value: str) -> str:
    quoted: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted == '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quoted == char:
                quoted = None
            elif quoted is None:
                quoted = char
            continue
        if char == "#" and quoted is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _split_key(value: str) -> tuple[str, str]:
    quoted: str | None = None
    for index, char in enumerate(value):
        if char in {'"', "'"}:
            quoted = None if quoted == char else (char if quoted is None else quoted)
        elif char == ":" and quoted is None:
            return value[:index].strip(), value[index + 1 :].strip()
    raise ConfigError(f"invalid YAML mapping entry: {value}")


def _split_inline(value: str) -> list[str]:
    try:
        result = ast.literal_eval(value.replace("true", "True").replace("false", "False"))
    except (SyntaxError, ValueError):
        result = None
    if isinstance(result, (list, tuple)):
        return [str(item) for item in result]
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [part.strip().strip("'\"") for part in inner.split(",")]


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        return _split_inline(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        if value[0] == '"':
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError):
                raise ConfigError(f"invalid quoted scalar: {value}") from None
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the intentionally small YAML schema used by agent-xplat.

    Supported constructs are mappings, indented lists, scalar values, quoted
    strings, and inline lists. Unsupported YAML is rejected explicitly.
    """
    entries: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.lstrip("\ufeff").splitlines(), start=1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ConfigError(f"line {number}: tabs are not supported for indentation")
        content = _strip_comment(raw).strip()
        if not content:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        entries.append((indent, content, number))
    if not entries:
        return {}
    if entries[0][0] != 0 or entries[0][1].startswith("-"):
        raise ConfigError("configuration root must be a mapping")
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for position, (indent, content, number) in enumerate(entries):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigError(f"line {number}: invalid indentation")
        parent = stack[-1][1]
        if content.startswith("-"):
            if not isinstance(parent, list):
                raise ConfigError(f"line {number}: list item has no list parent")
            item = content[1:].strip()
            if not item:
                raise ConfigError(f"line {number}: empty list item is not supported")
            parent.append(_scalar(item))
            continue
        key, raw_value = _split_key(content)
        if not key:
            raise ConfigError(f"line {number}: empty mapping key")
        if isinstance(parent, dict) and key in parent:
            raise ConfigError(f"line {number}: duplicate configuration key: {key}")
        if not raw_value:
            next_entry = entries[position + 1] if position + 1 < len(entries) else None
            container: Any = [] if next_entry and next_entry[0] > indent and next_entry[1].startswith("-") else {}
            parent[key] = container
            stack.append((indent, container))
        else:
            parent[key] = _scalar(raw_value)
    return root


def _as_string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{name} must be a list of strings")
    return tuple(value)


def _validate_target_list(values: tuple[str, ...], name: str) -> None:
    known = set(target_ids())
    for value in values:
        if value not in known:
            raise ConfigError(f"unknown target in {name}: {value}")


def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ConfigError("configuration must be a mapping")
    wrapped = document.get("agent-xplat")
    if wrapped is not None:
        if not isinstance(wrapped, dict):
            raise ConfigError("agent-xplat must contain a mapping")
        overlap = sorted((set(document) - {"agent-xplat"}) & set(wrapped))
        if overlap:
            raise ConfigError(f"configuration key duplicated between root and agent-xplat: {', '.join(overlap)}")
        document = {**{key: value for key, value in document.items() if key != "agent-xplat"}, **wrapped}
    unknown = sorted(set(document) - _KNOWN_KEYS)
    if unknown:
        raise ConfigError(f"unknown configuration key(s): {', '.join(unknown)}")
    return document


def load_config(root: Path) -> Config:
    root = Path(root)
    path = root / ".agent-xplat.yml"
    if not path.exists():
        return Config()
    try:
        document = _normalize_document(parse_yaml_subset(path.read_text(encoding="utf-8")))
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    targets = _as_string_tuple(document.get("targets"), "targets") or target_ids()
    exclude = _as_string_tuple(document.get("exclude"), "exclude")
    ignore = _as_string_tuple(document.get("ignore"), "ignore")
    supported = _as_string_tuple(document.get("supported"), "supported")
    unsupported = _as_string_tuple(document.get("unsupported"), "unsupported")
    _validate_target_list(targets, "targets")
    _validate_target_list(supported, "supported")
    _validate_target_list(unsupported, "unsupported")
    if set(supported) & set(unsupported):
        raise ConfigError("a target cannot be both supported and unsupported")
    outside_scan = (set(supported) | set(unsupported)) - set(targets)
    if outside_scan:
        raise ConfigError(f"contract target(s) must be included in targets: {', '.join(sorted(outside_scan))}")
    for rule_id in ignore:
        if not re.fullmatch(r"AX-[A-Z0-9-]+", rule_id):
            raise ConfigError(f"invalid ignore rule id: {rule_id}")
    from .rules.registry import get_rule

    unknown_rules = sorted(rule_id for rule_id in ignore if get_rule(rule_id.upper()) is None)
    if unknown_rules:
        raise ConfigError(f"unknown ignore rule id(s): {', '.join(unknown_rules)}")
    minimum_score = document.get("minimum_score", 85)
    if not isinstance(minimum_score, int) or not 0 <= minimum_score <= 100:
        raise ConfigError("minimum_score must be an integer from 0 to 100")
    fail_on = _as_string_tuple(document.get("fail_on"), "fail_on") or (Severity.BLOCKER.value, Severity.ERROR.value)
    invalid_severity = set(fail_on) - {severity.value for severity in Severity}
    if invalid_severity:
        raise ConfigError(f"invalid fail_on severity: {', '.join(sorted(invalid_severity))}")
    max_file_size = document.get("max_file_size", 1_000_000)
    if not isinstance(max_file_size, int) or max_file_size < 1_024:
        raise ConfigError("max_file_size must be an integer of at least 1024")
    requirements = document.get("requirements", {})
    if not isinstance(requirements, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in requirements.items()):
        raise ConfigError("requirements must be a mapping of names to strings")
    verification = document.get("verification", {})
    if not isinstance(verification, dict):
        raise ConfigError("verification must be a mapping")
    unknown_verification = sorted(set(verification) - {"command", "timeout"})
    if unknown_verification:
        raise ConfigError(f"unknown verification key(s): {', '.join(unknown_verification)}")
    if "command" in verification and not isinstance(verification["command"], str):
        raise ConfigError("verification.command must be a string")
    if "timeout" in verification and (not isinstance(verification["timeout"], int) or verification["timeout"] < 1):
        raise ConfigError("verification.timeout must be a positive integer")
    return Config(
        targets=targets,
        exclude=DEFAULT_EXCLUDES + tuple(pattern for pattern in exclude if pattern not in DEFAULT_EXCLUDES),
        ignore=ignore,
        minimum_score=minimum_score,
        fail_on=fail_on,
        supported=supported,
        unsupported=unsupported,
        requirements=dict(requirements),
        max_file_size=max_file_size,
        verification=dict(verification),
        config_path=path.as_posix(),
    )
