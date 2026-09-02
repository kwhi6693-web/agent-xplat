# agent-xplat Public Launch Kit

Status: `PUBLIC LAUNCH READY`<br>
Release: `agent-xplat 1.0.1`<br>
Last verified: 2026-09-02

This kit contains public-safe copy, installation snippets, verified claims, and
static display assets for the v1.0 series. Keep the claims below aligned with
the public README and the verification records.

## Canonical links

- PyPI: <https://pypi.org/project/agent-xplat/>
- GitHub: <https://github.com/kwhi6693-web/agent-xplat>
- Release: <https://github.com/kwhi6693-web/agent-xplat/releases/tag/v1.0.1>
- Cross-OS workflow: <https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml>
- Verification record: [docs/audit/verification-run.md](audit/verification-run.md)

## One-line positioning

Find the OS assumptions that break AI-agent workflows.

## Installation copy

The primary public installation path is:

```bash
python -m pip install agent-xplat
agent-xplat scan .
```

For an isolated CLI installation:

```bash
pipx install agent-xplat
agent-xplat scan .
```

## First-run demo

```bash
python -m pip install agent-xplat
agent-xplat scan .
```

The scanner produces a deterministic OS × Shell × Runtime compatibility matrix
for Windows PowerShell/CMD/Git Bash/WSL, macOS zsh/bash, and Linux bash/zsh.

## Short announcement

`agent-xplat 1.0.1` is now available on PyPI. Install it with `python -m pip
install agent-xplat` and scan an AI-agent workflow with `agent-xplat scan .`.
It highlights the OS, shell, runtime, path, quoting, package-manager, and
external-tool assumptions that can make a workflow fail outside its author’s
machine.

## Longer announcement

AI-agent workflows can look correct in one terminal and still fail on another
operating system. `agent-xplat` checks those portability assumptions across
Windows, macOS, and Linux, with shell and runtime context included in the
result. Version 1.0.1 is publicly distributed on PyPI, uses Trusted Publishing
for the release path, and has passed the project’s Windows/macOS/Linux hosted
workflow plus a fresh Windows Python 3.12 install from public PyPI.

Install it and inspect the current repository:

```bash
python -m pip install agent-xplat
agent-xplat scan .
```

## Verified public claims

- Public package: `agent-xplat==1.0.1` on PyPI.
- Python requirement: `>=3.10`.
- License metadata: MIT license expression with the packaged `LICENSE` file.
- Runtime parser dependencies resolve through normal package installation; no
  long-lived PyPI credential is required by the Trusted Publishing workflow.
- Fresh Windows Python 3.12 installation, console entry point, module fallback,
  runtime imports, `pip check`, and a clean self-scan passed.
- The hosted `windows-latest`, `macos-latest`, and `ubuntu-latest` jobs passed
  the project verification workflow.

## Honest boundaries

- Static findings are `INFERRED`; only a real runner or controlled local runtime
  check supplies `VERIFIED` evidence.
- The tool is a portability checker, not a security scanner, general linter,
  Agent Skill schema validator, or proof that every dynamic command will run.
- The public PyPI 1.0.1 description is the immutable release snapshot. The
  canonical GitHub README is kept PyPI-first for the current public docs.

## Display assets

- [Launch card](assets/agent-xplat-launch-card.svg) — public announcement and
  social-preview artwork.
- [Cross-OS Verified badge](assets/agent-xplat-verified.svg) — README status
  badge backed by hosted Windows/macOS/Linux evidence.

## Maintainer checklist

1. Link to the PyPI project page for installation.
2. Keep `python -m pip install agent-xplat` before the optional `pipx` path.
3. Link to the public README and the current verification record.
4. Describe hosted runner evidence separately from static inferred findings.
5. Do not claim a new version, tag, release asset, or package artifact unless it
   has its own build and public readback record.
