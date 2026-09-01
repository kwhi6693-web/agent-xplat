"""Auditable global and line-level finding suppression."""

from __future__ import annotations

import re

from .config import Config
from .models import Finding, SourceFile


_MARKER = re.compile(r"agent-xplat-ignore\s+((?:AX-[A-Z0-9-]+(?:\s*,\s*)?)+)", re.IGNORECASE)
_RULE = re.compile(r"AX-[A-Z0-9-]+", re.IGNORECASE)


def _line_suppressions(source: SourceFile) -> dict[int, set[str]]:
    result: dict[int, set[str]] = {}
    for line_index, line in enumerate(source.lines):
        marker = _MARKER.search(line)
        if not marker:
            continue
        result[line_index] = {rule.upper() for rule in _RULE.findall(marker.group(1))}
    return result


def apply_suppressions(findings: list[Finding], sources: dict[str, SourceFile], config: Config) -> list[Finding]:
    global_rules = {rule_id.upper() for rule_id in config.ignore}
    line_rules = {path: _line_suppressions(source) for path, source in sources.items()}
    for finding in findings:
        if finding.rule_id.upper() in global_rules:
            finding.ignored = True
            finding.suppression_reason = "global config ignore"
            continue
        lines = line_rules.get(finding.location.path, {})
        line_index = finding.location.line - 1
        matching = lines.get(line_index, set()) | lines.get(line_index - 1, set())
        if finding.rule_id.upper() in matching:
            finding.ignored = True
            finding.suppression_reason = "line suppression marker"
    return findings
