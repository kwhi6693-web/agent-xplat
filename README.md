# agent-xplat

> Find the OS assumptions that break AI-agent workflows.

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![PyPI](https://img.shields.io/pypi/v/agent-xplat?style=flat-square)](https://pypi.org/project/agent-xplat/)
[![Python](https://img.shields.io/pypi/pyversions/agent-xplat?style=flat-square)](https://pypi.org/project/agent-xplat/)
[![Cross-OS Verified](https://img.shields.io/badge/Cross--OS%20Verified-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-2ea44f?style=flat-square)](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml)
[![CI](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml/badge.svg?branch=master&style=flat-square)](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml)
[![License](https://img.shields.io/github/license/kwhi6693-web/agent-xplat?style=flat-square)](LICENSE)

![agent-xplat — Cross-OS portability for AI-agent workflows](docs/assets/agent-xplat-social-preview.png)

## Why agent-xplat

AI-agent workflows combine Markdown instructions, shell commands, Python, Node, package managers, and external tools. A workflow that is valid in Linux Bash can still fail in Windows PowerShell, Windows CMD, Git Bash, WSL, or macOS zsh.

agent-xplat is a deterministic cross-OS portability checker for AI-agent workflows, Agent Skills, agent configuration, and related scripts. It reports the OS × Shell × Runtime assumptions behind a failure—not just the operating system.

Skill validators check structure, and general linters check style. agent-xplat checks whether those otherwise-valid workflows can survive the environments where agents actually run. It is deliberately not a security scanner, Agent Skill schema validator, benchmark, general linter, or repository health tool.

Static analysis covers the full eight-target matrix and produces `INFERRED` findings. The current verification path also exercises real GitHub-hosted Windows, macOS, and Linux runners; only those runtime checks produce `VERIFIED` evidence.

## Quick Start

Install the published package from PyPI and scan the current repository:

```bash
python -m pip install agent-xplat
agent-xplat scan .
```

For an isolated CLI installation:

```bash
pipx install agent-xplat
agent-xplat scan .
```

Python 3.10 or newer is required. From a source checkout:

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

## Demo

The scan produces a deterministic, target-specific compatibility matrix:

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

This is the included mixed-platform fixture example, not a claim about every repository.

## Compatibility Matrix

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

The published verification path covers Windows, macOS, and Linux through GitHub-hosted jobs. A single local host verifies only its own runtime target.

## How It Works

1. Bounded discovery collects supported instruction files, scripts, manifests, and metadata while excluding generated, binary, cache, and oversized content.
2. Text detectors and Tree-sitter AST detectors identify portability assumptions in shell, Python, JavaScript, JSX, TypeScript, and TSX sources.
3. The 49-rule registry evaluates each source against all configured matrix targets and narrows findings to affected targets.
4. Suppressions, baselines, diff fingerprints, and the compatibility contract are applied without changing the source.
5. The same result model is rendered to terminal output, JSON, SARIF, Markdown, baseline, and diff artifacts.

The evidence boundary is explicit:

| Evidence | Status | Meaning |
|---|---|---|
| `STATIC` | `INFERRED` | A rule inferred a portability assumption from repository content. |
| `RUNTIME` | `VERIFIED` | A bounded command ran on the recorded host and produced runtime evidence. |

## What It Scans

Default bounded discovery includes `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `.github/**`, `.cursor/**`, `.claude/**`, `.codex/**`, `scripts/**`, package manifests and lockfiles, Python metadata, Docker/Make files, and common shell, Python, JavaScript, JSX, TypeScript, TSX, and batch extensions (`.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.mts`, `.cts`, `.tsx`).

`.git`, `node_modules`, `vendor`, `dist`, `build`, caches, binary files, and oversized files are excluded.

## Rules, Severity, and Confidence

The current registry contains 49 modular rules with stable `AX-*` identifiers. They cover paths, shell commands and environment syntax, quoting, Python, Node package scripts and Node/JS/TS AST facts, filesystems, package managers, external tools, runtime assumptions, and agent configuration. See [docs/RULES.md](docs/RULES.md).

JavaScript-family source is parsed structurally with Tree-sitter. Dynamic strings and behavior remain static inferences.

Severity is one of `BLOCKER`, `ERROR`, `WARNING`, or `INFO`. Confidence is one of `HIGH`, `MEDIUM`, or `LOW`. A low-confidence assumption is reported as such and does not become a blocker merely because it is inconvenient.

## Runtime Verification

```bash
agent-xplat test .
```

`scan` performs no target-code execution. `test` is explicit and bounded: it may run an allowlisted project test command with a timeout and records the actual host target, command, exit code, and output tail. A missing command is `INFERRED`, not `VERIFIED`. Runtime evidence from one host does not prove all matrix rows.

The release verification record documents successful GitHub-hosted Windows, macOS, and Linux jobs. Each job records its own `RUNTIME = VERIFIED` evidence; the static scan remains `STATIC = INFERRED`.

## GitHub Actions & SARIF

```bash
agent-xplat init-ci
```

The generated workflow runs on `windows-latest`, `macos-latest`, and `ubuntu-latest`. It installs the project, runs tests, performs a static scan, invokes controlled runtime verification, creates JSON/SARIF/Markdown artifacts, uploads artifacts, and uploads SARIF to Code Scanning.

A workflow file existing locally is not evidence that hosted jobs passed; the repository must run those jobs before claiming cross-OS verification.

## Reports

```bash
agent-xplat scan .
agent-xplat scan . --format json --output agent-xplat.json
agent-xplat scan . --format sarif --output agent-xplat.sarif
agent-xplat report .
```

JSON is versioned with `schema_version: 1.0` for agent and CI consumption and contains `targets`, `scores`, `findings`, `baseline`, `contract`, `verification`, and `summary`. SARIF output is version 2.1.0 and includes file, line, column, rule, level, message, and help. The Markdown report contains the executive summary, matrix, blocking issues, warnings, assumptions, contract violations, affected files, suggested fixes, evidence, ignored findings, and baseline status.

## Safe Fix

```bash
agent-xplat fix . --dry-run
agent-xplat fix .
```

Only deterministic, high-confidence, behavior-preserving fixes are eligible. v1.0.1 automatically normalizes CRLF shebang files to LF. Shell rewrites, path rewrites, environment syntax conversions, and dependency migrations remain suggestions because their equivalence cannot be proven from static text alone. Dry-run prints a unified patch and does not modify files.

## Baseline / Diff

```bash
agent-xplat baseline
agent-xplat scan . --baseline-only
agent-xplat scan . --diff master
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

### Configuration and ignoring rules

```bash
agent-xplat init
```

The schema supports `targets`, `exclude`, `ignore`, `minimum_score`, `fail_on`, `supported`, `unsupported`, `requirements`, `max_file_size`, and `verification`. Global suppression uses `ignore`. A line-level marker is explicit and auditable:

```text
# agent-xplat-ignore AX-SHELL-001
chmod +x scripts/render.sh
```

Ignored findings remain in machine-readable output with `ignored: true`, and the summary reports their count. Unknown keys, targets, severities, rule IDs, and invalid values fail with exit code 2. Unused line-level suppression markers are reported as suppression diagnostics instead of being silently accepted.

## Agent-native Usage

```bash
agent-xplat scan . --format json
```

Agents should consume `summary`, per-target `scores`, `findings`, and `contract.violations` rather than parsing terminal decoration.

### CLI surface

| Command | Purpose |
|---|---|
| `scan` | Infer cross-OS portability issues |
| `test` | Run controlled runtime verification |
| `fix` | Plan and apply safe deterministic fixes |
| `report` | Write a Markdown portability report |
| `explain` | Explain a portability rule |
| `doctor` | Probe local verification capabilities |
| `baseline` | Write the current findings baseline |
| `init` | Create a starter `.agent-xplat.yml` |
| `init-ci` | Create a three-OS GitHub Actions workflow |
| `badge` | Create a truthful static/runtime status badge |

The root command also supports `--version`. Exit codes are:

| Code | Meaning |
|---:|---|
| 0 | No configured portability gate failure |
| 1 | Portability violation, contract violation, or new diff regression |
| 2 | Invalid configuration, input, Git reference, or command arguments |
| 3 | Unexpected internal tool error |

### Badge and doctor

```bash
agent-xplat badge
agent-xplat doctor
```

The default badge says `Static Checked` and `Inference only`. A `Cross-OS Verified` badge must be backed by a verification artifact that records verified Windows, macOS, and Linux evidence; the badge label is never implied by a static scan. `doctor` only reports local availability of Git, Node, Python, Docker, PowerShell, Git Bash, WSL, Bash, and zsh. It does not inspect repository health.

## Security Model

Default commands are offline, read-only with respect to the target source, non-executing, non-telemetric, and do not upload data. `test` is the only command that may execute a selected allowlisted project test command, and it has no shell operators, a bounded timeout, and a clear runtime evidence record. There is no AI API, SaaS backend, credential upload, or hidden network path.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The core flow is:

```text
Config -> bounded discovery -> structured/text parsers -> rule registry
      -> target-specific findings -> suppression -> score/contract
      -> terminal / JSON / SARIF / Markdown / baseline / diff
```

## Limitations

Static analysis cannot prove every shell version, installed tool, filesystem policy, native binary, dynamic command string, or runtime behavior. JavaScript-family source has structured AST coverage for the supported suffixes, but dynamic evaluation, generated code, unsupported syntax recovery, and actual subprocess behavior remain runtime concerns.

The release workflow is generated and documented, but hosted runner evidence must come from the user's GitHub repository. Future work may add more runtime adapters and independently reviewed rules without changing the public finding contract.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), add a positive and negative fixture for every rule change, run `python -m pytest -q`, and preserve deterministic output. Do not add telemetry, network calls, secrets, or machine-specific paths.

## Release / PyPI

The current release is **v1.0.1**. The package is published to [PyPI](https://pypi.org/project/agent-xplat/) as a wheel and source distribution, and the GitHub [Release v1.0.1](https://github.com/kwhi6693-web/agent-xplat/releases/tag/v1.0.1) is the release record.

The release path uses GitHub Actions Trusted Publishing: an OIDC-based publication flow that avoids long-lived PyPI tokens. The [verification record](docs/audit/verification-run.md) documents local checks, hosted Windows/macOS/Linux evidence, package readback, and the boundary between inferred static findings and verified runtime results. Release changes are summarized in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
