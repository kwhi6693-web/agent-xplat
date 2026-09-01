# Project Definition of Done

The global Quality Standard Definition of Done applies first. For this project, all of the following are Required:

- The active task acceptance table is complete; every AC-01–AC-12 has current evidence.
- `python -m pytest -q` passes with rule, parser, CLI, report, schema, baseline, diff, config, and fix coverage.
- Package metadata builds without machine-specific paths or untracked generated artifacts.
- The scanner does not execute target code and default commands do not access the network.
- JSON and SARIF outputs validate structurally; Markdown and terminal output are readable in non-color CI mode.
- Fix dry-run is immutable; applied fixes are eligible-only, idempotent, and scope-limited.
- The CI workflow contains actual Windows, macOS, and Linux jobs. CI status is marked VERIFIED only after real runner output exists.
- Secrets, tokens, private URLs, debug files, absolute local paths, and misleading claims are absent from the repository.
- Known limitations, unverified runner evidence, and release blockers are disclosed in the final audit.

If local implementation is complete but remote runner evidence is unavailable, completion is `IMPLEMENTED BUT NOT VERIFIED` for release readiness rather than `DONE` for the entire release claim.
