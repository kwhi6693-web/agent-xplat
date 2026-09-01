# Examples

The real analyzer fixtures live under `tests/fixtures/` so they can be tested. This directory contains a small user-facing walkthrough.

```bash
agent-xplat scan examples/mixed-workflow
agent-xplat scan examples/mixed-workflow --format json
agent-xplat fix examples/mixed-workflow --dry-run
```

The example intentionally contains a shell and path assumption. It is not a claim that any external agent product uses this exact file format.
