# Verification Run

Run ID: `VX-2026-09-01-003`
Project: `agent-xplat` v1.0.0  
Verification plan: `docs/VERIFICATION_PLAN.md`  
Execution scope: local Windows host, isolated installs, fixture/report regression, and repository audit

## Local evidence

| Check | Result |
|---|---|
| `python -m compileall -q src` | PASS |
| `git diff --check` | PASS |
| `python -m pytest -q` | PASS — 88 passed |
| Snapshot report test | PASS — mixed fixture terminal output matches `tests/snapshots/mixed-terminal.txt` |
| `python -m pip wheel . --no-deps --wheel-dir <external-build-dir>` | PASS — `agent_xplat-1.0.0-py3-none-any.whl`; final hash/size recorded with the build evidence below |
| `agent-xplat --version` | PASS — `1.0.0` |
| All ten subcommand `--help` probes | PASS |
| Mixed fixture terminal scan | PASS as a negative test — expected exit code 1, seven active findings, target-specific matrix rendered |
| Node/TS AST fixture scan | PASS as a negative test — expected exit code 1, five findings with exact rule set AX-NODE-005/006/007/008 |
| JSON result validation | PASS — validator returned no errors, including AST metadata and coordinates |
| SARIF 2.1.0 validation | PASS — validator returned no errors, including AST locations/help |
| Markdown report required sections | PASS |
| Normalized repeated JSON scan | PASS — documents equal after removing nondeterministic `scan_timestamp`; fingerprints and scores are stable |
| Baseline clean scan | PASS — `CLEAN`, zero new findings |
| Baseline regression scan | PASS — `REGRESSION`, new finding blocked with exit code 1 |
| Git diff mode | PASS — reference tree materialized with `git archive`; no reference code executed; regression status is reported |
| `fix --dry-run` and fix idempotence | PASS — dry-run leaves files unchanged; only the tested CRLF shebang normalization is eligible for automatic fix |
| `agent-xplat test . --format json` | VERIFIED on current Windows/PowerShell host; project test command exited 0 and recorded the actual host only |
| Isolated editable install | PASS — parser dependencies and development extra installed; 88 tests passed in the isolated environment |
| Isolated wheel install and AST scan | PASS — installed version `1.0.0`; AST scan returned the expected portability gate code and valid JSON |
| Fresh `init` -> `init-ci` -> scan/report/baseline/diff/fix/doctor/badge chain | PASS; generated workflow scanned cleanly, baseline/diff were `CLEAN`, dry-run left configuration unchanged, and artifacts were read back |
| Runtime-verified badge without three-OS evidence | PASS negative test — refused with configuration/input exit code 2 |

## Evidence classification

- E1 — local static implementation, parser/rule, fixture, snapshot, and deterministic test evidence: PASS.
- E2 — JSON/SARIF/Markdown/schema, CLI, baseline/diff, fix, and isolated package evidence: PASS.
- E3 — current host runtime command: VERIFIED for Windows/PowerShell only.
- E4 — independent hosted Windows/macOS/Linux runner evidence: UNVERIFIED; no remote repository or completed hosted run was available.

Static findings remain `INFERRED`. The local runtime artifact records only the current Windows host and deliberately does not mark macOS or Linux as verified.

## Build evidence

- Wheel: `agent_xplat-1.0.0-py3-none-any.whl` from the external build directory
- Size: `71128` bytes
- SHA-256: `969021edd9e719b06aceb467c5db9d3939756a715226c3ceaa3493e846b8f53e`
- Metadata readback: package `agent-xplat`, version `1.0.0`, Python `>=3.10`, and the three bounded Tree-sitter runtime dependencies.
