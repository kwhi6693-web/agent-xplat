# agent-xplat Project Operating Rules

This repository implements the active task in `docs/task-specification.md`.

## Project facts

- Purpose: Cross-OS runtime portability checker for AI agent workflows.
- Stack: Python 3.10+, standard-library-first; pytest is development-only.
- Source: `src/agent_xplat/`.
- Tests: `tests/` and `tests/fixtures/`.
- Documentation and decisions: `docs/`.
- Generated local reports: ignored by `.gitignore` and written only to explicit user targets.

## Commands

| Operation | Command | Status |
|---|---|---|
| Install editable | `python -m pip install -e ".[dev]"` | Verified locally |
| Tests | `python -m pytest -q` | Verified locally: 54 passed |
| Build | `python -m pip wheel . --no-deps --wheel-dir <external-build-dir>` | Verified locally: wheel `1.0.0` |
| Static scan | `python -m agent_xplat scan .` | Verified locally: clean self-scan |
| Runtime verification | `python -m agent_xplat test .` | Verified on current Windows/PowerShell host only; hosted matrix pending |

## Scope controls

- Preserve user changes and source fixtures.
- Do not add machine-specific absolute paths, credentials, tokens, telemetry, or network calls.
- Do not execute target code in scan/report/fix/baseline/diff/init/doctor commands.
- Runtime verification must use an explicit allowlisted command model and label unavailable environments rather than inferring success.
- Fixes must be high-confidence, deterministic, tested, dry-run capable, and idempotent.

## Gate discipline

Run focused tests after each implementation phase. Do not call a gate passed from a tool acknowledgement alone. The verification record in `docs/audit/verification-run.md` is updated only from actual command output.
