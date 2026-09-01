"""Stable registry of modular portability rules."""

from __future__ import annotations

from ..config import Config
from ..environments import TARGETS
from ..models import Confidence, Severity, Finding, SourceFile
from .agent_config import detect_agent_config
from .common import ALL_TARGET_IDS, RuleContext, RuleSpec
from .external_tools import detect_external_tools
from .filesystem import detect_filesystem
from .node import detect_node
from .package_managers import detect_package_managers
from .paths import detect_paths
from .python import detect_python
from .quoting import detect_quoting
from .runtimes import detect_runtimes
from .shell import detect_shell


def _spec(
    rule_id: str,
    title: str,
    description: str,
    severity: Severity,
    confidence: Confidence,
    remediation: str,
    detector,
    example: str,
    test_case: str,
    severity_rationale: str,
    confidence_rationale: str,
) -> RuleSpec:
    return RuleSpec(
        rule_id, title, description, ALL_TARGET_IDS, severity, confidence, remediation,
        (example,), (test_case,), detector, severity_rationale, confidence_rationale,
    )


_RULES: tuple[RuleSpec, ...] = (
    _spec("AX-PATH-001", "POSIX absolute path", "Detects POSIX temporary and platform paths that native Windows shells cannot resolve.", Severity.WARNING, Confidence.HIGH, "Use an OS-neutral temporary-directory or path API.", detect_paths, "/tmp/cache", "POSIX path in a workflow", "Native Windows has no equivalent path spelling.", "The literal path is directly observable."),
    _spec("AX-PATH-002", "Windows-specific path", "Detects drive letters, UNC paths, and Windows profile/program path tokens.", Severity.ERROR, Confidence.HIGH, "Use a path API and resolve platform directories at runtime.", detect_paths, r"C:\\Program Files\\Tool", "Windows path in a Unix-targeted file", "The drive/separator syntax is explicit.", "The literal path is directly observable."),
    _spec("AX-PATH-003", "Path expansion or separator", "Detects shell-dependent home expansion and hardcoded separators.", Severity.WARNING, Confidence.MEDIUM, "Use a runtime path API or a portable launcher.", detect_paths, "~/cache", "Home expansion in a CMD path", "Expansion and separator semantics vary by shell.", "The text is clear but intent may be documentation."),
    _spec("AX-PATH-004", "Reserved Windows filename", "Detects reserved device names that cannot be ordinary Windows filenames.", Severity.ERROR, Confidence.HIGH, "Rename the path or validate it before creating files.", detect_paths, "CON", "Reserved filename in a script", "Windows rejects the name in normal file operations.", "The reserved-name list is deterministic."),
    _spec("AX-PATH-005", "Relative launcher spelling", "Detects ./ and .\\ launcher spellings that differ across shells.", Severity.WARNING, Confidence.MEDIUM, "Use a runtime path API or an explicit shell launcher.", detect_paths, "./scripts/build.sh", "Relative launcher in a CMD-sensitive workflow", "Relative path spellings have shell-specific execution semantics.", "The literal prefix is explicit."),
    _spec("AX-SHELL-001", "POSIX executable-bit command", "Detects chmod and executable-bit assumptions.", Severity.BLOCKER, Confidence.HIGH, "Use a portable launcher or avoid executable-bit requirements.", detect_shell, "chmod +x scripts/run.sh", "chmod in an agent workflow", "The command is unavailable in native Windows shells.", "The command token and effect are unambiguous."),
    _spec("AX-SHELL-002", "POSIX utility in native shell", "Detects common POSIX utilities without a shell qualification.", Severity.ERROR, Confidence.HIGH, "Use a portable runtime API or declare a shell/launcher requirement.", detect_shell, "grep pattern file", "grep in instructions", "Native PowerShell/CMD do not provide the same command contract.", "The command token is explicit."),
    _spec("AX-SHELL-003", "POSIX environment assignment", "Detects export and temporary NAME=value command syntax.", Severity.ERROR, Confidence.HIGH, "Use a cross-shell launcher or set the environment through the host runtime.", detect_shell, "NODE_ENV=production node build.js", "Inline environment assignment", "Native Windows shells parse this differently.", "Syntax is directly identifiable."),
    _spec("AX-SHELL-004", "PowerShell environment syntax", "Detects $env: variable syntax outside PowerShell.", Severity.ERROR, Confidence.HIGH, "Use a shell-neutral environment API or a target-specific branch.", detect_shell, "$env:FOO=bar", "PowerShell variable in Bash", "Other shells do not interpret the prefix.", "The syntax is explicit."),
    _spec("AX-SHELL-005", "CMD environment syntax", "Detects percent-style variables outside CMD.", Severity.ERROR, Confidence.HIGH, "Use a runtime environment API or target-specific launcher.", detect_shell, "%FOO%", "CMD variable in zsh", "Other shells do not expand percent variables.", "The syntax is explicit."),
    _spec("AX-SHELL-006", "POSIX source command", "Detects source/dot file loading outside a POSIX shell.", Severity.ERROR, Confidence.HIGH, "Use a portable launcher or invoke the file with the target shell.", detect_shell, "source scripts/env.sh", "source in PowerShell", "Native Windows shells do not provide POSIX source semantics.", "The command form is explicit."),
    _spec("AX-SHELL-007", "Version-sensitive command chaining", "Detects chaining whose support differs between Windows PowerShell versions.", Severity.WARNING, Confidence.MEDIUM, "Use a versioned shell or separate commands with explicit error handling.", detect_shell, "build && test", "&& in a script", "Windows PowerShell 5 differs from PowerShell 7.", "Impact depends on the actual shell version."),
    _spec("AX-SHELL-008", "Windows command lookup", "Detects where lookup syntax that is not portable to other shells.", Severity.ERROR, Confidence.HIGH, "Use a runtime lookup API or shell-neutral launcher.", detect_shell, "where node", "where in a POSIX script", "Lookup commands are shell-specific.", "The command form is explicit."),
    _spec("AX-SHELL-009", "CMD environment assignment", "Detects set NAME=value outside CMD.", Severity.ERROR, Confidence.HIGH, "Use a shell-neutral environment API or launcher.", detect_shell, "set FOO=bar", "set in a Bash script", "CMD assignment syntax differs from POSIX and PowerShell.", "The syntax is explicit."),
    _spec("AX-SHELL-010", "Semicolon command chain", "Detects semicolon command chaining in shell-like text.", Severity.INFO, Confidence.LOW, "Use separate commands with explicit error handling where portability matters.", detect_shell, "build; test", "semicolon chain", "Command separator and failure propagation differ by shell context.", "Natural-language or quoted semicolons are ambiguous."),
    _spec("AX-QUOTE-001", "POSIX brace interpolation", "Detects ${VAR} interpolation outside a POSIX shell.", Severity.ERROR, Confidence.HIGH, "Use a shell-neutral template or target-specific syntax.", detect_quoting, "${HOME}/bin", "Brace interpolation", "CMD/PowerShell do not expand it as Bash does.", "The syntax is explicit."),
    _spec("AX-QUOTE-002", "Command substitution", "Detects command substitution in a CMD-sensitive context.", Severity.ERROR, Confidence.HIGH, "Use a runtime API or a shell-specific wrapper.", detect_quoting, "$(pwd)", "Command substitution in CMD target", "CMD has no equivalent substitution syntax.", "The syntax is explicit."),
    _spec("AX-QUOTE-004", "Dollar variable in CMD", "Detects POSIX/PowerShell dollar variables in CMD-sensitive text.", Severity.ERROR, Confidence.HIGH, "Use a shell-neutral environment API or a target-specific launcher.", detect_quoting, "$FOO", "Dollar variable in CMD", "CMD does not expand dollar variables.", "The syntax is explicit."),
    _spec("AX-QUOTE-005", "POSIX redirection", "Detects /dev/null redirection and Bash here-strings.", Severity.ERROR, Confidence.HIGH, "Use a target-neutral stream API or the target shell's null device.", detect_quoting, "2>/dev/null", "POSIX redirection", "Native Windows uses different null-device and here-string syntax.", "The syntax is explicit."),
    _spec("AX-QUOTE-006", "CMD caret escaping", "Detects caret escapes that do not carry across shells.", Severity.WARNING, Confidence.MEDIUM, "Use a shell-specific launcher or an argument API.", detect_quoting, "echo ^&", "CMD escape", "Caret escaping is not interpreted by PowerShell or POSIX shells.", "The escape token is explicit."),
    _spec("AX-QUOTE-007", "Windows pipeline semantics", "Detects pipelines whose value semantics differ in PowerShell and text shells.", Severity.WARNING, Confidence.MEDIUM, "Use a runtime API or test the pipeline in each target shell.", detect_quoting, "producer | grep value", "Cross-shell pipeline", "PowerShell passes objects while Bash and CMD pass text.", "The pipeline token is explicit, but command behavior can still be guarded."),
    _spec("AX-QUOTE-003", "Shell line continuation", "Detects backslash line continuation that differs between shells.", Severity.WARNING, Confidence.MEDIUM, "Use explicit multiline configuration or the target shell's continuation form.", detect_quoting, "command \\", "Backslash continuation", "PowerShell uses a different continuation contract.", "Text context can change the intent."),
    _spec("AX-FS-001", "Shebang with CRLF", "Detects CRLF shebangs that can fail on POSIX executors.", Severity.ERROR, Confidence.HIGH, "Use LF for executable scripts or invoke the interpreter explicitly.", detect_filesystem, "#!/usr/bin/env bash with CRLF", "CRLF script fixture", "The carriage return becomes part of the interpreter path.", "Line ending and shebang are directly observed."),
    _spec("AX-FS-002", "Symlink or junction assumption", "Detects filesystem link operations with OS-specific permission behavior.", Severity.WARNING, Confidence.MEDIUM, "Provide a copy fallback or verify link capability at runtime.", detect_filesystem, "ln -s source target", "Symlink command", "Link behavior varies by OS, permissions, and filesystem.", "The operation is explicit but capability is environment-dependent."),
    _spec("AX-FS-003", "File locking API", "Detects platform-specific file-locking calls.", Severity.WARNING, Confidence.MEDIUM, "Use a cross-platform locking library or abstraction.", detect_filesystem, "fcntl.flock(fd)", "Locking API", "Locking semantics and APIs differ by OS.", "The API is identifiable, but usage may be guarded."),
    _spec("AX-FS-004", "Atomic rename assumption", "Flags text that assumes atomic rename while a file is open or locked.", Severity.INFO, Confidence.LOW, "Document the filesystem contract and use a retry/replace strategy.", detect_filesystem, "atomic rename after open", "Rename assumption", "Behavior varies with sharing and filesystem semantics.", "Natural-language context can be ambiguous."),
    _spec("AX-FS-005", "Case-collision filename", "Detects two repository paths that differ only by filename case.", Severity.ERROR, Confidence.HIGH, "Rename one path so all target filesystems address it uniquely.", detect_filesystem, "Readme.md and README.md", "Case collision fixture", "Case-insensitive filesystems address both paths as one file.", "The collision is computed from actual repository paths."),
    _spec("AX-FS-006", "Windows path length assumption", "Detects repository paths near common Windows path limits.", Severity.WARNING, Confidence.MEDIUM, "Shorten the path or document long-path requirements.", detect_filesystem, "a/very/long/path", "Long path fixture", "Some Windows environments impose path-length limits.", "Effective limits depend on OS policy and configuration."),
    _spec("AX-FS-007", "Illegal Windows filename", "Detects filename characters or trailing forms rejected by Windows.", Severity.ERROR, Confidence.HIGH, "Rename the file or document a target-specific generated path.", detect_filesystem, "report?.md", "Illegal filename fixture", "Windows rejects these filename forms.", "The filename is directly observed."),
    _spec("AX-FS-008", "Unicode path handling", "Flags non-ASCII paths so encoding and normalization can be tested explicitly.", Severity.INFO, Confidence.LOW, "Exercise the workflow with Unicode paths and preserve UTF-8 handling.", detect_filesystem, "工作流/输出.txt", "Unicode path fixture", "Encoding and normalization policies vary across tools.", "The path is observed, but Unicode itself is not an error."),
    _spec("AX-PY-001", "Python executable resolution", "Detects unqualified or platform-specific Python launcher assumptions.", Severity.WARNING, Confidence.MEDIUM, "Use a declared version and environment-aware launcher.", detect_python, "python3 -m pytest", "Python command in a script", "Executable resolution differs by installation and OS.", "The invocation is visible but environment policy may define it."),
    _spec("AX-PY-002", "Unix Python shebang", "Detects Unix-only Python shebangs.", Severity.ERROR, Confidence.HIGH, "Invoke through the environment or provide a Windows launcher.", detect_python, "#!/usr/bin/env python3", "Python shebang", "Native Windows does not execute the shebang contract.", "The shebang path is explicit."),
    _spec("AX-PY-003", "Platform-specific Python API", "Detects imports and platform branches tied to one OS.", Severity.ERROR, Confidence.HIGH, "Guard the import and supply an equivalent implementation or target declaration.", detect_python, "import winreg", "Platform-specific import", "The module is unavailable on another OS.", "AST import nodes provide direct evidence."),
    _spec("AX-PY-004", "Virtualenv path layout", "Detects hardcoded venv/bin or venv/Scripts paths.", Severity.ERROR, Confidence.HIGH, "Resolve the environment executable through the active interpreter.", detect_python, "venv/bin/python", "Virtualenv path", "Python environment directories differ by OS.", "Directory spelling is explicit."),
    _spec("AX-PY-005", "Undeclared Python version", "Detects a Python project without a requires-python declaration.", Severity.WARNING, Confidence.MEDIUM, "Declare the supported Python range in project metadata.", detect_python, "[project] without requires-python", "pyproject missing version", "A declared runtime floor prevents incompatible installs.", "The absence is directly checked in project metadata."),
    _spec("AX-PY-006", "Native Python dependency", "Detects Python dependencies likely to require platform-specific binaries or build toolchains.", Severity.WARNING, Confidence.MEDIUM, "Verify wheels or document the required compiler/runtime per target.", detect_python, "pywin32", "native Python dependency", "Native packages may not install identically on every target.", "The dependency name is explicit but availability still varies."),
    _spec("AX-PY-007", "Pip executable resolution", "Detects pip and pip3 PATH assumptions.", Severity.WARNING, Confidence.MEDIUM, "Use the active interpreter's module API or a declared environment.", detect_python, "python -m pip install", "pip launcher", "Pip command resolution varies by installation and shell.", "The executable token is explicit."),
    _spec("AX-NODE-001", "Node script environment assignment", "Detects POSIX environment assignments in package scripts.", Severity.ERROR, Confidence.HIGH, "Use a cross-shell launcher or set environment variables in JavaScript.", detect_node, "NODE_ENV=production node build.js", "package.json script", "npm scripts use a platform shell.", "package.json scripts are parsed structurally and syntax is explicit."),
    _spec("AX-NODE-002", "POSIX package script command", "Detects Unix utilities in package.json scripts.", Severity.ERROR, Confidence.HIGH, "Replace with a Node API or target-neutral package command.", detect_node, "rm -rf dist", "package script utility", "Native Windows shells do not share the POSIX utility contract.", "The script JSON value is directly inspected."),
    _spec("AX-NODE-003", "Node executable extension assumption", "Detects .sh or node_modules/.bin path assumptions in package scripts.", Severity.WARNING, Confidence.MEDIUM, "Call the package binary through npm/pnpm/yarn or a Node launcher.", detect_node, "./scripts/build.sh", "package script path", "Executable and separator behavior differs on Windows.", "The path is explicit but may be guarded."),
    _spec("AX-NODE-004", "Native Node dependency", "Detects dependencies likely to require platform-specific binaries or build toolchains.", Severity.WARNING, Confidence.MEDIUM, "Verify prebuild coverage or document the required compiler/runtime per target.", detect_node, "better-sqlite3", "native package dependency", "Native packages may not ship identical binaries for every target.", "The dependency name is explicit but availability still varies."),
    _spec("AX-PM-001", "Platform package manager", "Detects brew, apt, winget, choco, and related install commands.", Severity.ERROR, Confidence.HIGH, "Use a documented per-OS install matrix or a runtime capability check.", detect_package_managers, "brew install ffmpeg", "Package manager in README", "Package-manager availability is OS-specific.", "The manager token is explicit."),
    _spec("AX-TOOL-001", "External executable dependency", "Detects assumed external tools that static analysis cannot verify.", Severity.WARNING, Confidence.MEDIUM, "Declare the dependency and verify it in CI or provide a fallback.", detect_external_tools, "ffmpeg input.mp4", "External tool invocation", "PATH availability and versions vary across machines.", "Tool mention may be documentation rather than execution."),
    _spec("AX-RUNTIME-001", "Unversioned runtime command", "Detects runtime commands without an explicit version/capability declaration.", Severity.INFO, Confidence.LOW, "Declare supported Python/Node versions and check the runtime.", detect_runtimes, "node build.js", "Unversioned runtime", "An installed command may resolve differently.", "The command may be covered by external project policy."),
    _spec("AX-AGENT-001", "Agent shell requirement", "Detects an AI-agent file that names one shell without a fallback.", Severity.WARNING, Confidence.HIGH, "Document supported target shells or provide a portable launcher.", detect_agent_config, "shell: bash", "Agent configuration shell", "A declared shell is a direct portability assumption.", "The configuration key/value is explicit."),
)

_BY_ID = {rule.rule_id: rule for rule in _RULES}


def all_rules() -> tuple[RuleSpec, ...]:
    return _RULES


def get_rule(rule_id: str) -> RuleSpec | None:
    return _BY_ID.get(rule_id)


def analyze_source(source: SourceFile, config: Config) -> list[Finding]:
    context = RuleContext(config, tuple(target for target in TARGETS if target.id in config.targets))
    specs = {rule.rule_id: rule for rule in _RULES}
    findings_by_fingerprint: dict[str, Finding] = {}
    for rule in _RULES:
        for finding in rule.detector(source, context, specs):
            if finding is not None:
                findings_by_fingerprint[finding.fingerprint] = finding
    findings = list(findings_by_fingerprint.values())
    return sorted(
        (finding for finding in findings if finding is not None),
        key=lambda finding: (finding.location.path, finding.location.line, finding.location.column, finding.rule_id, finding.fingerprint),
    )
