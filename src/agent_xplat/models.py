"""Stable domain objects shared by the analyzer, reports, and CLI."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, order=True)
class Target:
    id: str
    os: str
    shell: str
    runtime: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "os": self.os,
            "shell": self.shell,
            "runtime": self.runtime,
            "display_name": self.display_name,
        }


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "path": self.path,
            "line": self.line,
            "column": self.column,
        }
        if self.end_line is not None:
            value["end_line"] = self.end_line
        if self.end_column is not None:
            value["end_column"] = self.end_column
        return value


@dataclass
class SourceFile:
    path: Path
    relative_path: str
    text: str
    size: int
    mode: int | None = None
    is_crlf: bool = False
    lines: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        self.lines = tuple(self.text.splitlines())

    def line_col_for(self, needle: str, line_index: int = 0) -> tuple[int, int]:
        """Return one-based line/column for a needle on a zero-based line."""
        if line_index < 0 or line_index >= len(self.lines):
            return (line_index + 1, 1)
        column = self.lines[line_index].find(needle)
        return (line_index + 1, (column if column >= 0 else 0) + 1)

    def location(self, line_index: int, needle: str = "") -> SourceLocation:
        line, column = self.line_col_for(needle, line_index)
        end_column = column + len(needle) if needle else None
        return SourceLocation(self.relative_path, line, column, line, end_column)


@dataclass
class Finding:
    rule_id: str
    title: str
    description: str
    location: SourceLocation
    severity: Severity
    confidence: Confidence
    affected_targets: tuple[str, ...]
    reason: str
    remediation: str
    examples: tuple[str, ...] = ()
    code: str = ""
    ignored: bool = False
    suppression_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        normalized = "|".join(
            (
                self.rule_id,
                self.location.path,
                str(self.location.line),
                str(self.location.column),
                self.code.strip(),
                self.reason,
            )
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "location": self.location.to_dict(),
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "affected_targets": list(self.affected_targets),
            "reason": self.reason,
            "remediation": self.remediation,
            "examples": list(self.examples),
            "code": self.code,
            "ignored": self.ignored,
            "suppression_reason": self.suppression_reason,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Score:
    target_id: str
    score: int
    status: str
    findings: int
    blockers: int
    errors: int
    warnings: int
    infos: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target_id,
            "score": self.score,
            "status": self.status,
            "finding_count": self.findings,
            "blockers": self.blockers,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }


@dataclass
class ScanResult:
    root: str
    targets: tuple[Target, ...]
    findings: list[Finding]
    scores: dict[str, Score]
    source_files: tuple[str, ...]
    skipped_files: tuple[str, ...] = ()
    summary: dict[str, Any] = field(default_factory=dict)
    contract: dict[str, Any] = field(default_factory=dict)
    baseline: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=lambda: {"status": "INFERRED", "evidence": []})
    scan_timestamp: str = ""
    tool_version: str = "1.0.1"

    @property
    def active_findings(self) -> list[Finding]:
        return [finding for finding in self.findings if not finding.ignored]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "tool_version": self.tool_version,
            "scan_timestamp": self.scan_timestamp,
            "root": self.root,
            "targets": [target.to_dict() for target in self.targets],
            "scores": [self.scores[target.id].to_dict() for target in self.targets],
            "findings": [finding.to_dict() for finding in self.findings],
            "baseline": self.baseline,
            "contract": self.contract,
            "verification": self.verification,
            "summary": self.summary,
            "source_files": list(self.source_files),
            "skipped_files": list(self.skipped_files),
        }
