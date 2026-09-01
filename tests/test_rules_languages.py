import json
from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source


def test_python_rules_use_ast_for_imports_and_interpreter_assumptions(tmp_path: Path):
    path = tmp_path / "tool.py"
    path.write_text(
        "#!/usr/bin/python3\nimport subprocess\nimport winreg\nimport sys\nif sys.platform == 'win32':\n    print('windows')\nsubprocess.run(['python3', '-m', 'pip'])\npython_cmd = 'venv/bin/python'\n",
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-PY-001" in ids
    assert "AX-PY-002" in ids
    assert "AX-PY-003" in ids
    assert "AX-PY-004" in ids
    platform_finding = next(finding for finding in findings if finding.rule_id == "AX-PY-003")
    assert platform_finding.confidence.value == "HIGH"


def test_node_scripts_are_structurally_read_from_package_json(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps({"scripts": {"build": "NODE_ENV=production node build.js && rm -rf dist"}}),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-NODE-001" in ids
    assert "AX-NODE-002" in ids


def test_package_managers_and_external_tools_are_inferred_not_verified(tmp_path: Path):
    path = tmp_path / "README.md"
    path.write_text("brew install ffmpeg\napt-get install docker.io\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    package = next(finding for finding in findings if finding.rule_id == "AX-PM-001")
    assert package.confidence.value == "HIGH"
    assert "macos-zsh" not in package.affected_targets
    assert "linux-bash" in package.affected_targets
    assert any(finding.rule_id == "AX-TOOL-001" for finding in findings)
