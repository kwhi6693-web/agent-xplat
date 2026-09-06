"""Execution-context facts that scope shell-sensitive detectors.

The scanner historically treated every line of every file as shell-corpus
text.  That produced three false-positive families observed in consumer
repositories:

A. Python source: call keyword arguments such as ``detail="..."`` or
   ``tempfile(..., dir=path)`` were read as POSIX ``NAME=value`` temporary
   environment assignments.  Python *code* lines can never be executed by a
   shell; only the text inside string literals can carry a real command
   (``subprocess.run("NODE_ENV=production node build.js", shell=True)``).

B. GitHub Actions workflows: ``run:`` blocks were reported against shells
   the job can never use (a bash step on an Ubuntu runner reported CMD
   dollar-variable findings).  The workflow's ``runs-on`` and shell
   selection (step ``shell:`` > ``defaults.run.shell`` > runner default)
   decide the real executor.

C. PowerShell/CMD files: ``$var`` in a ``.ps1`` file is PowerShell syntax,
   never executed by CMD; ``%VAR%`` in a ``.cmd`` file is CMD syntax, never
   executed by PowerShell.  File extension fixes the interpreter, except
   for explicit cross-interpreter invocations such as ``cmd /c`` or
   ``bash -c`` embedded in the file.

This module is deliberately conservative: when the executor cannot be
proven, detectors keep their historical behavior (``None``).  Markdown
code fences and ``.sh`` files stay historical too: they are knowledge
text that a user may copy into any shell, so cross-platform reminders
remain useful there.
"""

from __future__ import annotations

import re

from ..environments import TARGETS
from ..models import SourceFile
from .markdown_shell import shell_examples

_WORKFLOW_RE = re.compile(r"(?:^|/)\.github/workflows/[^/]+\.(?:ya?ml)$")

_PY_SUFFIX = ".py"

# PowerShell files are executed by PowerShell only, CMD files by CMD only.
_FILE_SHELL_TARGETS = {
    ".ps1": frozenset({"windows-powershell"}),
    ".cmd": frozenset({"windows-cmd"}),
    ".bat": frozenset({"windows-cmd"}),
}

# Explicit cross-interpreter invocation carriers.  When such text appears on
# a line, that line's content may additionally be executed by the referenced
# interpreter (e.g. ``cmd /c "echo %FOO%"`` inside a .ps1 file).
_CROSS_SHELL = (
    (
        re.compile(r"\bcmd(?:\.exe)?\s*/c\b", re.IGNORECASE),
        frozenset({"windows-cmd"}),
    ),
    (
        re.compile(r"\b(?:bash|sh|zsh)\s+-c\b", re.IGNORECASE),
        frozenset({"macos-bash", "linux-bash", "windows-git-bash", "windows-wsl"}),
    ),
    (
        re.compile(r"\b(?:pwsh|powershell(?:\.exe)?)\s+-Command\b", re.IGNORECASE),
        frozenset({"windows-powershell"}),
    ),
)

_SHELL_VALUE_TARGETS = {
    "bash": frozenset(target.id for target in TARGETS if target.shell == "bash"),
    "zsh": frozenset(target.id for target in TARGETS if target.shell == "zsh"),
    "powershell": frozenset({"windows-powershell"}),
    "cmd": frozenset({"windows-cmd"}),
}

_OS_FAMILY = (("ubuntu", "linux"), ("windows", "windows"), ("macos", "macos"))

_DEFAULT_SHELL_PER_OS = {"linux": "bash", "macos": "bash", "windows": "powershell"}


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _resolve_shell_name(shell: str) -> str | None:
    shell = shell.strip().lower()
    if not shell or shell.startswith("${{") or shell.startswith("!"):
        return None
    if shell in {"pwsh", "powershell"}:
        return "powershell"
    if shell in {"bash", "sh"}:
        return "bash"
    if shell == "cmd":
        return "cmd"
    if shell == "zsh":
        return "zsh"
    if shell == "python":
        return "python"
    return None


def _runner_oses(values: list[str]) -> frozenset[str] | None:
    """Resolve runs-on value(s) to OS families; None when unprovable."""
    oses: set[str] = set()
    for raw in values:
        item = raw.strip().lstrip("- ").strip()
        if not item or item.startswith("${{") or item.lower() == "self-hosted":
            return None
        label = item.lower()
        for prefix, family in _OS_FAMILY:
            if label == prefix or label.startswith(prefix + "-") or label == prefix + "-latest":
                oses.add(family)
                break
        else:
            return None
    return frozenset(oses) if oses else None


def _shell_targets_for(shell: str, oses: frozenset[str] | None) -> frozenset[str] | None:
    """Map a resolved shell + runner OS families to concrete target ids.

    GitHub hosted runners default to PowerShell on Windows and bash on
    Linux/macOS; a bash step on Windows runs Git Bash.  The mapping is the
    os x shell intersection of the supported target matrix, an
    approximation of hosted runner behavior.
    """
    if oses is None:
        return None
    if shell == "python":
        return frozenset()
    base = _SHELL_VALUE_TARGETS.get(shell)
    if base is None:
        return None
    return frozenset(target.id for target in TARGETS if target.id in base and target.os in oses)


def _workflow_executor_context(source: SourceFile) -> dict[int, frozenset[str] | None]:
    """Map 0-based workflow lines to executor target ids.

    Only ``run:`` content lines receive entries; every other line stays out
    of the mapping (historical behavior preserved).  A run line whose
    executor cannot be proven maps to None so callers can distinguish
    'filter nothing' from 'not a run line'.
    """
    context: dict[int, frozenset[str] | None] = {}
    text = source.text.splitlines()
    if not text:
        return context

    defaults_shell: str | None = None
    jobs_line: int | None = None
    index = 0
    while index < len(text):
        stripped = text[index].strip()
        if not stripped:
            index += 1
            continue
        if _indent_of(text[index]) != 0:
            index += 1
            continue
        if stripped == "jobs:":
            jobs_line = index
            break
        if stripped.startswith("defaults:"):
            ahead = index + 1
            run_seen = False
            while ahead < len(text) and _indent_of(text[ahead]) > 0:
                content = text[ahead].strip()
                indent = _indent_of(text[ahead])
                if indent == 2 and content == "run:":
                    run_seen = True
                elif indent == 4 and content.startswith("shell:") and run_seen:
                    defaults_shell = _resolve_shell_name(content.split(":", 1)[1])
                    run_seen = False
                ahead += 1
            index = ahead
            continue
        index += 1
    if jobs_line is None:
        return context

    section_end = len(text)
    for index in range(jobs_line + 1, len(text)):
        if text[index].strip() and _indent_of(text[index]) == 0:
            section_end = index
            break

    run_shell: str | None = None
    run_oses: frozenset[str] | None = None
    run_block_start: int | None = None
    run_block_indent: int = 0
    in_steps = False
    step_item = False

    def executor() -> frozenset[str] | None:
        if run_shell is None or run_oses is None:
            return None
        return _shell_targets_for(run_shell, run_oses)

    def flush_run_block(up_to: int) -> None:
        nonlocal run_block_start
        if run_block_start is None:
            return
        shells = executor()
        for line_no in range(run_block_start + 1, up_to):
            if line_no >= len(text):
                break
            if _indent_of(text[line_no]) > run_block_indent:
                context[line_no] = shells
        run_block_start = None

    index = jobs_line + 1
    while index < section_end:
        line = text[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        indent = _indent_of(line)
        if indent == 0:
            break
        if indent == 2:
            flush_run_block(index)
            key = stripped.split(":", 1)[0]
            if key in {
                "on", "name", "env", "permissions", "concurrency", "run-name",
                "runs-on", "steps", "strategy", "timeout-minutes", "if", "uses",
                "with", "needs", "continue-on-error", "defaults", "services",
            }:
                # Job attribute or workflow key that is not a job name.
                index += 1
                continue
            # New job begins.
            run_shell = defaults_shell
            run_oses = None
            run_block_start = None
            in_steps = False
            step_item = False
            index += 1
            continue
        if indent == 4:
            flush_run_block(index)
            content = stripped
            if content.startswith("runs-on:"):
                values = [content.split(":", 1)[1]]
                probe = index + 1
                while probe < section_end and _indent_of(text[probe]) == 6 and text[probe].strip().startswith("- "):
                    values.append(text[probe])
                    probe += 1
                run_oses = _runner_oses(values)
                index = probe
                continue
            if content == "strategy:":
                probe = index + 1
                matrix_oses: list[str] = []
                include_adds_os = False
                while probe < section_end and _indent_of(text[probe]) >= 6:
                    if _indent_of(text[probe]) == 6 and text[probe].strip().startswith("matrix:"):
                        inner = probe + 1
                        while inner < section_end and _indent_of(text[inner]) >= 8:
                            content_inner = text[inner].strip()
                            if _indent_of(text[inner]) == 8 and content_inner.startswith("os:"):
                                os_line = content_inner.split(":", 1)[1]
                                if os_line.strip():
                                    matrix_oses.append(os_line)
                                list_probe = inner + 1
                                while list_probe < section_end and _indent_of(text[list_probe]) == 10 and text[list_probe].strip().startswith("- "):
                                    matrix_oses.append(text[list_probe])
                                    list_probe += 1
                                inner = list_probe
                            elif _indent_of(text[inner]) == 8 and content_inner.startswith("include:"):
                                # include entries can add or override matrix
                                # combinations (including os); combinations
                                # beyond the os cross product cannot be
                                # enumerated cheaply, so treat any os-bearing
                                # include as an unprovable executor.
                                include_probe = inner + 1
                                while include_probe < section_end and _indent_of(text[include_probe]) == 10 and text[include_probe].strip().startswith("- "):
                                    entry = text[include_probe].strip()[2:]
                                    if re.search(r"(^|\s)os\s*:", entry, re.IGNORECASE):
                                        include_adds_os = True
                                    include_probe += 1
                                inner = include_probe
                            else:
                                inner += 1
                        probe = inner
                        break
                    probe += 1
                if matrix_oses and not include_adds_os:
                    run_oses = _runner_oses(matrix_oses)
                elif include_adds_os:
                    # os-bearing include: combinations unknown => conservative
                    # historical behavior for this job's run blocks.
                    run_oses = None
                index = probe
                continue
            if content == "steps:":
                in_steps = True
                index += 1
                continue
            index += 1
            continue
        if indent == 6:
            flush_run_block(index)
            content = stripped
            if in_steps and content.startswith("- "):
                inner = content[2:].strip()
                if inner.startswith("shell:"):
                    resolved = _resolve_shell_name(inner.split(":", 1)[1])
                    run_shell = resolved if resolved != "python" else "python"
                    index += 1
                    continue
                if inner.startswith("run:"):
                    value = inner.split(":", 1)[1].strip()
                    if value in {"|", ">", "|-", ">-", "|+", ">+"}:
                        value = ""
                    if value:
                        context[index] = executor()
                    else:
                        run_block_start = index
                        run_block_indent = indent
                    index += 1
                    continue
                step_item = True
                if run_oses is None:
                    run_shell = None
                index += 1
                continue
            index += 1
            continue
        # indent >= 8: attributes of the current step item.
        content = stripped
        if step_item and content.startswith("shell:"):
            resolved = _resolve_shell_name(content.split(":", 1)[1])
            run_shell = resolved if resolved != "python" else "python"
            if resolved == "python":
                run_shell = "python"
            index += 1
            continue
        if step_item and content.startswith("run:"):
            flush_run_block(index)
            value = content.split(":", 1)[1].strip()
            if value in {"|", ">", "|-", ">-", "|+", ">+"}:
                value = ""
            if value:
                context[index] = executor()
            else:
                run_block_start = index
                run_block_indent = indent
            index += 1
            continue
        index += 1
    flush_run_block(section_end)
    return context


def command_text_source(source: SourceFile) -> SourceFile:
    """Return the shell-corpus view of a source file.

    - Markdown: shell code fences and inline command spans (historical).
    - Python: only string literals passed to explicit shell-execution
      contexts (``subprocess`` calls, ``os.system``/``os.popen``) remain;
      code, comments, docstrings, and ordinary string text cannot be
      executed by a shell and carry no corpus text.
    - Everything else: unchanged.
    """
    if source.path.suffix.lower() == ".md":
        return shell_examples(source)
    if source.path.suffix.lower() == _PY_SUFFIX:
        masked = _python_string_text_source(source)
        masked.exec_context = {"python_shell_corpus": True}
        return masked
    return source


def is_python_shell_corpus(source: SourceFile) -> bool:
    """True when the source is the Python shell-execution corpus view.

    Every remaining line of such a source was already vetted by the AST
    extractor as string text of an explicit shell-execution call, so the
    line-prefix heuristics that guard Markdown/prose no longer apply.
    """
    return bool(source.exec_context and source.exec_context.get("python_shell_corpus"))


_SHELL_EXEC_MODULES = {"os", "subprocess"}
_OS_SHELL_EXEC_FUNCS = {"system", "popen"}
_SUBPROCESS_SHELL_EXEC_FUNCS = {"run", "call", "Popen", "check_call", "check_output"}
_SHELL_EXEC_FUNCS = _OS_SHELL_EXEC_FUNCS | _SUBPROCESS_SHELL_EXEC_FUNCS


def _python_shell_strings(source: SourceFile) -> list[tuple[str, int, int]]:
    """Return (value, lineno, col_offset) of string constants passed to an
    explicit shell-execution call.  Rows are 1-based like AST nodes.

    Supported call shapes (literal string arguments only):
    - ``subprocess.run("cmd", ...)`` / ``subprocess.call`` / ``Popen`` /
      ``check_call`` / ``check_output`` (also via ``from subprocess import
      run`` and via module aliases such as ``import subprocess as sp``)
    - ``os.system("cmd")`` / ``os.popen("cmd")`` (also with ``os`` aliases
      and ``from os import system`` import forms)

    Import aliases are resolved structurally from the module's import
    statements; rebinding an imported name to another function later in the
    module is not tracked (documented limitation).  Strings inside
    docstrings, error messages, or other application text are intentionally
    not corpus: their language is unknown, so the conservative choice is no
    shell detection.
    """
    import ast

    results: list[tuple[str, int, int]] = []
    try:
        tree = ast.parse(source.text)
    except SyntaxError:
        return results

    module_aliases: dict[str, str] = {}
    function_aliases: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _SHELL_EXEC_MODULES:
                    module_aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module in _SHELL_EXEC_MODULES:
            for alias in node.names:
                if alias.name in _SHELL_EXEC_FUNCS:
                    function_aliases[alias.asname or alias.name] = (node.module, alias.name)

    def module_name_for(value: ast.AST) -> str | None:
        if isinstance(value, ast.Name):
            return module_aliases.get(value.id, value.id)
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        module: str | None = None
        func_name: str | None = None
        if isinstance(function, ast.Attribute):
            func_name = function.attr
            if isinstance(function.value, ast.Name):
                module = module_name_for(function.value)
        elif isinstance(function, ast.Name):
            bound = function_aliases.get(function.id)
            if bound is not None:
                module, func_name = bound
            else:
                func_name = function.id
        if func_name is None:
            continue
        if module is not None:
            if module == "os" and func_name not in _OS_SHELL_EXEC_FUNCS:
                continue
            if module == "subprocess" and func_name not in _SUBPROCESS_SHELL_EXEC_FUNCS:
                continue
            if module not in _SHELL_EXEC_MODULES:
                continue
        elif func_name not in _SHELL_EXEC_FUNCS:
            # Unbound bare name (no import evidence): accept only the
            # unambiguous subprocess family names so a local helper named
            # e.g. ``call`` is not claimed; shell-shaped string content is
            # still required by the shell rules before anything fires.
            continue
        for argument in [node.args[0]] if node.args else []:
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                results.append((argument.value, argument.lineno, argument.col_offset))
        for keyword in node.keywords:
            if keyword.arg in {"args", "command", "cmd"} and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                results.append((keyword.value.value, keyword.value.lineno, keyword.value.col_offset))
    return results


def _python_string_text_source(source: SourceFile) -> SourceFile:
    """Mask a Python file so only shell-execution string literals remain.

    Every masked row keeps the original source width; string text is placed
    at the column where the literal starts, so finding columns stay close to
    the source.  Strings are split into physical rows, mapping each row back
    to its source line.
    """
    lines = list(source.lines)
    masked = [[" "] * len(line) if line else [] for line in lines]
    for value, lineno, col_offset in _python_shell_strings(source):
        rows = value.split("\n")
        row = lineno - 1
        if row < 0 or row >= len(masked):
            continue
        for part_index, part in enumerate(rows):
            if row >= len(masked):
                break
            if part_index == 0:
                _write_masked(masked, row, col_offset, part)
            else:
                _write_masked(masked, row, 0, part)
            row += 1
    return SourceFile(
        source.path,
        source.relative_path,
        "\n".join("".join(chars) for chars in masked),
        source.size,
        source.mode,
        source.is_crlf,
    )


def _write_masked(masked: list[list[str]], row: int, column: int, text: str) -> None:
    """Write text into a masked row at a column without resizing the row."""
    if row < 0 or row >= len(masked):
        return
    for offset, char in enumerate(text):
        column_at = column + offset
        if column_at < len(masked[row]):
            masked[row][column_at] = char


def line_reachable_targets(source: SourceFile, line_index: int) -> frozenset[str] | None:
    """Executor target ids for one 0-based line; None means 'no proof'.

    Applied to shell/quoting findings only.  Reachability is per file type:

    - ``.ps1``: PowerShell targets (plus cross-interpreter carriers on the
      same line).
    - ``.cmd``/``.bat``: CMD targets.
    - ``.github/workflows/*.ya?ml``: the run: block's executor; non-run
      lines stay None (historical behavior).
    - Python and Markdown are handled through ``command_text_source``
      masking and need no per-line reachability filter.
    """
    suffix = source.path.suffix.lower()
    if suffix in _FILE_SHELL_TARGETS:
        base = set(_FILE_SHELL_TARGETS[suffix])
        if suffix == ".ps1":
            line = source.lines[line_index] if 0 <= line_index < len(source.lines) else ""
            for pattern, extra in _CROSS_SHELL:
                if pattern.search(line):
                    base.update(extra)
        return frozenset(base)
    if source.path.suffix.lower() in {".yml", ".yaml"} and (
        _WORKFLOW_RE.match(source.relative_path) or _WORKFLOW_RE.match(source.path.as_posix())
    ):
        context = source.exec_context if isinstance(source.exec_context, dict) else {}
        if "workflow" not in context:
            context["workflow"] = _workflow_executor_context(source)
            source.exec_context = context
        mapping = context["workflow"]
        return mapping.get(line_index) if isinstance(mapping, dict) else None
    return None


def reachability_filter(source: SourceFile, affected_targets: tuple[str, ...], line_index: int) -> bool:
    """Return True when a finding with affected_targets survives on this line.

    Findings whose affected targets cannot intersect the line's proven
    executor are dropped; unprovable executors keep the finding.
    """
    reachable = line_reachable_targets(source, line_index)
    if reachable is None:
        return True
    return bool(set(affected_targets) & reachable)
