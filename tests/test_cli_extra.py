import json
import os
import subprocess
from pathlib import Path

from agent_xplat.cli import main


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})
    return subprocess.run(["git", *args], cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)


def test_baseline_only_blocks_new_finding_but_not_existing_finding(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("echo ok\n", encoding="utf-8")
    assert main(["baseline", str(tmp_path)]) == 0
    assert main(["scan", str(tmp_path), "--baseline-only"]) == 0
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--baseline-only", "--format", "json", "--output", str(tmp_path / "after.json")]) == 1
    document = json.loads((tmp_path / "after.json").read_text(encoding="utf-8"))
    assert document["baseline"]["new_count"] >= 1


def test_git_diff_mode_reads_reference_without_executing_reference_files(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("echo ok\n", encoding="utf-8")
    assert _git(tmp_path, "init").returncode == 0
    assert _git(tmp_path, "add", "SKILL.md").returncode == 0
    assert _git(tmp_path, "commit", "-m", "initial").returncode == 0
    marker = tmp_path / "executed.txt"
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    output = tmp_path / "diff.json"
    assert main(["scan", str(tmp_path), "--diff", "HEAD", "--format", "json", "--output", str(output)]) == 1
    assert not marker.exists()
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["baseline"]["regression"] is True


def test_scan_does_not_execute_target_python(tmp_path: Path):
    marker = tmp_path / "created-by-execution.txt"
    (tmp_path / "danger.py").write_text("from pathlib import Path\nPath('created-by-execution.txt').write_text('bad')\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--format", "json"]) == 0
    assert not marker.exists()
