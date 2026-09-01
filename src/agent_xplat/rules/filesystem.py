"""Filesystem behavior and line-ending detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows, is_posix_shell, is_windows_target
from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


def detect_filesystem(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    if source.is_crlf and source.lines and source.lines[0].startswith("#!"):
        affected = tuple(target.id for target in context.targets if is_posix_shell(target.id))
        finding = make_finding(
            specs["AX-FS-001"], source, context, 0, "#!", affected,
            "CRLF after a shebang can make the interpreter path include a carriage return on POSIX systems.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"\b(?:ln\s+-s|mklink|SymbolicLink|Junction)\b", re.IGNORECASE):
        finding = make_finding(
            specs["AX-FS-002"], source, context, line_index, match.group(0), context.target_ids,
            "Symlink or junction creation has different permissions and availability across OS/filesystems.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"\b(?:flock|fcntl\.flock|LockFileEx|msvcrt\.locking)\b", re.IGNORECASE):
        finding = make_finding(
            specs["AX-FS-003"], source, context, line_index, match.group(0), context.target_ids,
            "File-locking API is platform-specific and needs an OS-neutral abstraction.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"\b(?:rename|replace)\b.*\b(?:atomic|lock|open)\b", re.IGNORECASE):
        finding = make_finding(
            specs["AX-FS-004"], source, context, line_index, match.group(0).split()[0], context.target_ids,
            "Atomic rename and open-file behavior differs when another process holds the destination.",
            severity=Severity.INFO, confidence=Confidence.LOW,
        )
        if finding:
            findings.append(finding)
    return findings
