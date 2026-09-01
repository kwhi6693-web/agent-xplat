from pathlib import Path

from agent_xplat import __version__
from agent_xplat.rules.registry import all_rules


ROOT = Path(__file__).parents[1]


def test_documented_rule_catalog_covers_registry():
    text = (ROOT / "docs" / "RULES.md").read_text(encoding="utf-8")
    for rule in all_rules():
        assert rule.rule_id in text


def test_public_metadata_and_ci_contract_are_present():
    assert __version__ == "1.0.1"
    assert (ROOT / "LICENSE").exists()
    workflow = (ROOT / ".github" / "workflows" / "agent-xplat.yml").read_text(encoding="utf-8")
    for runner in ("windows-latest", "macos-latest", "ubuntu-latest"):
        assert runner in workflow
    for command in ("scan", "test", "fix", "report", "explain", "doctor", "baseline", "init", "init-ci", "badge"):
        assert f'"{command}"' in (ROOT / "src" / "agent_xplat" / "cli.py").read_text(encoding="utf-8")
