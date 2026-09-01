"""Structured JavaScript/TypeScript portability facts and findings."""

from __future__ import annotations

import ast as python_ast
import json
import re
from dataclasses import dataclass

from tree_sitter import Node

from ..models import Confidence, Finding, Severity, SourceFile
from ..parsers import ParsedJavaScript, iter_named_nodes, node_text, parse_javascript, source_location_for_node
from .common import RuleContext, RuleSpec


CHILD_PROCESS_APIS = frozenset({"exec", "execSync", "spawn", "spawnSync"})
_POSIX_COMMAND = re.compile(
    r"(?:^|[\s;&|])(?:sudo\s+)?(?:chmod|chown|grep|sed|awk|find|which|rm|cp|mv|touch|cat|head|tail|xargs)\b",
    re.IGNORECASE,
)
_POSIX_ENV_ASSIGNMENT = re.compile(r"(?:^|[\s;&|])[A-Za-z_][A-Za-z0-9_]*=(?=\S)")
_WINDOWS_SHELL = re.compile(
    r"(?:^|[\s/&|])(?:cmd(?:\.exe)?(?:\s|$)|powershell(?:\.exe)?(?:\s|$)|pwsh(?:\.exe)?(?:\s|$))",
    re.IGNORECASE,
)
_POSIX_SHELL = re.compile(
    r"(?:^|[\s/&|])(?:bash|sh)(?:\.exe)?(?:\s|$|-c)",
    re.IGNORECASE,
)
_PLATFORM_TO_OS = {"win32": "windows", "darwin": "macos", "linux": "linux"}


@dataclass(frozen=True)
class _Bindings:
    module_aliases: frozenset[str]
    api_aliases: dict[str, str]


def _string_value(parsed: ParsedJavaScript, node: Node | None) -> str | None:
    if node is None or node.type not in {"string", "template_string"}:
        return None
    raw = node_text(parsed, node)
    if node.type == "template_string":
        return raw[1:-1] if len(raw) >= 2 else ""
    try:
        value = json.loads(raw) if raw.startswith('"') else python_ast.literal_eval(raw)
        return value if isinstance(value, str) else None
    except (SyntaxError, ValueError, json.JSONDecodeError):
        return raw[1:-1] if len(raw) >= 2 else raw


def _is_child_process_module(value: str | None) -> bool:
    return value in {"child_process", "node:child_process"}


def _require_module(parsed: ParsedJavaScript, node: Node | None) -> str | None:
    if node is None or node.type != "call_expression":
        return None
    function = node.child_by_field_name("function")
    if function is None or node_text(parsed, function) != "require":
        return None
    arguments = node.child_by_field_name("arguments")
    if arguments is None or not arguments.named_children:
        return None
    return _string_value(parsed, arguments.named_children[0])


def _register_object_pattern(parsed: ParsedJavaScript, pattern: Node, api_aliases: dict[str, str]) -> None:
    for child in pattern.named_children:
        if child.type == "shorthand_property_identifier_pattern":
            name = node_text(parsed, child)
            if name in CHILD_PROCESS_APIS:
                api_aliases[name] = name
        elif child.type == "pair_pattern":
            key = child.child_by_field_name("key")
            value = child.child_by_field_name("value")
            key_name = node_text(parsed, key) if key is not None else ""
            local_name = node_text(parsed, value) if value is not None else ""
            if key_name in CHILD_PROCESS_APIS and local_name:
                api_aliases[local_name] = key_name


def _bindings(parsed: ParsedJavaScript) -> _Bindings:
    module_aliases: set[str] = set()
    api_aliases: dict[str, str] = {}
    for statement in iter_named_nodes(parsed, "import_statement"):
        source_node = statement.child_by_field_name("source")
        if not _is_child_process_module(_string_value(parsed, source_node)):
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
                    if imported in CHILD_PROCESS_APIS and local:
                        api_aliases[local] = imported

    for declaration in iter_named_nodes(parsed, "variable_declarator"):
        value = declaration.child_by_field_name("value")
        name = declaration.child_by_field_name("name")
        required_module = _require_module(parsed, value)
        if _is_child_process_module(required_module) and name is not None:
            if name.type == "identifier":
                module_aliases.add(node_text(parsed, name))
            elif name.type == "object_pattern":
                _register_object_pattern(parsed, name, api_aliases)
            continue
        if value is None or value.type != "member_expression" or name is None or name.type != "identifier":
            continue
        object_node = value.child_by_field_name("object")
        property_node = value.child_by_field_name("property")
        if _is_child_process_module(_require_module(parsed, object_node)) and property_node is not None:
            property_name = node_text(parsed, property_node)
            if property_name in CHILD_PROCESS_APIS:
                api_aliases[node_text(parsed, name)] = property_name
    return _Bindings(frozenset(module_aliases), api_aliases)


def _callee_api(parsed: ParsedJavaScript, call: Node, bindings: _Bindings) -> str | None:
    function = call.child_by_field_name("function")
    if function is None:
        return None
    if function.type == "identifier":
        return bindings.api_aliases.get(node_text(parsed, function))
    if function.type != "member_expression":
        return None
    object_node = function.child_by_field_name("object")
    property_node = function.child_by_field_name("property")
    if property_node is None:
        return None
    property_name = node_text(parsed, property_node)
    if property_name not in CHILD_PROCESS_APIS:
        return None
    if object_node is not None and object_node.type == "identifier" and node_text(parsed, object_node) in bindings.module_aliases:
        return property_name
    if _is_child_process_module(_require_module(parsed, object_node)):
        return property_name
    return None


def _arguments(call: Node) -> tuple[Node, ...]:
    arguments = call.child_by_field_name("arguments")
    return tuple(arguments.named_children) if arguments is not None else ()


def _shell_true(parsed: ParsedJavaScript, call: Node) -> bool:
    for argument in _arguments(call):
        if argument.type != "object":
            continue
        for pair in argument.named_children:
            if pair.type != "pair":
                continue
            key = pair.child_by_field_name("key")
            value = pair.child_by_field_name("value")
            if key is not None and value is not None and node_text(parsed, key) == "shell" and node_text(parsed, value).lower() == "true":
                return True
    return False


def _contains(ancestor: Node | None, descendant: Node) -> bool:
    return ancestor is not None and ancestor.start_byte <= descendant.start_byte and descendant.end_byte <= ancestor.end_byte


def _if_has_fallback(node: Node | None) -> bool:
    if node is None or node.type != "if_statement":
        return node is not None
    alternative = node.child_by_field_name("alternative")
    if alternative is None:
        return False
    nested = next((child for child in alternative.named_children if child.type == "if_statement"), None)
    return _if_has_fallback(nested) if nested is not None else True


def _unwrap_expression(node: Node | None) -> Node | None:
    while node is not None and node.type in {"parenthesized_expression", "as_expression", "type_assertion"}:
        named = node.named_children
        node = named[0] if named else None
    return node


def _platform_member(node: Node | None, parsed: ParsedJavaScript) -> bool:
    return node is not None and node.type == "member_expression" and node_text(parsed, node).strip() == "process.platform"


def _binary_operator(node: Node) -> str | None:
    return next(
        (child.type for child in node.children if not child.is_named and child.type in {"===", "!==", "==", "!="}),
        None,
    )


def _is_platform_guarded(node: Node, parsed: ParsedJavaScript) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type == "if_statement":
            condition = parent.child_by_field_name("condition")
            if _contains(parent, node) and _platform_condition(condition, parsed) is not None and _if_has_fallback(parent):
                return True
        elif parent.type in {"ternary_expression", "conditional_expression"}:
            condition = parent.child_by_field_name("condition")
            if _contains(parent, node) and _platform_condition(condition, parsed) is not None:
                return True
        parent = parent.parent
    return False


def _platform_condition(condition: Node | None, parsed: ParsedJavaScript) -> tuple[str, str] | None:
    condition = _unwrap_expression(condition)
    if condition is None or condition.type != "binary_expression":
        return None
    operator = _binary_operator(condition)
    left = _unwrap_expression(condition.child_by_field_name("left"))
    right = _unwrap_expression(condition.child_by_field_name("right"))
    if operator is None or left is None or right is None:
        return None
    if _platform_member(left, parsed):
        platform_name = _string_value(parsed, right)
    elif _platform_member(right, parsed):
        platform_name = _string_value(parsed, left)
    else:
        return None
    if platform_name not in _PLATFORM_TO_OS:
        return None
    return operator, platform_name


def _branch_targets(parsed: ParsedJavaScript, node: Node, context: RuleContext) -> tuple[str, ...]:
    allowed = set(context.target_ids)
    target_by_id = {target.id: target for target in context.targets}
    parent = node.parent
    while parent is not None:
        branch: bool | None = None
        condition: Node | None = None
        if parent.type == "if_statement":
            condition = parent.child_by_field_name("condition")
            if _contains(parent.child_by_field_name("consequence"), node):
                branch = True
            elif _contains(parent.child_by_field_name("alternative"), node):
                branch = False
        elif parent.type in {"ternary_expression", "conditional_expression"}:
            condition = parent.child_by_field_name("condition")
            if _contains(parent.child_by_field_name("consequence"), node):
                branch = True
            elif _contains(parent.child_by_field_name("alternative"), node):
                branch = False
        if branch is not None:
            platform_condition = _platform_condition(condition, parsed)
            if platform_condition is not None:
                operator, platform_name = platform_condition
                is_condition_true = operator == "==="
                branch_matches_os = is_condition_true if branch else not is_condition_true
                os_name = _PLATFORM_TO_OS[platform_name]
                allowed = {
                    target_id
                    for target_id in allowed
                    if (_runtime_os(target_by_id[target_id]) == os_name) == branch_matches_os
                }
        parent = parent.parent
    return tuple(target.id for target in context.targets if target.id in allowed)


def _runtime_os(target) -> str:
    """Return the OS exposed to a Node process for one matrix target."""

    return "linux" if target.runtime == "wsl" else target.os


def _node_windows_targets(context: RuleContext) -> tuple[str, ...]:
    """Windows runtimes whose Node process uses Windows child-process semantics."""

    return tuple(
        target.id
        for target in context.targets
        if target.os == "windows" and target.runtime in {"native", "git-bash"}
    )


def _node_finding(
    spec: RuleSpec,
    source: SourceFile,
    parsed: ParsedJavaScript,
    node: Node,
    affected: tuple[str, ...],
    reason: str,
    *,
    severity: Severity | None = None,
    confidence: Confidence | None = None,
    metadata: dict | None = None,
) -> Finding | None:
    if not affected:
        return None
    location = source_location_for_node(source, node)
    code = source.lines[location.line - 1].strip() if location.line <= len(source.lines) else ""
    effective_confidence = confidence or spec.confidence
    if parsed.syntax_error is not None and effective_confidence == Confidence.HIGH:
        effective_confidence = Confidence.MEDIUM
    return Finding(
        rule_id=spec.rule_id,
        title=spec.title,
        description=spec.description,
        location=location,
        severity=severity or spec.severity,
        confidence=effective_confidence,
        affected_targets=affected,
        reason=reason,
        remediation=spec.remediation,
        examples=spec.examples,
        code=code,
        metadata={
            "severity_rationale": spec.severity_rationale,
            "confidence_rationale": spec.confidence_rationale,
            "analysis": "tree-sitter-ast",
            "language": parsed.language,
            **({"syntax_recovery": parsed.syntax_error} if parsed.syntax_error else {}),
            **(metadata or {}),
        },
    )


def _command_strings(parsed: ParsedJavaScript, call: Node) -> tuple[tuple[Node, str], ...]:
    values: list[tuple[Node, str]] = []
    for argument in _arguments(call):
        value = _string_value(parsed, argument)
        if value is not None:
            values.append((argument, value))
    return tuple(values[:1])


def _is_windows_executable(value: str) -> bool:
    lowered = value.lower().strip()
    return bool(
        re.search(r"(?:^|[\\/])(?:cmd|powershell|pwsh)(?:\.exe)?(?:$|\s)", lowered)
        or re.search(r"(?:^|[\\/])[^\\/\s]+\.cmd(?:$|\s)", lowered)
        or re.match(r"^[a-z]:[\\/]", lowered)
        or lowered.startswith("\\\\")
    )


def _is_posix_executable(value: str) -> bool:
    lowered = value.lower().strip()
    return bool(
        re.search(r"(?:^|[\\/])(?:bash|sh)(?:\.exe)?(?:$|\s|-c)", lowered)
        or re.search(r"(?:^|[\\/])[^\\/\s]+\.sh(?:$|\s)", lowered)
        or lowered.startswith(("/bin/", "/sbin/", "/usr/", "/opt/", "/applications/", "/tmp/"))
    )


def _has_environment_fallback(node: Node, parsed: ParsedJavaScript) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type == "binary_expression":
            text = node_text(parsed, parent)
            if "??" in text or "||" in text:
                return True
        if parent.type in {"expression_statement", "program", "statement_block", "lexical_declaration", "variable_declarator", "return_statement"}:
            break
        parent = parent.parent
    return False


def detect_node_ast(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    parsed = parse_javascript(source)
    if parsed.tree is None:
        return []
    bindings = _bindings(parsed)
    findings: list[Finding] = []
    native_windows = _node_windows_targets(context)
    non_windows = tuple(target.id for target in context.targets if target.id not in native_windows)

    for call in iter_named_nodes(parsed, "call_expression"):
        api = _callee_api(parsed, call, bindings)
        if api is None:
            continue
        branch_targets = _branch_targets(parsed, call, context)
        command_values = _command_strings(parsed, call)
        if _shell_true(parsed, call):
            finding = _node_finding(
                specs["AX-NODE-005"], source, parsed, call, branch_targets,
                f"child_process.{api} enables shell parsing; the default shell and quoting contract vary by OS and target shell.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
                metadata={"api": api, "shell": True},
            )
            if finding:
                findings.append(finding)
        if not command_values:
            continue
        command_node, command = command_values[0]
        if _POSIX_COMMAND.search(command) or _POSIX_ENV_ASSIGNMENT.search(command):
            affected = tuple(target_id for target_id in branch_targets if target_id in native_windows)
            reason = (
                f"child_process.{api} embeds a POSIX inline environment assignment ({command.strip()[:80]}) that is unavailable in native Windows shells."
                if _POSIX_ENV_ASSIGNMENT.search(command) and not _POSIX_COMMAND.search(command)
                else f"child_process.{api} embeds POSIX command syntax ({command.strip()[:80]}) that is unavailable in native Windows shells."
            )
            finding = _node_finding(
                specs["AX-NODE-005"], source, parsed, call, affected,
                reason,
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"api": api, "command": command},
            )
            if finding:
                findings.append(finding)
        elif _WINDOWS_SHELL.search(command):
            affected = tuple(target_id for target_id in branch_targets if target_id in non_windows)
            finding = _node_finding(
                specs["AX-NODE-005"], source, parsed, call, affected,
                f"child_process.{api} invokes a Windows-specific shell command ({command.strip()[:80]}).",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"api": api, "command": command},
            )
            if finding:
                findings.append(finding)
        elif _POSIX_SHELL.search(command):
            affected = tuple(target_id for target_id in branch_targets if target_id in native_windows)
            finding = _node_finding(
                specs["AX-NODE-005"], source, parsed, call, affected,
                f"child_process.{api} invokes a POSIX shell ({command.strip()[:80]}) that is not guaranteed in native Windows shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"api": api, "command": command},
            )
            if finding:
                findings.append(finding)
        if _is_windows_executable(command):
            affected = tuple(target_id for target_id in branch_targets if target_id in non_windows)
            finding = _node_finding(
                specs["AX-NODE-008"], source, parsed, command_node, affected,
                f"child_process.{api} uses a hardcoded Windows executable or path ({command.strip()[:80]}).",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"api": api, "command": command, "kind": "windows-executable"},
            )
            if finding:
                findings.append(finding)
        elif _is_posix_executable(command):
            affected = tuple(target_id for target_id in branch_targets if target_id in native_windows)
            finding = _node_finding(
                specs["AX-NODE-008"], source, parsed, command_node, affected,
                f"child_process.{api} uses a hardcoded POSIX executable or path ({command.strip()[:80]}).",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"api": api, "command": command, "kind": "posix-executable"},
            )
            if finding:
                findings.append(finding)
        elif "\\" in command:
            affected = tuple(target_id for target_id in branch_targets if target_id in non_windows)
            finding = _node_finding(
                specs["AX-NODE-008"], source, parsed, command_node, affected,
                f"child_process.{api} embeds a backslash path separator that assumes Windows path semantics.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
                metadata={"api": api, "command": command, "kind": "separator"},
            )
            if finding:
                findings.append(finding)

    for member in iter_named_nodes(parsed, "member_expression"):
        if node_text(parsed, member).strip() != "process.platform" or _is_platform_guarded(member, parsed):
            continue
        finding = _node_finding(
            specs["AX-NODE-007"], source, parsed, member, context.target_ids,
            "process.platform drives OS-specific behavior without a complete alternate branch that static analysis can verify.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            metadata={"kind": "platform-branch"},
        )
        if finding:
            findings.append(finding)

    environment_nodes = (*iter_named_nodes(parsed, "member_expression"), *iter_named_nodes(parsed, "subscript_expression"))
    for member in environment_nodes:
        text = node_text(parsed, member).strip()
        if member.type == "member_expression":
            object_node = member.child_by_field_name("object")
            direct_access = object_node is not None and node_text(parsed, object_node).strip() == "process.env"
        else:
            object_node = member.child_by_field_name("object")
            direct_access = object_node is not None and node_text(parsed, object_node).strip() == "process.env"
        if not direct_access or _has_environment_fallback(member, parsed):
            continue
        finding = _node_finding(
            specs["AX-NODE-006"], source, parsed, member, context.target_ids,
            "process.env is read without a visible fallback or declaration; behavior depends on host-provided environment state.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            metadata={"kind": "environment-read", "access": text},
        )
        if finding:
            findings.append(finding)
    return findings
