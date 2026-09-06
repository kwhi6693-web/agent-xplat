# Adoption upgrade: capability audit

Base commit: `6ca6c8fcfdfc515f8e8bcb4e456a683b09b43549` (1.0.1).
This task follows the user's approved adoption/real-world validation prompt. The
2026-09-01 task specification describes the original implementation and its old
local-only authorization; it is historical for this change. This task permits an
isolated branch and draft PR, but no merge, release, or third-party messages.

| Capability | Before | This change |
|---|---|---|
| Eight-target scan and JSON/SARIF/Markdown | Implemented | Reused; report provenance and new-findings section added |
| Baseline and Git diff | Implemented | Fix unchanged-error gating, severity threshold and line-shift matching |
| Generated CI | Self-development workflow assuming installable Python project | Consumer static workflow, separate scanner installation, isolated imports, summary/artifacts |
| Static badge | Rendered without running a scan | Run scan and save companion evidence |
| Runtime badge | Trusted three OS labels without source binding | Require matching clean source, version and per-OS command records |
| Rule detection | Each family rerun for every registered rule | Each family runs once |
| Markdown shell detection | Prose/backticks confused with commands | Bound shell/quote rules to conservative command examples |
| Deterministic fixes | CRLF shebang normalization only | Unchanged |
| External adoption | No evidence in this task | Generated shell steps exercised against an unrelated fixture; no real maintainer adoption claimed |

Original baseline test run: 88 passed on Linux, Python 3.12. Installation used an
isolated venv. No source target was installed or executed during corpus scans.
The existing self-scan excludes source, tests, docs, workflows and most metadata;
its zero findings cannot establish detector accuracy. The pinned external corpus
is the evidence for this change's limited accuracy improvements.

## Boundaries

Markdown extraction is conservative and is not a full Markdown or shell parser.
Unknown bare commands, nested/list fences and unusual formatting may be missed.
Path/runtime/Python rules still have context limitations. Explicit Bash/PowerShell
requirements and workflow runner declarations are not universally inferred.
Source-bound badge records are user-supplied assertions with reviewable links,
not authenticated attestations. Do not advertise universal compatibility or
unattended blocking of arbitrary repositories based on this candidate.
