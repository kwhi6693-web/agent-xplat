# Verification Run

Run ID: `VX-2026-09-01-001`  
Project: `agent-xplat` v1.0.0  
Verification plan: `docs/VERIFICATION_PLAN.md`  
Execution scope: local Windows host plus isolated package installation

## Local evidence

| Check | Result |
|---|---|
| `python -m compileall -q src` | PASS |
| `git diff --check` | PASS |
| `python -m pytest -q` | PASS — 53 passed |
| `python -m pip wheel . --no-deps --wheel-dir <external-build-dir>` | PASS — `agent_xplat-1.0.0-py3-none-any.whl` |
| `agent-xplat --version` | PASS — `1.0.0` |
| All ten subcommand `--help` probes | PASS |
| Mixed fixture terminal scan | PASS as a negative test — expected exit code 1, seven active findings, target-specific matrix rendered |
| JSON result validation | PASS — validator returned no errors |
| SARIF 2.1.0 validation | PASS — validator returned no errors |
| Markdown report required sections | PASS |
| Baseline clean scan | PASS — `CLEAN`, zero new findings |
| Baseline regression scan | PASS — `REGRESSION`, new findings blocked with exit code 1 |
| `fix --dry-run` on mixed fixture | PASS — no files modified; no safe fixes available |
| `agent-xplat test . --format json` | VERIFIED on current Windows/PowerShell host; project command exited 0 with 53 passed |
| Isolated wheel install and scan of portable fixture | PASS — installed without runtime dependencies; JSON output valid and no active findings |
| `init`, `init-ci`, and static badge generation | PASS; generated files read back and inspected |
| Runtime-verified badge without three-OS evidence | PASS negative test — refused with configuration/input exit code 2 |

## Evidence classification

- E1 — local static implementation and deterministic test evidence: PASS.
- E2 — JSON/SARIF/Markdown/schema and CLI evidence: PASS.
- E3 — current host runtime command: VERIFIED for Windows/PowerShell only.
- E4 — independent hosted Windows/macOS/Linux runner evidence: UNVERIFIED; no remote repository or completed hosted run was available.

Static findings remain `INFERRED`. The local runtime artifact records only the current Windows host and deliberately does not mark macOS or Linux as verified.
