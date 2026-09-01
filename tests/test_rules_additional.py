from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source


def test_shell_detection_covers_where_set_and_dollar_variables(tmp_path: Path):
    path = tmp_path / "commands.sh"
    path.write_text("where node\nset FOO=bar\necho $FOO\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-SHELL-008" in ids
    assert "AX-SHELL-009" in ids
    assert "AX-QUOTE-004" in ids


def test_python_manifest_without_version_and_native_node_script_are_reported(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    node = tmp_path / "package.json"
    node.write_text('{"scripts":{"build":"tool.cmd"},"dependencies":{"better-sqlite3":"^9"}}', encoding="utf-8")
    python_findings = analyze_source(source_file_from_path(pyproject, tmp_path), Config())
    node_findings = analyze_source(source_file_from_path(node, tmp_path), Config())
    assert any(finding.rule_id == "AX-PY-005" for finding in python_findings)
    assert any(finding.rule_id == "AX-NODE-004" for finding in node_findings)


def test_relative_launcher_spellings_are_shell_specific(tmp_path: Path):
    path = tmp_path / "README.md"
    path.write_text("Run ./scripts/build.sh or .\\scripts\\build.ps1 from the current directory.\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-PATH-005" in {finding.rule_id for finding in findings}


def test_metadata_checks_unicode_paths_and_symlinks_when_host_allows_them(tmp_path: Path):
    (tmp_path / "工作流.txt").write_text("data\n", encoding="utf-8")
    result = __import__("agent_xplat.engine", fromlist=["scan"]).scan(tmp_path, Config())
    assert "AX-FS-008" in {finding.rule_id for finding in result.active_findings}
    target = tmp_path / "target.txt"
    target.write_text("data\n", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        return
    result = __import__("agent_xplat.engine", fromlist=["scan"]).scan(tmp_path, Config())
    assert "AX-FS-002" in {finding.rule_id for finding in result.active_findings}


def test_shell_pipeline_redirection_and_semicolon_syntax_is_explicit(tmp_path: Path):
    path = tmp_path / "run.sh"
    path.write_text("echo one | grep one; echo done\n2>/dev/null\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert {"AX-SHELL-010", "AX-QUOTE-005", "AX-QUOTE-007"}.issubset(ids)


def test_python_pip_and_native_dependencies_are_reported(tmp_path: Path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("pywin32>=306\n", encoding="utf-8")
    script = tmp_path / "install.sh"
    script.write_text("pip3 install -r requirements.txt\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(requirements, tmp_path), Config())
    findings += analyze_source(source_file_from_path(script, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert {"AX-PY-006", "AX-PY-007"}.issubset(ids)
