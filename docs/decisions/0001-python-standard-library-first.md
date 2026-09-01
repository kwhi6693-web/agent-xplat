# ADR 0001: Python standard-library-first CLI

## Status

Accepted for the Python CLI and core engine. The JavaScript-family parser portion is superseded by ADR 0002.

## Context

Agent Xplat needs a cross-platform CLI with a low-friction install path, Python AST inspection, deterministic text analysis, stable JSON/SARIF output, and reliable Windows support. Python remains the best fit for the existing engine and installation path, while JavaScript/TypeScript AST parsing requires a narrowly scoped parser dependency for acceptable correctness.

## Decision

Use Python 3.10+ with a standard-library-first implementation. Use `ast` for Python source, `json` for package manifests and result artifacts, `pathlib` for path handling, `argparse` for the CLI, and a small documented YAML subset parser/validator for `.agent-xplat.yml`. Use the Tree-sitter bindings selected in ADR 0002 only for JavaScript-family source ASTs. Keep `pytest` development-only.

## Consequences

- Python workflows and AST rules are first-class and do not require a third-party parser.
- The published CLI can be installed with `pipx`, a virtual environment, or a source checkout; package installation resolves only the focused parser runtime dependencies.
- YAML support is intentionally limited to the documented schema; unsupported YAML features fail with an actionable configuration error instead of being guessed.
- Node scripts are analyzed structurally where JSON is available; the source-AST decision is now recorded in ADR 0002.
- Cross-OS behavior is verified by the same package on Windows, macOS, and Linux runners.
