# Ten-repository exploratory portability study

This is a targeted diagnostic study, not a benchmark of defect rates or a claim that these projects are broken. All sources are public and pinned below. No target scripts, Skills or tests were executed. Repository instructions were treated as data.

## Reproduce

Use the candidate scanner commit from this PR and clone each listed repository at its recorded SHA. From outside each target, run:

```bash
python -I -m agent_xplat scan TARGET --no-baseline --format json --output REPORT.json
```

Default scope: all eight targets, candidate file families, UTF-8 text below 1 MB, generated/vendor exclusions. `files_scanned` is the selected text count, not the total repository size. Both before and after scan the same commits. Before: base scanner 1.0.1; after: unreleased 1.0.2. Source/configuration evidence and final report hashes are in [the machine-readable record](real-world-study.json). Large reports and third-party sources are intentionally not committed.

## Results

| Repository | Commit | Selected files | Before findings | After findings |
|---|---|---:|---:|---:|
| [anthropics/skills](https://github.com/anthropics/skills) | `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f` | 232 | 1697 | 966 |
| [openai/skills](https://github.com/openai/skills) | `49f948faa9258a0c61caceaf225e179651397431` | 174 | 2503 | 1925 |
| [obra/superpowers](https://github.com/obra/superpowers) | `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` | 94 | 5094 | 5043 |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `063bee94c3f4df8453406c830b0a7df0f2860278` | 198 | 2230 | 1849 |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | `7b1ebe6333397841ca918dec904d24d4695fe953` | 1008 | 20940 | 15748 |
| [microsoft/skills](https://github.com/microsoft/skills) | `02e0b2f852b39ea00c43283f999b83fc12079273` | 1640 | 35746 | 21517 |
| [expo/skills](https://github.com/expo/skills) | `d0075ffa09928f1edb3e7ac4f5af07586d4b344d` | 58 | 1735 | 1184 |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | `8331f910845103c08d51f6ca1d86ebb7d1f745e3` | 12 | 141 | 115 |
| [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) | `c2d65dfe492f74d360d35b859b88932222470bd8` | 52 | 475 | 329 |
| [aloth/PowerSkills](https://github.com/aloth/PowerSkills) | `c6fac3dd2301818b9d7feed1699f9dc301351ab1` | 18 | 1576 | 1507 |

Counts include warnings and informational assumptions. A count reduction is not a measured precision improvement: conservative extraction can also miss unusual commands. Every scan exited 1 because default policy found errors; this does not establish third-party defects.

## Manual review

Reviewed exactly 30 baseline entries: the first three ERROR/BLOCKER entries per repository in deterministic report order, with surrounding source and relevant platform declarations. This deliberately biased sample locates early report noise; it does not estimate repository-wide precision.

- 25 false positives; 22 no longer emitted and 3 remain.
- 5 intentional platform designs: macOS-specific skill or Ubuntu-only workflows; all remain reported by broad default targets.
- 0 confirmed third-party compatibility defects in this sample; 0 unresolved classifications. Thousands of other findings remain **unreviewed**.
- Remaining reviewed false positives: Python documentation string, JavaScript home-path normalization, and an escaped regular expression misread as a UNC path.
- Do not automatically file issues against these projects using raw scanner findings.

| Repository / location | Rule | Review | Remains |
|---|---|---|---|
| [anthropics/skills · README.md:20](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/README.md#L20) | AX-SHELL-006 | License prose uses the word source; not shell execution. | no |
| [anthropics/skills · README.md:20](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/README.md#L20) | AX-SHELL-006 | A prose sentence boundary is not dot-source syntax. | no |
| [anthropics/skills · skills/algorithmic-art/SKILL.md:223](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/algorithmic-art/SKILL.md#L223) | AX-SHELL-006 | Instruction sentence punctuation outside an inline file path is not a shell command. | no |
| [openai/skills · README.md:19](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md#L19) | AX-QUOTE-004 | Agent skill identifier is not shell variable expansion. | no |
| [openai/skills · README.md:24](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md#L24) | AX-QUOTE-004 | Agent invocation in an unlabelled fence is not CMD input. | no |
| [openai/skills · README.md:30](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md#L30) | AX-QUOTE-004 | Agent invocation in an unlabelled fence is not CMD input. | no |
| [obra/superpowers · .hermes-plugin/__init__.py:64](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/.hermes-plugin/__init__.py#L64) | AX-SHELL-006 | Python string describing agent invocation is not a shell source command. | yes |
| [obra/superpowers · .opencode/plugins/superpowers.js:41](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/.opencode/plugins/superpowers.js#L41) | AX-PATH-003 | JS normalizes a home token using a path API; it is not CMD expansion. | yes |
| [obra/superpowers · README.md:346](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/README.md#L346) | AX-SHELL-002 | Prose word which is not a utility invocation. | no |
| [vercel-labs/agent-skills · .github/workflows/agent-skills-discovery.yml:42](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/.github/workflows/agent-skills-discovery.yml#L42) | AX-QUOTE-001 | Ubuntu-only job uses legitimate shell interpolation. | yes |
| [vercel-labs/agent-skills · .github/workflows/agent-skills-discovery.yml:44](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/.github/workflows/agent-skills-discovery.yml#L44) | AX-QUOTE-004 | Ubuntu-only release job uses a legitimate shell variable. | yes |
| [vercel-labs/agent-skills · .github/workflows/agent-skills-discovery.yml:44](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/.github/workflows/agent-skills-discovery.yml#L44) | AX-QUOTE-005 | Ubuntu-only release job uses legitimate POSIX redirection. | yes |
| [github/awesome-copilot · .github/agents/agentic-workflows.md:28](https://github.com/github/awesome-copilot/blob/7b1ebe6333397841ca918dec904d24d4695fe953/.github/agents/agentic-workflows.md#L28) | AX-SHELL-006 | Source-file prose is not source execution. | no |
| [github/awesome-copilot · .github/agents/agentic-workflows.md:230](https://github.com/github/awesome-copilot/blob/7b1ebe6333397841ca918dec904d24d4695fe953/.github/agents/agentic-workflows.md#L230) | AX-SHELL-006 | Prose and URL punctuation are not dot-source syntax. | no |
| [github/awesome-copilot · .github/agents/agentic-workflows.md:231](https://github.com/github/awesome-copilot/blob/7b1ebe6333397841ca918dec904d24d4695fe953/.github/agents/agentic-workflows.md#L231) | AX-SHELL-006 | Workflow documentation prose is not a shell command. | no |
| [microsoft/skills · .github/agents/backend.agent.md:101](https://github.com/microsoft/skills/blob/02e0b2f852b39ea00c43283f999b83fc12079273/.github/agents/backend.agent.md#L101) | AX-SHELL-003 | Python fenced function arguments are not shell environment assignment. | no |
| [microsoft/skills · .github/agents/backend.agent.md:102](https://github.com/microsoft/skills/blob/02e0b2f852b39ea00c43283f999b83fc12079273/.github/agents/backend.agent.md#L102) | AX-SHELL-003 | Python fenced parameters are not shell environment assignment. | no |
| [microsoft/skills · .github/agents/backend.agent.md:179](https://github.com/microsoft/skills/blob/02e0b2f852b39ea00c43283f999b83fc12079273/.github/agents/backend.agent.md#L179) | AX-SHELL-003 | Inline model configuration example is not a shell environment assignment. | no |
| [expo/skills · .claude/skills/expo-skill-eval/SKILL.md:6](https://github.com/expo/skills/blob/d0075ffa09928f1edb3e7ac4f5af07586d4b344d/.claude/skills/expo-skill-eval/SKILL.md#L6) | AX-PATH-003 | This skill explicitly requires macOS/Xcode; a CMD diagnostic is outside its declared use. | yes |
| [expo/skills · .claude/skills/expo-skill-eval/SKILL.md:13](https://github.com/expo/skills/blob/d0075ffa09928f1edb3e7ac4f5af07586d4b344d/.claude/skills/expo-skill-eval/SKILL.md#L13) | AX-SHELL-006 | Requirements sentence is not a dot-source command. | no |
| [expo/skills · .claude/skills/expo-skill-eval/SKILL.md:19](https://github.com/expo/skills/blob/d0075ffa09928f1edb3e7ac4f5af07586d4b344d/.claude/skills/expo-skill-eval/SKILL.md#L19) | AX-SHELL-006 | Instruction prose is not dot-source syntax. | no |
| [supabase/agent-skills · AGENTS.md:39](https://github.com/supabase/agent-skills/blob/8331f910845103c08d51f6ca1d86ebb7d1f745e3/AGENTS.md#L39) | AX-SHELL-006 | Release prose is not a dot-source command. | no |
| [supabase/agent-skills · AGENTS.md:62](https://github.com/supabase/agent-skills/blob/8331f910845103c08d51f6ca1d86ebb7d1f745e3/AGENTS.md#L62) | AX-PATH-002 | Escaped regular-expression dots are not a UNC path. | yes |
| [supabase/agent-skills · skills/supabase/SKILL.md:31](https://github.com/supabase/agent-skills/blob/8331f910845103c08d51f6ca1d86ebb7d1f745e3/skills/supabase/SKILL.md#L31) | AX-SHELL-002 | Database advice uses the word which in prose, not a POSIX command. | no |
| [hashicorp/agent-skills · .github/workflows/validate.yml:23](https://github.com/hashicorp/agent-skills/blob/c2d65dfe492f74d360d35b859b88932222470bd8/.github/workflows/validate.yml#L23) | AX-SHELL-001 | The job explicitly runs on Ubuntu; chmod is appropriate for that declared runner. | yes |
| [hashicorp/agent-skills · AGENTS.md:29](https://github.com/hashicorp/agent-skills/blob/c2d65dfe492f74d360d35b859b88932222470bd8/AGENTS.md#L29) | AX-SHELL-006 | Team ownership prose is not dot-source syntax. | no |
| [hashicorp/agent-skills · README.md:39](https://github.com/hashicorp/agent-skills/blob/c2d65dfe492f74d360d35b859b88932222470bd8/README.md#L39) | AX-SHELL-006 | Plugin installation prose is not dot-source syntax. | no |
| [aloth/PowerSkills · .github/ISSUE_TEMPLATE/bug_report.md:26](https://github.com/aloth/PowerSkills/blob/c6fac3dd2301818b9d7feed1699f9dc301351ab1/.github/ISSUE_TEMPLATE/bug_report.md#L26) | AX-QUOTE-004 | Issue template asks for the PowerShell version; not a CMD command. | no |
| [aloth/PowerSkills · README.md:74](https://github.com/aloth/PowerSkills/blob/c6fac3dd2301818b9d7feed1699f9dc301351ab1/README.md#L74) | AX-SHELL-003 | Browser command-line flag is not a temporary environment assignment. | no |
| [aloth/PowerSkills · SKILL.md:22](https://github.com/aloth/PowerSkills/blob/c6fac3dd2301818b9d7feed1699f9dc301351ab1/SKILL.md#L22) | AX-SHELL-006 | Installation prose contains a sentence boundary, not a dot-source command. | no |

## Decision

The sample substantiates fixing Markdown prose interpretation and prioritizing scope configuration. It does **not** yet substantiate marketing this as a low-noise required gate across arbitrary repositories. The consumer integration is suitable for a reviewed pilot; broad unattended adoption remains unvalidated. Three independent maintainer installations and sustained use have not occurred in this task.

The scanner self-scan excludes its detector/test/documentation sources and therefore cannot replace this external evaluation. Real CI runner results for the candidate are recorded separately in the verification log.
