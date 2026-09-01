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
- SHA-256: `8042a15b661de4a1c5ea54731b012839bd6c510c6c50e460e07dcaa703ebcdaa`
- Metadata readback: package `agent-xplat`, version `1.0.0`, Python `>=3.10`, and the three bounded Tree-sitter runtime dependencies.

## Hosted runner evidence

Hosted verification record: `VX-2026-09-01-004`
Repository: `https://github.com/kwhi6693-web/agent-xplat`
Workflow run: [33511871082](https://github.com/kwhi6693-web/agent-xplat/actions/runs/33511871082)
Workflow event: `push` to `master`
Workflow head SHA: `6b4ae053d7df0f0abacd064096b8f32c540ee00d`
Lifecycle: `AUDITED`
Overall result: `PASS`

| GitHub-hosted job | Job ID | Result | Runtime environment | Project test evidence |
|---|---:|---|---|---|
| `windows-latest` | `99869261153` | PASS | `windows-powershell` / Windows | `88 passed in 1.45s` |
| `macos-latest` | `99869261464` | PASS | `macos-zsh` / macOS | `88 passed in 0.79s` |
| `ubuntu-latest` | `99869261505` | PASS | `linux-bash` / Linux | `88 passed in 0.73s` |

Each job completed install, tests, static scan, controlled runtime verification, Markdown report, SARIF report, artifact upload, SARIF upload, and the workflow gates without a failed step. The enforcement steps were skipped after their preceding checks passed; this is the expected conditional path, not an unrun required check.

### Hosted evidence classification

- E4 — GitHub-hosted runner execution and independently downloaded artifacts: `VALID`, `PASS` for Windows, macOS, and Linux.
- Static `agent-xplat-scan.json` and `agent-xplat.sarif` remain `INFERRED`; no static artifact is treated as runtime proof.
- `agent-xplat-verification.json` is `RUNTIME` / `VERIFIED` and records only its corresponding hosted OS and shell/runtime class.

### Artifact readback

The GitHub Actions artifact API returned three non-expired artifacts, each bound to workflow run `33511871082` and head SHA `6b4ae053d7df0f0abacd064096b8f32c540ee00d`:

| Artifact | Contents | Readback |
|---|---|---|
| `agent-xplat-windows-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [windows]` |
| `agent-xplat-macos-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [macos]` |
| `agent-xplat-ubuntu-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [linux]` |

The downloaded file hashes were recorded in the release evidence outside source control. The public workflow file and README blob hashes also matched the local commit readback. The generated verified badge was accepted only after all three OS evidence files were combined and validated; the SVG readback contained `Cross-OS Verified` and the three OS labels.
