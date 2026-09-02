# Verification Run

Run ID: `VX-2026-09-01-003`
Project: `agent-xplat` v1.0.0  
Verification plan: `docs/VERIFICATION_PLAN.md`  
Execution scope: local Windows host, isolated installs, fixture/report regression, and repository audit

## Local evidence

| Check | Result |
|---|---|
| `python -m compileall -q src` | PASS |
| `git diff --check` | PASS |
| `python -m pytest -q` | PASS — 88 passed |
| Snapshot report test | PASS — mixed fixture terminal output matches `tests/snapshots/mixed-terminal.txt` |
| `python -m pip wheel . --no-deps --wheel-dir <external-build-dir>` | PASS — `agent_xplat-1.0.0-py3-none-any.whl`; final hash/size recorded with the build evidence below |
| `agent-xplat --version` | PASS — `1.0.0` |
| All ten subcommand `--help` probes | PASS |
| Mixed fixture terminal scan | PASS as a negative test — expected exit code 1, seven active findings, target-specific matrix rendered |
| Node/TS AST fixture scan | PASS as a negative test — expected exit code 1, five findings with exact rule set AX-NODE-005/006/007/008 |
| JSON result validation | PASS — validator returned no errors, including AST metadata and coordinates |
| SARIF 2.1.0 validation | PASS — validator returned no errors, including AST locations/help |
| Markdown report required sections | PASS |
| Normalized repeated JSON scan | PASS — documents equal after removing nondeterministic `scan_timestamp`; fingerprints and scores are stable |
| Baseline clean scan | PASS — `CLEAN`, zero new findings |
| Baseline regression scan | PASS — `REGRESSION`, new finding blocked with exit code 1 |
| Git diff mode | PASS — reference tree materialized with `git archive`; no reference code executed; regression status is reported |
| `fix --dry-run` and fix idempotence | PASS — dry-run leaves files unchanged; only the tested CRLF shebang normalization is eligible for automatic fix |
| `agent-xplat test . --format json` | VERIFIED on current Windows/PowerShell host; project test command exited 0 and recorded the actual host only |
| Isolated editable install | PASS — parser dependencies and development extra installed; 88 tests passed in the isolated environment |
| Isolated wheel install and AST scan | PASS — installed version `1.0.0`; AST scan returned the expected portability gate code and valid JSON |
| Fresh `init` -> `init-ci` -> scan/report/baseline/diff/fix/doctor/badge chain | PASS; generated workflow scanned cleanly, baseline/diff were `CLEAN`, dry-run left configuration unchanged, and artifacts were read back |
| Runtime-verified badge without three-OS evidence | PASS negative test — refused with configuration/input exit code 2 |

## Evidence classification

- E1 — local static implementation, parser/rule, fixture, snapshot, and deterministic test evidence: PASS.
- E2 — JSON/SARIF/Markdown/schema, CLI, baseline/diff, fix, and isolated package evidence: PASS.
- E3 — current host runtime command: VERIFIED for Windows/PowerShell only.
- E4 — independent hosted Windows/macOS/Linux runner evidence: UNVERIFIED; no remote repository or completed hosted run was available.

Static findings remain `INFERRED`. The local runtime artifact records only the current Windows host and deliberately does not mark macOS or Linux as verified.

## Build evidence

- Wheel: `agent_xplat-1.0.0-py3-none-any.whl` from the external build directory
- Size: `71128` bytes
- SHA-256: `8042a15b661de4a1c5ea54731b012839bd6c510c6c50e460e07dcaa703ebcdaa`
- Metadata readback: package `agent-xplat`, version `1.0.0`, Python `>=3.10`, and the three bounded Tree-sitter runtime dependencies.

## Hosted runner evidence

Hosted verification record: `VX-2026-09-01-004`
Repository: `https://github.com/kwhi6693-web/agent-xplat`
Workflow run: [33511871082](https://github.com/kwhi6693-web/agent-xplat/actions/runs/33511871082)
Workflow event: `push` to `master`
Workflow head SHA: `6b4ae053d7df0f0abacd064096b8f32c540ee00d`
Lifecycle: `AUDITED`
Overall result: `PASS`

| GitHub-hosted job | Job ID | Result | Runtime environment | Project test evidence |
|---|---:|---|---|---|
| `windows-latest` | `99869261153` | PASS | `windows-powershell` / Windows | `88 passed in 1.45s` |
| `macos-latest` | `99869261464` | PASS | `macos-zsh` / macOS | `88 passed in 0.79s` |
| `ubuntu-latest` | `99869261505` | PASS | `linux-bash` / Linux | `88 passed in 0.73s` |

Each job completed install, tests, static scan, controlled runtime verification, Markdown report, SARIF report, artifact upload, SARIF upload, and the workflow gates without a failed step. The enforcement steps were skipped after their preceding checks passed; this is the expected conditional path, not an unrun required check.

### Hosted evidence classification

- E4 — GitHub-hosted runner execution and independently downloaded artifacts: `VALID`, `PASS` for Windows, macOS, and Linux.
- Static `agent-xplat-scan.json` and `agent-xplat.sarif` remain `INFERRED`; no static artifact is treated as runtime proof.
- `agent-xplat-verification.json` is `RUNTIME` / `VERIFIED` and records only its corresponding hosted OS and shell/runtime class.

### Artifact readback

The GitHub Actions artifact API returned three non-expired artifacts, each bound to workflow run `33511871082` and head SHA `6b4ae053d7df0f0abacd064096b8f32c540ee00d`:

| Artifact | Contents | Readback |
|---|---|---|
| `agent-xplat-windows-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [windows]` |
| `agent-xplat-macos-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [macos]` |
| `agent-xplat-ubuntu-latest` | JSON, SARIF, Markdown, runtime evidence | All files non-empty; project JSON/SARIF validators passed; runtime status `VERIFIED`, `verified_os: [linux]` |

The downloaded file hashes were recorded in the release evidence outside source control. The public workflow file and README blob hashes also matched the local commit readback. The generated verified badge was accepted only after all three OS evidence files were combined and validated; the SVG readback contained `Cross-OS Verified` and the three OS labels.

## v1.0.1 release-trigger preflight

Run ID: `VX-2026-09-02-001`
Project: `agent-xplat` v1.0.1
Execution scope: release-only version metadata, necessary release documentation, local Windows verification, isolated wheel/sdist installation, package integrity, `twine check`, security audit, and remote release preflight.

| Check | Result |
|---|---|
| Scoped diff | PASS — only `pyproject.toml`, runtime version identifiers, version-only test expectations, `README.md`, `CHANGELOG.md`, and the two release audit records changed; core behavior and `.github/workflows/publish-pypi.yml` were not modified |
| `python -m pytest -q` | PASS — 88 passed |
| `python -m compileall -q src` | PASS |
| CLI help/version probes | PASS — root plus ten subcommands; version `1.0.1` |
| Self-scan | PASS — eight target rows, `100/100`, zero portability findings |
| Controlled runtime verification | VERIFIED — Windows/PowerShell host; project test command exited 0 with 88 passed |
| Build | PASS — `agent_xplat-1.0.1-py3-none-any.whl` and `agent_xplat-1.0.1.tar.gz` |
| `twine check` | PASS — wheel and sdist |
| Archive readback | PASS — final wheel 70,951 bytes / SHA-256 `020b95956997541693f33eaf99bd8f0a35c11d3f003ad0d3761e321cbf4a046c`; final sdist 72,877 bytes / SHA-256 `20f63e8f6d48c63d857477c6a64dac898539ee4c45f2ab8374f85620d9fa6ddf`; metadata version `1.0.1`; console entry point present |
| Isolated wheel/sdist smoke | PASS — both installed and reported `1.0.1`; both clean self-scans passed |
| Determinism and CLI chain | PASS — normalized repeated JSON scans identical; fresh init through badge chain passed |
| Security audit | PASS — `pip-audit . --strict` and the toolchain audit reported no known vulnerabilities; repository security/release-route audit passed |
| Remote preflight | PASS — baseline `de8faab` matched `origin/master`; no remote `v1.0.1` tag/release; publish workflow active; `pypi` environment present without protection rules |

Evidence classification:

- E1 — focused diff and release/workflow/security-route inspection: PASS.
- E2 — full tests, compile, build, `twine check`, deterministic JSON, security audit, and CLI-chain checks: PASS.
- E3 — installed wheel/sdist behavior and archive metadata readback: PASS; local runtime is verified only for Windows/PowerShell.
- E4 — the external `v1.0.1` Release event and PyPI workflow outcome were not yet run when this preflight was recorded.

The release gate remains open until the commit/tag/release and the triggered PyPI workflow are independently read back. Any manual approval request or workflow failure is a terminal stop under the current task.

## v1.0.1 public PyPI installation readback

Run ID: `VX-2026-09-02-002`
Project: `agent-xplat` 1.0.1
Target: public PyPI package and public GitHub `master` README
Environment: fresh Windows virtual environment, Python 3.12.10; package index explicitly set to `https://pypi.org/simple`; pip cache disabled
Lifecycle: `AUDITED`
Overall result: `PARTIAL` — public package installation and metadata/runtime checks passed; the local README was corrected, but the public GitHub README remains unchanged because no push was authorized under the active project scope.

| Check | Result |
|---|---|
| `python -m pip install --upgrade agent-xplat` | PASS — exit code 0; installed `agent-xplat-1.0.1`, `tree-sitter-0.26.0`, `tree-sitter-javascript-0.25.0`, and `tree-sitter-typescript-0.23.2` from public PyPI; no dependency resolution warning/error, only pip's self-update notice |
| Installed distribution version | PASS — `1.0.1` in the fresh environment |
| Console entry point | PASS — `agent-xplat` resolved to the fresh environment; `agent-xplat --version` returned `1.0.1`; metadata maps to `agent_xplat.cli:main` |
| `agent-xplat --help` | PASS — exit code 0 |
| `agent-xplat scan .` | PASS — exit code 0; eight target rows at `100/100 PASS`, zero findings |
| `python -m agent_xplat --help` | PASS — exit code 0 |
| Runtime dependency imports | PASS — `tree_sitter`, `tree_sitter_javascript`, and `tree_sitter_typescript` imported successfully |
| `python -m pip check` | PASS — `No broken requirements found.` |
| Fresh smoke rerun | PASS — version, console help, scan, module help, dependency check, and imports all returned exit code 0 |
| Public wheel readback | PASS — `agent_xplat-1.0.1-py3-none-any.whl`, 70,907 bytes, SHA-256 `e2d41774cec932a85de5abc42acebf3eefaffb56c19e08e1e2428d0ed3839d52`; archive contains the package/entry point and no `tests/` or `docs/` paths |
| Public wheel metadata | PASS — name `agent-xplat`, version `1.0.1`, Python `>=3.10`, MIT license expression, and console entry point present |
| PyPI JSON metadata | PASS — description, Markdown content type, five project URLs, runtime requirements, and wheel/sdist records match the release contract |
| PyPI README rendering | PASS — project page HTTP 200; rendered description panel, heading, README body, and code block are present |
| Publish workflow readback | PASS — run `33531926116` is `release`/`completed`/`success`; head SHA `5b4ffe72d10d8f95eea4d6132709b9066656fcf3`; both jobs passed and the `Publish package distributions to PyPI` step passed |
| Local README update | PASS — the first-screen install path now prefers `pipx install agent-xplat` with `python -m pip install agent-xplat` fallback; `git diff --check` passed |
| Local regression after README update | PASS — `python -m pytest -q` returned `88 passed`; `compileall` and local wheel `twine==7.0.0 check` passed |
| Public GitHub `master` README readback | BLOCKED — raw public README still contains the GitHub Release wheel as “Fastest install” and does not contain the new PyPI-first text; the local correction has not been pushed |

Evidence classification:

- E1 — scoped diff and public-source metadata/README inspection: `VALID`; only `README.md` is locally changed, with core source and `.github/workflows/publish-pypi.yml` untouched.
- E2 — pytest, compile, local wheel build, isolated `twine check`, deterministic assertions, and `pip check`: `VALID`, PASS.
- E3 — fresh public PyPI install, CLI behavior, dependency imports, public wheel archive/hash readback, and rendered PyPI project page: `VALID`, PASS.
- E4 — representative new-user installation from public PyPI on a fresh Windows Python environment and independent public workflow/package readback: `VALID`, PASS for package distribution; cross-OS installation remains outside this single-host run.

Verification harness recoveries were preserved in the execution history: one version probe had a WindowsPath string-formatting error and was rerun with a corrected assertion; one PyPI DOM probe used the wrong element names and was rerun against the actual project-description structure; one workflow probe initially treated a publish step as a job and was rerun with job/step separation; the development environment lacked `twine`, so the pinned tool was run in an isolated packaging-tools environment. None of these recoveries identified a package or release failure.

Known limitation: `pipx` is not installed on the validation host, so the advertised pipx command was not directly executed; the package's console entry point was verified through the required fresh `pip` installation. The public PyPI 1.0.1 README is a release snapshot and still renders the pre-update GitHub-wheel-first wording; changing that immutable release description would require a future package release.
