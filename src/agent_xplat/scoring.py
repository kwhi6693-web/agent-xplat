"""Explainable, deterministic target-specific scoring."""

from __future__ import annotations

from collections import Counter

from .models import Finding, Score, Severity, Target


PENALTIES = {
    Severity.BLOCKER: 35,
    Severity.ERROR: 20,
    Severity.WARNING: 8,
    Severity.INFO: 2,
}


def score_findings(findings: list[Finding], targets: tuple[Target, ...], minimum_score: int = 85) -> dict[str, Score]:
    result: dict[str, Score] = {}
    for target in targets:
        relevant = [finding for finding in findings if not finding.ignored and target.id in finding.affected_targets]
        counts = Counter(finding.severity for finding in relevant)
        score = max(0, 100 - sum(PENALTIES[finding.severity] for finding in relevant))
        blockers = counts[Severity.BLOCKER]
        errors = counts[Severity.ERROR]
        if blockers:
            status = "BLOCKED"
        elif score >= minimum_score and errors == 0:
            status = "PASS"
        else:
            status = "PARTIAL"
        result[target.id] = Score(
            target_id=target.id,
            score=score,
            status=status,
            findings=len(relevant),
            blockers=blockers,
            errors=errors,
            warnings=counts[Severity.WARNING],
            infos=counts[Severity.INFO],
        )
    return result
