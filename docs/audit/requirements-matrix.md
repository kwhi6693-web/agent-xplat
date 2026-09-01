# Agent Xplat v1.0 Requirements Matrix

Audit run: `VX-2026-09-01-001`  
Specification: `docs/task-specification.md` v1.0  
Scope: local release-candidate implementation and evidence review

| Requirement | Implementation | Test / evidence | Status |
|---|---|---|---|
| AC-01 CLI contract and stable exit codes | `src/agent_xplat/cli.py` | `tests/test_cli.py`, `tests/test_cli_extra.py`, all ten command help probes | PASS |
| AC-02 Bounded deterministic discovery | `src/agent_xplat/discovery.py` | `tests/test_models_config_discovery.py`, binary/size/exclude checks | PASS |
| AC-03 Eight OS × Shell × Runtime targets | `src/agent_xplat/environments.py` | `tests/test_models_config_discovery.py`, JSON matrix output | PASS |
| AC-04 Modular rules with metadata and target impact | `src/agent_xplat/rules/` and `docs/RULES.md` | rule and fixture tests; registry/documentation coverage | PASS |
| AC-05 Structured Python/JSON analysis | `src/agent_xplat/parsers.py`, Python AST and package JSON detectors | `tests/test_parsers.py`, `tests/test_rules_languages.py` | PASS |
| AC-06 Deterministic explainable scoring | `src/agent_xplat/scoring.py` | repeated-scan score/fingerprint assertions | PASS |
| AC-07 Config, suppression, contract, baseline, diff | `config.py`, `suppression.py`, `contracts.py`, `baseline.py`, `diff.py` | `tests/test_suppression_contract.py`, `tests/test_baseline_diff.py`, manual baseline regression | PASS |
| AC-08 Terminal, JSON, SARIF, Markdown, explain, badge, doctor | `reporting.py`, `schemas.py`, `explain.py`, `init.py`, `doctor.py` | JSON/SARIF validators, report section checks, CLI tests | PASS |
| AC-09 Safe deterministic autofix and dry-run | `src/agent_xplat/fixing.py` | `tests/test_fixing.py`; dry-run output and idempotence assertions | PASS |
| AC-10 Three-runner GitHub Actions generation | `.github/workflows/agent-xplat.yml` and `init.py` | workflow content test; static inspection of Windows/macOS/Linux matrix | PASS (workflow present) |
| AC-11 Fixtures, docs, metadata, package build | `tests/fixtures/`, `README.md`, package metadata and repository templates | documentation contract tests, isolated wheel installation | PASS |
| AC-12 Full regression plus actual hosted three-OS runner evidence | local tests and generated workflow exist | 53 local tests and Windows runtime evidence; no configured remote/hosted run available | UNVERIFIED |

The only release-readiness evidence gap is AC-12's actual `windows-latest`, `macos-latest`, and `ubuntu-latest` run result. The workflow file itself is not treated as runtime evidence.
