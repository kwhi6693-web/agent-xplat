import json
from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan


FIXTURES = Path(__file__).parent / "fixtures"


def test_fixture_catalog_matches_expected_rule_contracts():
    for fixture in sorted(path for path in FIXTURES.iterdir() if path.is_dir()):
        expected_path = fixture / "expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        result = scan(fixture, Config())
        by_rule = {}
        for finding in result.active_findings:
            by_rule.setdefault(finding.rule_id, []).append(finding)
        for rule_id in expected["expected_rules"]:
            assert rule_id in by_rule, f"{fixture.name} missing {rule_id}"
        for rule_id, target_id in expected.get("affected_contains", {}).items():
            assert any(target_id in finding.affected_targets for finding in by_rule[rule_id]), f"{fixture.name} target mismatch for {rule_id}"
        for rule_id, severity in expected.get("severity", {}).items():
            assert all(finding.severity.value == severity for finding in by_rule[rule_id])
        for rule_id, confidence in expected.get("confidence", {}).items():
            assert all(finding.confidence.value == confidence for finding in by_rule[rule_id])
        if "exact_rules" in expected:
            assert set(by_rule) == set(expected["exact_rules"]), f"{fixture.name} unexpected rule set: {sorted(set(by_rule) - set(expected['exact_rules']))}"
        for rule_id in expected.get("forbidden_rules", []):
            assert rule_id not in by_rule, f"{fixture.name} unexpectedly reported {rule_id}"
