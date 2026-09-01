# JSON result schema 1.0

`agent-xplat scan --format json` emits an object with the following required top-level keys:

| Key | Type | Purpose |
|---|---|---|
| `schema_version` | string | Public result schema, currently `1.0` |
| `tool_version` | string | Agent Xplat version |
| `scan_timestamp` | string | UTC scan time |
| `targets` | array | OS, shell, runtime target descriptors |
| `scores` | array | Per-target score, status, and severity counts |
| `findings` | array | Findings, including ignored entries and fingerprints |
| `baseline` | object | Baseline/diff status and counts |
| `contract` | object | Declared support, requirements, and violations |
| `verification` | object | Inferred/runtime evidence state |
| `summary` | object | File, finding, suppression, and contract counts |

`findings[].location` uses relative POSIX paths and one-based `line` and `column`. `severity` is `BLOCKER`, `ERROR`, `WARNING`, or `INFO`; `confidence` is `HIGH`, `MEDIUM`, or `LOW`. `affected_targets` contains stable target IDs from the matrix.

The runtime validator in `src/agent_xplat/schemas.py` checks required shape and score ranges without requiring a schema dependency. `RESULT_SCHEMA` exposes a JSON Schema-compatible summary for consumers that want to integrate their own validator.
