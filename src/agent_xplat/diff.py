"""Scan result comparison for Git reference/diff mode."""

from __future__ import annotations

from typing import Any
import io
import subprocess
import tarfile
import tempfile
from pathlib import Path

from .models import ScanResult


def compare_scans(before: ScanResult, after: ScanResult) -> dict[str, Any]:
    before_fingerprints = {finding.fingerprint for finding in before.active_findings}
    after_fingerprints = {finding.fingerprint for finding in after.active_findings}
    new = sorted(after_fingerprints - before_fingerprints)
    resolved = sorted(before_fingerprints - after_fingerprints)
    scores: dict[str, Any] = {}
    regression = False
    for target in after.targets:
        old_score = before.scores.get(target.id).score if target.id in before.scores else 100
        new_score = after.scores[target.id].score
        scores[target.id] = {"before": old_score, "after": new_score, "delta": new_score - old_score}
        regression = regression or new_score < old_score
    return {
        "before_findings": len(before.active_findings),
        "after_findings": len(after.active_findings),
        "new": new,
        "resolved": resolved,
        "new_count": len(new),
        "resolved_count": len(resolved),
        "scores": scores,
        "regression": regression,
        "status": "REGRESSION" if regression or new else "CLEAN",
    }


def scan_git_reference(root: Path, reference: str, config) -> ScanResult:
    """Materialize a Git reference in a temporary directory and scan it.

    `git archive` reads repository objects; it never invokes files from the
    reference. The caller still reports a normal inferred static scan.
    """
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "archive", "--format=tar", reference],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"cannot read Git reference {reference}: {message or 'git archive failed'}")
    with tempfile.TemporaryDirectory(prefix="agent-xplat-diff-") as directory:
        with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
            destination = Path(directory).resolve()
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                output = (destination / member.name).resolve()
                if destination not in output.parents:
                    raise ValueError("Git reference contains an unsafe archive path")
                output.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, output.open("wb") as target:
                    if source is not None:
                        target.write(source.read())
        from .engine import scan

        return scan(Path(directory), config)
