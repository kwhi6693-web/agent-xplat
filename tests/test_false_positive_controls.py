from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source


def test_natural_language_and_build_metadata_do_not_become_shell_commands(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("The source code is stored here. Find the package metadata in Python.\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.setuptools.packages.find]\nwhere = ['src']\n", encoding="utf-8")
    readme_findings = analyze_source(source_file_from_path(readme, tmp_path), Config())
    pyproject_findings = analyze_source(source_file_from_path(pyproject, tmp_path), Config())
    assert not {finding.rule_id for finding in readme_findings} & {"AX-SHELL-002", "AX-SHELL-006", "AX-PY-001"}
    assert "AX-SHELL-002" not in {finding.rule_id for finding in pyproject_findings}


def test_node_ast_does_not_treat_a_guarded_platform_selection_as_a_portability_failure(tmp_path: Path):
    path = tmp_path / "platform.js"
    path.write_text(
        """
const command = process.platform === "win32" ? usePowerShell : useBash;
""".lstrip(),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-NODE-007" not in {finding.rule_id for finding in findings}


def test_node_member_names_are_not_misread_as_shell_commands(tmp_path: Path):
    path = tmp_path / "process.js"
    path.write_text(
        'const cp = require("child_process");\ncp.exec("echo ok", { shell: true });\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-SHELL-002" not in {finding.rule_id for finding in findings}
    assert "AX-NODE-005" in {finding.rule_id for finding in findings}


def test_node_path_api_makes_literal_separator_portable_but_not_standalone_path(tmp_path: Path):
    path = tmp_path / "paths.js"
    path.write_text(
        'const path = require("node:path");\nconst joined = path.join("folder\\\\", "file");\nconst standalone = "folder\\\\file";\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    separator_findings = [finding for finding in findings if finding.rule_id == "AX-PATH-003"]
    assert len(separator_findings) == 1
    assert separator_findings[0].location.line == 3


def test_path_api_detection_does_not_hide_unrelated_windows_path_literals(tmp_path: Path):
    path = tmp_path / "paths.js"
    path.write_text(
        'const path = require("node:path");\nconst joined = path.join("folder", "file");\nconst fixed = "C:\\\\Program Files\\\\Agent";\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    windows = [finding for finding in findings if finding.rule_id == "AX-PATH-002"]
    separators = [finding for finding in findings if finding.rule_id == "AX-PATH-003"]
    assert windows
    assert separators


def test_named_path_api_imports_are_recognized_structurally(tmp_path: Path):
    path = tmp_path / "named-path.mjs"
    path.write_text(
        'const { join: joinPath } = require("node:path");\nconst joined = joinPath("folder\\\\file");\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-PATH-003" not in {finding.rule_id for finding in findings}


def test_github_setup_action_satisfies_workflow_runtime_provisioning(tmp_path: Path):
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        """name: ci
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pytest -q
""",
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(workflow, tmp_path), Config())
    assert "AX-TOOL-001" not in {finding.rule_id for finding in findings}
