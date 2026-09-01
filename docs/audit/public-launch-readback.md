# Public Launch Readback

Readback date: 2026-09-01 (Asia/Shanghai)<br>
Repository: https://github.com/kwhi6693-web/agent-xplat<br>
Authorized scope: publish the frozen `agent-xplat` v1.0.0 project, configure public repository metadata, publish the GitHub Release and downloadable package assets, and independently verify the public destination.

## Release identity

- Release: [agent-xplat v1.0.0](https://github.com/kwhi6693-web/agent-xplat/releases/tag/v1.0.0), published, not draft, not prerelease.
- Annotated tag object: `235b8f6be63062138b1da9f887da87306c96101c`.
- Peeled tag commit: `3ae71ec54a5ba433a50d8ff5de49bd892006d67d`.
- Release assets were built from the peeled commit and independently downloaded from GitHub.

## Repository metadata

- Description: `Detect cross-OS portability issues in AI agent workflows, skills, configs, and scripts across Windows, macOS, and Linux.`
- Topics: `agent-skills`, `ai-agent`, `bash`, `cli`, `cross-platform`, `developer-tools`, `github-actions`, `linux`, `macos`, `portability`, `powershell`, `python`, `sarif`, `static-analysis`, `windows`.
- Repository visibility: public; default branch: `master`.

## Public README and Badge readback

- Public `README.md` blob SHA: `e37299207de6fa897714aac691a876452256f9bf`, equal to the release source commit's README blob.
- Public `docs/assets/agent-xplat-verified.svg` blob SHA: `2adca9f186e0380ef51f94b7e96528dd20a4a184`, equal to the release source commit's Badge blob.
- Public README includes the first-screen positioning, Windows/macOS/Linux status, the static-versus-runtime evidence distinction, the v1.0.0 wheel install URL, and `agent-xplat scan .`.
- Public Badge readback contains `Cross-OS Verified` and the three OS labels. It is backed by the hosted runtime evidence below.

## Hosted runtime evidence

Workflow run: [33520727803](https://github.com/kwhi6693-web/agent-xplat/actions/runs/33520727803), head commit `3ae71ec54a5ba433a50d8ff5de49bd892006d67d`, attempt 2, overall conclusion `success`.

| Runner | Job ID | Runtime target | Result |
|---|---:|---|---|
| `windows-latest` | `99904579914` | `windows-powershell` | PASS / `VERIFIED` |
| `macos-latest` | `99904577298` | `macos-zsh` | PASS / `VERIFIED` |
| `ubuntu-latest` | `99904634376` | `linux-bash` | PASS / `VERIFIED` |

The project command recorded `88 passed` on each runner. Static scan documents remain `INFERRED`; only the runner-specific runtime evidence is `VERIFIED`. The first workflow attempt had a macOS job cancelled before any step started; the failed job was rerun without changing project code or workflow content and then passed.

## Workflow artifact validation

The four artifacts from each runner were downloaded and checked for existence, non-empty content, correct environment, and current tool version. Project validators returned no errors for JSON schema `1.0` and SARIF `2.1.0`; Markdown required sections were present.

## Release asset validation

| Asset | Size | SHA-256 |
|---|---:|---|
| `agent_xplat-1.0.0-py3-none-any.whl` | 71430 bytes | `f2b04bb290a4b14969e45e5e68d04ecb344e93380719d306c105b762e8119380` |
| `agent_xplat-1.0.0.tar.gz` | 73212 bytes | `31fa22c15d2e7d2a3f4d8cdf02e1c6a5da805c0692e272b13b8ef168a43c56f1` |

GitHub asset API digests and sizes matched the local build. The downloaded wheel installed in a fresh isolated environment, reported version `1.0.0`, and produced the expected five-finding Node AST fixture result.

## Audit result

- Security search: PASS; no secrets, credentials, telemetry, private URLs, or machine-specific paths were added.
- Repository scope: PASS; the launch change was limited to public metadata, README/Badge presentation, release notes, and release audit evidence; core implementation remained frozen.
- Installation distribution: PASS through GitHub Release wheel and source distribution. PyPI publication was not attempted because it was not an authorized target for this launch.
- Public-launch readback: PASS.
