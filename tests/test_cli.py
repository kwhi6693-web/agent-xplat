import json
from pathlib import Path

from agent_xplat.cli import main


def test_scan_prints_matrix_and_returns_portability_gate_code(tmp_path: Path, capsys):
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--no-color"]) == 1
    output = capsys.readouterr().out
    assert "Compatibility Matrix" in output
    assert "Windows / PowerShell" in output
    assert "AX-SHELL-001" in output


def test_scan_json_writes_machine_readable_output(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("echo ok\n", encoding="utf-8")
    output = tmp_path / "scan.json"
    assert main(["scan", str(tmp_path), "--format", "json", "--output", str(output)]) == 0
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["summary"]["findings"] == 0


def test_cli_handles_explain_invalid_input_and_missing_root(capsys, tmp_path: Path):
    assert main(["explain", "AX-SHELL-001"]) == 0
    assert "Rule meaning" in capsys.readouterr().out
    assert main(["explain", "AX-NOT-A-RULE"]) == 2
    assert main(["scan", str(tmp_path / "missing")]) == 2


def test_every_required_command_has_help():
    commands = ["scan", "test", "fix", "report", "explain", "doctor", "baseline", "init", "init-ci", "badge"]
    for command in commands:
        assert main([command, "--help"]) == 0
