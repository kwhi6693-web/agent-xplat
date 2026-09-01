import json
from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.discovery import source_file_from_path
from agent_xplat.rules import analyze_source


def test_python_rules_use_ast_for_imports_and_interpreter_assumptions(tmp_path: Path):
    path = tmp_path / "tool.py"
    path.write_text(
        "#!/usr/bin/python3\nimport subprocess\nimport winreg\nimport sys\nif sys.platform == 'win32':\n    print('windows')\nsubprocess.run(['python3', '-m', 'pip'])\npython_cmd = 'venv/bin/python'\n",
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-PY-001" in ids
    assert "AX-PY-002" in ids
    assert "AX-PY-003" in ids
    assert "AX-PY-004" in ids
    platform_finding = next(finding for finding in findings if finding.rule_id == "AX-PY-003")
    assert platform_finding.confidence.value == "HIGH"


def test_node_scripts_are_structurally_read_from_package_json(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps({"scripts": {"build": "NODE_ENV=production node build.js && rm -rf dist"}}),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-NODE-001" in ids
    assert "AX-NODE-002" in ids


def test_node_package_script_rules_do_not_scan_non_script_json_values(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps(
            {
                "description": "rm -rf dist is mentioned here",
                "dependencies": {"rm": "1.0.0", "NODE_ENV": "1.0.0"},
                "scripts": {"build": "node build.js"},
            }
        ),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-NODE-002" not in {finding.rule_id for finding in findings}


def test_node_package_scripts_scope_shell_chaining_to_script_values(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps({"description": "build && test; this is prose", "scripts": {"build": "node build.js && npm test; echo done"}}),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    ids = {finding.rule_id for finding in findings}
    assert "AX-SHELL-007" in ids
    assert "AX-SHELL-010" in ids
    assert all(finding.location.column > path.read_text(encoding="utf-8").index('"description"') + 1 for finding in findings if finding.rule_id in {"AX-SHELL-007", "AX-SHELL-010"})


def test_node_ast_reports_unbound_shell_and_environment_assumptions(tmp_path: Path):
    path = tmp_path / "workflow.ts"
    path.write_text(
        """
import * as cp from "node:child_process";
const output = process.env.OUTPUT;
cp.exec("rm -rf dist");
cp.spawnSync("cmd.exe", ["/c", "echo", "ok"]);
if (process.platform === "win32") {
  cp.spawnSync("powershell.exe");
}
""".lstrip(),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    by_rule = {finding.rule_id: finding for finding in findings}
    assert {"AX-NODE-005", "AX-NODE-006", "AX-NODE-007", "AX-NODE-008"}.issubset(by_rule)
    command_finding = next(finding for finding in findings if finding.rule_id == "AX-NODE-005" and finding.location.line == 3)
    assert "windows-powershell" in command_finding.affected_targets
    assert "linux-bash" in by_rule["AX-NODE-008"].affected_targets


def test_node_ast_does_not_flag_a_complete_platform_fallback_branch(tmp_path: Path):
    path = tmp_path / "guarded.js"
    path.write_text(
        """
if (process.platform === "win32") {
  usePowerShell();
} else {
  useBash();
}
""".lstrip(),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-NODE-007" not in {finding.rule_id for finding in findings}


def test_node_ast_binds_import_require_and_alias_forms_for_all_child_process_calls(tmp_path: Path):
    path = tmp_path / "bindings.mts"
    path.write_text(
        """
import { exec, execSync as sync, spawn, spawnSync as spawnNow } from "node:child_process";
exec("rm");
sync("rm");
spawn("rm");
spawnNow("rm");
const cp = require("child_process");
cp.exec("rm");
const { execSync: run } = require("child_process");
run("rm");
const direct = require("child_process").spawn;
direct("rm");
""".lstrip(),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    calls = [finding for finding in findings if finding.rule_id == "AX-NODE-005"]
    assert len(calls) == 7
    assert {finding.location.line for finding in calls} == {2, 3, 4, 5, 7, 9, 11}


def test_node_ast_detects_posix_inline_environment_assignment_in_command_strings(tmp_path: Path):
    path = tmp_path / "env-command.js"
    path.write_text(
        'const cp = require("child_process");\ncp.exec("NODE_ENV=production node build.js");\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    command = next(finding for finding in findings if finding.rule_id == "AX-NODE-005")
    assert "environment assignment" in command.reason
    assert "windows-powershell" in command.affected_targets


def test_node_ast_detects_hardcoded_posix_binary_paths(tmp_path: Path):
    path = tmp_path / "binary-path.js"
    path.write_text(
        'const cp = require("node:child_process");\ncp.exec("/bin/rm -rf dist");\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    binary = next(finding for finding in findings if finding.rule_id == "AX-NODE-008")
    assert binary.metadata["kind"] == "posix-executable"
    assert "windows-powershell" in binary.affected_targets


def test_node_ast_accepts_explicit_environment_fallback(tmp_path: Path):
    path = tmp_path / "env.cjs"
    path.write_text(
        'const required = process.env.REQUIRED ?? "default";\nconst optional = process.env.OPTIONAL || "fallback";\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-NODE-006" not in {finding.rule_id for finding in findings}


def test_node_ast_requires_a_structural_child_process_binding(tmp_path: Path):
    path = tmp_path / "unrelated.js"
    path.write_text(
        'const child_process = { exec: callback };\nchild_process.exec("rm -rf dist");\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert "AX-NODE-005" not in {finding.rule_id for finding in findings}


def test_node_native_dependency_detection_is_scoped_to_dependency_keys(tmp_path: Path):
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps(
            {
                "description": "better-sqlite3 is mentioned in this prose",
                "scripts": {"build": "node build.js"},
                "dependencies": {"better-sqlite3": "1.0.0"},
                "devDependencies": {"sharp": "1.0.0"},
            }
        ),
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    native = [finding for finding in findings if finding.rule_id == "AX-NODE-004"]
    assert len(native) == 2
    assert any("package better-sqlite3" in finding.reason for finding in native)
    assert any("package sharp" in finding.reason for finding in native)
    better_sqlite = next(finding for finding in native if "better-sqlite3" in finding.reason)
    text = path.read_text(encoding="utf-8")
    dependency_key = text.index('"better-sqlite3"', text.index('"dependencies"'))
    assert better_sqlite.location.line == 1
    assert better_sqlite.location.column == dependency_key + 1


def test_node_path_and_profile_detection_preserve_spaces_and_userprofile(tmp_path: Path):
    path = tmp_path / "workflow.md"
    path.write_text(
        "Run C:\\Program Files\\Agent Tools\\agent.exe\nUse $USERPROFILE\\bin\\agent.exe\nUse $HOME\nUse $HOME_VAR\n",
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    windows_paths = [finding for finding in findings if finding.rule_id == "AX-PATH-002"]
    assert any("C:\\Program Files\\Agent Tools\\agent.exe" in finding.reason for finding in windows_paths)
    assert any("$USERPROFILE" in finding.reason for finding in windows_paths)
    home_paths = [finding for finding in findings if finding.rule_id == "AX-PATH-003"]
    assert any("$HOME" in finding.reason for finding in home_paths)
    assert not any("$HOME_VAR" in finding.reason for finding in home_paths)


def test_node_ast_routes_every_supported_javascript_family_suffix_through_tree_sitter(tmp_path: Path):
    for suffix in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx"):
        path = tmp_path / f"child-process{suffix}"
        path.write_text(
            'import { exec } from "node:child_process";\nexec("rm -rf dist");\n',
            encoding="utf-8",
        )
        findings = analyze_source(source_file_from_path(path, tmp_path), Config())
        ast_findings = [finding for finding in findings if finding.rule_id == "AX-NODE-005"]
        assert ast_findings, suffix
        assert ast_findings[0].metadata["analysis"] == "tree-sitter-ast"


def test_node_ast_does_not_report_fully_guarded_child_process_selection(tmp_path: Path):
    path = tmp_path / "guarded.tsx"
    path.write_text(
        'import * as cp from "node:child_process";\n'
        'if (process.platform === "win32") {\n'
        '  cp.spawnSync("powershell.exe");\n'
        '} else {\n'
        '  cp.spawnSync("bash", ["-lc", "echo ok"]);\n'
        '}\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    assert not {finding.rule_id for finding in findings} & {"AX-NODE-005", "AX-NODE-007", "AX-NODE-008"}


def test_node_platform_branches_follow_runtime_os_for_wsl_and_git_bash(tmp_path: Path):
    path = tmp_path / "runtime.js"
    path.write_text(
        'import * as cp from "node:child_process";\n'
        'if (process.platform === "win32") {\n'
        '  cp.exec("rm -rf dist");\n'
        '}\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    command = next(finding for finding in findings if finding.rule_id == "AX-NODE-005")
    assert "windows-powershell" in command.affected_targets
    assert "windows-git-bash" in command.affected_targets
    assert "windows-wsl" not in command.affected_targets


def test_node_ast_downgrades_recovered_syntax_findings_to_medium_confidence(tmp_path: Path):
    path = tmp_path / "recovered.js"
    path.write_text(
        'import { exec } from "node:child_process";\nexec("rm -rf dist");\nconst broken = ;\n',
        encoding="utf-8",
    )
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    command = next(finding for finding in findings if finding.rule_id == "AX-NODE-005")
    assert command.confidence.value == "MEDIUM"
    assert command.metadata["syntax_recovery"]


def test_package_managers_and_external_tools_are_inferred_not_verified(tmp_path: Path):
    path = tmp_path / "README.md"
    path.write_text("brew install ffmpeg\napt-get install docker.io\n", encoding="utf-8")
    findings = analyze_source(source_file_from_path(path, tmp_path), Config())
    package = next(finding for finding in findings if finding.rule_id == "AX-PM-001")
    assert package.confidence.value == "HIGH"
    assert "macos-zsh" not in package.affected_targets
    assert "linux-bash" in package.affected_targets
    assert any(finding.rule_id == "AX-TOOL-001" for finding in findings)
