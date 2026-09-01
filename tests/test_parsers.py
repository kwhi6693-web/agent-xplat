from pathlib import Path

from agent_xplat.discovery import source_file_from_path
from agent_xplat.parsers import (
    iter_named_nodes,
    javascript_suffixes,
    json_object_member_key_spans,
    json_object_string_spans,
    node_text,
    parse_javascript,
    parse_python,
)


def test_source_file_preserves_line_and_column_data(tmp_path: Path):
    path = tmp_path / "script.sh"
    path.write_text("#!/usr/bin/env bash\nchmod +x scripts/run.sh\n", encoding="utf-8")
    source = source_file_from_path(path, tmp_path)
    assert source.relative_path == "script.sh"
    assert source.lines[1] == "chmod +x scripts/run.sh"
    assert source.line_col_for("chmod", 1) == (2, 1)


def test_python_parser_returns_ast_and_syntax_error_without_execution(tmp_path: Path):
    path = tmp_path / "tool.py"
    path.write_text("import os\nfrom sys import platform\n", encoding="utf-8")
    source = source_file_from_path(path, tmp_path)
    parsed = parse_python(source)
    assert parsed.tree is not None
    assert parsed.imports == ("os", "sys")


def test_javascript_parser_selects_javascript_typescript_and_tsx_grammars(tmp_path: Path):
    cases = (
        ("tool.js", "const cp = require('child_process'); cp.exec('rm -rf dist');", "javascript"),
        ("tool.jsx", "export const View = () => <div />;", "javascript"),
        ("tool.ts", "const platform: string = process.platform;", "typescript"),
        ("tool.mts", "export const value: number = 1;", "typescript"),
        ("tool.cts", "module.exports = { value: 1 };", "typescript"),
        ("tool.tsx", "export const View = () => <div />;", "tsx"),
    )
    assert {".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx"} == set(javascript_suffixes())
    for name, text, language in cases:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        parsed = parse_javascript(source_file_from_path(path, tmp_path))
        assert parsed.tree is not None
        assert parsed.language == language
        assert parsed.syntax_error is None


def test_javascript_parser_reports_recoverable_syntax_errors_without_execution(tmp_path: Path):
    marker = tmp_path / "executed.txt"
    path = tmp_path / "broken.ts"
    path.write_text(
        f"import {{ writeFileSync }} from 'node:fs';\nwriteFileSync('{marker.name}', 'bad');\nconst value: = 1;\n",
        encoding="utf-8",
    )
    parsed = parse_javascript(source_file_from_path(path, tmp_path))
    assert parsed.tree is not None
    assert parsed.syntax_error is not None
    assert not marker.exists()


def test_javascript_parser_exposes_structured_path_calls(tmp_path: Path):
    path = tmp_path / "paths.ts"
    path.write_text(
        'const joined = path.join("folder", "file");\nconst resolved = path.resolve("folder");\n',
        encoding="utf-8",
    )
    parsed = parse_javascript(source_file_from_path(path, tmp_path))
    calls = [node_text(parsed, node) for node in iter_named_nodes(parsed, "call_expression")]
    assert calls == ['path.join("folder", "file")', 'path.resolve("folder")']


def test_json_object_spans_are_scoped_to_nested_members(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        '{\n'
        '  "description": "rm -rf dist",\n'
        '  "scripts": {"build": "NODE_ENV=production node build.js"},\n'
        '  "dependencies": {"better-sqlite3": "1.0.0"}\n'
        '}\n',
        encoding="utf-8",
    )
    source = source_file_from_path(path, tmp_path)
    scripts = json_object_string_spans(source, "scripts")
    dependencies = json_object_member_key_spans(source, ("dependencies",))
    assert [(span.key, span.value) for span in scripts] == [("build", "NODE_ENV=production node build.js")]
    assert [(span.key, span.object_key) for span in dependencies] == [("better-sqlite3", "dependencies")]
    assert source.text[dependencies[0].start : dependencies[0].end] == '"better-sqlite3"'
