# Architecture

## Design goal

Agent Xplat answers one question: which assumptions in an AI-agent workflow can break when the same workflow moves across a specific OS, shell, and runtime context?

## Data flow

```text
.agent-xplat.yml
        |
        v
OS × Shell × Runtime target matrix
        |
        v
bounded deterministic discovery
        |
        +--> Python AST / JSON / text parsers
        |
        v
modular AX-* rules
        |
        v
Finding {location, severity, confidence, affected_targets, fingerprint}
        |
        +--> suppression audit
        +--> target score and status
        +--> Compatibility Contract
        +--> baseline / Git diff
        |
        v
terminal | JSON 1.0 | SARIF 2.1.0 | Markdown | fix/test artifacts
```

## Modules

| Module | Responsibility |
|---|---|
| `models.py` | Stable dataclasses for targets, locations, findings, scores, and scan results |
| `environments.py` | The eight first-class OS × Shell × Runtime target identities |
| `config.py` | Documented YAML subset parser, defaults, and schema validation |
| `discovery.py` | Deterministic include/exclude traversal, binary and size bounds |
| `parsers.py` | Python AST and JSON parsing without code execution |
| `rules/` | Focused detectors and rule metadata registry |
| `engine.py` | Scan orchestration and repository metadata checks |
| `suppression.py` | Global and line-level suppression with audit state |
| `scoring.py` | Repeatable target-specific score penalties and status mapping |
| `contracts.py` | Declared support versus detected assumptions |
| `baseline.py`, `diff.py` | Fingerprint state and Git reference comparisons |
| `reporting.py`, `schemas.py` | Public JSON, SARIF, Markdown, terminal, and validation contracts |
| `fixing.py` | Eligible deterministic fixes with hashes and dry-run patches |
| `verification.py` | Explicit bounded runtime command execution and evidence labeling |
| `doctor.py`, `init.py` | Local capability reporting and project/CI artifact generation |
| `cli.py` | Stable command surface and exit-code boundary |

## Target model

The target ID is not an alias for an OS. For example, `windows-powershell` and `windows-git-bash` share an OS but have different command, quoting, executable, and environment semantics. `runtime` further distinguishes native Windows, Git Bash, WSL, and native Unix execution contexts. Rules compute affected target IDs, then scoring aggregates only those targets.

## Finding contract

Every finding has a stable rule ID, title, description, relative source path, one-based line/column, severity, confidence, affected target IDs, reason, remediation, code context, and a fingerprint. Suppression never removes a finding; it marks it ignored and increments the summary. Fingerprints are deterministic SHA-256 prefixes over rule, location, code, and reason.

## Static safety boundary

Discovery reads bytes and metadata. Python analysis uses `ast.parse`, not `import`. JSON is parsed as data. Shell snippets are inspected lexically. No scan path invokes a target script, package manager, subprocess, shell, or network. The separate `test` command is the explicit runtime boundary and only runs a no-shell-operator allowlisted command with a timeout.

## Scoring

Each active finding applies a fixed penalty to each affected target: blocker 35, error 20, warning 8, info 2. The score is `max(0, 100 - total penalties)`. A target is `BLOCKED` with any blocker, `PASS` at or above the configured minimum with no errors, and `PARTIAL` otherwise. The math is intentionally simple enough to explain in a report and test exactly.
