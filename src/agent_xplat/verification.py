"""Explicit, bounded runtime verification; static scan never calls this module."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .config import Config


def _host_target() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows-powershell" if shutil.which("pwsh") or shutil.which("powershell") else "windows-cmd"
    if system == "darwin":
        return "macos-zsh" if shutil.which("zsh") else "macos-bash"
    return "linux-bash" if shutil.which("bash") else "linux-zsh"


def _platform_label(value: str) -> str:
    normalized = value.lower()
    return "macos" if normalized == "darwin" else normalized


def _select_command(root: Path, config: Config) -> list[str] | None:
    configured = config.verification.get("command") if config.verification else None
    if configured:
        if not isinstance(configured, str):
            raise ValueError("verification.command must be a string")
        return _safe_command(configured)
    if (root / "tests").is_dir() and shutil.which("python"):
        return [sys.executable, "-m", "pytest", "-q"]
    if (root / "package.json").exists() and shutil.which("npm"):
        return ["npm", "test", "--", "--runInBand"]
    return None


def _safe_command(command: str) -> list[str]:
    import shlex

    if any(token in command for token in ("&&", "||", ";", "|", ">", "<", "`", "$()")):
        raise ValueError("verification.command must not use shell operators")
    parts = shlex.split(command, posix=os.name != "nt")
    if not parts:
        raise ValueError("verification.command cannot be empty")
    executable = Path(parts[0]).name.lower()
    allowed = {"python", "python3", "pytest", "node", "npm", "npx", "pnpm", "yarn", "bun"}
    if executable not in allowed and Path(parts[0]).resolve() != Path(sys.executable).resolve():
        raise ValueError(f"verification command is not allowlisted: {parts[0]}")
    return parts


def run_verification(root: Path, config: Config, timeout: int = 120) -> dict[str, Any]:
    root = Path(root).resolve()
    environment = _host_target()
    checks: list[dict[str, Any]] = [
        {
            "name": "host-capability",
            "status": "VERIFIED",
            "observation": f"The current host can execute the {environment} target class.",
            "environment": environment,
        }
    ]
    command = _select_command(root, config)
    if command is None:
        checks.append({"name": "project-command", "status": "INFERRED", "observation": "No allowlisted project test command was configured or discovered."})
        return {
            "status": "INFERRED",
            "evidence_type": "INFERRED",
            "environment": environment,
            "verified_os": [],
            "checks": checks,
            "note": "Static compatibility is not runtime verification; add a project test command or run the generated CI workflow.",
        }
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=max(1, timeout), check=False)
        output = completed.stdout[-4000:]
        status = "VERIFIED" if completed.returncode == 0 else "FAIL"
        observation = f"{command!r} exited {completed.returncode}."
        check = {
            "name": "project-command",
            "status": status,
            "command": command,
            "exit_code": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "observation": observation,
            "output_tail": output,
            "environment": environment,
        }
    except subprocess.TimeoutExpired as exc:
        check = {
            "name": "project-command",
            "status": "FAIL",
            "command": command,
            "observation": f"Command exceeded timeout of {timeout} seconds.",
            "output_tail": str(exc.stdout or "")[-4000:],
            "environment": environment,
        }
    checks.append(check)
    final_status = "VERIFIED" if all(item["status"] == "VERIFIED" for item in checks) else "FAIL"
    return {
        "status": final_status,
        "evidence_type": "RUNTIME",
        "environment": environment,
        "verified_os": [_platform_label(platform.system())] if final_status == "VERIFIED" else [],
        "checks": checks,
        "note": "Runtime result applies only to the recorded host and command; it does not prove every matrix target.",
    }
