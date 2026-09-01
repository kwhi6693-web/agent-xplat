"""Deterministic, bounded source-file discovery."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from .config import Config, ConfigError
from .models import SourceFile


INCLUDE_NAMES = {
    "SKILL.md",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "copilot-instructions.md",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
    ".agent-xplat.yml",
}
INCLUDE_SUFFIXES = {
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".cmd",
    ".bat",
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".mts",
    ".cts",
    ".tsx",
}


def _is_excluded(relative_path: str, config: Config) -> bool:
    normalized = relative_path.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in {".git", "node_modules", "vendor", "dist", "build", "__pycache__"} for part in parts):
        return True
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(normalized + "/", pattern) for pattern in config.exclude)


def _is_candidate(relative_path: str) -> bool:
    path = Path(relative_path)
    if path.name in INCLUDE_NAMES:
        return True
    if path.name.startswith("requirements-") and path.suffix == ".txt":
        return True
    if any(part in {".github", ".cursor", ".claude", ".codex", "scripts"} for part in path.parts):
        return True
    return path.suffix.lower() in INCLUDE_SUFFIXES


def _is_binary(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def source_file_from_path(path: Path, root: Path) -> SourceFile:
    path = Path(path)
    root = Path(root)
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"cannot decode text file as UTF-8: {path}") from exc
    relative = path.relative_to(root).as_posix()
    stat = path.stat()
    return SourceFile(path, relative, text, len(data), stat.st_mode, b"\r\n" in data)


def discover_files(root: Path, config: Config) -> list[SourceFile]:
    root = Path(root)
    if not root.exists() or not root.is_dir():
        raise ConfigError(f"scan root is not a directory: {root}")
    files: list[SourceFile] = []
    for path in sorted(root.rglob("*"), key=lambda item: (item.relative_to(root).as_posix().lower(), item.relative_to(root).as_posix())):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if _is_excluded(relative, config) or not _is_candidate(relative):
            continue
        try:
            stat = path.stat()
            if stat.st_size > config.max_file_size:
                continue
            data = path.read_bytes()
            if _is_binary(data):
                continue
            files.append(source_file_from_path(path, root))
        except (OSError, ConfigError):
            continue
    return files
