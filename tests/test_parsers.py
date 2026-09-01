from pathlib import Path

from agent_xplat.discovery import source_file_from_path
from agent_xplat.parsers import parse_python


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
