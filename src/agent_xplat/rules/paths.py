"""Filesystem path assumption detectors."""

from __future__ import annotations

import ast as python_ast
import json
import re

from ..environments import is_native_windows, is_windows_target
from ..models import Confidence, Severity, Finding, SourceFile
from ..parsers import ParsedJavaScript, iter_named_nodes, javascript_suffixes, node_text, parse_javascript, source_location_for_node
from .common import RuleContext, RuleSpec, line_matches, make_finding


def _native_windows(context: RuleContext) -> tuple[str, ...]:
    return tuple(target.id for target in context.targets if is_native_windows(target.id))


def _non_windows(context: RuleContext) -> tuple[str, ...]:
    return tuple(target.id for target in context.targets if not is_windows_target(target.id))


def _javascript_string_value(raw: str) -> str:
    if raw.startswith("`"):
        return raw[1:-1]
    try:
        value = json.loads(raw) if raw.startswith('"') else python_ast.literal_eval(raw)
        return value if isinstance(value, str) else ""
    except (SyntaxError, ValueError, json.JSONDecodeError):
        return raw[1:-1] if len(raw) >= 2 else raw


def _path_bindings(parsed: ParsedJavaScript) -> tuple[frozenset[str], frozenset[str]]:
    """Return structurally recognized path-module and path-function aliases."""

    module_aliases: set[str] = set()
    function_aliases: set[str] = set()

    def register_object_pattern(pattern) -> None:
        for child in pattern.named_children:
            if child.type == "shorthand_property_identifier_pattern":
                name = node_text(parsed, child)
                if name in {"join", "resolve"}:
                    function_aliases.add(name)
            elif child.type == "pair_pattern":
                key = child.child_by_field_name("key")
                value = child.child_by_field_name("value")
                imported = node_text(parsed, key) if key is not None else ""
                local = node_text(parsed, value) if value is not None else ""
                if imported in {"join", "resolve"} and local:
                    function_aliases.add(local)

    for statement in iter_named_nodes(parsed, "import_statement"):
        source_node = statement.child_by_field_name("source")
        module_name = _javascript_string_value(node_text(parsed, source_node)) if source_node is not None else ""
        if module_name not in {"path", "node:path"}:
            continue
        clause = next((child for child in statement.named_children if child.type == "import_clause"), None)
        if clause is None:
            continue
        for child in clause.named_children:
            if child.type == "identifier":
                module_aliases.add(node_text(parsed, child))
            elif child.type == "namespace_import":
                identifiers = [item for item in child.named_children if item.type == "identifier"]
                if identifiers:
                    module_aliases.add(node_text(parsed, identifiers[-1]))
            elif child.type == "named_imports":
                for specifier in child.named_children:
                    if specifier.type != "import_specifier":
                        continue
                    name = specifier.child_by_field_name("name")
                    alias = specifier.child_by_field_name("alias")
                    imported = node_text(parsed, name) if name is not None else ""
                    local = node_text(parsed, alias) if alias is not None else imported
                    if imported in {"join", "resolve"} and local:
                        function_aliases.add(local)
    for declaration in iter_named_nodes(parsed, "variable_declarator"):
        name = declaration.child_by_field_name("name")
        value = declaration.child_by_field_name("value")
        if name is None:
            continue
        if value is not None and value.type == "call_expression":
            function = value.child_by_field_name("function")
            arguments = value.child_by_field_name("arguments")
            if function is not None and node_text(parsed, function) == "require" and arguments is not None and arguments.named_children:
                required = _javascript_string_value(node_text(parsed, arguments.named_children[0]))
                if required in {"path", "node:path"}:
                    if name.type == "identifier":
                        module_aliases.add(node_text(parsed, name))
                    elif name.type == "object_pattern":
                        register_object_pattern(name)
        if value is not None and value.type == "member_expression" and name.type == "identifier":
            object_node = value.child_by_field_name("object")
            property_node = value.child_by_field_name("property")
            if object_node is not None and property_node is not None and object_node.type == "call_expression":
                function = object_node.child_by_field_name("function")
                arguments = object_node.child_by_field_name("arguments")
                if function is not None and node_text(parsed, function) == "require" and arguments is not None and arguments.named_children:
                    required = _javascript_string_value(node_text(parsed, arguments.named_children[0]))
                    if required in {"path", "node:path"} and node_text(parsed, property_node) in {"join", "resolve"}:
                        function_aliases.add(node_text(parsed, name))
    return frozenset(module_aliases), frozenset(function_aliases)


def _is_direct_path_api_argument(node, parsed: ParsedJavaScript, bindings: tuple[frozenset[str], frozenset[str]]) -> bool:
    arguments = node.parent
    if arguments is None or arguments.type != "arguments" or node not in arguments.named_children:
        return False
    call = arguments.parent
    if call is None or call.type != "call_expression":
        return False
    function = call.child_by_field_name("function")
    if function is None:
        return False
    if function.type == "identifier":
        return node_text(parsed, function) in bindings[1]
    if function.type != "member_expression":
        return False
    object_node = function.child_by_field_name("object")
    property_node = function.child_by_field_name("property")
    return (
        object_node is not None
        and property_node is not None
        and node_text(parsed, object_node) in bindings[0]
        and node_text(parsed, property_node) in {"join", "resolve"}
    )


def _javascript_separator_findings(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    if source.path.suffix.lower() not in javascript_suffixes():
        return []
    parsed = parse_javascript(source)
    if parsed.tree is None:
        return []
    findings: list[Finding] = []
    path_bindings = _path_bindings(parsed)
    for node in (*iter_named_nodes(parsed, "string"), *iter_named_nodes(parsed, "template_string")):
        value = _javascript_string_value(node_text(parsed, node))
        if "\\" not in value or _is_direct_path_api_argument(node, parsed, path_bindings):
            continue
        location = source_location_for_node(source, node)
        if not _non_windows(context):
            continue
        spec = specs["AX-PATH-003"]
        findings.append(
            Finding(
                rule_id=spec.rule_id,
                title=spec.title,
                description=spec.description,
                location=location,
                severity=Severity.WARNING,
                confidence=Confidence.MEDIUM,
                affected_targets=_non_windows(context),
                reason="JavaScript string contains a hardcoded backslash path separator outside path.join/path.resolve.",
                remediation=spec.remediation,
                examples=spec.examples,
                code=source.lines[location.line - 1].strip() if location.line <= len(source.lines) else "",
                metadata={
                    "severity_rationale": spec.severity_rationale,
                    "confidence_rationale": spec.confidence_rationale,
                    "analysis": "tree-sitter-ast",
                    "language": parsed.language,
                    "kind": "separator",
                },
            )
        )
    return findings


def detect_paths(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    native_windows = _native_windows(context)
    non_windows = _non_windows(context)
    for line_index, line, match in line_matches(
        source,
        r"(?<![A-Za-z0-9_])/(?:tmp|var/tmp|Applications|usr/local|opt/homebrew)(?:/[A-Za-z0-9_.+@%~-]+)*",
    ):
        if line.startswith("#!"):
            continue
        value = match.group(0)
        findings.append(
            make_finding(
                specs["AX-PATH-001"],
                source,
                context,
                line_index,
                value,
                native_windows,
                f"POSIX absolute path {value} is not available in native Windows shells.",
                severity=Severity.ERROR if value.startswith(("/Applications", "/opt/homebrew")) else Severity.WARNING,
                confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(
        source,
        r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/][^\r\n'\"`<>|]+|\\\\[^\r\n'\"`<>|]+)",
    ):
        value = match.group(0).rstrip(".,;:)]}")
        if not value:
            continue
        findings.append(
            make_finding(
                specs["AX-PATH-002"],
                source,
                context,
                line_index,
                value,
                non_windows,
                f"Windows-specific path {value} assumes a drive letter or Windows separator.",
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_$%:])(?:Program Files|AppData|%USERPROFILE%|\$env:USERPROFILE|\$USERPROFILE|USERPROFILE)(?![A-Za-z0-9_])", re.IGNORECASE):
        value = match.group(0)
        findings.append(
            make_finding(
                specs["AX-PATH-002"],
                source,
                context,
                line_index,
                value,
                non_windows,
                f"Windows profile/program path token {value} is not portable across Unix targets.",
                severity=Severity.ERROR,
                confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(?:~/|\$(?:HOME|USER)(?![A-Za-z0-9_]))"):
        value = match.group(0)
        findings.append(
            make_finding(
                specs["AX-PATH-003"],
                source,
                context,
                line_index,
                value,
                tuple(target.id for target in context.targets if target.shell == "cmd"),
                f"Home/user path token {value} has shell-specific expansion semantics and is not valid in CMD.",
                severity=Severity.ERROR if value.startswith("~/") else Severity.WARNING,
                confidence=Confidence.MEDIUM if value.startswith("~/") else Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(?:\./|\.\\)"):
        value = match.group(0)
        if value == "./":
            affected = tuple(target.id for target in context.targets if target.shell == "cmd")
        else:
            affected = non_windows
        findings.append(
            make_finding(
                specs["AX-PATH-005"], source, context, line_index, value, affected,
                f"Relative launcher spelling {value} relies on one shell's path convention.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?=$|[.\s'\"/\\])", re.IGNORECASE):
        value = match.group(0)
        findings.append(
            make_finding(
                specs["AX-PATH-004"],
                source,
                context,
                line_index,
                value,
                tuple(target.id for target in context.targets if is_windows_target(target.id)),
                f"{value} is reserved by Windows and cannot be used safely as an ordinary filename.",
                severity=Severity.ERROR,
                confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<!\\)\\(?=[A-Za-z0-9_.-])"):
        if "\\n" in line or "\\t" in line:
            continue
        findings.append(
            make_finding(
                specs["AX-PATH-003"],
                source,
                context,
                line_index,
                match.group(0),
                non_windows,
                "Hardcoded backslash path separator assumes Windows path semantics.",
                severity=Severity.WARNING,
                confidence=Confidence.MEDIUM,
            )
        )
    findings.extend(_javascript_separator_findings(source, context, specs))
    return [finding for finding in findings if finding is not None]
