"""Baseline creation and comparison."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ScanResult


def baseline_document(result: ScanResult) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "tool_version": result.tool_version,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "findings": [
            {
                "fingerprint": finding.fingerprint,
                "match_key": finding_match_key(finding),
                "rule_id": finding.rule_id,
                "path": finding.location.path,
                "line": finding.location.line,
                "severity": finding.severity.value,
            }
            for finding in result.active_findings
        ],
        "scores": {target_id: score.to_dict() for target_id, score in result.scores.items()},
    }


def compare_baseline(result: ScanResult, baseline: dict[str, Any]) -> dict[str, Any]:
    new, existing, resolved = match_findings(result.active_findings, baseline.get("findings", []))
    return {
        "status": "REGRESSION" if new else "CLEAN",
        "new": new,
        "existing": existing,
        "resolved": resolved,
        "new_count": len(new),
        "existing_count": len(existing),
        "resolved_count": len(resolved),
        "baseline_present": True,
    }


def load_baseline(path: Path) -> dict[str, Any] | None:
    import json

    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid baseline file {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.0" or not isinstance(value.get("findings"), list):
        raise ValueError(f"invalid baseline schema: {path}")
    for item in value["findings"]:
        if not isinstance(item, dict) or not isinstance(item.get("fingerprint"), str):
            raise ValueError(f"invalid baseline finding: {path}")
        if "match_key" in item and not isinstance(item["match_key"], str):
            raise ValueError(f"invalid baseline match_key: {path}")
    return value


def write_baseline(path: Path, result: ScanResult) -> None:
    import json

    path.write_text(json.dumps(baseline_document(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finding_match_key(finding) -> str:
    """Location-independent identity; multiplicity is handled by match_findings."""
    payload = [finding.rule_id, finding.location.path, finding.code.strip(),
               finding.reason, finding.severity.value, sorted(finding.affected_targets)]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()


def match_findings(findings, previous):
    """Match occurrences, retaining support for old fingerprint-only baselines."""
    by_key = defaultdict(list)
    legacy = defaultdict(list)
    for item in previous:
        if item.get("match_key"):
            by_key[item["match_key"]].append(item["fingerprint"])
        elif item.get("fingerprint"):
            legacy[item["fingerprint"]].append(item["fingerprint"])
    new, existing = [], []
    for finding in findings:
        bucket = by_key.get(finding_match_key(finding)) or legacy.get(finding.fingerprint)
        if bucket:
            bucket.pop()
            existing.append(finding.fingerprint)
        else:
            new.append(finding.fingerprint)
    resolved = [fingerprint for bucket in (*by_key.values(), *legacy.values()) for fingerprint in bucket]
    return sorted(new), sorted(existing), sorted(resolved)
