"""Python AST and interpreter portability detectors."""

from __future__ import annotations

import ast
import re

from ..environments import is_native_windows, is_windows_target
from ..models import Confidence, Severity, Finding, SourceFile, SourceLocation
from ..parsers import parse_python
from .common import RuleContext, RuleSpec, line_matches, make_finding


def _ast_finding(spec: RuleSpec, source: SourceFile, context: RuleContext, node: ast.AST, affected: tuple[str, ...], reason: str, severity: Severity | None = None) -> Finding | None:
    if not affected or not getattr(node, "lineno", None):
        return None
    line = getattr(node, "lineno", 1)
    column = getattr(node, "col_offset", 0) + 1
    end_line = getattr(node, "end_lineno", line)
    end_column = getattr(node, "end_col_offset", column) + 1
    return Finding(
        rule_id=spec.rule_id,
        title=spec.title,
        description=spec.description,
        location=SourceLocation(source.relative_path, line, column, end_line, end_column),
        severity=severity or spec.severity,
        confidence=spec.confidence,
        affected_targets=tuple(target.id for target in context.targets if target.id in affected),
        reason=reason,
        remediation=spec.remediation,
        examples=spec.examples,
        code=source.lines[line - 1].strip() if source.lines else "",
        metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
    )


def detect_python(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    if source.path.name == "pyproject.toml" and "[project]" in source.text and not re.search(r"^\s*requires-python\s*=", source.text, re.IGNORECASE | re.MULTILINE):
        finding = make_finding(
            specs["AX-PY-005"], source, context, 0, "[project]", context.target_ids,
            "The Python project does not declare a supported Python version, so runtime portability cannot be gated deterministically.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(python3?|py)(?=\s|$|[-m])", re.IGNORECASE):
        if source.path.suffix.lower() not in {".sh", ".bash", ".zsh", ".ps1", ".cmd", ".bat"} and "`" not in line and not line.lstrip().lower().startswith(("python ", "python3 ", "py ")):
            continue
        command = match.group(0)
        if command == "py":
            affected = tuple(target.id for target in context.targets if not is_windows_target(target.id))
        elif command == "python3":
            affected = tuple(target.id for target in context.targets if is_native_windows(target.id))
        else:
            affected = tuple(target.id for target in context.targets if is_native_windows(target.id))
        finding = make_finding(
            specs["AX-PY-001"], source, context, line_index, command, affected,
            f"Interpreter invocation {command} is not guaranteed to resolve to the required Python executable on every target.",
            severity=Severity.ERROR if command == "python3" else Severity.WARNING,
            confidence=Confidence.HIGH if command != "python" else Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])pip3?(?=\s|$)", re.IGNORECASE):
        if source.path.suffix.lower() not in {".sh", ".bash", ".zsh", ".ps1", ".cmd", ".bat"} and "`" not in line and not line.lstrip().lower().startswith(("pip ", "pip3 ")):
            continue
        finding = make_finding(
            specs["AX-PY-007"], source, context, line_index, match.group(0), context.target_ids,
            f"Pip executable {match.group(0)} is assumed to be on PATH instead of using the active Python environment.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"^#!\s*/usr/bin/(?:env\s+)?python3?\b"):
        affected = tuple(target.id for target in context.targets if is_native_windows(target.id))
        finding = make_finding(
            specs["AX-PY-002"], source, context, line_index, match.group(0), affected,
            "Unix-specific Python shebang is not executable by native Windows shells.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?:venv|\.venv)[\\/]?(?:bin[\\/]python|Scripts[\\/]python(?:\.exe)?)"):
        value = match.group(0)
        if "Scripts" in value or "\\" in value:
            affected = tuple(target.id for target in context.targets if not is_windows_target(target.id))
        else:
            affected = tuple(target.id for target in context.targets if is_windows_target(target.id))
        finding = make_finding(
            specs["AX-PY-004"], source, context, line_index, value, affected,
            f"Virtual-environment executable path {value} hardcodes one platform's directory layout.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    if source.path.suffix.lower() == ".py":
        parsed = parse_python(source)
        if parsed.tree is not None:
            for node in ast.walk(parsed.tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.fullmatch(r"python3?|py", node.value, re.IGNORECASE):
                    command = node.value.lower()
                    affected = tuple(target.id for target in context.targets if (command == "py" and not is_windows_target(target.id)) or (command != "py" and is_native_windows(target.id)))
                    finding = _ast_finding(
                        specs["AX-PY-001"], source, context, node, affected,
                        f"Python executable name {node.value} is embedded in source and may resolve differently across installations.",
                        severity=Severity.WARNING if command == "python" else Severity.ERROR,
                    )
                    if finding:
                        findings.append(finding)
                module = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        if module.split(".")[0].lower() in {"winreg", "msvcrt", "fcntl", "termios", "pwd", "grp", "resource"}:
                            if module.split(".")[0].lower() in {"winreg", "msvcrt"}:
                                affected = tuple(target.id for target in context.targets if not is_windows_target(target.id))
                            else:
                                affected = tuple(target.id for target in context.targets if is_windows_target(target.id))
                            finding = _ast_finding(
                                specs["AX-PY-003"], source, context, node, affected,
                                f"Platform-specific Python import {module} is unavailable on some target operating systems.",
                                severity=Severity.ERROR,
                            )
                            if finding:
                                findings.append(finding)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                    if module.split(".")[0].lower() in {"winreg", "msvcrt", "fcntl", "termios", "pwd", "grp", "resource"}:
                        if module.split(".")[0].lower() in {"winreg", "msvcrt"}:
                            affected = tuple(target.id for target in context.targets if not is_windows_target(target.id))
                        else:
                            affected = tuple(target.id for target in context.targets if is_windows_target(target.id))
                        finding = _ast_finding(
                            specs["AX-PY-003"], source, context, node, affected,
                            f"Platform-specific Python import {module} is unavailable on some target operating systems.",
                            severity=Severity.ERROR,
                        )
                        if finding:
                            findings.append(finding)
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in {"sys", "os"} and node.attr in {"platform", "name"}:
                    finding = _ast_finding(
                        specs["AX-PY-003"], source, context, node, context.target_ids,
                        f"Runtime platform check {node.value.id}.{node.attr} indicates OS-specific branching that needs coverage on each target.",
                        severity=Severity.WARNING,
                    )
                    if finding:
                        findings.append(finding)
    if source.path.name.startswith("requirements") or source.path.name in {"Pipfile", "pyproject.toml"}:
        native_packages = {
            "pywin32": {"windows"},
            "pypiwin32": {"windows"},
            "pyobjc": {"macos"},
            "uvloop": {"linux", "macos"},
            "lxml": set(),
        }
        for line_index, line, match in line_matches(
            source,
            r"(?<![A-Za-z0-9_-])[\"']?(pywin32|pypiwin32|pyobjc|uvloop|lxml)(?=[\"']?\s*(?:[<>=!~;,\]]|$))",
            re.IGNORECASE,
        ):
            package = match.group(1).lower()
            supported_os = native_packages[package]
            affected = tuple(target.id for target in context.targets if not supported_os or target.os not in supported_os)
            finding = make_finding(
                specs["AX-PY-006"], source, context, line_index, match.group(1), affected,
                f"Python dependency {match.group(1)} may require a platform-specific binary or build toolchain.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            )
            if finding:
                findings.append(finding)
    return findings
