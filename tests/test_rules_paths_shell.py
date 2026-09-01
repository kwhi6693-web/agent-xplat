from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source
from agent_xplat.rules.registry import all_rules


def _findings(tmp_path: Path, name: str, text: str):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return analyze_source(source_file_from_path(path, tmp_path), Config())


def test_rule_registry_is_modular_and_metadata_complete():
    rules = all_rules()
    ids = [rule.rule_id for rule in rules]
    assert len(ids) >= 15
    assert len(ids) == len(set(ids))
    assert all(rule.title and rule.description and rule.remediation for rule in rules)
    assert all(rule.severity and rule.confidence and rule.affected_environments for rule in rules)


def test_shell_and_path_rules_locate_portability_assumptions(tmp_path: Path):
    findings = _findings(
        tmp_path,
        "SKILL.md",
        """Run `chmod +x scripts/render.sh`
Cache at /tmp/agent-xplat and use $HOME/bin.
export FOO=bar
$env:FOO=bar
FOO=bar command
source scripts/env.sh
Use C:\\Program Files\\Tool\\tool.exe
        """,
    )
    ids = {finding.rule_id for finding in findings}
    assert "AX-SHELL-001" in ids
    assert "AX-PATH-001" in ids
    assert "AX-SHELL-003" in ids
    assert "AX-SHELL-004" in ids
    chmod = next(finding for finding in findings if finding.rule_id == "AX-SHELL-001")
    assert "windows-powershell" in chmod.affected_targets
    assert "windows-cmd" in chmod.affected_targets
    assert chmod.severity.value == "BLOCKER"
    assert chmod.confidence.value == "HIGH"
    assert chmod.location.line == 1
    assert chmod.location.column == 6


def test_reserved_windows_names_and_windows_paths_are_target_specific(tmp_path: Path):
    findings = _findings(tmp_path, "paths.txt", "open('CON')\nC:\\Temp\\out.txt\n")
    reserved = next(finding for finding in findings if finding.rule_id == "AX-PATH-004")
    windows_path = next(finding for finding in findings if finding.rule_id == "AX-PATH-002")
    assert "windows-powershell" in reserved.affected_targets
    assert "linux-bash" not in reserved.affected_targets
    assert "linux-bash" in windows_path.affected_targets
