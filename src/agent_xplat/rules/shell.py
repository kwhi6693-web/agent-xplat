"""Shell command and shell-specific syntax detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows
from ..models import Confidence, Severity, Finding, SourceFile
from ..parsers import javascript_suffixes
from .common import RuleContext, RuleSpec, line_matches, make_finding


POSIX_COMMANDS = "grep|sed|awk|find|which|rm|cp|mv|touch|cat|head|tail|xargs|chown"


def _shell_like(line: str, source: SourceFile) -> bool:
    stripped = line.strip()
    if source.path.suffix.lower() in {".sh", ".bash", ".zsh", ".ps1", ".cmd", ".bat"} or "`" in line:
        return True
    if re.match(r"^(?:chmod|export|source|where|set|(?:grep|sed|awk|find|which|rm|cp|mv|touch|cat|head|tail|xargs|chown)\b|\$env:|[A-Za-z_][A-Za-z0-9_]*=)", stripped, re.IGNORECASE):
        return True
    return bool(re.search(r"(?:^|[|;&])\s*(?:grep|sed|awk|find|which|rm|cp|mv|touch|cat|head|tail|xargs|chown)\b", stripped, re.IGNORECASE))


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


def _native_windows(context: RuleContext) -> tuple[str, ...]:
    return tuple(target.id for target in context.targets if is_native_windows(target.id))


def detect_shell(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    # JavaScript-family source is analyzed by the binding-aware AST detector.
    # Treating member names such as ``cp.exec("cp ...")`` as shell commands
    # here would create a false positive outside an actual child-process call.
    if source.path.suffix.lower() in javascript_suffixes():
        return []
    findings: list[Finding] = []
    native_windows = _native_windows(context)
    for line_index, line, match in line_matches(source, r"\bchmod\s+(?:[+\-][rwxXst]+\s+)?[^\s`]+", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        findings.append(
            make_finding(
                specs["AX-SHELL-001"], source, context, line_index, "chmod", native_windows,
                "POSIX executable-bit command is unavailable in native Windows shells.",
                severity=Severity.BLOCKER, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, rf"\b(?:{POSIX_COMMANDS})\b", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        command = match.group(0)
        findings.append(
            make_finding(
                specs["AX-SHELL-002"], source, context, line_index, command, native_windows,
                f"POSIX utility {command} is not a native command in PowerShell or CMD.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"\bexport\s+[A-Za-z_][A-Za-z0-9_]*\s*=", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        findings.append(
            make_finding(
                specs["AX-SHELL-003"], source, context, line_index, "export", native_windows,
                "POSIX export syntax does not set process variables in native Windows shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"\$env:[A-Za-z_][A-Za-z0-9_]*", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        affected = tuple(target.id for target in context.targets if target.shell != "powershell")
        findings.append(
            make_finding(
                specs["AX-SHELL-004"], source, context, line_index, match.group(0), affected,
                "PowerShell environment-variable syntax is not interpreted by Bash, zsh, or CMD.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"%[A-Za-z_][A-Za-z0-9_]*%"):
        if not _shell_like(line, source):
            continue
        affected = tuple(target.id for target in context.targets if target.shell != "cmd")
        findings.append(
            make_finding(
                specs["AX-SHELL-005"], source, context, line_index, match.group(0), affected,
                "CMD percent-variable syntax is not portable to PowerShell or POSIX shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![\w.])(?:source\s+[^\s`]+|\.\s+[^\s`]+)", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        findings.append(
            make_finding(
                specs["AX-SHELL-006"], source, context, line_index, match.group(0).split()[0], native_windows,
                "POSIX shell source syntax is not available in native Windows shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![|])(?:&&|\|\|)(?![|])"):
        if not _shell_like(line, source):
            continue
        affected = tuple(target.id for target in context.targets if target.id == "windows-powershell")
        findings.append(
            make_finding(
                specs["AX-SHELL-007"], source, context, line_index, match.group(0), affected,
                "Command chaining syntax depends on PowerShell version and is not valid in Windows PowerShell 5.",
                severity=Severity.WARNING, confidence=Confidence.MEDIUM,
            )
        )
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)=[^\s]+(?=\s+[^=\s]+)"):
        if not _shell_like(line, source):
            continue
        prefix = line[: match.start()].rstrip().lower()
        if prefix.endswith(("export", "set", "$env:")):
            continue
        findings.append(
            make_finding(
                specs["AX-SHELL-003"], source, context, line_index, match.group(1), native_windows,
                "POSIX temporary environment assignment before a command is not accepted by native Windows shells.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
                metadata={"syntax": "temporary-environment-assignment"},
            )
        )
    for line_index, line, match in line_matches(source, r"\bwhere\s+(?:node|python|npm|git)\b", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        affected = tuple(target.id for target in context.targets if target.id != "windows-cmd")
        findings.append(
            make_finding(
                specs["AX-SHELL-008"], source, context, line_index, "where", affected,
                "The where command is a CMD/Windows lookup contract and conflicts with POSIX shells and PowerShell aliases.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r"\bset\s+[A-Za-z_][A-Za-z0-9_]*=", re.IGNORECASE):
        if not _shell_like(line, source):
            continue
        affected = tuple(target.id for target in context.targets if target.id != "windows-cmd")
        findings.append(
            make_finding(
                specs["AX-SHELL-009"], source, context, line_index, "set", affected,
                "CMD set syntax is not a portable environment-variable assignment in POSIX shells or PowerShell.",
                severity=Severity.ERROR, confidence=Confidence.HIGH,
            )
        )
    for line_index, line, match in line_matches(source, r";"):
        if not _shell_like(line, source) or not _is_unquoted(line, match.start()):
            continue
        if not line[match.end():].strip():
            continue
        finding = make_finding(
            specs["AX-SHELL-010"], source, context, line_index, ";", context.target_ids,
            "Semicolon command chaining has shell-specific parsing and error-propagation semantics.",
            severity=Severity.INFO, confidence=Confidence.LOW,
            metadata={"syntax": "semicolon-chain"},
        )
        if finding:
            findings.append(finding)
    return [finding for finding in findings if finding is not None]
