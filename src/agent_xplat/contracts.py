"""Compatibility Contract evaluation."""

from __future__ import annotations

from typing import Any

from .config import Config
from .models import Finding, Score, Severity


def evaluate_contract(config: Config, scores: dict[str, Score], findings: list[Finding]) -> dict[str, Any]:
    if not config.supported and not config.unsupported and not config.requirements:
        return {
            "status": "NOT_DECLARED",
            "supported": [],
            "unsupported": [],
            "requirements": {},
            "violations": [],
        }
    violations: list[dict[str, Any]] = []
    for target_id in config.supported:
        relevant = [finding for finding in findings if not finding.ignored and target_id in finding.affected_targets]
        blocking = [finding for finding in relevant if finding.severity in {Severity.BLOCKER, Severity.ERROR}]
        score = scores[target_id]
        if blocking or score.score < config.minimum_score:
            violations.append(
                {
                    "target": target_id,
                    "declared": "supported",
                    "detected_assumptions": [finding.rule_id for finding in blocking] or ["score-below-minimum"],
                    "finding_ids": [finding.fingerprint for finding in blocking],
                    "reason": "Declared support conflicts with detected portability assumptions.",
                }
            )
    return {
        "status": "VIOLATION" if violations else "PASS",
        "supported": list(config.supported),
        "unsupported": list(config.unsupported),
        "requirements": dict(config.requirements),
        "violations": violations,
    }
