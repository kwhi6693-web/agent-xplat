"""Structured shell environment-variable syntax helpers."""

from __future__ import annotations

import re


def classify_assignment(text: str) -> str | None:
    if re.search(r"\$env:[A-Za-z_][A-Za-z0-9_]*\s*=", text):
        return "powershell"
    if re.search(r"(?:^|\s)set\s+[A-Za-z_][A-Za-z0-9_]*\s*=", text, re.IGNORECASE):
        return "cmd"
    if re.search(r"(?:^|\s)[A-Za-z_][A-Za-z0-9_]*=[^\s]+\s+\S+", text):
        return "posix-inline"
    if re.search(r"(?:^|\s)export\s+[A-Za-z_][A-Za-z0-9_]*\s*=", text):
        return "posix-export"
    return None


def find_variable_syntax(text: str) -> tuple[str, ...]:
    values = set(re.findall(r"\$(?!env:)([A-Za-z_][A-Za-z0-9_]*)", text, re.IGNORECASE))
    values.update(re.findall(r"%([A-Za-z_][A-Za-z0-9_]*)%", text))
    values.update(re.findall(r"\$env:([A-Za-z_][A-Za-z0-9_]*)", text, re.IGNORECASE))
    return tuple(sorted(values))
