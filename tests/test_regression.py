import json
from pathlib import Path

from agent_xplat.cli import main


def test_fresh_project_workflow_completes_without_overwriting_user_files(tmp_path: Path, capsys):
    (tmp_path / "SKILL.md").write_text("echo portable\n", encoding="utf-8")
    assert main(["init", str(tmp_path)]) == 0
    assert main(["scan", str(tmp_path), "--format", "json", "--output", str(tmp_path / "scan.json")]) == 0
    assert main(["report", str(tmp_path)]) == 0
    assert (tmp_path / "agent-xplat-report.md").exists()
    assert main(["baseline", str(tmp_path)]) == 0
    assert (tmp_path / ".agent-xplat-baseline.json").exists()
    assert main(["scan", str(tmp_path), "--format", "json", "--baseline-only", "--output", str(tmp_path / "scan-2.json")]) == 0
    assert main(["fix", str(tmp_path), "--dry-run"]) == 0
    assert main(["doctor", "--format", "json", "--output", str(tmp_path / "doctor.json")]) == 0
    assert main(["init-ci", str(tmp_path)]) == 0
    assert (tmp_path / ".github" / "workflows" / "agent-xplat.yml").exists()
    assert json.loads((tmp_path / "scan.json").read_text(encoding="utf-8"))["schema_version"] == "1.0"
    assert json.loads((tmp_path / "doctor.json").read_text(encoding="utf-8"))["capabilities"]
    assert (tmp_path / "SKILL.md").read_text(encoding="utf-8") == "echo portable\n"
