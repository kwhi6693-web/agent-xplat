"""Terminal, JSON, Markdown, and SARIF renderers."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .models import Finding, ScanResult, Severity
from .rules.registry import all_rules, get_rule


def render_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _sarif_level(severity: Severity) -> str:
    if severity in {Severity.BLOCKER, Severity.ERROR}:
        return "error"
    if severity == Severity.WARNING:
        return "warning"
    return "note"


def render_sarif(result: ScanResult) -> str:
    used = {finding.rule_id for finding in result.active_findings}
    rules = []
    for spec in all_rules():
        if spec.rule_id not in used:
            continue
        rules.append(
            {
                "id": spec.rule_id,
                "name": spec.title,
                "shortDescription": {"text": spec.description},
                "help": {"text": f"{spec.remediation} Severity: {spec.severity.value}. Confidence: {spec.confidence.value}."},
                "helpUri": f"docs/RULES.md#{spec.rule_id.lower()}",
                "properties": {
                    "severity": spec.severity.value,
                    "confidence": spec.confidence.value,
                    "affectedEnvironments": list(spec.affected_environments),
                },
            }
        )
    results = []
    for finding in result.active_findings:
        result_item = {
            "ruleId": finding.rule_id,
            "level": _sarif_level(finding.severity),
            "message": {"text": f"{finding.reason} Suggested remediation: {finding.remediation}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.location.path},
                        "region": {
                            "startLine": finding.location.line,
                            "startColumn": finding.location.column,
                            **({"endLine": finding.location.end_line} if finding.location.end_line else {}),
                            **({"endColumn": finding.location.end_column} if finding.location.end_column else {}),
                        },
                    }
                }
            ],
            "help": {"text": finding.remediation},
            "partialFingerprints": {"primaryLocationLineHash": finding.fingerprint},
            "properties": {
                "severity": finding.severity.value,
                "confidence": finding.confidence.value,
                "affectedTargets": list(finding.affected_targets),
            },
        }
        results.append(result_item)
    document = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "agent-xplat", "semanticVersion": result.tool_version, "rules": rules}},
                "results": results,
                "invocations": [{"executionSuccessful": True}],
            }
        ],
    }
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _matrix_lines(result: ScanResult) -> list[str]:
    lines = ["| Environment | Score | Status | Findings |", "|---|---:|---|---:|"]
    for target in result.targets:
        score = result.scores[target.id]
        lines.append(f"| {target.display_name} | {score.score}/100 | {score.status} | {score.findings} |")
    return lines


def render_markdown(result: ScanResult) -> str:
    active = result.active_findings
    blocking = [finding for finding in active if finding.severity in {Severity.BLOCKER, Severity.ERROR}]
    warnings = [finding for finding in active if finding.severity == Severity.WARNING]
    grouped: dict[str, list[str]] = defaultdict(list)
    for finding in active:
        grouped[finding.location.path].append(f"{finding.location.line}:{finding.location.column} {finding.rule_id}")
    lines = [
        "# Agent Xplat Report",
        "",
        "## Executive Summary",
        "",
        f"Scanned **{result.summary.get('files_scanned', 0)}** files and found **{len(active)}** active portability issues. Static results are **INFERRED**; runtime evidence is **{result.verification.get('status', 'INFERRED')}**.",
        "",
        "## Compatibility Matrix",
        "",
        *_matrix_lines(result),
        "",
        "## Blocking Issues",
        "",
        *_finding_markdown(blocking),
        "",
        "## Warnings",
        "",
        *_finding_markdown(warnings),
        "",
        "## Environment Assumptions",
        "",
        "Findings are mapped to OS × Shell × Runtime targets; untested runtime availability is not treated as proof.",
        "",
        "## Contract Violations",
        "",
        *_contract_markdown(result),
        "",
        "## Affected Files",
        "",
        *([f"- `{path}` — {', '.join(items)}" for path, items in sorted(grouped.items())] or ["- None"]),
        "",
        "## Suggested Fixes",
        "",
        *([f"- **{finding.rule_id}**: {finding.remediation}" for finding in active] or ["- None"]),
        "",
        "## Verification Evidence",
        "",
        f"- Static analysis: INFERRED; tool version `{result.tool_version}`.",
        f"- Runtime verification: {result.verification.get('status', 'INFERRED')}.",
        "",
        "## Ignored Findings",
        "",
        f"- {result.summary.get('ignored_findings', 0)} ignored findings; ignored findings remain present in JSON with `ignored: true`.",
        *[
            f"- Suppression diagnostic: `{item.get('path')}:{item.get('line')}` `{item.get('rule_id')}` — {item.get('message')}."
            for item in result.summary.get("suppression_diagnostics", [])
        ],
        "",
        "## Baseline Status",
        "",
        *_baseline_markdown(result),
        "",
    ]
    return "\n".join(lines)


def _finding_markdown(findings: list[Finding]) -> list[str]:
    if not findings:
        return ["- None"]
    return [
        f"- `{finding.location.path}:{finding.location.line}:{finding.location.column}` **{finding.rule_id}** ({finding.severity.value}, {finding.confidence.value}) — {finding.reason} Remediation: {finding.remediation}"
        for finding in findings
    ]


def _contract_markdown(result: ScanResult) -> list[str]:
    violations = result.contract.get("violations", [])
    if not violations:
        return [f"- {result.contract.get('status', 'NOT_DECLARED')}"]
    return [f"- `{item['target']}` declared `{item['declared']}` but detected `{', '.join(item['detected_assumptions'])}`." for item in violations]


def _baseline_markdown(result: ScanResult) -> list[str]:
    if not result.baseline:
        return ["- No baseline loaded."]
    lines = [
        f"- Status: {result.baseline.get('status', 'UNKNOWN')}.",
        f"- New findings: {result.baseline.get('new_count', 0)}; existing findings: {result.baseline.get('existing_count', 0)}; resolved findings: {result.baseline.get('resolved_count', 0)}.",
    ]
    for target_id, change in sorted(result.baseline.get("scores", {}).items()):
        lines.append(f"- `{target_id}`: {change['before']}/100 -> {change['after']}/100 ({change['delta']:+d}).")
    return lines


def render_terminal(result: ScanResult, color: bool = False) -> str:
    del color  # output is intentionally readable without ANSI codes
    lines = [
        "Agent Workflow Portability",
        "===========================",
        "",
        "Compatibility Matrix",
        "---------------------",
        f"{'Environment':<24} {'Score':>7} {'Status':<9} {'Findings':>8}",
    ]
    for target in result.targets:
        score = result.scores[target.id]
        lines.append(f"{target.display_name:<24} {score.score:>3}/100 {score.status:<9} {score.findings:>8}")
    lines.extend(
        [
            "",
            f"{result.summary.get('findings', 0)} portability issues found ({result.summary.get('ignored_findings', 0)} ignored)",
            "",
            "Findings",
            "--------",
        ]
    )
    if result.baseline.get("scores"):
        lines.extend(["", "Diff", "----", f"Regression status: {result.baseline.get('status', 'UNKNOWN')}"])
        lines.append(f"New portability regressions: {result.baseline.get('new_count', 0)}")
        lines.append(f"Resolved issues: {result.baseline.get('resolved_count', 0)}")
        lines.append("Before / After scores")
        for target in result.targets:
            change = result.baseline["scores"].get(target.id)
            if change:
                lines.append(f"  {target.display_name}: {change['before']}/100 -> {change['after']}/100 ({change['delta']:+d})")
    for finding in result.active_findings:
        targets = ", ".join(finding.affected_targets)
        lines.append(f"{finding.location.path}:{finding.location.line}:{finding.location.column} {finding.rule_id} [{finding.severity.value}/{finding.confidence.value}]")
        if finding.code:
            lines.append(f"  {finding.code}")
            span = max(1, (finding.location.end_column or finding.location.column) - finding.location.column)
            lines.append(f"  {' ' * (finding.location.column - 1)}{'^' * min(span, 80)}")
        lines.append(f"  Affected: {targets}")
        lines.append(f"  Reason: {finding.reason}")
        lines.append(f"  Suggested remediation: {finding.remediation}")
    if not result.active_findings:
        lines.append("  None")
    if result.summary.get("suppression_diagnostics"):
        lines.extend(["", "Suppression diagnostics", "-----------------------"])
        lines.extend(
            f"  {item.get('path')}:{item.get('line')} {item.get('rule_id')}: {item.get('message')}"
            for item in result.summary["suppression_diagnostics"]
        )
    if result.contract.get("violations"):
        lines.extend(["", "Contract violations", "--------------------"])
        lines.extend(f"  {item['target']}: {', '.join(item['detected_assumptions'])}" for item in result.contract["violations"])
    return "\n".join(lines) + "\n"
