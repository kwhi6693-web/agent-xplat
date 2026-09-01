"""Auditable global and line-level finding suppression."""

from __future__ import annotations

import re

from .config import Config
from .models import Finding, SourceFile


_MARKER = re.compile(r"agent-xplat-ignore\s+((?:AX-[A-Z0-9-]+(?:\s*,\s*)?)+)", re.IGNORECASE)
_RULE = re.compile(r"AX-[A-Z0-9-]+", re.IGNORECASE)


def _line_suppressions(source: SourceFile) -> tuple[dict[int, set[str]], list[dict[str, object]]]:
    result: dict[int, set[str]] = {}
    markers: list[dict[str, object]] = []
    for line_index, line in enumerate(source.lines):
        marker = _MARKER.search(line)
        if not marker:
            continue
        rules = {rule.upper() for rule in _RULE.findall(marker.group(1))}
        result[line_index] = rules
        markers.append({"path": source.relative_path, "line": line_index + 1, "rules": sorted(rules), "used_rules": set()})
    return result, markers


def apply_suppressions(
    findings: list[Finding], sources: dict[str, SourceFile], config: Config
) -> tuple[list[Finding], list[dict[str, object]]]:
    global_rules = {rule_id.upper() for rule_id in config.ignore}
    parsed = {path: _line_suppressions(source) for path, source in sources.items()}
    line_rules = {path: value[0] for path, value in parsed.items()}
    marker_records = [marker for _, value in parsed.values() for marker in value]
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
            for marker in marker_records:
                if marker["path"] != finding.location.path:
                    continue
                marker_line = int(marker["line"]) - 1
                if marker_line in {line_index, line_index - 1} and finding.rule_id.upper() in marker["rules"]:
                    used_rules = marker["used_rules"]
                    if isinstance(used_rules, set):
                        used_rules.add(finding.rule_id.upper())
    diagnostics: list[dict[str, object]] = []
    for marker in marker_records:
        used_rules = marker["used_rules"]
        for rule_id in marker["rules"]:
            if not isinstance(used_rules, set) or rule_id in used_rules:
                continue
            diagnostics.append(
                {
                    "path": marker["path"],
                    "line": marker["line"],
                    "rule_id": rule_id,
                    "message": "suppression marker did not match a finding",
                }
            )
    return findings, diagnostics
