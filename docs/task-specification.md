# Task Specification: Agent Xplat v1.0 Full Implementation

## Identity and lifecycle

| Field | Value |
|---|---|
| Task | Agent Xplat v1.0 full implementation and release preparation |
| Objective | Implement a stable open-source CLI for cross-OS runtime portability analysis of AI-agent workflows, skills, configuration, and scripts |
| Project | agent-xplat |
| Target | New local repository under the configured project directory; release preparation artifacts only |
| Classification | Complex software feature: static analyzer, CLI, reports, bounded fixer, CI integration |
| Delivery class | Formal release candidate preparation |
| Risk level | L2 — multi-file/cross-component local change with meaningful regression risk; no production or external write is authorized |
| Specification status | APPROVED |
| Specification version | 1.0 |
| Approval authority | User, by the current implementation prompt |
| Approval basis | Current user request in this Codex task |
| Approval time | 2026-09-01 Asia/Shanghai |
| Activation status | ACTIVE |
| Activation check result | PASS |
| Activated by | Codex |
| Execution status | IMPLEMENTED; RELEASE VERIFICATION UNVERIFIED |

## Scope

### Authorized

- Create and modify only the new repository under the configured project directory.
- Implement the user-requested CLI, analyzers, rules, models, reports, fixes, baseline/diff, contract checks, CI workflow, fixtures, tests, documentation, and release metadata.
- Run local deterministic tests and safe capability probes; inspect but do not execute target-repository code during static commands.
- Record evidence and release limitations in project documentation.

### Prohibited

- Do not modify, move, or redirect the protected Codex workspace or any Codex/AppData/configuration directory.
- Do not publish, push, create a GitHub repository, install plugins, send external messages, or perform external writes.
- Do not claim macOS/Linux runtime or GitHub Actions success without actual runner evidence.
- Do not upload scanned source, call AI APIs, add telemetry, or execute unknown repository scripts during static analysis.
- Do not add SaaS, accounts, payments, MCP server, editor extensions, or unrelated repository-health features.

## Acceptance criteria

| ID | Required observable condition | Verification |
|---|---|---|
| AC-01 | `agent-xplat --help` and every required subcommand `--help` work from a clean environment | CLI test and fresh-install check |
| AC-02 | Scanner discovers the required agent/config/script/package file families with deterministic excludes, binary detection, file-size bound, line/column locations | Discovery/parser tests |
| AC-03 | Environment model covers Windows PowerShell/CMD/Git Bash/WSL, macOS zsh/bash, Linux bash/zsh with OS × Shell × Runtime target identities | Model and matrix tests |
| AC-04 | Core portability rules emit stable AX-* findings with severity, confidence, affected targets, reason, remediation, examples, and fingerprints | Rule fixture tests |
| AC-05 | Python uses AST/structured analysis where applicable; package.json scripts are parsed as JSON; shell and config syntax is located deterministically | Parser/rule tests |
| AC-06 | Scores are deterministic, target-specific, explainable, unit-tested, and reported as 0–100 | Scoring tests and JSON assertions |
| AC-07 | Config schema, global/line suppression, contract violations, baseline, and diff mode work and expose ignored/new/resolved findings | Configuration/baseline/diff tests |
| AC-08 | Terminal, stable JSON, SARIF 2.1.0, Markdown report, explain, badge, and doctor outputs are valid and distinguish inferred/static from verified/runtime evidence | Report/schema/CLI tests |
| AC-09 | Fix supports dry-run, only applies eligible deterministic fixes, proves idempotence, and produces no collateral edits | Fix tests and hash/diff inspection |
| AC-10 | `init-ci` generates Windows/macOS/Linux Actions with install, tests, scan, runtime verification, SARIF, and report artifacts | Workflow content tests |
| AC-11 | Project includes fixtures, release metadata, security/contribution docs, architecture/rules/schema docs, and truthful README examples | Repository audit and documentation checks |
| AC-12 | Full local regression passes; remote three-OS runner result is either recorded as PASS from actual evidence or disclosed as an explicit release blocker | Verification run and final gate record |

## Quality and verification binding

- Primary rubric: Software Feature, with Documentation checks as a project-required extension.
- Required DoD: all global DoD items plus AC-01–AC-12, packaging/build validation, schema validation, and scope/secrets audit.
- Quality target: 90/100 for release-candidate code quality; release readiness still requires every Required criterion and applicable runner evidence.
- Verification levels: E1 for source/structure inspection, E2 for deterministic tests/build/schema checks, E3 for actual CLI behavior and generated artifact inspection, E4 only for independent/real runner evidence.
- Final Governance applicability: NOT REQUIRED for local implementation/delivery because no production release, external write, or scope beyond this controlled repository is requested. If a future publish action is requested, re-evaluate under the canonical Governance rule.

## Decomposition and recovery

1. Architecture and project contract.
2. Core engine and data model.
3. Rule families and fixtures.
4. CLI and report formats.
5. Fix engine and verification workflow.
6. CI/docs/release metadata.
7. Full regression and audit.

Each phase has a gate. On failure, inspect the cause, patch the smallest responsible component, and rerun that phase's focused tests before proceeding. Recovery is local file restoration from the working tree diff; no destructive reset or source overwrite is permitted.

## Expected outputs

- Source package, tests, fixtures, examples, CI workflow, package metadata, documentation, and audit records under this repository.
- A runnable `agent-xplat` console script and `python -m agent_xplat` fallback.
- Final delivery report in the assistant response with completion status, evidence levels, limitations, and release readiness.
