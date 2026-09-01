"""AI-agent instruction/configuration portability detectors."""

from __future__ import annotations

import re

from ..environments import is_native_windows
from ..models import Confidence, Severity, Finding, SourceFile
from .common import RuleContext, RuleSpec, line_matches, make_finding


AGENT_NAMES = {"SKILL.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "copilot-instructions.md"}


def detect_agent_config(source: SourceFile, context: RuleContext, specs: dict[str, RuleSpec]) -> list[Finding]:
    if source.path.name not in AGENT_NAMES and not any(part in {".cursor", ".claude", ".codex"} for part in source.path.parts):
        return []
    findings: list[Finding] = []
    for line_index, line, match in line_matches(source, r"\b(?:shell|terminal)\s*:\s*(bash|zsh|powershell|cmd)\b", re.IGNORECASE):
        shell = match.group(1).lower()
        if shell in {"bash", "zsh"}:
            affected = tuple(target.id for target in context.targets if is_native_windows(target.id))
            reason = f"Agent configuration requires {shell}, which is not a native Windows shell."
        else:
            affected = tuple(target.id for target in context.targets if target.shell not in {shell})
            reason = f"Agent configuration requires {shell}; other target shells need an explicit launcher or fallback."
        finding = make_finding(
            specs["AX-AGENT-001"], source, context, line_index, shell, affected, reason,
            severity=Severity.WARNING, confidence=Confidence.HIGH,
        )
        if finding:
            findings.append(finding)
    return findings
