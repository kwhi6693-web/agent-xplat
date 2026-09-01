# Decision Log

- 2026-09-01: Use Python standard-library-first for the cross-platform CLI. See `docs/decisions/0001-python-standard-library-first.md`.
- 2026-09-01: Add narrowly scoped Tree-sitter JavaScript/TypeScript grammars for source AST analysis; see `docs/decisions/0002-tree-sitter-javascript-typescript-parser.md`.
- 2026-09-01: Keep the target model as OS × Shell × Runtime; OS-only scores are not an internal source of truth.
- 2026-09-01: Treat static assumptions as `INFERRED` and real runner observations as `VERIFIED`; the two statuses are never merged.
- 2026-09-01: Do not package the repeated PR/release workflow as a new generic asset because `unified-autonomous-workflow` already covers it; agent-xplat only owns portability evidence for its own project and users.
