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
        by_rule = {finding.rule_id: finding for finding in result.active_findings}
        for rule_id in expected["expected_rules"]:
            assert rule_id in by_rule, f"{fixture.name} missing {rule_id}"
        for rule_id, target_id in expected.get("affected_contains", {}).items():
            assert target_id in by_rule[rule_id].affected_targets, f"{fixture.name} target mismatch for {rule_id}"
        for rule_id, severity in expected.get("severity", {}).items():
            assert by_rule[rule_id].severity.value == severity
        for rule_id, confidence in expected.get("confidence", {}).items():
            assert by_rule[rule_id].confidence.value == confidence
