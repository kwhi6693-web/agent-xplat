# Distribution Readiness Audit

Date: 2026-09-01
Project: `agent-xplat`
Scope: PyPI package metadata, build validation, isolated installation, and Trusted Publishing preparation. Core analyzer behavior and the existing `v1.0.0` tag/release are out of scope.

## Package metadata

| Field | Verified value |
|---|---|
| Name | `agent-xplat` |
| Version | `1.0.0` |
| Description | Detect cross-OS portability issues in AI agent workflows, skills, configs, and scripts. |
| Python | `>=3.10` |
| License | MIT SPDX expression with packaged `LICENSE` file |
| Runtime dependencies | `tree-sitter`, `tree-sitter-javascript`, `tree-sitter-typescript` with bounded minor-version ranges |
| Development dependency | `pytest>=8.0` under the `dev` extra |
| Console entry point | `agent-xplat = agent_xplat.cli:main` |
| Project URLs | Homepage, Repository, Documentation, Issues, and Changelog |

The README is declared as the long description and passed `twine check` for both distributions. The wheel metadata contains the MIT license expression, license file, project URLs, Python requirement, runtime dependencies, and console entry point.

## Local build and installation evidence

| Check | Result |
|---|---|
| `python -m pytest -q` | PASS — 88 passed |
| `python -m compileall -q src` | PASS |
| `python -m agent_xplat scan . --no-color` | PASS — 8 target rows, 100/100, 0 findings |
| Required CLI help probes | PASS — root plus 10 subcommands |
| `python -m build --sdist --wheel` | PASS |
| `twine check` on wheel and sdist | PASS |
| Fresh wheel installation | PASS — version `1.0.0`, `agent-xplat --help`, and self-scan pass |
| Fresh sdist installation | PASS — version `1.0.0`, and self-scan pass |
| `pip-audit` on installed runtime environment | PASS — no known vulnerabilities found |
| Repository credential/path/size audit | PASS — no tracked credential patterns, personal absolute paths, or files over 1 MiB |

Build artifacts from this audit:

- `agent_xplat-1.0.0-py3-none-any.whl` — 70,950 bytes — SHA-256 `5b48a59a57144c89765957559c57b343ba8548121fcdf27b4ebd74958c0092d9`
- `agent_xplat-1.0.0.tar.gz` — 72,826 bytes — SHA-256 `37c138bbc0c3b3cc7b7dbcb3baf2f3e9df10bf581b8f7cfcd4bdb464b1d09115`

These digests identify the exact local release-gate build inspected above. Both archive digests are build-instance-specific because the backend preserves source-file timestamps; every rebuilt archive was independently checked with `twine check` and contained the same validated package files.

## Trusted Publishing workflow

Workflow: `.github/workflows/publish-pypi.yml`

- Trigger: published GitHub Release only.
- Eligibility: non-prerelease `v*` tag, with an exact `v<project.version>` check before artifact upload.
- Build job: creates the wheel and sdist, runs metadata validation, and uploads the validated artifact.
- Publish job: downloads the artifact, validates it again, and runs on `ubuntu-latest`.
- Permissions: workflow-level `contents: read`; publish-job `id-token: write` and `contents: read` only.
- Authentication: no PyPI token, password, username, repository secret, or credential is configured.
- Action safety: third-party actions are pinned to immutable commit SHAs.
- The existing `v1.0.0` tag/release was not recreated or mutated.

## Trusted Publisher status

PyPI-side Trusted Publisher registration is pending maintainer action. No PyPI upload was attempted. Before the first formal release publication, register the GitHub publisher for:

- PyPI project: `agent-xplat`
- Owner: `kwhi6693-web`
- Repository: `agent-xplat`
- Workflow filename: `publish-pypi.yml`
- GitHub environment: `pypi`

The GitHub repository environment named `pypi` should be created with manual approval protection before enabling the first publish.

## Limitations

Trusted Publishing cannot be proven by local execution because it requires the PyPI-side publisher registration and a real GitHub Release event. The workflow is intentionally prepared for a future formal release/tag and will reject non-`v*`, prerelease, and tag/version-mismatch releases before publication.
