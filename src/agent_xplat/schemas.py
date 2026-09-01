"""Small dependency-free validators for the public JSON contracts."""

from __future__ import annotations

from typing import Any


RESULT_REQUIRED = {
    "schema_version", "tool_version", "scan_timestamp", "targets", "scores", "findings",
    "baseline", "contract", "verification", "summary",
}

_SEVERITIES = {"BLOCKER", "ERROR", "WARNING", "INFO"}
_CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}


def validate_result_document(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be an object"]
    missing = sorted(RESULT_REQUIRED - set(document))
    errors.extend(f"missing key: {key}" for key in missing)
    if document.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not isinstance(document.get("targets"), list):
        errors.append("targets must be a list")
    if not isinstance(document.get("scores"), list):
        errors.append("scores must be a list")
    if not isinstance(document.get("findings"), list):
        errors.append("findings must be a list")
    for index, target in enumerate(document.get("targets", [])):
        if not isinstance(target, dict) or not {"id", "os", "shell", "runtime"}.issubset(target):
            errors.append(f"targets[{index}] must include id, os, shell, runtime")
    for index, score in enumerate(document.get("scores", [])):
        if not isinstance(score, dict) or not {"target", "score", "status"}.issubset(score):
            errors.append(f"scores[{index}] must include target, score, status")
        elif not isinstance(score["score"], int) or not 0 <= score["score"] <= 100:
            errors.append(f"scores[{index}].score must be an integer from 0 to 100")
    for index, finding in enumerate(document.get("findings", [])):
        required = {"fingerprint", "rule_id", "location", "severity", "confidence", "affected_targets", "ignored"}
        if not isinstance(finding, dict) or not required.issubset(finding):
            errors.append(f"findings[{index}] is missing required finding fields")
            continue
        if finding["severity"] not in _SEVERITIES:
            errors.append(f"findings[{index}].severity is invalid")
        if finding["confidence"] not in _CONFIDENCES:
            errors.append(f"findings[{index}].confidence is invalid")
        if not isinstance(finding["location"], dict) or not {"path", "line", "column"}.issubset(finding["location"]):
            errors.append(f"findings[{index}].location must include path, line, column")
        if not isinstance(finding["affected_targets"], list):
            errors.append(f"findings[{index}].affected_targets must be a list")
        if not isinstance(finding["ignored"], bool):
            errors.append(f"findings[{index}].ignored must be boolean")
    return errors


def validate_sarif_document(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["SARIF document must be an object"]
    if document.get("version") != "2.1.0":
        errors.append("SARIF version must be 2.1.0")
    if not isinstance(document.get("runs"), list) or not document["runs"]:
        errors.append("SARIF runs must be a non-empty list")
        return errors
    for index, run in enumerate(document["runs"]):
        if not isinstance(run, dict) or not isinstance(run.get("tool"), dict) or not isinstance(run.get("results"), list):
            errors.append(f"runs[{index}] must include tool and results")
            continue
        driver = run["tool"].get("driver")
        if not isinstance(driver, dict) or not {"name", "semanticVersion"}.issubset(driver):
            errors.append(f"runs[{index}].tool.driver must include name and semanticVersion")
        for result_index, result in enumerate(run["results"]):
            if not isinstance(result, dict) or not {"ruleId", "level", "message", "locations"}.issubset(result):
                errors.append(f"runs[{index}].results[{result_index}] is missing required SARIF fields")
    return errors


RESULT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agent-xplat:schema:result:1.0",
    "title": "agent-xplat scan result",
    "type": "object",
    "required": sorted(RESULT_REQUIRED),
    "properties": {
        "schema_version": {"const": "1.0"},
        "tool_version": {"type": "string"},
        "scan_timestamp": {"type": "string"},
        "targets": {"type": "array"},
        "scores": {"type": "array"},
        "findings": {"type": "array"},
        "baseline": {"type": "object"},
        "contract": {"type": "object"},
        "verification": {"type": "object"},
        "summary": {"type": "object"},
    },
}
