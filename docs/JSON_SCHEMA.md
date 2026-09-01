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

The nested contracts are intentionally stable:

| Nested value | Required shape |
|---|---|
| `targets[]` | `id`, `os`, `shell`, `runtime`, and `display_name` as non-empty strings |
| `scores[]` | `target` string, `score` integer `0..100`, `status` of `PASS`, `PARTIAL`, or `BLOCKED`; generated score counts are non-negative integers |
| `findings[]` | fingerprint, rule metadata, location, severity/confidence, affected target strings, reason/remediation, examples, code, ignored flag, nullable suppression reason, and object metadata |
| `findings[].location` | relative `path`, positive one-based `line`/`column`, and optional positive end coordinates |
| `baseline`, `contract`, `verification`, `summary` | JSON objects; their additional keys are versioned by the command that populated them |

When present, `summary.suppression_diagnostics` is a list of `{path, line,
rule_id, message}` objects for line markers that did not suppress a matching
finding. This keeps suppression mistakes auditable without inventing a
portability finding.

Consumers should treat additive keys as forward-compatible and gate on
`schema_version`, not on the order of object keys. Finding fingerprints are
stable only while the rule, source location, code, and reason remain unchanged.

AST-backed Node findings may include `metadata.analysis: "tree-sitter-ast"`, `metadata.language` (`javascript`, `typescript`, or `tsx`), an API name, and a bounded command/access classification. These fields are additive and consumers must ignore unknown metadata keys. AST analysis is still `verification.status: "INFERRED"` until an explicit runtime verification check records otherwise.

The runtime validator in `src/agent_xplat/schemas.py` checks the nested shape,
enums, coordinates, and score ranges without requiring another validation
dependency. `RESULT_SCHEMA` exposes the same JSON Schema-compatible contract
for consumers that want to integrate their own validator. SARIF output remains
SARIF 2.1.0 and is validated for its driver, result, message, artifact URI, and
positive source-region coordinates.
