# Contributing

## Development setup

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Rule changes

Add a positive and negative fixture, assert the exact rule ID/location/affected target/severity/confidence, and update `docs/RULES.md` when adding a rule. Keep rule detectors deterministic and do not use an AI service or network call.

## CLI and schema changes

Preserve the JSON schema within the v1.0 contract. Add CLI tests for success, invalid input, and the documented exit code. SARIF changes must retain version 2.1.0 validity.

## Fixes and runtime checks

Autofixes need a failing test first, a dry-run assertion, an idempotence assertion, and a no-collateral-change assertion. Runtime verification must be explicit, bounded, allowlisted, and labeled with the actual environment.

## Pull requests

Describe the portability problem, affected targets, tests run, and any environment evidence. Do not include secrets, user source uploads, machine-specific paths, or claims based only on an unrun workflow.
