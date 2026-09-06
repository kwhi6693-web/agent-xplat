# Changelog

All notable changes to agent-xplat are documented here.

## [Unreleased]

### Changed

- Scoped shell and quoting detectors to real execution contexts, removing three
  observed false-positive families:
  - Python code lines (call keyword arguments, assignments, type annotations)
    are no longer read as POSIX shell text; only string literals passed to
    explicit shell-execution calls (`subprocess` functions, `os.system`,
    `os.popen`) remain shell corpus.
  - GitHub Actions `run:` blocks are scoped to the executor selected by
    `runs-on` and the shell chain (step `shell:` > `defaults.run.shell` >
    runner default). Explicit-bash jobs on Linux/macOS runners no longer
    receive CMD/PowerShell-lens findings; matrix runners keep findings for
    their Windows legs; unprovable runners (`self-hosted`, expressions) keep
    the historical behavior.
  - `.ps1` files are PowerShell source and `.cmd`/`.bat` files are CMD source:
    legal native syntax (`$var`, `$env:`, `set`, `%VAR%`, `where`) is no
    longer reported through another shell's lens, while explicit
    cross-interpreter text (`cmd /c`, `bash -c`) and genuine errors such as
    `$VAR` inside `.cmd` stay detected.
- Markdown command examples and `.sh` files keep their historical scope: they
  remain cross-shell knowledge text, so cross-platform reminders there are
  unchanged.

### Fixed

- AX-SHELL-003 no longer fires on Python keyword arguments such as
  `detail="..."` or `tempfile(..., dir=path)` (observed: 102 of 102
  AX-SHELL-003 findings in a consumer repository were this pattern).
- AX-SHELL-006 no longer fires on Python `source = ...` assignments.
- AX-QUOTE-007 no longer fires on Python `X | Y` type annotations.
- AX-QUOTE-004 no longer fires on PowerShell `$var` inside `.ps1` files.

### Notes

- Docstring text and ordinary strings are not shell corpus: their language is
  unknown, and the conservative choice is no shell detection there. Commands
  that are built dynamically or passed through variables remain undetected by
  design (static literal strings only).
- No rule is disabled globally; positive controls for real shell-execution
  contexts are covered by new regression tests
  (`tests/test_source_context_false_positives.py`).

## [1.0.2] - 2026-09-06

- Generate a consumer workflow that installs only the scanner, uses isolated Python,
  compares PRs with their base commit, preserves reports, and needs only contents:read.
- Match new baselines across line shifts while preserving duplicate occurrences and
  legacy fingerprint-only baselines. New-only gates honor fail_on severity.
- Restrict Markdown shell/quoting rules to command examples; avoid prose, tables,
  agent invocations and explicitly non-shell fences. Run each detector family once.
- Add source commit/worktree/text digest and a new-findings section to Markdown reports.
- Produce evidence alongside static badges and require source-bound runtime records.
- Record a pinned ten-repository exploratory study, including unresolved false positives.
- No release or universal-compatibility claim is made by this candidate.

## [1.0.1] - 2026-09-02

### Changed

- Updated the distribution and runtime version identifiers for the first PyPI Trusted Publishing release trigger.
- No core analyzer functionality or portability rules changed.

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
