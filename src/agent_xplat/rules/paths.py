"""Filesystem path assumption detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows, is_windows_target
from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


def _native_windows(context: RuleContext) -> tuple[str, ...]:
    return tuple(target.id for target in context.targets if is_native_windows(target.id))


def _non_windows(context: RuleContext) -> tuple[str, ...]:
    return tuple(target.id for target in context.targets if not is_windows_target(target.id))


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
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\)[^\s'\"`]+"):
        value = match.group(0)
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
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_$%:])(?:Program Files|AppData|%USERPROFILE%|\$env:USERPROFILE|USERPROFILE)(?![A-Za-z0-9_])", re.IGNORECASE):
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
    for line_index, line, match in line_matches(source, r"(?<![A-Za-z0-9_])(?:~/|\$HOME(?:/|\\)|\$USER(?:/|\\))"):
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
    return [finding for finding in findings if finding is not None]
