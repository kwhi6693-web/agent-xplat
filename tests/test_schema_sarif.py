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


def test_ast_findings_keep_structured_analysis_metadata_and_sarif_help(tmp_path: Path):
    (tmp_path / "workflow.ts").write_text(
        'import * as cp from "node:child_process";\ncp.exec("rm -rf dist");\n',
        encoding="utf-8",
    )
    result = scan(tmp_path, Config())
    result_doc = json.loads(render_json(result))
    finding = next(item for item in result_doc["findings"] if item["rule_id"] == "AX-NODE-005")
    assert finding["metadata"]["analysis"] == "tree-sitter-ast"
    assert finding["metadata"]["language"] == "typescript"
    assert finding["location"]["line"] == 2
    sarif_doc = json.loads(render_sarif(result))
    sarif_result = next(item for item in sarif_doc["runs"][0]["results"] if item["ruleId"] == "AX-NODE-005")
    assert sarif_result["locations"][0]["physicalLocation"]["region"]["startLine"] == 2
    assert sarif_result["help"]["text"]


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


def test_result_validator_checks_nested_contract_types_and_ranges():
    document = {
        "schema_version": "1.0",
        "tool_version": "1.0.0",
        "scan_timestamp": "now",
        "targets": [{"id": 1, "os": "windows", "shell": "powershell", "runtime": "native", "display_name": "x"}],
        "scores": [{"target": "windows-powershell", "score": 101, "status": "UNKNOWN"}],
        "findings": [],
        "baseline": {},
        "contract": {},
        "verification": {},
        "summary": {},
    }
    errors = validate_result_document(document)
    assert any("fields must be non-empty strings" in error for error in errors)
    assert any("score" in error for error in errors)
    assert any("status" in error for error in errors)


def test_sarif_validator_checks_location_shape_and_region_coordinates():
    document = {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "agent-xplat", "semanticVersion": "1.0.0"}},
            "results": [{
                "ruleId": "AX-TEST",
                "level": "error",
                "message": {"text": "problem"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "x.md"},
                    "region": {"startLine": 0, "startColumn": "one"},
                }}],
            }],
        }],
    }
    errors = validate_sarif_document(document)
    assert any("locations" in error for error in errors)
