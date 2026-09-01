# Agent Xplat v1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkboxes for tracking.

**Goal:** Build a deterministic, read-only-by-default Python CLI that identifies cross-OS assumptions in AI-agent workflows, skills, agent configuration, and related scripts, then reports, safely fixes, baselines, and distinguishes inferred portability from real runner verification.

**Architecture:** A small standard-library-first Python package separates immutable domain models, target discovery, structured Python/JSON parsing, Tree-sitter JavaScript-family parsing, text/shell rules, scoring, contract evaluation, reporting, fixing, and controlled verification. The environment model is `OS × Shell × Runtime`; each finding carries affected target IDs, severity, confidence, source location, suppression state, and deterministic fingerprints. CLI commands orchestrate one scan result schema used by terminal, JSON, SARIF, Markdown, baseline, diff, CI, and agent callers.

**Tech Stack:** Python 3.10+ (tested on Python 3.12), `argparse`, `ast`, `json`, `pathlib`, `tomllib`-compatible standard library modules, a dependency-free YAML subset parser/validator for the documented configuration schema, and narrowly scoped Tree-sitter JavaScript/TypeScript grammar bindings for source AST analysis. `pytest` is a development-only test dependency. GitHub Actions supplies the real Windows/macOS/Linux verification matrix.

**Spec:** The active task contract is `docs/task-specification.md`; the user-provided Agent Xplat v1.0 implementation prompt is the governing product specification.

## Global Constraints

- Core identity: **Cross-OS Runtime Portability for AI Agent Workflows**.
- Default scan is read-only, local, deterministic, offline, non-executing, and non-telemetric.
- Targets are modeled as OS × Shell × Runtime, not OS-only.
- No target repository code executes during `scan`, `report`, `baseline`, `diff`, `fix`, `doctor`, `init`, or `init-ci`.
- `test` is explicit, bounded runtime verification and reports `INFERRED` versus `VERIFIED`.
- Automatic fixes require high confidence, deterministic replacement, semantic-equivalence rationale, and tests.
- Source files are preserved; fixes support dry-run and never rewrite unrelated files.
- Excludes include `.git`, `node_modules`, `vendor`, `dist`, `build`, common caches, binaries, and files over the configured size limit.
- Exit codes: 0 pass, 1 portability gate failure, 2 configuration/input error, 3 internal error.
- No SaaS, account system, AI API, MCP server, telemetry, or hidden network access.

---

### Task 1: Active project and domain contract

**Files:**
- Create: `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/PROJECT_RULES.md`, `docs/PROJECT_DEFINITION_OF_DONE.md`, `docs/PROJECT_QUALITY_PROFILE.md`, `docs/VERIFICATION_PLAN.md`, `docs/DECISIONS.md`, `docs/task-specification.md`
- Create: `docs/decisions/0001-python-standard-library-first.md`
- Create: `src/agent_xplat/__init__.py`, `src/agent_xplat/__main__.py`, `pyproject.toml`

**Interfaces:**
- Package name `agent_xplat`; console entry point `agent-xplat` calls `agent_xplat.cli:main`.
- Active target IDs are stable strings such as `windows-powershell`, `linux-bash`, and `macos-zsh`.

- [x] Write package metadata and the active L2 task/verification records.
- [x] Record the Python decision and explicit non-goals.
- [x] Verify the package imports and the entry point can print help.

### Task 2: Domain models, targets, config, and discovery

**Files:**
- Create: `src/agent_xplat/models.py`, `src/agent_xplat/environments.py`, `src/agent_xplat/config.py`, `src/agent_xplat/discovery.py`, `src/agent_xplat/parsers.py`
- Test: `tests/test_models_config_discovery.py`, `tests/test_parsers.py`

**Interfaces:**
- `Target(id, os, shell, runtime)`; `Finding`; `ScanResult`; `Config`; `SourceLocation`.
- `load_config(root: Path) -> Config` validates `.agent-xplat.yml` and produces actionable configuration errors.
- `discover_files(root: Path, config: Config) -> list[Path]` is bounded and deterministic.
- `parse_python(path)` uses `ast`; JSON manifests use `json`; text retains exact line/column data.

- [x] Write failing tests for target matrix, config validation, excludes, size/binary bounds, and line/column parsing.
- [x] Implement models/config/discovery/parsers.
- [x] Run focused tests and then the core test slice.

### Task 3: Rule registry and portability detectors

**Files:**
- Create: `src/agent_xplat/rules/__init__.py`, `src/agent_xplat/rules/registry.py`, `src/agent_xplat/rules/common.py`
- Create: `src/agent_xplat/rules/paths.py`, `shell.py`, `filesystem.py`, `env.py`, `python.py`, `node.py`, `runtimes.py`, `executables.py`, `quoting.py`, `line_endings.py`, `package_managers.py`, `external_tools.py`, `agent_config.py`
- Test: `tests/test_rules_paths_shell.py`, `tests/test_rules_languages.py`, `tests/test_rules_filesystem_tools.py`, fixture files under `tests/fixtures/`

**Interfaces:**
- Rule protocol `Rule.analyze(file: SourceFile, context: RuleContext) -> Iterable[Finding]`.
- Registry exposes `get_rule(rule_id)` and `all_rules()`; rules use stable AX-* IDs.
- Findings have deterministic fingerprints and never silently disappear when ignored.

- [x] Write positive/negative fixture tests for path, shell, environment syntax, Python, Node, filesystem, package-manager, external-tool, and agent-file assumptions.
- [x] Implement structured parsing for Python imports/AST, package.json scripts, and JavaScript-family source AST; use narrowly scoped lexical detectors for shell/text.
- [x] Add per-target impact mapping, severity, confidence, remediation, examples, and line/column anchors.
- [x] Run rule slices and verify no fixture uses a hard-coded expected score.

### Task 4: Engine, suppression, contract, and scoring

**Files:**
- Create: `src/agent_xplat/engine.py`, `src/agent_xplat/suppression.py`, `src/agent_xplat/contracts.py`, `src/agent_xplat/scoring.py`, `src/agent_xplat/baseline.py`, `src/agent_xplat/diff.py`
- Test: `tests/test_engine_scoring.py`, `tests/test_suppression_contract.py`, `tests/test_baseline_diff.py`

**Interfaces:**
- `scan(root, config) -> ScanResult`.
- `score_findings(findings, targets) -> dict[target_id, Score]` with explainable caps/penalties.
- `evaluate_contract(config, targets, findings) -> ContractResult`.
- `compare_baseline(current, baseline) -> BaselineComparison`; `compare_scan(before, after) -> DiffResult`.

- [x] Write failing tests for deterministic score math, target-specific impact, global and line suppressions, contract violations, baseline new/existing/resolved states, and diff regressions.
- [x] Implement the engine and stable JSON-safe result model.
- [x] Verify repeat scans produce identical findings, fingerprints, target ordering, and scores.

### Task 5: CLI, reports, and agent-facing outputs

**Files:**
- Create: `src/agent_xplat/cli.py`, `src/agent_xplat/terminal.py`, `src/agent_xplat/reporting.py`, `src/agent_xplat/schemas.py`, `src/agent_xplat/explain.py`, `src/agent_xplat/init.py`
- Test: `tests/test_cli.py`, `tests/test_reports.py`, `tests/test_schema_sarif.py`, `tests/test_init_commands.py`

**Interfaces:**
- Commands: `scan`, `test`, `fix`, `report`, `explain`, `doctor`, `baseline`, `init`, `init-ci`, `badge`.
- `scan --format json|sarif|markdown|terminal`; JSON schema version is `1.0` and SARIF is 2.1.0.
- Every command supports `--help`; non-color output is default-safe for CI.

- [x] Write CLI tests for success, gate failure, invalid config, missing rule, output formats, and all exit codes.
- [x] Implement terminal/JSON/SARIF/Markdown renderers, stable timestamps option, explain output, init files, badge SVG/text, and doctor capability facts.
- [x] Validate generated JSON/SARIF structurally and assert messages include file, line, rule, severity, and help.

### Task 6: Bounded fix engine and runtime verification

**Files:**
- Create: `src/agent_xplat/fixing.py`, `src/agent_xplat/verification.py`
- Test: `tests/test_fixing.py`, `tests/test_verification.py`

**Interfaces:**
- `plan_fixes(scan_result) -> list[Fix]`; `apply_fixes(root, fixes, dry_run) -> FixResult`.
- `run_verification(root, config) -> VerificationResult` only executes the project-defined safe verification command model and records unavailable environments as not verified.

- [x] Write failing tests for dry-run immutability, high-confidence deterministic replacements, idempotence, no collateral edits, and inferred/verified separation.
- [x] Implement only narrowly proven fixes such as portable `python` launcher guidance and safe line suppression insertion where the exact replacement is known; leave risky rewrites as suggestions.
- [x] Implement controlled local capability probing and GitHub Actions workflow generation without executing arbitrary repository scripts during scan.
- [x] Verify fix plans before/after with hashes and diff inspection.

### Task 7: Fixtures, CI, metadata, and documentation

**Files:**
- Create: `tests/fixtures/**`, `examples/**`, `.github/workflows/agent-xplat.yml`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/release.yml`
- Create: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `docs/JSON_SCHEMA.md`, `docs/RULES.md`, `docs/ARCHITECTURE.md`, `docs/RELEASE_NOTES_TEMPLATE.md`
- Test: `tests/test_regression.py`

- [x] Populate real fixtures with expected findings, affected environments, severity, and confidence manifests.
- [x] Generate a three-runner workflow for install, tests, scan, runtime verification, SARIF, and Markdown artifacts.
- [x] Document every implemented command, exit code, rule family, schema, safety boundary, competitive boundary, and limitation.
- [x] Run a fresh-clone-like install/init/scan/report/baseline/diff/fix dry-run/doctor/init-ci sequence.

### Task 8: Gates, audit, and release candidate assessment

**Files:**
- Create: `docs/audit/requirements-matrix.md`, `docs/audit/repository-audit.md`, `docs/audit/verification-run.md`, `docs/audit/gate-decision-package.md`
- Modify: `docs/PROJECT_DEFINITION_OF_DONE.md`, `docs/VERIFICATION_PLAN.md`, `CHANGELOG.md`

- [x] Run full local test suite, packaging/build checks, CLI regression, schema checks, and repository audit.
- [x] Inspect the final diff for secrets, machine paths, debug artifacts, placeholders, and unverified claims.
- [x] Record local evidence honestly; mark macOS/Linux runner evidence as unverified unless actual GitHub Actions results are available.
- [x] Decide `READY FOR RELEASE` only if all required evidence exists; otherwise report `NOT READY` with only real blockers.

## Plan self-review

- Requirements map to Tasks 2–7: environment model, scanning, rules, scores, config/ignore, baseline/diff, explain, fix, runtime verification, CI, SARIF/JSON/Markdown, badge/doctor/init, fixtures, docs, and metadata.
- The plan keeps runtime dependencies limited to parser bindings and does not claim local evidence for unavailable operating systems.
- All production interfaces referenced by later tasks are defined in earlier task contracts.
- The only known release evidence gap after local implementation hardening is real GitHub-hosted Windows/macOS/Linux CI execution; it must be re-read from an actual workflow run.
