# Adopt agent-xplat in another repository

This is an **unreleased 1.0.2 candidate**. PyPI 1.0.1 does not contain these
changes. For preview, install this PR's full commit SHA (replace COMMIT_SHA):

```bash
python -m pip install 'agent-xplat @ git+https://github.com/kwhi6693-web/agent-xplat.git@COMMIT_SHA'
agent-xplat init-ci --tool-ref COMMIT_SHA
```

`--tool-ref` accepts exactly 40 lowercase hexadecimal characters. Review the
resulting `.github/workflows/agent-xplat.yml`, then commit it. After 1.0.2 is
actually published, `agent-xplat init-ci` can use its version-pinned PyPI default.
Do not use that default for this unreleased preview.

## What runs

The consumer workflow runs the scanner on Ubuntu against all configured target
environments. It installs **the scanner**, never the target repository. Checkout
lives in `target/`; `python -I` is invoked from its parent to prevent target
`sitecustomize.py` / `agent_xplat.py` shadowing. It does not run target tests,
package install scripts, Skills, or runtime verification. Only `contents: read`
is required. It uses `pull_request`, not `pull_request_target`; no additional PAT
is needed. Reports are saved before enforcing the gate, and Markdown is copied
to Job Summary (bounded at 900 KB; download artifacts for the full report).

This is distinct from agent-xplat's own three-OS development workflow, which
installs and tests trusted project code. Neither workflow establishes that an
arbitrary scanned project actually runs in all eight target environments.

## Review policy before blocking PRs

The ten-repository study found substantial remaining context limitations. Start
with a narrow set of supported targets and review findings before enabling a
required branch check. A Bash-only skill need not support CMD. Explicit platform
requirements in prose and workflow `runs-on` are not fully interpreted today;
configure targets/exclusions accordingly. Do not equate counts with defects.

```yaml
targets:
  - linux-bash
  - macos-bash
fail_on:
  - BLOCKER
  - ERROR
exclude:
  - tests/fixtures/**
```

Existing `.agent-xplat.yml` configuration is preserved by `init-ci`. Review policy
changes in PRs: their target/exclusion/fail_on changes affect the comparison.
This is a contributor tool, not an adversarial policy enforcement service.

## Existing issues and PR comparisons

For a push with existing debt, review findings and create a committed baseline:

```bash
agent-xplat baseline .
agent-xplat scan . --baseline-only
```

On PRs, the workflow uses `--diff` with the base commit SHA and `--baseline-only`.
Both trees use the current scan policy. The Git tree is read, not executed.
Only new findings at `fail_on` severities fail the new-only gate. Explicit
`supported` contract violations remain hard failures even with a baseline.
Without a baseline or PR comparison the gate falls back to all active findings.
A changed policy is not itself assessed for regression.

New baselines add `match_key`: it ignores line/column movement but includes path,
rule, code, reason, severity and affected targets. Repeated identical occurrences
are counted; adding a duplicate is new. Legacy fingerprint-only baselines still
load but cannot recognize line moves; regenerate them after reviewing an upgrade.
Moving/renaming a file or editing the command is deliberately treated as new.

| Exit | Meaning |
|---|---|
| 0 | No gate-triggering findings in the selected comparison; not runtime proof |
| 1 | Portability gate or declared support contract failed |
| 2 | Invalid input/configuration or inaccessible required input |
| 3 | Internal error or incomplete workflow scan |

## Reports and badges

Markdown includes the source commit, worktree state, tool version, timestamp,
scanned-text digest, affected environments, and a New Findings section. JSON 1.0
keeps existing fields and adds `summary.source_identity`. The digest covers
selected text paths/content, not every repository byte, file mode, or configuration.
A dirty worktree is explicitly distinguished from the commit. Non-Git inputs have
an unavailable commit. Artifact files inside the target may make later runs dirty;
write reports outside the target for repeatable provenance.

`agent-xplat badge .` now scans and writes `agent-xplat-badge.json` alongside the
SVG. It says only **Static Checked / Inference only**, even if issues exist.
Link the badge to the evidence/report, not to an unsupported compatibility claim.

`--runtime-verified` requires a clean committed tree and a manually assembled
`agent-xplat-verification.json` with matching `source_commit`, `tool_version`,
`status: VERIFIED`, `verified_os: [windows, macos, linux]`, and `runs` containing
successful records for all three OSes. Each run must include `os`, `status`,
`exit_code: 0`, `source_commit`, `tool_version`, `command`, and `evidence_url`.
Keep evidence/output files ignored so they do not dirty the source tree. Evidence
is locally supplied, not cryptographically attested; the tool does not fetch or
authenticate the URLs. Ordinary one-host `test` output is insufficient. No badge
should be interpreted as proof of every OS × Shell × Runtime combination.
