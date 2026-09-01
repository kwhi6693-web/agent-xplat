"""Narrow, deterministic autofixes with dry-run and hash protection."""

from __future__ import annotations

import difflib
import hashlib
from pathlib import Path
from typing import Any

from .models import ScanResult


def plan_fixes(result: ScanResult) -> list[dict[str, Any]]:
    """Return only fixes with a deterministic, behavior-preserving proof."""
    fixes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for finding in result.active_findings:
        if finding.rule_id != "AX-FS-001" or finding.location.path in seen:
            continue
        seen.add(finding.location.path)
        fixes.append(
            {
                "rule_id": finding.rule_id,
                "path": finding.location.path,
                "description": "Normalize CRLF to LF for a shebang script.",
                "proof": "Only line-ending bytes change; script text and order remain identical.",
            }
        )
    return sorted(fixes, key=lambda fix: (fix["path"], fix["rule_id"]))


def apply_fixes(root: Path, fixes: list[dict[str, Any]], dry_run: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    patches: list[str] = []
    applied = 0
    skipped = 0
    before_hashes: dict[str, str] = {}
    after_hashes: dict[str, str] = {}
    for fix in fixes:
        relative = Path(fix["path"])
        path = (root / relative).resolve()
        if root not in path.parents and path != root:
            skipped += 1
            continue
        if not path.exists() or not path.is_file() or path.is_symlink():
            skipped += 1
            continue
        before = path.read_bytes()
        after = before.replace(b"\r\n", b"\n")
        before_hashes[relative.as_posix()] = _hash(before)
        after_hashes[relative.as_posix()] = _hash(after)
        if before == after:
            skipped += 1
            continue
        old_text = before.decode("utf-8")
        new_text = after.decode("utf-8")
        patches.extend(
            difflib.unified_diff(
                old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                fromfile=f"a/{relative.as_posix()}", tofile=f"b/{relative.as_posix()}", lineterm="",
            )
        )
        if not dry_run:
            path.write_bytes(after)
        applied += 1
    return {
        "dry_run": dry_run,
        "applied": 0 if dry_run else applied,
        "planned": applied,
        "skipped": skipped,
        "diff": "\n".join(patches) + ("\n" if patches else "No safe fixes available.\n"),
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
    }


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
