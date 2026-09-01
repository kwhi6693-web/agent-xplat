"""Command substitution, interpolation, and chaining ambiguity detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows
from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


SHELL_SUFFIXES = {".sh", ".bash", ".zsh", ".ps1", ".cmd", ".bat"}


def _shell_like(line: str, source: SourceFile) -> bool:
    stripped = line.strip()
    if source.path.suffix.lower() in SHELL_SUFFIXES or "`" in line:
        return True
    return bool(re.match(r"^(?:echo|printf|set|export|source|chmod|python|python3|node|npm|npx|pnpm|yarn|bun|[A-Za-z_][A-Za-z0-9_]*=)", stripped, re.IGNORECASE))


def _is_unquoted(line: str, position: int) -> bool:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if index == position:
            return quote is None and not escaped
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote != '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
    return quote is None and not escaped


def detect_quoting(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    native_windows = tuple(target.id for target in context.targets if is_native_windows(target.id))
    for line_index, line, match in line_matches(source, r"\$\{[A-Za-z_][A-Za-z0-9_]*\}"):
        findings.append(
            make_finding(
                specs["AX-QUOTE-001"], source, context, line_index, match.group(0), native_windows,
                "Brace-style POSIX variable interpolation is not valid in native Windows shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"\$\([^\n)]+\)"):
        affected = tuple(target.id for target in context.targets if target.shell in {"cmd"})
        findings.append(
            make_finding(
                specs["AX-QUOTE-002"], source, context, line_index, match.group(0), affected,
                "Command substitution is not available in CMD and may require a shell-specific launcher.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"\\$"):
        findings.append(
            make_finding(
                specs["AX-QUOTE-003"], source, context, line_index, match.group(0), native_windows,
                "Backslash line continuation has different meanings in PowerShell and POSIX shells.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![\w$])\$[A-Za-z_][A-Za-z0-9_]*"):
        affected = tuple(target.id for target in context.targets if target.shell == "cmd")
        findings.append(
            make_finding(
                specs["AX-QUOTE-004"], source, context, line_index, match.group(0), affected,
                "Dollar-variable interpolation is not supported by CMD.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?:\d?>|<)\s*/dev/null\b|<<<"):
        affected = tuple(target.id for target in context.targets if target.shell in {"powershell", "cmd"})
        finding = make_finding(
            specs["AX-QUOTE-005"], source, context, line_index, match.group(0), affected,
            "POSIX redirection to /dev/null or a Bash here-string is not portable to native Windows shells.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
            metadata={"syntax": "posix-redirection"},
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"\^(?:[&|<>^])"):
        if not _is_unquoted(line, match.start()):
            continue
        affected = tuple(target.id for target in context.targets if target.shell != "cmd")
        finding = make_finding(
            specs["AX-QUOTE-006"], source, context, line_index, match.group(0), affected,
            "CMD caret escaping is interpreted differently by PowerShell and POSIX shells.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            metadata={"syntax": "cmd-escape"},
        )
        if finding:
            findings.append(finding)
    for line_index, line, match in line_matches(source, r"(?<!\|)\|(?!\|)"):
        if not _shell_like(line, source) or not _is_unquoted(line, match.start()):
            continue
        affected = tuple(target.id for target in context.targets if target.os == "windows")
        finding = make_finding(
            specs["AX-QUOTE-007"], source, context, line_index, "|", affected,
            "Pipeline behavior is shell-specific; PowerShell passes objects while Bash/CMD pass text.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            metadata={"syntax": "pipeline"},
        )
        if finding:
            findings.append(finding)
    return [finding for finding in findings if finding is not None]
