# JavaScript/TypeScript AST Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Node source limitation with deterministic Tree-sitter JavaScript/JSX/TypeScript/TSX analysis while reducing package-script false positives and preserving the existing cross-OS finding contract.

**Architecture:** Keep the existing Python CLI, rule registry, target matrix, scoring, suppression, and report contracts. Add a small parser adapter in `parsers.py` that selects one Tree-sitter grammar by suffix and exposes immutable AST facts/locations to `rules/node.py`; package JSON detection will operate only on parsed `scripts` values. The new source rules remain static inference, use conservative target impact, and never execute JavaScript or invoke a shell.

**Tech Stack:** Python 3.10+, `tree-sitter` 0.26.x, `tree-sitter-javascript` 0.25.x, `tree-sitter-typescript` 0.23.x, pytest. Tree-sitter is selected because its Python `Parser` accepts an explicit grammar and the published JavaScript grammar covers JavaScript and JSX while the TypeScript package exposes TypeScript and TSX grammars.

**Spec:** `docs/audit/gap-analysis.md`, `docs/task-specification.md`, and the original Agent Xplat v1.0 implementation prompt.

## Global Constraints

- Preserve the OS × Shell × Runtime target model and stable `AX-*` finding/output contracts.
- Scan remains offline, read-only, deterministic, bounded, and never executes target code.
- Only high-confidence deterministic fixes remain auto-fixable; AST findings are suggestion-only.
- Keep native parser dependencies limited to JavaScript/TypeScript analysis and document their licenses/install impact.
- Add a positive and negative test for every new AST behavior, including a correctly guarded platform branch.
- Do not claim hosted Windows/macOS/Linux evidence until an actual GitHub runner result is read back.

---

### Task 1: Establish failing parser, discovery, and false-positive tests

**Files:**
- Modify: `tests/test_parsers.py`
- Modify: `tests/test_models_config_discovery.py`
- Modify: `tests/test_rules_languages.py`
- Modify: `tests/test_false_positive_controls.py`
- Create: `tests/fixtures/node-ast/expected.json`
- Create: `tests/fixtures/node-ast/workflow.ts`
- Create: `tests/fixtures/node-ast/guarded.ts`
- Create: `tests/fixtures/node-ast/component.tsx`

**Interfaces:**
- The tests will require `parse_javascript(source) -> ParsedJavaScript` and `javascript_suffixes()` from `agent_xplat.parsers`.
- The tests will require source findings for `child_process`, platform branches, environment access, path APIs, and shell strings to expose new stable rule IDs.

- [x] **Step 1: Add parser tests that demand all supported JavaScript-family suffixes.**

```python
def test_javascript_parser_selects_js_tsx_grammars(tmp_path: Path):
    for name, text, language in (
        ("tool.js", "const cp = require('child_process'); cp.exec('rm -rf dist');", "javascript"),
        ("tool.jsx", "export const View = () => <div />;", "javascript"),
        ("tool.ts", "const p: string = process.platform;", "typescript"),
        ("tool.mts", "export const value: number = 1;", "typescript"),
        ("tool.cts", "module.exports = { value: 1 };", "typescript"),
        ("tool.tsx", "export const View = () => <div />;", "tsx"),
    ):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        parsed = parse_javascript(source_file_from_path(path, tmp_path))
        assert parsed.tree is not None
        assert parsed.language == language
        assert parsed.syntax_error is None
```

- [x] **Step 2: Add a malformed-source test and run it before implementation.**

Run: `python -m pytest tests/test_parsers.py -q`

Expected: FAIL because `parse_javascript` and the new structured parser contract do not exist yet.

- [x] **Step 3: Add discovery assertions for `.jsx`, `.mts`, `.cts`, and `.tsx`.**

```python
for name in ("view.jsx", "module.mts", "module.cts", "view.tsx"):
    (tmp_path / name).write_text("export const value = 1;\n", encoding="utf-8")
assert {item.relative_path for item in discover_files(tmp_path, Config())} >= {
    "view.jsx", "module.mts", "module.cts", "view.tsx"
}
```

- [x] **Step 4: Add rule tests for guarded and unguarded platform branches plus non-script JSON text.**

```python
guarded = """
if (process.platform === "win32") {
  usePowerShell();
} else {
  useBash();
}
"""
assert "AX-NODE-007" not in {f.rule_id for f in analyze(guarded, "workflow.js")}

unguarded = 'const command = process.platform === "win32" ? "cmd.exe" : "bash";\n'
assert "AX-NODE-007" in {f.rule_id for f in analyze(unguarded, "workflow.js")}

package_json = '{"description":"rm is mentioned","dependencies":{"rm":"1.0.0"},"scripts":{"build":"node build.js"}}'
assert "AX-NODE-002" not in {f.rule_id for f in analyze(package_json, "package.json")}
```

- [x] **Step 5: Run the focused tests again and record the expected red failures before production edits.**

The pre-implementation focused run failed at collection because the parser
adapter was intentionally absent; after the adapter and rule wiring, the same
slice passed.

Run: `python -m pytest tests/test_parsers.py tests/test_models_config_discovery.py tests/test_rules_languages.py tests/test_false_positive_controls.py -q`

Expected: FAIL only on the new parser/discovery/AST assertions, not on existing behavior.

### Task 2: Add the structured JavaScript/TypeScript parser adapter

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/agent_xplat/parsers.py`
- Test: `tests/test_parsers.py`
- Create: `docs/decisions/0002-tree-sitter-javascript-typescript-parser.md`

**Interfaces:**
- `ParsedJavaScript(tree: object | None, language: str, syntax_error: str | None, source_bytes: bytes)`.
- `parse_javascript(source: SourceFile) -> ParsedJavaScript`.
- `javascript_suffixes() -> frozenset[str]`.
- `iter_named_nodes(parsed: ParsedJavaScript, node_type: str | None = None) -> Iterator[object]`.

- [x] **Step 1: Declare bounded parser dependencies and document the decision.**

Add to `[project].dependencies`:

```toml
"tree-sitter>=0.26,<0.27",
"tree-sitter-javascript>=0.25,<0.26",
"tree-sitter-typescript>=0.23,<0.24",
```

The ADR records that the new dependencies are the smallest maintained grammar set that closes the requested source-AST gap, are MIT licensed, support Python 3.10+, and do not execute scanned code.

- [x] **Step 2: Select grammars by suffix and parse UTF-8 bytes with a bounded parser.**

```python
JAVASCRIPT_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".jsx"})
TYPESCRIPT_SUFFIXES = frozenset({".ts", ".mts", ".cts"})
TSX_SUFFIXES = frozenset({".tsx"})

def parse_javascript(source: SourceFile) -> ParsedJavaScript:
    language_name, language = _language_for_suffix(source.path.suffix.lower())
    parser = Parser(language)
    tree = parser.parse(source.text.encode("utf-8"))
    return ParsedJavaScript(tree, language_name, _syntax_error(tree), source.text.encode("utf-8"))
```

Use named-node traversal only; no query or evaluation path may execute source. Record parser errors as metadata and continue lexical analysis rather than raising an internal error for recoverable syntax errors.

- [x] **Step 3: Add byte-to-source location helpers and parser tests.**

Test root language, named node kinds, syntax-error reporting, Unicode before the finding, JSX, TS type annotations, and no subprocess/import execution. Run: `python -m pytest tests/test_parsers.py -q`.

- [x] **Step 4: Run the full existing suite.**

Run: `python -m pytest -q`

Expected: existing 54 tests plus the new parser tests pass after the minimal adapter is wired.

### Task 3: Implement AST facts and Node/TypeScript portability rules

**Files:**
- Modify: `src/agent_xplat/rules/node.py`
- Modify: `src/agent_xplat/rules/registry.py`
- Modify: `src/agent_xplat/discovery.py`
- Modify: `src/agent_xplat/rules/paths.py`
- Test: `tests/test_rules_languages.py`
- Test: `tests/test_false_positive_controls.py`
- Test: `tests/fixtures/node-ast/*`

**Interfaces:**
- Keep `detect_node(source, context, specs) -> list[Finding]` as the registry detector boundary.
- Add internal AST helpers that return call/member/branch facts with Tree-sitter nodes and source spans.
- New stable rules: `AX-NODE-005` child-process shell/command portability, `AX-NODE-006` Node environment access without fallback, `AX-NODE-007` unguarded platform-dependent branch, and `AX-NODE-008` hardcoded Node executable/path separator.

- [x] **Step 1: Implement binding-aware call detection.**

Recognize direct imports/requires and aliases for `child_process` and report only calls to `exec`, `execSync`, `spawn`, or `spawnSync` bound to that module. For direct calls, inspect the first string argument; for options objects, inspect `shell: true`. Use the call node span for line/column.

- [x] **Step 2: Implement structured command-string classification.**

Classify `rm`, `cp`, `mv`, `grep`, `sed`, `awk`, `find`, `chmod`, `bash`, `sh -c`, `pwsh`, `powershell`, `cmd`, `cmd.exe`, and explicit `.exe` command names only inside child-process command arguments. Map native Windows and POSIX targets separately; keep ambiguous dynamic/template strings at MEDIUM confidence.

- [x] **Step 3: Implement platform and environment facts with guard awareness.**

Find `process.platform` member expressions and `if`/conditional expressions. A two-sided `if (process.platform === ...) { ... } else { ... }` is considered guarded and emits no branch finding. A one-sided or non-conditional use emits `AX-NODE-007` with WARNING/MEDIUM. Report `process.env.NAME` only when read without `??`, `||`, or an explicit default, using INFO/LOW or WARNING/MEDIUM according to the direct AST context.

- [x] **Step 4: Treat `path.join` and `path.resolve` as recognized portable APIs.**

Do not flag separators in literal arguments when they are direct arguments of these APIs; continue flagging a separately assigned hardcoded path or a separator used outside a recognized path API. Detect absolute Windows/POSIX executable paths passed to a child-process call as `AX-NODE-008`.

- [x] **Step 5: Add registry metadata and focused positive/negative fixture assertions.**

Every new rule gets severity, confidence, target metadata, remediation, example, test case, and rationale. Assert rule IDs, locations, affected target IDs, severity, confidence, and no finding for the correctly guarded example. Run: `python -m pytest tests/test_parsers.py tests/test_rules_languages.py tests/test_false_positive_controls.py tests/test_fixtures.py -q`.

### Task 4: Make package scripts structurally scoped and update public contracts

**Files:**
- Modify: `src/agent_xplat/rules/node.py`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/RULES.md`
- Modify: `docs/JSON_SCHEMA.md`
- Modify: `docs/decisions/0001-python-standard-library-first.md`
- Test: `tests/test_rules_languages.py`
- Test: `tests/test_documentation_contract.py`

**Interfaces:**
- `detect_node` must inspect only values under the parsed `package.json` `scripts` object for package-script rules.
- Existing `AX-NODE-001..004` IDs remain stable; AST IDs are additive.

- [x] **Step 1: Extract script values structurally and preserve source locations.**

Use a JSON token walk or a scoped decoder to identify each `scripts` string value and its raw source span. Apply package-script regexes only within those spans; do not classify dependency names, descriptions, or arbitrary JSON values as commands.

- [x] **Step 2: Add false-positive tests for dependencies, descriptions, and escaped script strings.**

Assert that non-script `rm`, `NODE_ENV`, and `.sh` text creates no package-script finding, while the same tokens under `scripts` still do.

- [x] **Step 3: Replace the Node AST limitation with the actual parser contract.**

Document supported JS/JSX/TS/TSX suffixes, Tree-sitter dependencies, static-only behavior, rule boundaries, and the fact that runtime verification still requires `agent-xplat test` or hosted CI.

- [x] **Step 4: Run docs and report contract tests.**

Run: `python -m pytest tests/test_documentation_contract.py tests/test_rules_languages.py tests/test_reports.py tests/test_schema_sarif.py -q`.

### Task 5: Full regression, packaging, and release-preparation audit

**Files:**
- Modify: `docs/audit/gap-analysis.md`
- Modify: `docs/audit/requirements-matrix.md`
- Modify: `docs/audit/verification-run.md`
- Modify: `docs/audit/repository-audit.md`
- Modify: `docs/audit/gate-decision-package.md`
- Modify: `AGENTS.md` only if verified project commands/dependency facts change
- Test: all `tests/`

- [x] **Step 1: Run the full local verification set.**

Run:

```text
python -m pytest -q
python -m compileall -q src
git diff --check
python -m pip wheel . --no-deps --wheel-dir <external-build-dir>
```

Validated fresh editable and wheel installs in isolated Windows virtual environments, then ran the README command sequence against portable, mixed, Node, and node-ast fixtures. Final local suite: `88 passed`; compile and diff checks passed; final wheel metadata/hash is recorded in `docs/audit/verification-run.md`.

- [x] **Step 2: Validate JSON, SARIF, Markdown, baseline, diff, fix dry-run, CLI help, and static safety.**

Generated documents passed the project validators, AST locations and affected targets were asserted, normalized repeated JSON was equal, the dangerous-source scan did not execute target code, and the fresh end-to-end fixture chain covered baseline regression, Git diff, and no-op dry-run behavior.

- [x] **Step 3: Re-run repository audit.**

The post-hardening repository audit found no secrets, private URLs, machine paths, debug artifacts, or tracked build output; it read back the final dependency metadata, license, package entry point, workflow, and public AST documentation.

- [x] **Step 4: Update evidence honestly and stop at the actual release boundary.**

Fresh local results are recorded in the audit matrix, verification run, repository audit, and gate decision package. Hosted three-runner evidence remains `UNVERIFIED`; the project is intentionally not marked `READY FOR RELEASE` from local evidence alone.
