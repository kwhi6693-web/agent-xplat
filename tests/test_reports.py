import json
from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan
from agent_xplat.reporting import render_json, render_markdown, render_sarif, render_terminal


def _result(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    return scan(tmp_path, Config())


def test_json_report_has_stable_agent_facing_contract(tmp_path: Path):
    document = json.loads(render_json(_result(tmp_path)))
    for key in {"tool_version", "scan_timestamp", "targets", "scores", "findings", "baseline", "contract", "verification", "summary"}:
        assert key in document
    assert document["findings"][0]["location"]["line"] == 1
    assert document["scores"][0]["target"] == "windows-powershell"


def test_sarif_report_is_versioned_and_has_help_locations(tmp_path: Path):
    document = json.loads(render_sarif(_result(tmp_path)))
    assert document["version"] == "2.1.0"
    run = document["runs"][0]
    assert run["tool"]["driver"]["name"] == "agent-xplat"
    assert run["results"][0]["ruleId"] == "AX-SHELL-001"
    assert run["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] == 1
    assert run["results"][0]["help"]["text"]


def test_markdown_and_terminal_reports_include_matrix_and_actionable_sections(tmp_path: Path):
    result = _result(tmp_path)
    markdown = render_markdown(result)
    terminal = render_terminal(result, color=False)
    for heading in ["Executive Summary", "Compatibility Matrix", "Blocking Issues", "Suggested Fixes", "Verification Evidence", "Ignored Findings", "Baseline Status"]:
        assert f"## {heading}" in markdown
    assert "Windows / PowerShell" in terminal
    assert "AX-SHELL-001" in terminal
    assert "BLOCKER" in terminal
    assert "^^^^^" in terminal
