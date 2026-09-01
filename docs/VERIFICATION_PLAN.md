# Verification Plan

## Verification run

Each run records a timestamp, commit/tree identity, command, environment, exit code, result, artifact path/hash, and limitations in `docs/audit/verification-run.md`.

## Required local checks

1. `python -m pytest -q` — unit, rule, parser, CLI, configuration, reports, fix, baseline, diff, schema, and integration behavior.
2. `python -m pip install -e ".[dev]"` in a clean virtual environment — installation evidence.
3. `python -m agent_xplat --help` plus every subcommand `--help` — CLI contract evidence.
4. Fresh-clone-like command sequence from the README — end-to-end evidence.
5. A scan repeated twice with stable normalized JSON — determinism evidence.
6. Repository audit scripts/checks for secrets, machine paths, debug artifacts, placeholders, and generated-file scope.

## Cross-OS verification

GitHub Actions defines `windows-latest`, `macos-latest`, and `ubuntu-latest` jobs. Each job installs the package, runs tests, scans the repository, runs the safe verification path, uploads JSON/SARIF/Markdown artifacts, and publishes a job summary. Actual runner outcomes are required before labeling any matrix row `VERIFIED`.

## Failure policy

- A known failing Required check is `FAIL` and makes completion `NOT DONE`.
- An unavailable external runner is `UNVERIFIED` when no failure is known; it blocks release readiness but does not justify a fabricated result.
- A malformed configuration is exit code 2.
- An internal uncaught tool error is exit code 3.
- A portability gate failure is exit code 1.
- Retry only after diagnosing the failure; do not erase previous evidence.

## Evidence storage

Small, reviewable evidence records live in `docs/audit/`. Large generated reports stay outside source control unless they are explicitly part of a release artifact. No scanned source is uploaded.
