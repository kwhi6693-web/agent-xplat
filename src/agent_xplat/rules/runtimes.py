"""Runtime-version and executable resolution detectors."""

from __future__ import annotations

import re

from ..models import Confidence, Severity, Finding, SourceFile
from ..parsers import javascript_suffixes
from .common import RuleContext, RuleSpec, line_matches, make_finding


def detect_runtimes(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    # A ``node:`` import or a JavaScript identifier is not an unversioned
    # shell/runtime command. Package scripts and workflow text remain covered.
    if source.path.suffix.lower() in javascript_suffixes():
        return []
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, r"\b(?:node|npm|npx|pnpm|yarn|bun)\b", re.IGNORECASE):
        if re.search(r"\b(?:node|npm|npx|pnpm|yarn|bun)\s+(?:--version|-v|v?\d+(?:\.\d+)*)\b", line, re.IGNORECASE):
            continue
        finding = make_finding(
            specs["AX-RUNTIME-001"], source, context, line_index, match.group(0), context.target_ids,
            f"Runtime command {match.group(0)} is assumed to be available without a declared version or capability check.",
            severity=Severity.INFO, confidence=Confidence.LOW,
        )
        if finding:
            findings.append(finding)
    return findings
