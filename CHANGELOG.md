# Changelog

All notable changes to agent-xplat are documented here.

## [1.0.0] - 2026-09-01

### Added

- Cross-OS OS × Shell × Runtime matrix for Windows, macOS, and Linux.
- Deterministic static rules for paths, shells, environment syntax, quoting, Python, Node, filesystems, package managers, external tools, runtimes, and agent configuration.
- Tree-sitter-backed JavaScript/JSX/TypeScript/TSX analysis for bound child-process calls, platform branches, environment reads, executable/path assumptions, and shell command strings; package-script analysis is scoped to parsed manifest values.
- Terminal, JSON 1.0, SARIF 2.1.0, Markdown, explain, baseline, diff, contract, fix, test, doctor, init, init-ci, and badge commands.
- Offline/read-only scan safety boundary and bounded explicit runtime verification.
- Fixtures, unit/integration/CLI/report/fix/schema tests, GitHub Actions workflow, and release documentation.

### Verification note

The three-runner workflow was executed in the public repository at [run 33511871082](https://github.com/kwhi6693-web/agent-xplat/actions/runs/33511871082) for source commit `6b4ae053d7df0f0abacd064096b8f32c540ee00d`. Windows, macOS, and Linux jobs passed and their JSON, SARIF, Markdown, and runtime artifacts were read back. Static findings remain `INFERRED`; only the recorded runner evidence is `VERIFIED`.
