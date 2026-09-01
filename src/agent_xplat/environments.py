"""The supported OS × Shell × Runtime target matrix."""

from __future__ import annotations

from .models import Target


TARGETS: tuple[Target, ...] = (
    Target("windows-powershell", "windows", "powershell", "native", "Windows / PowerShell"),
    Target("windows-cmd", "windows", "cmd", "native", "Windows / CMD"),
    Target("windows-git-bash", "windows", "bash", "git-bash", "Windows / Git Bash"),
    Target("windows-wsl", "windows", "bash", "wsl", "Windows / WSL"),
    Target("macos-zsh", "macos", "zsh", "native", "macOS / zsh"),
    Target("macos-bash", "macos", "bash", "native", "macOS / bash"),
    Target("linux-bash", "linux", "bash", "native", "Linux / bash"),
    Target("linux-zsh", "linux", "zsh", "native", "Linux / zsh"),
)

TARGET_BY_ID = {target.id: target for target in TARGETS}


def target_by_id(target_id: str) -> Target:
    try:
        return TARGET_BY_ID[target_id]
    except KeyError as exc:
        raise KeyError(f"unknown target: {target_id}") from exc


def target_ids() -> tuple[str, ...]:
    return tuple(target.id for target in TARGETS)


def is_native_windows(target_id: str) -> bool:
    return target_id in {"windows-powershell", "windows-cmd"}


def is_posix_shell(target_id: str) -> bool:
    return target_by_id(target_id).shell in {"bash", "zsh"}


def is_windows_target(target_id: str) -> bool:
    return target_by_id(target_id).os == "windows"


def is_native_unix_target(target_id: str) -> bool:
    target = target_by_id(target_id)
    return target.os in {"macos", "linux"} and target.runtime == "native"
