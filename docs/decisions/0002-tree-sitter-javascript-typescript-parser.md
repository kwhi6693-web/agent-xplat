# ADR 0002: Tree-sitter parser for JavaScript-family source

## Status

Accepted for Agent Xplat v1.0 source analysis.

## Context

The v1.0 contract requires reliable structured analysis of JavaScript and TypeScript source, including child-process calls, platform branches, environment access, path APIs, executable names, and shell command strings. The previous Python implementation used JSON parsing for `package.json` and focused lexical checks for source files. That approach could not distinguish a bound `child_process.exec` call from an unrelated identifier or prove that a `process.platform` branch had an alternate path.

The CLI remains Python 3.10+ because the existing engine, installation path, reporting stack, and Windows support are already implemented in Python. A complete ECMAScript/TypeScript parser is a meaningful technical dependency for this requirement; a regex-only replacement would leave the known v1.0 limitation in place.

## Decision

Use the maintained Python Tree-sitter binding with the JavaScript and TypeScript grammar packages:

- `tree-sitter>=0.26,<0.27`
- `tree-sitter-javascript>=0.25,<0.26`
- `tree-sitter-typescript>=0.23,<0.24`

Map `.js`, `.mjs`, `.cjs`, and `.jsx` to the JavaScript grammar; `.ts`, `.mts`, and `.cts` to the TypeScript grammar; and `.tsx` to the TSX grammar. Keep parsing bounded by the existing UTF-8, binary, and maximum-file-size discovery controls. Use named AST nodes and source spans; never import, evaluate, or execute scanned code.

## Alternatives considered

- A Node parser package would require a second runtime dependency path and would complicate the existing Python wheel and Windows CLI installation.
- A regex-only parser would be smaller but cannot provide binding-aware calls, syntax recovery, or guard-aware branches with acceptable false-positive control.
- A bundled custom parser would create a larger unmaintained implementation and a higher correctness risk than the focused grammar dependencies.

## Consequences

- The normal install now resolves three MIT-licensed runtime packages, and package metadata/audits must include that dependency surface.
- Source findings remain static `INFERRED` evidence; Tree-sitter parsing does not prove runtime subprocess behavior or installed tools.
- Dynamic strings, generated code, and semantics not represented in the AST remain documented limitations.
- AST rules are suggestion-only in v1.0; no automatic rewrite is enabled for them.
