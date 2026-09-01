"""Local verifier capability probe; it does not inspect repository health."""

from __future__ import annotations

import platform
import shutil
from typing import Any


CAPABILITIES = (
    ("Git", ("git",)),
    ("Node", ("node",)),
    ("Python", ("python", "python3")),
    ("Docker", ("docker",)),
    ("PowerShell", ("pwsh", "powershell")),
    ("Git Bash", ("bash",)),
    ("WSL", ("wsl",)),
    ("bash", ("bash",)),
    ("zsh", ("zsh",)),
)


def probe_capabilities() -> dict[str, Any]:
    capabilities = []
    for name, commands in CAPABILITIES:
        path = next((shutil.which(command) for command in commands if shutil.which(command)), None)
        capabilities.append({"name": name, "available": path is not None, "path": path})
    return {
        "platform": platform.platform(),
        "os": platform.system().lower(),
        "capabilities": capabilities,
        "note": "Availability is local capability evidence, not proof that a target workflow passes.",
    }


def render_doctor(document: dict[str, Any]) -> str:
    lines = ["agent-xplat doctor", "==================", f"Host: {document['platform']}", "", f"{'Capability':<16} {'Available':<10} Path"]
    for item in document["capabilities"]:
        lines.append(f"{item['name']:<16} {('yes' if item['available'] else 'no'):<10} {item['path'] or '-'}")
    lines.extend(["", document["note"], ""])
    return "\n".join(lines)
