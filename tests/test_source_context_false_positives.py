"""Regression tests for execution-context false positives.

Covers the three observed false-positive families and their positive
controls:

A. Python keyword arguments must not be read as POSIX temporary
   environment assignments, while real commands inside Python string
   literals must still be detected.
B. GitHub Actions run: blocks must be scoped to the executor chosen by
   runs-on and the shell selection chain; unprovable executors keep the
   historical behavior.
C. .ps1 files are PowerShell source, .cmd/.bat files are CMD source:
   legal native syntax must not be reported through another shell's lens,
   while genuine cross-interpreter text (cmd /c, $VAR in .cmd) stays
   detected.
"""

from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source


def _scan(tmp_path: Path, relative_name: str, text: str):
    path = tmp_path / relative_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    return [finding for finding in findings if finding.rule_id.startswith(("AX-SHELL-", "AX-QUOTE-"))]


def _rule_ids(findings):
    return {finding.rule_id for finding in findings}


# --- A. Python call arguments are not shell text -------------------------

def test_python_keyword_arguments_are_not_shell_assignments(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "doctor.py",
        """def _fail(**kwargs):
    return kwargs


def check() -> None:
    result = _fail(
        detail="unsupported platform",
        what_failed="host platform support",
        required="Windows, Ubuntu/Linux, or macOS",
    )
    print(result)
""",
    )
    assert not any(f.rule_id == "AX-SHELL-003" for f in findings)


def test_python_named_arguments_are_not_shell_assignments(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "compose.py",
        """import tempfile
from pathlib import Path


def atomic(destination: Path) -> None:
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{destination.stem}.", suffix=destination.suffix, dir=destination.parent, delete=False
    )
    handle.close()
""",
    )
    assert not [f for f in findings if f.rule_id == "AX-SHELL-003"]


def test_python_imports_and_assignments_are_not_shell_text(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "tool.py",
        """import os
MODE = "production"
result = os.getenv("MODE") or MODE
print(result)
""",
    )
    assert not [f for f in findings if f.rule_id in {"AX-SHELL-003", "AX-SHELL-002", "AX-SHELL-006"}]


def test_python_string_literal_shell_command_stays_detected(tmp_path: Path):
    """Positive control: a real command in a subprocess string still fires."""
    findings = _scan(
        tmp_path,
        "runner.py",
        """import subprocess


def run() -> None:
    subprocess.run("NODE_ENV=production node build.js", shell=True)
""",
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert matches
    assert matches[0].location.line == 5


def test_python_os_system_command_stays_detected(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "osrun.py",
        """import os


def main() -> None:
    os.system("MODE=production node build.js")
""",
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert matches
    assert matches[0].location.line == 5


def test_python_docstring_and_message_text_are_not_shell_corpus(tmp_path: Path):
    """Docstrings and error-message strings are not shell-execution
    contexts; their language is unknown, so the conservative choice is no
    shell detection."""
    findings = _scan(
        tmp_path,
        "tool.py",
        '''"""Usage example:

FOO=bar command --flag
source .venv/bin/activate
"""


def main() -> None:
    raise FileNotFoundError("source image not found at the expected path")
''',
    )
    assert not [f for f in findings if f.rule_id.startswith(("AX-SHELL-", "AX-QUOTE-"))]


def test_python_import_aliases_keep_shell_execution_detection(tmp_path: Path):
    """from-import aliases and module aliases stay detectable."""
    bodies = [
        "import subprocess as sp\n\n\nsp.run('NODE_ENV=production node build.js', shell=True)\n",
        "from subprocess import run as sub_run\n\n\nsub_run('NODE_ENV=production node build.js', shell=True)\n",
        "import os as operating_system\n\n\noperating_system.system('MODE=production node build.js')\n",
        "from os import system as os_system\n\n\nos_system('MODE=production node build.js')\n",
    ]
    for body in bodies:
        findings = _scan(tmp_path, "aliased.py", body)
        matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
        assert matches, body
        assert matches[0].location.line == 4


def test_python_cross_interpreter_strings_inside_subprocess_stay_detected(tmp_path: Path):
    """A bash -c / cmd /c command string passed to subprocess is real
    shell-execution text; its inner assignments must still be reported."""
    findings = _scan(
        tmp_path,
        "cross.py",
        """import subprocess


def run_bash() -> None:
    subprocess.run('bash -c "FOO=bar echo hi"', shell=True)


def run_cmd() -> None:
    subprocess.run('cmd /c "echo %FOO%"', shell=True)
""",
    )
    assert [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert [f for f in findings if f.rule_id == "AX-SHELL-005"]


def test_python_dynamic_command_strings_are_a_documented_limit(tmp_path: Path):
    """Concatenated and variable-built commands are not statically
    resolvable; they must not fire (documented limitation), while the
    code lines themselves must not become shell text either."""
    findings = _scan(
        tmp_path,
        "dynamic.py",
        """import subprocess


def main(name: str) -> None:
    subprocess.run('NODE_ENV=production ' + name, shell=True)
    command = 'MODE=production node build.js'
    subprocess.run(command, shell=True)
    subprocess.run(f'MODE=production {name}', shell=True)
""",
    )
    assert not [f for f in findings if f.rule_id.startswith(("AX-SHELL-", "AX-QUOTE-"))]


# --- B. Workflow run blocks follow the job executor ----------------------

_BASH_STEP = """name: ci
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: resolve
        shell: bash
        run: |
          pulls="$(gh api repos/a/b/pulls)"
          if [[ -n "$pulls" ]]; then
            echo "$pulls" | jq length
          fi
"""


def test_workflow_bash_step_is_not_reported_for_other_shells(tmp_path: Path):
    findings = _scan(tmp_path, ".github/workflows/ci.yml", _BASH_STEP)
    assert not [f for f in findings if f.rule_id in {"AX-SHELL-003", "AX-QUOTE-002", "AX-QUOTE-004"}]


def test_workflow_default_bash_shell_on_ubuntu_is_scoped(tmp_path: Path):
    findings = _scan(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: ci
on: [push]
defaults:
  run:
    shell: bash
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          FOO=bar echo hi
          echo "$FOO"
""",
    )
    assert not [f for f in findings if f.rule_id in {"AX-SHELL-003", "AX-QUOTE-004"}]


def test_workflow_windows_runner_keeps_native_shell_findings(tmp_path: Path):
    """On a Windows runner the default shell is PowerShell, where POSIX
    temporary assignments and CMD-specific assumptions are real issues."""
    findings = _scan(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: ci
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - run: |
          FOO=bar echo hi
""",
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert matches
    assert "windows-powershell" in matches[0].affected_targets


def test_workflow_matrix_runner_keeps_findings_for_windows_leg(tmp_path: Path):
    findings = _scan(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: ci
on: [push]
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    steps:
      - run: |
          FOO=bar echo hi
""",
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert matches
    assert "windows-powershell" in matches[0].affected_targets


def test_workflow_matrix_include_with_os_is_unprovable_and_keeps_findings(tmp_path: Path):
    """matrix.include entries that add os combinations cannot be enumerated
    cheaply, so the executor is unprovable and the historical behavior
    (keep findings) applies."""
    findings = _scan(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: ci
on: [push]
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest]
        include:
          - os: windows-latest
            extra: true
    steps:
      - run: |
          FOO=bar echo hi
""",
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-003"]
    assert matches


def test_workflow_unprovable_runner_keeps_historical_behavior(tmp_path: Path):
    findings = _scan(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: ci
on: [push]
jobs:
  build:
    runs-on: self-hosted
    steps:
      - run: |
          FOO=bar echo hi
          echo "$FOO"
""",
    )
    matches = [f for f in findings if f.rule_id in {"AX-SHELL-003", "AX-QUOTE-004"}]
    assert matches


# --- C. PowerShell and CMD file language boundaries ----------------------

def test_powershell_dollar_variables_are_not_cmd_text(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "resolve-runtimes.ps1",
        '$ErrorActionPreference = "Stop"\n$foo = Join-Path $home "x"\nWrite-Output $foo\n',
    )
    assert not [f for f in findings if f.rule_id == "AX-QUOTE-004"]


def test_powershell_env_syntax_is_not_reported_in_ps1(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "run.ps1",
        '$env:FIXTURE_MODE = "1"\nWrite-Output $env:FIXTURE_MODE\n',
    )
    assert not [f for f in findings if f.rule_id == "AX-SHELL-004"]


def test_powershell_cmd_c_cross_interpreter_text_stays_detected(tmp_path: Path):
    """Positive control: explicit cmd /c text still receives CMD findings."""
    findings = _scan(
        tmp_path,
        "run.ps1",
        '$env:FIXTURE_MODE = "1"\ncmd /c "echo %FIXTURE_MODE% in cmd"\n',
    )
    matches = [f for f in findings if f.rule_id == "AX-SHELL-005"]
    assert matches
    assert "windows-cmd" not in matches[0].affected_targets


def test_cmd_dollar_variable_stays_detected(tmp_path: Path):
    """Positive control: $VAR inside a .cmd file is a genuine error."""
    findings = _scan(
        tmp_path,
        "run.cmd",
        "@echo off\nif defined FOO echo %FOO% is $FOO\n",
    )
    matches = [f for f in findings if f.rule_id == "AX-QUOTE-004"]
    assert matches
    assert "windows-cmd" in matches[0].affected_targets


def test_cmd_native_syntax_is_not_reported_for_other_shells(tmp_path: Path):
    findings = _scan(
        tmp_path,
        "run.cmd",
        "@echo off\nset FIXTURE_MODE=1\nwhere python\necho %FIXTURE_MODE%\n",
    )
    assert not [f for f in findings if f.rule_id in {"AX-SHELL-008", "AX-SHELL-009", "AX-SHELL-005"}]
