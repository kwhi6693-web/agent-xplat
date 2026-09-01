# Agent Xplat v1.0 Requirements Matrix

Audit run: `VX-2026-09-01-003`
Specification: `docs/task-specification.md` v1.0  
Scope: post-hardening local release-candidate implementation and evidence review

| Requirement | Implementation | Test / evidence | Status |
|---|---|---|---|
| AC-01 CLI contract and stable exit codes | `src/agent_xplat/cli.py` | CLI tests, invalid-input tests, all ten command help probes, isolated `1.0.0` entry point | PASS |
| AC-02 Bounded deterministic discovery | `src/agent_xplat/discovery.py` | Discovery bounds/exclude/binary tests; deterministic traversal; all documented source suffixes | PASS |
| AC-03 Eight OS × Shell × Runtime targets | `src/agent_xplat/environments.py` | Target model tests, report matrix assertions, Node WSL/Git Bash runtime mapping tests | PASS |
| AC-04 Modular rules with metadata and target impact | `src/agent_xplat/rules/` and `docs/RULES.md` | 49-rule registry/documentation coverage, rule tests, fixture catalog, severity/confidence assertions | PASS |
| AC-05 Structured Python/JSON/JavaScript/TypeScript analysis | `parsers.py`, Python AST, JSON token spans, Tree-sitter JavaScript/TypeScript/TSX adapter, `rules/node_ast.py` | Parser tests, all eight suffixes, binding variants, guarded branches, malformed-source recovery, scoped package JSON tests, AST fixture | PASS |
| AC-06 Deterministic explainable scoring | `src/agent_xplat/scoring.py` | Score math tests, AST score assertions, repeated normalized JSON comparison | PASS |
| AC-07 Config, suppression, contract, baseline, diff | `config.py`, `suppression.py`, `contracts.py`, `baseline.py`, `diff.py` | Configuration/duplicate/unknown-rule tests, suppression diagnostics, contract tests, baseline regression, Git diff test, end-to-end chain | PASS |
| AC-08 Terminal, JSON, SARIF, Markdown, explain, badge, doctor | `reporting.py`, `schemas.py`, `explain.py`, `init.py`, `doctor.py` | Schema validators, SARIF/AST location-help checks, Markdown section checks, snapshot test, CLI tests, badge negative case | PASS |
| AC-09 Safe deterministic autofix and dry-run | `src/agent_xplat/fixing.py` | Before/after, idempotence, no-collateral-change, and dry-run tests; AST rules remain suggestion-only | PASS |
| AC-10 Three-runner GitHub Actions generation | `.github/workflows/agent-xplat.yml` and `init.py` | Workflow content test and static inspection of Windows/macOS/Linux matrix, artifacts, and gates | PASS (workflow present; execution unverified) |
| AC-11 Fixtures, docs, metadata, package build | `tests/fixtures/`, `tests/snapshots/`, README/docs, package metadata, repository templates | Full local suite, documentation contract, isolated editable install, isolated wheel install, wheel metadata readback | PASS |
| AC-12 Full regression plus actual hosted three-OS runner evidence | Local tests, generated workflow, current Windows runtime artifact | `88 passed`, local Windows runtime evidence, and workflow definition; no completed hosted run/artifact readback is available | UNVERIFIED |

The only release-readiness evidence gap is AC-12's actual `windows-latest`, `macos-latest`, and `ubuntu-latest` run result and artifact readback. The workflow file itself is not treated as runtime evidence.
