"""Operating-system-specific package-manager detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows, is_native_unix_target
from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


def detect_package_managers(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, r"\b(brew|apt-get|apt|dnf|yum|pacman|winget|choco|scoop)\b", re.IGNORECASE):
        manager = match.group(1).lower()
        if manager == "brew":
            affected = tuple(target.id for target in context.targets if not (target.os == "macos" and target.runtime == "native"))
        elif manager in {"apt", "apt-get", "dnf", "yum", "pacman"}:
            affected = tuple(target.id for target in context.targets if not (target.os == "linux" and target.runtime == "native"))
        else:
            affected = tuple(target.id for target in context.targets if not is_native_windows(target.id))
        finding = make_finding(
            specs["AX-PM-001"], source, context, line_index, manager, affected,
            f"Package manager {manager} is platform-specific and cannot be assumed on every target.",
            severity=Severity.ERROR, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    return findings
