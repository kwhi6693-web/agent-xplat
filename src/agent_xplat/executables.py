"""Executable-name classification used by runtime and Python rules."""

from __future__ import annotations

from pathlib import PurePath


def executable_kind(value: str) -> str | None:
    name = PurePath(value.replace("\\", "/")).name.lower()
    if name.startswith("python") or name == "py":
        return "python"
    if name in {"node", "node.exe", "npm", "npm.cmd", "npx", "pnpm", "yarn", "bun"}:
        return "node"
    if name in {"bash", "zsh", "pwsh", "powershell", "cmd", "cmd.exe"}:
        return "shell"
    return None
