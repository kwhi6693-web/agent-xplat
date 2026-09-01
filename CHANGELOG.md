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

This source release includes the three-runner workflow. Hosted Windows/macOS/Linux results must be collected in the target GitHub repository before claiming runtime cross-OS verification.
