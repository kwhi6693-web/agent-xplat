"""Small dependency-free validators for the public JSON contracts."""

from __future__ import annotations

from typing import Any


RESULT_REQUIRED = {
    "schema_version", "tool_version", "scan_timestamp", "targets", "scores", "findings",
    "baseline", "contract", "verification", "summary",
}

_SEVERITIES = {"BLOCKER", "ERROR", "WARNING", "INFO"}
_CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
_SCORE_STATUSES = {"BLOCKED", "PARTIAL", "PASS"}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


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
    targets = document.get("targets", []) if isinstance(document.get("targets", []), list) else []
    scores = document.get("scores", []) if isinstance(document.get("scores", []), list) else []
    findings = document.get("findings", []) if isinstance(document.get("findings", []), list) else []
    for index, target in enumerate(targets):
        required = {"id", "os", "shell", "runtime", "display_name"}
        if not isinstance(target, dict) or not required.issubset(target):
            errors.append(f"targets[{index}] must include id, os, shell, runtime, display_name")
        elif not all(_is_non_empty_string(target[field]) for field in required):
            errors.append(f"targets[{index}] fields must be non-empty strings")
    for index, score in enumerate(scores):
        if not isinstance(score, dict) or not {"target", "score", "status"}.issubset(score):
            errors.append(f"scores[{index}] must include target, score, status")
        else:
            if not isinstance(score["score"], int) or not 0 <= score["score"] <= 100:
                errors.append(f"scores[{index}].score must be an integer from 0 to 100")
            if not _is_non_empty_string(score["target"]):
                errors.append(f"scores[{index}].target must be a non-empty string")
            if score["status"] not in _SCORE_STATUSES:
                errors.append(f"scores[{index}].status is invalid")
        for count_key in ("finding_count", "blockers", "errors", "warnings", "infos"):
            if isinstance(score, dict) and count_key in score and (not isinstance(score[count_key], int) or score[count_key] < 0):
                errors.append(f"scores[{index}].{count_key} must be a non-negative integer")
    for index, finding in enumerate(findings):
        required = {
            "fingerprint", "rule_id", "title", "description", "location", "severity", "confidence",
            "affected_targets", "reason", "remediation", "examples", "code", "ignored", "suppression_reason", "metadata",
        }
        if not isinstance(finding, dict) or not required.issubset(finding):
            errors.append(f"findings[{index}] is missing required finding fields")
            continue
        for string_key in ("fingerprint", "rule_id", "title", "description", "reason", "remediation", "code"):
            if not isinstance(finding[string_key], str):
                errors.append(f"findings[{index}].{string_key} must be a string")
        if finding["severity"] not in _SEVERITIES:
            errors.append(f"findings[{index}].severity is invalid")
        if finding["confidence"] not in _CONFIDENCES:
            errors.append(f"findings[{index}].confidence is invalid")
        location = finding["location"]
        if not isinstance(location, dict) or not {"path", "line", "column"}.issubset(location):
            errors.append(f"findings[{index}].location must include path, line, column")
        elif (
            not _is_non_empty_string(location["path"])
            or not isinstance(location["line"], int)
            or location["line"] < 1
            or not isinstance(location["column"], int)
            or location["column"] < 1
        ):
            errors.append(f"findings[{index}].location must use a path and positive line/column")
        if isinstance(location, dict) and "end_line" in location and (not isinstance(location["end_line"], int) or location["end_line"] < 1):
            errors.append(f"findings[{index}].location.end_line must be a positive integer")
        if isinstance(location, dict) and "end_column" in location and (not isinstance(location["end_column"], int) or location["end_column"] < 1):
            errors.append(f"findings[{index}].location.end_column must be a positive integer")
        if not isinstance(finding["affected_targets"], list):
            errors.append(f"findings[{index}].affected_targets must be a list")
        elif not all(_is_non_empty_string(target) for target in finding["affected_targets"]):
            errors.append(f"findings[{index}].affected_targets must contain strings")
        if not isinstance(finding["examples"], list) or not all(isinstance(example, str) for example in finding["examples"]):
            errors.append(f"findings[{index}].examples must be a list of strings")
        if not isinstance(finding["ignored"], bool):
            errors.append(f"findings[{index}].ignored must be boolean")
        if finding["suppression_reason"] is not None and not isinstance(finding["suppression_reason"], str):
            errors.append(f"findings[{index}].suppression_reason must be a string or null")
        if not isinstance(finding["metadata"], dict):
            errors.append(f"findings[{index}].metadata must be an object")
    for key in ("baseline", "contract", "verification", "summary"):
        if not isinstance(document.get(key), dict):
            errors.append(f"{key} must be an object")
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
        elif not all(_is_non_empty_string(driver[field]) for field in ("name", "semanticVersion")):
            errors.append(f"runs[{index}].tool.driver name and semanticVersion must be strings")
        for result_index, result in enumerate(run["results"]):
            if not isinstance(result, dict) or not {"ruleId", "level", "message", "locations"}.issubset(result):
                errors.append(f"runs[{index}].results[{result_index}] is missing required SARIF fields")
                continue
            if not _is_non_empty_string(result["ruleId"]):
                errors.append(f"runs[{index}].results[{result_index}].ruleId must be a string")
            if result["level"] not in {"error", "warning", "note", "none"}:
                errors.append(f"runs[{index}].results[{result_index}].level is invalid")
            if not isinstance(result["message"], dict) or not _is_non_empty_string(result["message"].get("text")):
                errors.append(f"runs[{index}].results[{result_index}].message must include text")
            locations = result["locations"]
            if not isinstance(locations, list) or not locations:
                errors.append(f"runs[{index}].results[{result_index}].locations must be a non-empty list")
                continue
            for location_index, location in enumerate(locations):
                physical = location.get("physicalLocation") if isinstance(location, dict) else None
                artifact = physical.get("artifactLocation") if isinstance(physical, dict) else None
                region = physical.get("region") if isinstance(physical, dict) else None
                if not isinstance(artifact, dict) or not _is_non_empty_string(artifact.get("uri")) or not isinstance(region, dict):
                    errors.append(f"runs[{index}].results[{result_index}].locations[{location_index}] must include artifact URI and region")
                    continue
                if not isinstance(region.get("startLine"), int) or region["startLine"] < 1 or not isinstance(region.get("startColumn"), int) or region["startColumn"] < 1:
                    errors.append(f"runs[{index}].results[{result_index}].locations[{location_index}] region must use positive start coordinates")
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
        "targets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "os", "shell", "runtime", "display_name"],
                "properties": {key: {"type": "string", "minLength": 1} for key in ("id", "os", "shell", "runtime", "display_name")},
            },
        },
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["target", "score", "status"],
                "properties": {
                    "target": {"type": "string", "minLength": 1},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "status": {"enum": sorted(_SCORE_STATUSES)},
                },
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["fingerprint", "rule_id", "title", "description", "location", "severity", "confidence", "affected_targets", "reason", "remediation", "examples", "code", "ignored", "suppression_reason", "metadata"],
                "properties": {
                    "fingerprint": {"type": "string"},
                    "rule_id": {"type": "string"},
                    "severity": {"enum": sorted(_SEVERITIES)},
                    "confidence": {"enum": sorted(_CONFIDENCES)},
                    "affected_targets": {"type": "array", "items": {"type": "string"}},
                    "ignored": {"type": "boolean"},
                    "location": {
                        "type": "object",
                        "required": ["path", "line", "column"],
                        "properties": {
                            "path": {"type": "string", "minLength": 1},
                            "line": {"type": "integer", "minimum": 1},
                            "column": {"type": "integer", "minimum": 1},
                        },
                    },
                    "metadata": {"type": "object"},
                },
            },
        },
        "baseline": {"type": "object"},
        "contract": {"type": "object"},
        "verification": {"type": "object"},
        "summary": {"type": "object"},
    },
}
