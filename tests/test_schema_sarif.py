import json
from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan
from agent_xplat.reporting import render_json, render_sarif
from agent_xplat.schemas import validate_result_document, validate_sarif_document


def test_result_and_sarif_validators_accept_generated_documents(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("echo ok\n", encoding="utf-8")
    result = scan(tmp_path, Config())
    result_doc = json.loads(render_json(result))
    sarif_doc = json.loads(render_sarif(result))
    assert validate_result_document(result_doc) == []
    assert validate_sarif_document(sarif_doc) == []


def test_result_validator_reports_missing_required_keys():
    errors = validate_result_document({"schema_version": "1.0"})
    assert any("missing key" in error for error in errors)


def test_result_and_sarif_validators_reject_malformed_finding_shapes():
    document = {
        "schema_version": "1.0",
        "tool_version": "1.0.0",
        "scan_timestamp": "now",
        "targets": [],
        "scores": [],
        "findings": [{"rule_id": "AX-TEST", "severity": "BROKEN"}],
        "baseline": {},
        "contract": {},
        "verification": {},
        "summary": {},
    }
    assert any("missing required finding fields" in error for error in validate_result_document(document))
    sarif = {"version": "2.1.0", "runs": [{"tool": {"driver": {}}, "results": [{"ruleId": "AX-TEST"}]}]}
    errors = validate_sarif_document(sarif)
    assert any("driver" in error for error in errors)
    assert any("missing required SARIF fields" in error for error in errors)
