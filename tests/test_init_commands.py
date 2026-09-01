import json
from pathlib import Path

from agent_xplat.cli import main


def test_init_init_ci_and_badge_are_non_destructive(tmp_path: Path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    assert (tmp_path / ".agent-xplat.yml").exists()
    original = (tmp_path / ".agent-xplat.yml").read_text(encoding="utf-8")
    assert main(["init", str(tmp_path)]) == 2
    assert (tmp_path / ".agent-xplat.yml").read_text(encoding="utf-8") == original
    assert main(["init-ci", str(tmp_path)]) == 0
    workflow = tmp_path / ".github" / "workflows" / "agent-xplat.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "windows-latest" in text and "macos-latest" in text and "ubuntu-latest" in text
    assert main(["badge", str(tmp_path)]) == 0
    assert (tmp_path / "agent-xplat-badge.svg").exists()
    assert "Static Checked" in capsys.readouterr().out


def test_runtime_verified_badge_requires_three_os_evidence(tmp_path: Path):
    assert main(["badge", str(tmp_path), "--runtime-verified"]) == 2
    (tmp_path / "agent-xplat-verification.json").write_text(
        '{"status":"VERIFIED","verified_os":["windows","macos","linux"]}\n', encoding="utf-8"
    )
    assert main(["badge", str(tmp_path), "--runtime-verified"]) == 0
    assert "Cross-OS Verified" in (tmp_path / "agent-xplat-badge.svg").read_text(encoding="utf-8")
