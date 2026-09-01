# Project Context

## Identity

`agent-xplat` is a local, open-source CLI focused on **Cross-OS Runtime Portability for AI Agent Workflows**. It finds assumptions that can break skills, agent instructions, workflow scripts, and package commands when moved among Windows shells, macOS shells, and Linux shells.

## Boundaries

Agent Xplat is not a security scanner, schema validator, benchmark, general linter, or repository health tool. Its output is a portability matrix and evidence-aware findings. Static findings are inferred; runner observations are verified only when the actual environment runs them.

## User journey

```text
agent-xplat scan .
        -> findings + OS × Shell × Runtime matrix
        -> explain / fix --dry-run / fix
        -> baseline / diff / contract gate
        -> agent-xplat test . on explicit CI runners
        -> JSON/SARIF/Markdown artifacts
```

## Environment matrix

The first-class target set is:

`windows-powershell`, `windows-cmd`, `windows-git-bash`, `windows-wsl`, `macos-zsh`, `macos-bash`, `linux-bash`, `linux-zsh`.

Runtime is represented independently so future runtime constraints do not collapse shell distinctions.
