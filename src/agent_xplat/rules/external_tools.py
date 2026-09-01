"""External executable dependency detectors."""

from __future__ import annotations

import re

from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


TOOLS = r"Chrome|Chromium|Firefox|ffmpeg|ImageMagick|magick|LibreOffice|soffice|Docker|docker|Git|git|Java|java|Node|node|Python|python"


def _workflow_provisions_tool(source: SourceFile, tool: str) -> bool:
    """Avoid treating an explicit setup action as an unverified PATH assumption."""

    normalized = source.relative_path.replace("\\", "/")
    if not normalized.startswith(".github/workflows/"):
        return False
    action = {
        "python": r"uses\s*:\s*actions/setup-python@",
        "node": r"uses\s*:\s*actions/setup-node@",
    }.get(tool.lower())
    return bool(action and re.search(action, source.text, re.IGNORECASE))


def detect_external_tools(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, rf"(?<![A-Za-z0-9_])({TOOLS})(?![A-Za-z0-9_])"):
        tool = match.group(1)
        if _workflow_provisions_tool(source, tool):
            continue
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
