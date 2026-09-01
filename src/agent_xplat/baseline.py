"""Baseline creation and comparison."""

from __future__ import annotations

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
    old = {item.get("fingerprint") for item in baseline.get("findings", []) if item.get("fingerprint")}
    current = {finding.fingerprint for finding in result.active_findings}
    new = sorted(current - old)
    existing = sorted(current & old)
    resolved = sorted(old - current)
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
    return value


def write_baseline(path: Path, result: ScanResult) -> None:
    import json

    path.write_text(json.dumps(baseline_document(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
