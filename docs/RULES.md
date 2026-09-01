# Rule catalog

All rules are registered in `src/agent_xplat/rules/registry.py`. Each rule has an ID, title, description, affected-environment metadata, default severity, confidence, remediation, examples, test cases, and rationale. Actual findings narrow the affected targets to the configured matrix.

| Rule | Family | Default severity | Confidence | Meaning |
|---|---|---|---|---|
| AX-PATH-001 | paths | WARNING | HIGH | POSIX absolute temporary/platform path |
| AX-PATH-002 | paths | ERROR | HIGH | Drive, UNC, profile, or Windows program path |
| AX-PATH-003 | paths | WARNING | MEDIUM | Shell-dependent home expansion or separator |
| AX-PATH-004 | paths | ERROR | HIGH | Reserved Windows filename |
| AX-PATH-005 | paths | WARNING | MEDIUM | Relative launcher spelling |
| AX-SHELL-001 | shell | BLOCKER | HIGH | `chmod` executable-bit requirement |
| AX-SHELL-002 | shell | ERROR | HIGH | POSIX utility in a native Windows shell |
| AX-SHELL-003 | shell/env | ERROR | HIGH | `export` or `NAME=value command` syntax |
| AX-SHELL-004 | shell/env | ERROR | HIGH | `$env:NAME` outside PowerShell |
| AX-SHELL-005 | shell/env | ERROR | HIGH | `%NAME%` outside CMD |
| AX-SHELL-006 | shell | ERROR | HIGH | `source` or dot-file POSIX loading |
| AX-SHELL-007 | shell | WARNING | MEDIUM | PowerShell-version-sensitive chaining |
| AX-SHELL-008 | shell | ERROR | HIGH | Windows `where` lookup outside CMD |
| AX-SHELL-009 | shell/env | ERROR | HIGH | `set NAME=value` outside CMD |
| AX-SHELL-010 | shell | INFO | LOW | Semicolon command chain |
| AX-QUOTE-001 | quoting | ERROR | HIGH | POSIX `${NAME}` interpolation |
| AX-QUOTE-002 | quoting | ERROR | HIGH | `$()` command substitution in CMD context |
| AX-QUOTE-003 | quoting | WARNING | MEDIUM | Backslash continuation across shells |
| AX-QUOTE-004 | quoting | ERROR | HIGH | Dollar variable in CMD context |
| AX-QUOTE-005 | quoting | ERROR | HIGH | POSIX redirection or Bash here-string |
| AX-QUOTE-006 | quoting | WARNING | MEDIUM | CMD caret escaping |
| AX-QUOTE-007 | quoting | WARNING | MEDIUM | Windows pipeline semantics |
| AX-FS-001 | filesystem | ERROR | HIGH | CRLF shebang on POSIX executor |
| AX-FS-002 | filesystem | WARNING | MEDIUM | Symlink or junction operation |
| AX-FS-003 | filesystem | WARNING | MEDIUM | Platform-specific file locking |
| AX-FS-004 | filesystem | INFO | LOW | Atomic rename/open-file assumption |
| AX-FS-005 | filesystem | ERROR | HIGH | Case-collision paths |
| AX-FS-006 | filesystem | WARNING | MEDIUM | Windows path-length assumption |
| AX-FS-007 | filesystem | ERROR | HIGH | Illegal Windows filename |
| AX-FS-008 | filesystem | INFO | LOW | Unicode path handling |
| AX-PY-001 | python | WARNING | MEDIUM | Unqualified/platform-specific Python launcher |
| AX-PY-002 | python | ERROR | HIGH | Unix Python shebang |
| AX-PY-003 | python | ERROR | HIGH | Platform-specific import or branch |
| AX-PY-004 | python | ERROR | HIGH | `venv/bin` or `venv/Scripts` layout |
| AX-PY-005 | python | WARNING | MEDIUM | Missing `requires-python` declaration |
| AX-PY-006 | python | WARNING | MEDIUM | Native Python dependency/build toolchain |
| AX-PY-007 | python | WARNING | MEDIUM | `pip`/`pip3` executable resolution |
| AX-NODE-001 | node | ERROR | HIGH | POSIX env assignment in package script |
| AX-NODE-002 | node | ERROR | HIGH | POSIX utility in package script |
| AX-NODE-003 | node | WARNING | MEDIUM | `.sh` or `.bin` executable path |
| AX-NODE-004 | node | WARNING | MEDIUM | Native Node dependency/build toolchain |
| AX-PM-001 | package managers | ERROR | HIGH | OS-specific package manager |
| AX-TOOL-001 | external tools | WARNING | MEDIUM | External executable assumed on PATH |
| AX-RUNTIME-001 | runtimes | INFO | LOW | Runtime command without version/capability declaration |
| AX-AGENT-001 | agent config | WARNING | HIGH | Agent file names one shell without fallback |

Use `agent-xplat explain AX-SHELL-001` for the full meaning, why it matters, examples, remediation, and severity/confidence rationale.
