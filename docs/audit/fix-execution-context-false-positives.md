# Regression comparison: execution-context false-positive fixes

Candidate: unreleased `main` after the execution-context fix (branch
`fix/language-context-false-positives`).
Baseline: released `agent-xplat==1.0.2` installed in an isolated venv.

Fixed corpus commits (both verified equal to their remote `main`):

| Repository | Commit | Why chosen |
| --- | --- | --- |
| `kwhi6693-web/photo-abstract-editorial` | `80a83a022d222593b3b7916839fe5ff27f603c60` | remote `main` at trial time; matches the previous 203-finding baseline report |
| `kwhi6693-web/presentation-studio` | `6c03789649f8002f11a46c7b47d376336bbfee85` | remote `main` at trial time; matches the previous 8634-finding baseline report |

Commands (identical for both versions, JSON output, default configuration and
targets, scanned from a clean detached worktree, no target code executed):

```text
python -I -m agent_xplat scan <worktree> --format json --output scan-<version>.json
```

## Totals

| Repository | 1.0.2 | Candidate | Removed | Added | Kept |
| --- | ---: | ---: | ---: | ---: | ---: |
| photo-abstract-editorial | 203 | 86 | 117 | 0 | 86 |
| presentation-studio | 8634 | 5205 | 3429 | 0 | 5205 |

The complete removed-finding lists (rule, path, line, code, reason) are
archived alongside the scan reports that produced them (`removed.json` per
repository) for independent audit.

Removed findings by file zone:

| Zone | photo | presentation | Meaning |
| --- | ---: | ---: | --- |
| Python (`.py`) | 117 | 1697 | keyword arguments, `source = ...` assignments, `X \| Y` annotations, string text that is not an execution context |
| Workflow (`.github/workflows`) | 0 | 1399 | explicit bash steps on Linux/macOS runners reported through a CMD/PowerShell lens |
| PowerShell (`.ps1`) | 0 | 333 | legal `$var`/`$env:` reported through a CMD lens |
| Markdown (`.md`) | 0 | 0 | **unchanged** — Markdown command examples keep the historical cross-shell scope |
| Added | 0 | 0 | no unexpected findings |

## photo-abstract-editorial detail

All 117 removed findings are Python-zone. The 102 AX-SHELL-003 findings
claimed by the previous review round are confirmed one by one: every removed
finding's `code` is a Python keyword argument or assignment
(`detail="..."`, `tempfile(..., dir=...)`, `min_area=...`, `date_time=...`).

| Rule | Removed | Explanation |
| --- | ---: | --- |
| AX-SHELL-003 | 102 | Python kwargs read as POSIX `NAME=value command` |
| AX-SHELL-006 | 9 | Python `source = ...` assignments read as POSIX `source` |
| AX-QUOTE-007 | 5 | Python `X \| Y` type annotations read as pipelines |
| AX-QUOTE-004 | 1 | `$photo-...` text inside a test assertion string |

## presentation-studio detail

| Rule | Removed | Explanation |
| --- | ---: | --- |
| AX-SHELL-003 | 1284 | bash `name="$(...)"` assignments in explicit-bash Ubuntu jobs; Python kwargs |
| AX-QUOTE-004 | 1282 | `$var` in `.ps1` (PowerShell syntax) and in bash steps |
| AX-QUOTE-003 | 217 | backslash continuations in Python code lines |
| AX-SHELL-006 | 168 | Python `source = ...` assignments |
| AX-QUOTE-002 | 139 | `$(...)` command substitution in bash steps on Linux/macOS runners |
| AX-QUOTE-005 | 122 | `/dev/null`/here-string text in bash-only jobs and non-execution strings |
| AX-SHELL-002 | 80 | POSIX utilities in Python code text |
| AX-QUOTE-007 | 57 | pipelines in bash-only steps and Python annotations/strings |
| AX-QUOTE-001 | 35 | `${VAR}` in bash-only steps and Python strings |
| AX-SHELL-010 | 32 | semicolon chains in Python code lines |
| AX-SHELL-007 | 13 | `&&`/`\|\|` in Python code lines |

Zone split for presentation: workflow 1399, Python 1697, `.ps1` 333.

## Positive controls still detected

- Markdown code fences and inline commands: zero removed and zero added
  findings in `.md` files across both repositories.
- `.cmd` files: `$VAR` still fires AX-QUOTE-004 (CMD cannot expand it);
  legal CMD syntax (`set`, `%VAR%`, `where`) no longer fires cross-shell
  rules (fixture `cmd-only` updated accordingly).
- `.ps1` explicit cross-interpreter text: `cmd /c "echo %VAR%"` still fires
  AX-SHELL-005 (fixture `powershell-only` updated accordingly).
- Python explicit shell-execution strings: `subprocess.run("NODE_ENV=production
  node build.js", shell=True)` and `os.system("MODE=production node build.js")`
  fire AX-SHELL-003 at the exact line (regression tests
  `tests/test_source_context_false_positives.py`).
- Workflow Windows legs keep their findings: a `windows-latest` job (default
  PowerShell) still reports `FOO=bar cmd`; a `ubuntu-latest` + `windows-latest`
  matrix still reports it for the Windows leg; `self-hosted` and expression
  runners keep the historical behavior.

## Audit notes

- The 102-photo AX-SHELL-003 claim is re-derived here from the full removed
  list (see archived `removed.json`), not from a sample.
- No rule is disabled, no path is excluded, and no severity was changed.
- The candidate scans the same corpus commits as the baseline, so removed and
  added sets are comparable finding by finding.
- Both consumer trial PRs (photo #5, presentation #29) keep their draft and
  report mode and still run the released 1.0.2; this candidate has not been
  pointed at them.
