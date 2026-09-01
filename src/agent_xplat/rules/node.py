"""Node.js and package-script portability detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows
from ..models import Confidence, Severity, Finding, SourceFile
from ..parsers import parse_json
from .common import RuleContext, RuleSpec, line_matches, make_finding


def detect_node(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    if source.path.name != "package.json":
        return []
    document = parse_json(source)
    if not isinstance(document, dict):
        return []
    native_windows = tuple(target.id for target in context.targets if is_native_windows(target.id))
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, r"\"(better-sqlite3|sharp|node-gyp|canvas|fsevents)\"\s*:"):
        finding = make_finding(
            specs["AX-NODE-004"], source, context, line_index, match.group(1), context.target_ids,
            f"Native Node package {match.group(1)} may require a platform-specific binary or build toolchain.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    if not isinstance(document.get("scripts"), dict):
        return findings
    for line_index, line, match in line_matches(source, r"\b[A-Za-z_][A-Za-z0-9_]*=(?:[^\s\"']+|['\"][^'\"]+['\"])(?=\s+(?:node|npm|npx|pnpm|yarn|bun)\b)"):
        finding = make_finding(
            specs["AX-NODE-001"], source, context, line_index, match.group(0).split("=", 1)[0], native_windows,
            "POSIX inline environment assignment in an npm script is not accepted by native Windows shells.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(?:rm|cp|mv|chmod|grep|sed|awk|find)\b", re.IGNORECASE):
        finding = make_finding(
            specs["AX-NODE-002"], source, context, line_index, match.group(0), native_windows,
            f"POSIX command {match.group(0)} in package.json scripts assumes a Unix shell.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?:^|[\s\"'])\./[^\s\"']+\.(?:sh|cmd)\b|node_modules[\\/]\.bin[\\/]"):
        finding = make_finding(
            specs["AX-NODE-003"], source, context, line_index, match.group(0).strip(), native_windows,
            "Package script assumes a POSIX executable or separator instead of a package-manager-neutral command.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    return findings
