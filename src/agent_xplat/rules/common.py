"""Shared rule protocol and finding construction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

from ..config import Config
from ..environments import TARGETS
from ..models import Confidence, Finding, Severity, SourceFile, SourceLocation, Target


@dataclass(frozen=True)
class RuleContext:
    config: Config
    targets: tuple[Target, ...]

    @property
    def target_ids(self) -> tuple[str, ...]:
        return tuple(target.id for target in self.targets)


Detector = Callable[[SourceFile, RuleContext], Iterable[Finding]]


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    title: str
    description: str
    affected_environments: tuple[str, ...]
    severity: Severity
    confidence: Confidence
    remediation: str
    examples: tuple[str, ...]
    test_cases: tuple[str, ...]
    detector: Detector
    severity_rationale: str
    confidence_rationale: str


ALL_TARGET_IDS = tuple(target.id for target in TARGETS)


def make_finding(
    spec: RuleSpec,
    source: SourceFile,
    context: RuleContext,
    line_index: int,
    needle: str,
    affected_targets: Iterable[str],
    reason: str,
    *,
    code: str | None = None,
    severity: Severity | None = None,
    confidence: Confidence | None = None,
    metadata: dict | None = None,
) -> Finding:
    affected = tuple(target_id for target_id in context.target_ids if target_id in set(affected_targets))
    if not affected:
        return None  # type: ignore[return-value]
    return Finding(
        rule_id=spec.rule_id,
        title=spec.title,
        description=spec.description,
        location=source.location(line_index, needle),
        severity=severity or spec.severity,
        confidence=confidence or spec.confidence,
        affected_targets=affected,
        reason=reason,
        remediation=spec.remediation,
        examples=spec.examples,
        code=code if code is not None else source.lines[line_index].strip() if source.lines else "",
        metadata={
            "severity_rationale": spec.severity_rationale,
            "confidence_rationale": spec.confidence_rationale,
            **(metadata or {}),
        },
    )


def line_matches(source: SourceFile, pattern: str, flags: int = 0):
    compiled = re.compile(pattern, flags)
    for line_index, line in enumerate(source.lines):
        for match in compiled.finditer(line):
            yield line_index, line, match


def first_match(source: SourceFile, pattern: str, flags: int = 0):
    return next(line_matches(source, pattern, flags), None)
