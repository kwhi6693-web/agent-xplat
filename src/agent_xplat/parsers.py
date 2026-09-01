"""Structured parsers used by portability rules; never execute target code."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Any

from .models import SourceFile


@dataclass(frozen=True)
class ParsedPython:
    tree: ast.AST | None
    imports: tuple[str, ...]
    syntax_error: str | None = None


def parse_python(source: SourceFile) -> ParsedPython:
    try:
        tree = ast.parse(source.text, filename=source.relative_path)
    except SyntaxError as exc:
        return ParsedPython(None, (), f"{exc.msg} at line {exc.lineno or 1}")
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return ParsedPython(tree, tuple(sorted(set(imports))))


def parse_json(source: SourceFile) -> dict[str, Any] | list[Any] | None:
    try:
        value = json.loads(source.text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, (dict, list)) else None
