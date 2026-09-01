"""Structured parsers used by portability rules; never execute target code."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Any, Iterator

from tree_sitter import Language, Node, Parser, Tree
import tree_sitter_javascript
import tree_sitter_typescript

from .models import SourceFile, SourceLocation


@dataclass(frozen=True)
class ParsedPython:
    tree: ast.AST | None
    imports: tuple[str, ...]
    syntax_error: str | None = None


@dataclass(frozen=True)
class ParsedJavaScript:
    """A parse-only Tree-sitter result for JavaScript-family source files.

    Tree-sitter can recover a tree for incomplete source. ``syntax_error`` is
    therefore diagnostic metadata rather than a reason to execute or reject
    the file. The original UTF-8 bytes are retained so rule code can resolve
    exact node text and byte spans without reparsing source with regexes.
    """

    tree: Tree | None
    language: str
    source_bytes: bytes
    syntax_error: str | None = None


@dataclass(frozen=True)
class JsonStringSpan:
    """A decoded JSON string and its raw source span."""

    key: str
    value: str
    start: int
    end: int


@dataclass(frozen=True)
class JsonMemberKeySpan:
    """A decoded key of a member in a named top-level JSON object."""

    object_key: str
    key: str
    start: int
    end: int


_JAVASCRIPT_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".jsx"})
_TYPESCRIPT_SUFFIXES = frozenset({".ts", ".mts", ".cts"})
_TSX_SUFFIXES = frozenset({".tsx"})


def javascript_suffixes() -> frozenset[str]:
    """Return all JavaScript/TypeScript suffixes with structured parsing."""

    return _JAVASCRIPT_SUFFIXES | _TYPESCRIPT_SUFFIXES | _TSX_SUFFIXES


def _language_for_suffix(suffix: str) -> tuple[str, Language] | None:
    normalized = suffix.lower()
    if normalized in _JAVASCRIPT_SUFFIXES:
        return "javascript", Language(tree_sitter_javascript.language())
    if normalized in _TYPESCRIPT_SUFFIXES:
        return "typescript", Language(tree_sitter_typescript.language_typescript())
    if normalized in _TSX_SUFFIXES:
        return "tsx", Language(tree_sitter_typescript.language_tsx())
    return None


def parse_javascript(source: SourceFile) -> ParsedJavaScript:
    """Parse a JavaScript-family source file without importing or running it."""

    source_bytes = source.text.encode("utf-8")
    selected = _language_for_suffix(source.path.suffix)
    if selected is None:
        return ParsedJavaScript(None, "unknown", source_bytes, "unsupported JavaScript-family suffix")
    language_name, language = selected
    tree = Parser(language).parse(source_bytes)
    syntax_error = _first_tree_error(tree.root_node) if tree is not None else "parser returned no tree"
    return ParsedJavaScript(tree, language_name, source_bytes, syntax_error)


def _first_tree_error(node: Node) -> str | None:
    if node.type == "ERROR" or node.is_missing:
        point = node.start_point
        return f"syntax error at line {point.row + 1}, column {point.column + 1}"
    for child in node.named_children:
        error = _first_tree_error(child)
        if error is not None:
            return error
    return None


def iter_named_nodes(parsed: ParsedJavaScript, node_type: str | None = None) -> Iterator[Node]:
    """Yield named AST nodes in source order, optionally filtered by type."""

    if parsed.tree is None:
        return

    def walk(node: Node) -> Iterator[Node]:
        if node_type is None or node.type == node_type:
            yield node
        for child in node.named_children:
            yield from walk(child)

    yield from walk(parsed.tree.root_node)


def node_text(parsed: ParsedJavaScript, node: Node) -> str:
    """Return a decoded UTF-8 source slice for one AST node."""

    return parsed.source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def source_location_for_node(source: SourceFile, node: Node) -> SourceLocation:
    """Map Tree-sitter byte offsets to one-based Unicode line/column values."""

    source_bytes = source.text.encode("utf-8")

    def point(offset: int) -> tuple[int, int]:
        prefix = source_bytes[: max(0, min(offset, len(source_bytes)))].decode("utf-8", errors="replace")
        line = prefix.count("\n") + 1
        column = len(prefix.rsplit("\n", 1)[-1]) + 1
        return line, column

    line, column = point(node.start_byte)
    end_line, end_column = point(node.end_byte)
    return SourceLocation(source.relative_path, line, column, end_line, end_column)


def json_object_string_spans(source: SourceFile, object_key: str) -> tuple[JsonStringSpan, ...]:
    """Return string-valued members of one top-level JSON object member.

    ``json.loads`` remains the source of truth for validity. The small token
    walk only adds raw offsets, allowing rules to analyze package scripts
    without matching unrelated descriptions, dependency names, or lock data.
    """

    try:
        document = json.loads(source.text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(document, dict) or not isinstance(document.get(object_key), dict):
        return ()
    decoder = json.JSONDecoder()

    def whitespace(index: int) -> int:
        while index < len(source.text) and source.text[index] in " \t\r\n":
            index += 1
        return index

    def decoded_string(index: int) -> tuple[str, int]:
        value, end = decoder.raw_decode(source.text, index)
        if not isinstance(value, str):
            raise ValueError("expected JSON string")
        return value, end

    def skip_value(index: int) -> int:
        _, end = decoder.raw_decode(source.text, whitespace(index))
        return end

    def members(index: int, *, collect_strings: bool = False) -> tuple[list[JsonStringSpan], int]:
        index = whitespace(index)
        if index >= len(source.text) or source.text[index] != "{":
            raise ValueError("expected JSON object")
        index += 1
        collected: list[JsonStringSpan] = []
        while True:
            index = whitespace(index)
            if index >= len(source.text):
                raise ValueError("unterminated JSON object")
            if source.text[index] == "}":
                return collected, index + 1
            key, index = decoded_string(index)
            index = whitespace(index)
            if index >= len(source.text) or source.text[index] != ":":
                raise ValueError("expected JSON colon")
            value_start = whitespace(index + 1)
            if collect_strings and value_start < len(source.text) and source.text[value_start] == '"':
                value, value_end = decoded_string(value_start)
                collected.append(JsonStringSpan(key, value, value_start, value_end))
                index = value_end
            else:
                index = skip_value(value_start)
            index = whitespace(index)
            if index < len(source.text) and source.text[index] == ",":
                index += 1
                continue
            if index < len(source.text) and source.text[index] == "}":
                return collected, index + 1
            raise ValueError("expected JSON comma or object end")

    try:
        top_level = whitespace(0)
        if top_level >= len(source.text) or source.text[top_level] != "{":
            return ()
        top_level += 1
        while True:
            top_level = whitespace(top_level)
            if top_level >= len(source.text) or source.text[top_level] == "}":
                return ()
            key, top_level = decoded_string(top_level)
            top_level = whitespace(top_level)
            if top_level >= len(source.text) or source.text[top_level] != ":":
                return ()
            value_start = whitespace(top_level + 1)
            if key == object_key:
                spans, _ = members(value_start, collect_strings=True)
                return tuple(spans)
            top_level = skip_value(value_start)
            top_level = whitespace(top_level)
            if top_level < len(source.text) and source.text[top_level] == ",":
                top_level += 1
                continue
            if top_level < len(source.text) and source.text[top_level] == "}":
                return ()
            return ()
    except (ValueError, json.JSONDecodeError):
        return ()


def json_object_member_key_spans(source: SourceFile, object_keys: tuple[str, ...]) -> tuple[JsonMemberKeySpan, ...]:
    """Return direct member keys from named top-level JSON objects.

    This is deliberately narrower than a general JSON token API: the document
    is first validated with ``json.loads`` and only direct keys under the
    requested object members are returned. It lets package rules distinguish a
    dependency name from the same text in a description or lockfile value.
    """

    try:
        document = json.loads(source.text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(document, dict):
        return ()
    wanted = set(object_keys)
    if not wanted:
        return ()
    decoder = json.JSONDecoder()

    def whitespace(index: int) -> int:
        while index < len(source.text) and source.text[index] in " \t\r\n":
            index += 1
        return index

    def decoded_string(index: int) -> tuple[str, int]:
        value, end = decoder.raw_decode(source.text, index)
        if not isinstance(value, str):
            raise ValueError("expected JSON string")
        return value, end

    def skip_value(index: int) -> int:
        _, end = decoder.raw_decode(source.text, whitespace(index))
        return end

    def object_member_keys(index: int, object_key: str) -> tuple[JsonMemberKeySpan, ...]:
        index = whitespace(index)
        if index >= len(source.text) or source.text[index] != "{":
            raise ValueError("expected JSON object")
        index += 1
        collected: list[JsonMemberKeySpan] = []
        while True:
            index = whitespace(index)
            if index >= len(source.text):
                raise ValueError("unterminated JSON object")
            if source.text[index] == "}":
                return tuple(collected)
            key_start = index
            key, index = decoded_string(index)
            collected.append(JsonMemberKeySpan(object_key, key, key_start, index))
            index = whitespace(index)
            if index >= len(source.text) or source.text[index] != ":":
                raise ValueError("expected JSON colon")
            index = skip_value(index + 1)
            index = whitespace(index)
            if index < len(source.text) and source.text[index] == ",":
                index += 1
                continue
            if index < len(source.text) and source.text[index] == "}":
                return tuple(collected)
            raise ValueError("expected JSON comma or object end")

    try:
        index = whitespace(0)
        if index >= len(source.text) or source.text[index] != "{":
            return ()
        index += 1
        result: list[JsonMemberKeySpan] = []
        while True:
            index = whitespace(index)
            if index >= len(source.text) or source.text[index] == "}":
                return tuple(result)
            top_key, index = decoded_string(index)
            index = whitespace(index)
            if index >= len(source.text) or source.text[index] != ":":
                return ()
            value_start = whitespace(index + 1)
            if top_key in wanted and isinstance(document.get(top_key), dict):
                result.extend(object_member_keys(value_start, top_key))
            else:
                index = skip_value(value_start)
            if top_key in wanted and isinstance(document.get(top_key), dict):
                index = skip_value(value_start)
            index = whitespace(index)
            if index < len(source.text) and source.text[index] == ",":
                index += 1
                continue
            if index < len(source.text) and source.text[index] == "}":
                return tuple(result)
            return ()
    except (ValueError, json.JSONDecodeError):
        return ()


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
