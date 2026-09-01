# ADR 0001: Python standard-library-first CLI

## Status

Accepted for v1.0 implementation.

## Context

Agent Xplat needs a cross-platform CLI with a low-friction install path, Python AST inspection, deterministic text analysis, stable JSON/SARIF output, and reliable Windows support. TypeScript has a strong CLI ecosystem, but JavaScript/TypeScript AST parsing would add a parser dependency and increase the install surface for a tool that must run in minimal CI environments.

## Decision

Use Python 3.10+ with a standard-library-first implementation. Use `ast` for Python source, `json` for package manifests and result artifacts, `pathlib` for path handling, `argparse` for the CLI, and a small documented YAML subset parser/validator for `.agent-xplat.yml`. Keep `pytest` development-only.

## Consequences

- Python workflows and AST rules are first-class and do not require a third-party parser.
- The published CLI can be installed with `pipx`, a virtual environment, or a source checkout without a runtime dependency download.
- YAML support is intentionally limited to the documented schema; unsupported YAML features fail with an actionable configuration error instead of being guessed.
- Node scripts are analyzed structurally where JSON is available and lexically for shell syntax; a future parser can be added behind the same rule interface.
- Cross-OS behavior is verified by the same package on Windows, macOS, and Linux runners.
