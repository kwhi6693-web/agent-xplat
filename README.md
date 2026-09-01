# agent-xplat

## Find the OS assumptions that break AI-agent workflows.

`agent-xplat` is a deterministic cross-OS portability checker for AI agent workflows, Agent Skills, agent configuration, and related scripts. It reports where a workflow can fail across **Windows, macOS, and Linux**, including the shell and runtime context—not just the operating system.

```text
agent-xplat scan .
```

Example from the included mixed-platform fixture:

```text
Agent Workflow Portability
===========================

Compatibility Matrix
---------------------
Environment                Score Status    Findings
Windows / PowerShell      41/100 BLOCKED          4
Windows / CMD              1/100 BLOCKED          6
Windows / Git Bash        76/100 PARTIAL          3
Windows / WSL             76/100 PARTIAL          3
macOS / zsh               56/100 PARTIAL          4
macOS / bash              56/100 PARTIAL          4
Linux / bash              56/100 PARTIAL          4
Linux / zsh               56/100 PARTIAL          4

7 portability issues found (0 ignored)
```

The scores are deterministic and explainable. Static findings are marked as inferred; only a real runner or local runtime check can produce verified evidence.

## Why it exists

Agent workflows often mix Markdown instructions, shell snippets, Python, Node scripts, package managers, and external tools. A workflow can be valid on Linux Bash and still fail in Windows PowerShell, Windows CMD, Git Bash, WSL, or macOS zsh. General linters and security scanners are not designed to answer that portability question.

The boundary is deliberate: agent-xplat is not a security scanner, Agent Skill schema validator, benchmark, general linter, or repository health tool. It focuses on **Cross-OS Runtime Portability for AI Agent Workflows**.

## Quick start

Install from a checkout:

```bash
python -m pip install .
agent-xplat scan .
```

For development:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The module invocation is always available as a fallback:

```bash
python -m agent_xplat scan . --format json
```

## Installation

Python 3.10 or newer is required. The runtime package has no third-party dependencies. `pytest` is only a development extra. `pipx install .` is a convenient isolated CLI installation when working from a release checkout.

## Supported environments

The internal model is OS × Shell × Runtime:

| Target | OS | Shell | Runtime context |
|---|---|---|---|
| `windows-powershell` | Windows | PowerShell | native |
| `windows-cmd` | Windows | CMD | native |
| `windows-git-bash` | Windows | Bash | Git Bash |
| `windows-wsl` | Windows | Bash | WSL |
| `macos-zsh` | macOS | zsh | native |
| `macos-bash` | macOS | Bash | native |
| `linux-bash` | Linux | Bash | native |
| `linux-zsh` | Linux | zsh | native |

## What is scanned

The default bounded discovery includes `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `.github/**`, `.cursor/**`, `.claude/**`, `.codex/**`, `scripts/**`, package manifests/lockfiles, Python metadata, Docker/Make files, and common shell, Python, JavaScript, TypeScript, and batch extensions. `.git`, `node_modules`, `vendor`, `dist`, `build`, caches, binary files, and oversized files are excluded.

## Examples

Included fixtures exercise portable, OS-specific, shell-specific, Python, Node, mixed, and agent-instruction workflows:

```bash
agent-xplat scan tests/fixtures/mixed
agent-xplat scan tests/fixtures/python --format json
agent-xplat scan tests/fixtures/node --format sarif --output agent-xplat.sarif
```

The fixture metadata in `tests/fixtures/*/expected.json` records expected rules, affected targets, severity, and confidence. It is test data, not a claim about a third-party tool's standard.

## Rules, severity, and confidence

Rules are modular and use stable `AX-*` identifiers. They cover paths, shell commands and environment syntax, quoting, Python, Node, filesystems, package managers, external tools, runtime assumptions, and agent configuration. See [docs/RULES.md](docs/RULES.md).

Severity is one of `BLOCKER`, `ERROR`, `WARNING`, or `INFO`. Confidence is one of `HIGH`, `MEDIUM`, or `LOW`. A low-confidence assumption is reported as such and does not become a blocker merely because it is inconvenient.

## Scan and reports

```bash
agent-xplat scan .
agent-xplat scan . --format json --output agent-xplat.json
agent-xplat scan . --format sarif --output agent-xplat.sarif
agent-xplat report .
```

JSON is versioned (`schema_version: 1.0`) for agent and CI consumption and contains `targets`, `scores`, `findings`, `baseline`, `contract`, `verification`, and `summary`. SARIF output is version 2.1.0 and includes file, line, column, rule, level, message, and help. The Markdown report contains the executive summary, matrix, blocking issues, warnings, assumptions, contract violations, affected files, suggested fixes, evidence, ignored findings, and baseline status.

## Safe fixes

```bash
agent-xplat fix . --dry-run
agent-xplat fix .
```

Only deterministic, high-confidence, behavior-preserving fixes are eligible. v1.0 automatically normalizes CRLF shebang files to LF. Shell rewrites, path rewrites, environment syntax conversions, and dependency migrations remain suggestions because their equivalence cannot be proven from static text alone. Dry-run prints a unified patch and does not modify files.

## Runtime verification

```bash
agent-xplat test .
```

`scan` performs no target-code execution. `test` is explicit and bounded: it may run an allowlisted project test command with a timeout and records the actual host target, command, exit code, and output tail. A missing command is `INFERRED`, not `VERIFIED`. Runtime evidence from one host does not prove all matrix rows.

## GitHub Actions and SARIF

```bash
agent-xplat init-ci
```

The generated workflow runs on `windows-latest`, `macos-latest`, and `ubuntu-latest`, installs the project, runs tests, performs a static scan, invokes controlled runtime verification, creates JSON/SARIF/Markdown artifacts, and uploads SARIF to Code Scanning. A workflow file existing locally is not evidence that the hosted jobs passed; the repository must run those jobs before claiming cross-OS verification.

## Baseline and diff mode

```bash
agent-xplat baseline
agent-xplat scan . --baseline-only
agent-xplat scan . --diff main
agent-xplat scan . --diff HEAD~1 --format markdown
```

Baselines distinguish existing, new, and resolved fingerprints. `--baseline-only` gates on new findings. Diff mode compares before/after scores and issue fingerprints from a Git reference without executing the reference tree.

## Compatibility Contract

`.agent-xplat.yml` accepts declared support and requirements:

```yaml
supported:
  - windows-powershell
  - windows-git-bash
  - windows-wsl
  - macos-zsh
  - linux-bash
unsupported:
  - windows-cmd
requirements:
  python: ">=3.11"
  node: ">=22"
minimum_score: 85
fail_on:
  - BLOCKER
  - ERROR
```

The optional `agent-xplat:` wrapper is also accepted. Declared support is compared to detected assumptions and reported as `VIOLATION`; unsupported targets are not treated as contract failures.

## Configuration and ignoring rules

```bash
agent-xplat init
```

The schema supports `targets`, `exclude`, `ignore`, `minimum_score`, `fail_on`, `supported`, `unsupported`, `requirements`, `max_file_size`, and `verification`. Global suppression uses `ignore`. A line-level marker is explicit and auditable:

```text
# agent-xplat-ignore AX-SHELL-001
chmod +x scripts/render.sh
```

Ignored findings remain in machine-readable output with `ignored: true`, and the summary reports their count. Unknown keys, targets, severities, rule IDs, and invalid values fail with exit code 2.

## Agent-native usage and exit codes

```bash
agent-xplat scan . --format json
```

| Code | Meaning |
|---:|---|
| 0 | No configured portability gate failure |
| 1 | Portability violation, contract violation, or new diff regression |
| 2 | Invalid configuration, input, Git reference, or command arguments |
| 3 | Unexpected internal tool error |

Agents should consume `summary`, per-target `scores`, `findings`, and `contract.violations` rather than parsing terminal decoration.

## Badge and doctor

```bash
agent-xplat badge
agent-xplat doctor
```

The default badge says `Static Checked` and `Inference only`. A `Cross-OS Verified` badge must be backed by a verification artifact that records verified Windows, macOS, and Linux evidence; the badge label is never implied by a static scan. `doctor` only reports local availability of Git, Node, Python, Docker, PowerShell, Git Bash, WSL, Bash, and zsh. It does not inspect repository health.

## Security model

Default commands are offline, read-only with respect to the target source, non-executing, non-telemetric, and do not upload data. `test` is the only command that may execute a selected allowlisted project test command, and it has no shell operators, a bounded timeout, and a clear runtime evidence record. There is no AI API, SaaS backend, credential upload, or hidden network path.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The core flow is:

```text
Config -> bounded discovery -> structured/text parsers -> rule registry
      -> target-specific findings -> suppression -> score/contract
      -> terminal / JSON / SARIF / Markdown / baseline / diff
```

## Limitations and roadmap

Static text cannot prove every shell version, installed tool, filesystem policy, native binary, or runtime behavior. Node source is analyzed through package JSON and focused lexical rules in v1.0; a full JavaScript AST is a future extension. The release workflow is generated and documented, but hosted runner evidence must come from the user's GitHub repository. Future work may add more runtime adapters and independently reviewed parser plugins without changing the public finding contract.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), add a positive and negative fixture for every rule change, run `python -m pytest -q`, and preserve deterministic output. Do not add telemetry, network calls, secrets, or machine-specific paths.

## License

MIT. See [LICENSE](LICENSE).
