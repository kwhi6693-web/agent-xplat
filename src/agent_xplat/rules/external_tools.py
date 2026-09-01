"""External executable dependency detectors."""

from __future__ import annotations

import re

from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


TOOLS = r"Chrome|Chromium|Firefox|ffmpeg|ImageMagick|magick|LibreOffice|soffice|Docker|docker|Git|git|Java|java|Node|node|Python|python"


def detect_external_tools(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, rf"(?<![A-Za-z0-9_])({TOOLS})(?![A-Za-z0-9_])"):
        tool = match.group(1)
        if tool.lower() in {"node", "git", "python", "java"} and re.search(r"(?:package|requires?|version|runtime|install|command|which|where)", line, re.IGNORECASE) is None:
            continue
        finding = make_finding(
            specs["AX-TOOL-001"], source, context, line_index, tool, context.target_ids,
            f"External tool {tool} is assumed to be on PATH; static analysis cannot prove installation or version.",
            severity=Severity.WARNING, confidence=Confidence.MEDIUM,
        )
        if finding:
            findings.append(finding)
    return findings
