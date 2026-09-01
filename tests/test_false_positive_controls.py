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
