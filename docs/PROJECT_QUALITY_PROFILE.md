# Project Quality Profile

## Selected rubric

Primary rubric: Software Feature (100 points). Documentation and repository audit are Required DoD extensions, not a substitute for feature evidence.

## Target

- Quality target for release-candidate implementation: 90/100.
- Required DoD and evidence validity take precedence over the numeric score.
- A missing actual three-OS runner result prevents a `READY FOR RELEASE` claim even if local score is high.

## Evidence plan

- E1: architecture, source, schema, fixture, and diff inspection.
- E2: focused/full pytest, packaging, schema, deterministic repeatability, CLI exit-code, and fix idempotence checks.
- E3: actual installed CLI flows and inspected generated JSON/SARIF/Markdown artifacts.
- E4: independent GitHub-hosted Windows/macOS/Linux runner results or equivalent real environments.

## Review limit

Two focused quality-improvement loops after initial evaluation, as allowed by the global self-review protocol.
