"""Node.js and package-script portability detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows
from ..models import Confidence, Severity, Finding, SourceFile
from ..parsers import json_object_member_key_spans, json_object_string_spans, parse_json
from .common import RuleContext, RuleSpec, line_matches, make_finding
from .node_ast import detect_node_ast


def detect_node(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    if source.path.name != "package.json":
        from ..parsers import javascript_suffixes

        return detect_node_ast(source, context, specs) if source.path.suffix.lower() in javascript_suffixes() else []
    document = parse_json(source)
    if not isinstance(document, dict):
        return []
    native_windows = tuple(target.id for target in context.targets if is_native_windows(target.id))
    findings: list[Finding] = []
    native_packages = {"better-sqlite3", "sharp", "node-gyp", "canvas", "fsevents"}
    for span in json_object_member_key_spans(
        source,
        ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"),
    ):
        if span.key not in native_packages:
            continue
        line_index = source.text.count("\n", 0, span.start)
        line = source.lines[line_index] if line_index < len(source.lines) else ""
        line_start = source.text.rfind("\n", 0, span.start) + 1
        finding = make_finding(
            specs["AX-NODE-004"], source, context, line_index, span.key, context.target_ids,
            f"Native Node package {span.key} may require a platform-specific binary or build toolchain.",
            column=span.start - line_start + 1,
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    if not isinstance(document.get("scripts"), dict):
        return findings
    for line_index, line, match, column in _scoped_matches(source, "scripts", r"\b[A-Za-z_][A-Za-z0-9_]*=(?:[^\s\"']+|['\"][^'\"]+['\"])(?=\s+(?:node|npm|npx|pnpm|yarn|bun)\b)"):
        finding = make_finding(
            specs["AX-NODE-001"], source, context, line_index, match.group(0).split("=", 1)[0], native_windows,
            "POSIX inline environment assignment in an npm script is not accepted by native Windows shells.",
            column=column,
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match, column in _scoped_matches(source, "scripts", r"(?<![A-Za-z0-9_])(?:rm|cp|mv|chmod|grep|sed|awk|find)\b", re.IGNORECASE):
        finding = make_finding(
            specs["AX-NODE-002"], source, context, line_index, match.group(0), native_windows,
            f"POSIX command {match.group(0)} in package.json scripts assumes a Unix shell.",
            column=column,
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match, column in _scoped_matches(source, "scripts", r"(?:^|[\s\"'])\./[^\s\"']+\.(?:sh|cmd)\b|node_modules[\\/]\.bin[\\/]"):
        finding = make_finding(
            specs["AX-NODE-003"], source, context, line_index, match.group(0).strip(), native_windows,
            "Package script assumes a POSIX executable or separator instead of a package-manager-neutral command.",
            column=column,
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    powershell_legacy = tuple(target.id for target in context.targets if target.id == "windows-powershell")
    for line_index, line, match, column in _scoped_matches(source, "scripts", r"(?<!\|)(?:&&|\|\|)(?!\|)"):
        finding = make_finding(
            specs["AX-SHELL-007"], source, context, line_index, match.group(0), powershell_legacy,
            "Package-script command chaining depends on the PowerShell version when invoked through a native Windows shell.",
            column=column,
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            metadata={"syntax": "package-script-chain"},
        )
        if finding:
            findings.append(finding)
    for line_index, line, match, column in _scoped_matches(source, "scripts", r";"):
        finding = make_finding(
            specs["AX-SHELL-010"], source, context, line_index, match.group(0), context.target_ids,
            "Semicolon command chaining in a package script has shell-specific parsing and error-propagation semantics.",
            column=column,
            severity=Severity.INFO, confidence=Confidence.LOW,
            metadata={"syntax": "package-script-chain"},
        )
        if finding:
            findings.append(finding)
    return findings


def _scoped_matches(source: SourceFile, object_key: str, pattern: str, flags: int = 0):
    """Match only decoded-string members of a parsed JSON object."""
    compiled = re.compile(pattern, flags)
    for span in json_object_string_spans(source, object_key):
        raw = source.text[span.start : span.end]
        for match in compiled.finditer(raw):
            absolute = span.start + match.start()
            line_index = source.text.count("\n", 0, absolute)
            line = source.lines[line_index] if line_index < len(source.lines) else ""
            line_start = source.text.rfind("\n", 0, absolute) + 1
            yield line_index, line, match, absolute - line_start + 1
