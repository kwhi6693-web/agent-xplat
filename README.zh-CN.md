# agent-xplat

> 找出那些会破坏 AI Agent 工作流的操作系统假设。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![PyPI](https://img.shields.io/pypi/v/agent-xplat?style=flat-square)](https://pypi.org/project/agent-xplat/)
[![Python](https://img.shields.io/pypi/pyversions/agent-xplat?style=flat-square)](https://pypi.org/project/agent-xplat/)
[![Cross-OS Verified](https://img.shields.io/badge/Cross--OS%20Verified-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-2ea44f?style=flat-square)](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml)
[![CI](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml/badge.svg?branch=master&style=flat-square)](https://github.com/kwhi6693-web/agent-xplat/actions/workflows/agent-xplat.yml)
[![License](https://img.shields.io/github/license/kwhi6693-web/agent-xplat?style=flat-square)](LICENSE)

![agent-xplat — Cross-OS portability for AI-agent workflows](docs/assets/agent-xplat-social-preview.png)

## 为什么是 agent-xplat

AI Agent 工作流通常会组合 Markdown 指令、Shell 命令、Python、Node、包管理器和外部工具。一个在 Linux Bash 中有效的工作流，仍可能在 Windows PowerShell、Windows CMD、Git Bash、WSL 或 macOS zsh 中失败。

agent-xplat 是一个确定性的跨操作系统可移植性检查器，用于检查 AI Agent 工作流、Agent Skills、Agent 配置及相关脚本。它报告导致失败的 OS × Shell × Runtime 假设，而不只是指出操作系统不同。

Skill validator 检查结构，通用 linter 检查风格；agent-xplat 检查这些表面上有效的工作流能否在 Agent 实际运行的环境中生存。它明确不是安全扫描器、Agent Skill schema validator、benchmark、通用 linter 或仓库健康检查工具。

静态分析覆盖完整的 8 个目标矩阵，产生的发现状态为 `INFERRED`。当前验证路径还会在真实的 GitHub-hosted Windows、macOS 和 Linux runner 上执行；只有这些运行时检查才能产生 `VERIFIED` 证据。

## 快速开始

从 PyPI 安装已发布的 package，并扫描当前仓库：

```bash
python -m pip install agent-xplat
agent-xplat scan .
```

如果需要隔离的 CLI 安装：

```bash
pipx install agent-xplat
agent-xplat scan .
```

要求 Python 3.10 或更高版本。从 source checkout 安装：

```bash
python -m pip install .
agent-xplat scan .
```

开发环境安装：

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

始终可以使用 module invocation 作为 fallback：

```bash
python -m agent_xplat scan . --format json
```

## 示例

扫描会生成确定性的、按 target 区分的兼容性矩阵：

```text
Agent Workflow Portability
===========================

Compatibility Matrix
---------------------
Environment                Score Status    Findings
Windows / PowerShell      41/100 BLOCKED          4
Windows / CMD              1/100 BLOCKED          6
Windows / Git Bash        76/100 PARTIAL          3
Windows / WSL             76/100 PARTIAL          3
macOS / zsh               56/100 PARTIAL          4
macOS / bash              56/100 PARTIAL          4
Linux / bash              56/100 PARTIAL          4
Linux / zsh               56/100 PARTIAL          4

7 portability issues found (0 ignored)
```

这是仓库内置的 mixed-platform fixture 示例，不代表每个仓库都会得到相同结果。

## 兼容性矩阵

内部模型是 OS × Shell × Runtime：

| Target | OS | Shell | Runtime context |
|---|---|---|---|
| `windows-powershell` | Windows | PowerShell | native |
| `windows-cmd` | Windows | CMD | native |
| `windows-git-bash` | Windows | Bash | Git Bash |
| `windows-wsl` | Windows | Bash | WSL |
| `macos-zsh` | macOS | zsh | native |
| `macos-bash` | macOS | Bash | native |
| `linux-bash` | Linux | Bash | native |
| `linux-zsh` | Linux | zsh | native |

已发布的验证路径通过 GitHub-hosted jobs 覆盖 Windows、macOS 和 Linux。一次本地运行时只能验证当前主机对应的 target。

## 工作方式

1. 受限发现流程收集受支持的指令文件、脚本、manifest 和 metadata，同时排除生成文件、二进制文件、缓存和超大文件。
2. 文本 detector 与 Tree-sitter AST detector 在 Shell、Python、JavaScript、JSX、TypeScript 和 TSX source 中识别可移植性假设。
3. 49 条规则组成的 registry 会针对所有已配置的矩阵 target 检查每个 source，并把发现范围收窄到受影响的 target。
4. suppression、baseline、diff fingerprint 和兼容性契约会在不修改 source 的前提下应用。
5. 同一个 result model 会被渲染为 terminal 输出、JSON、SARIF、Markdown、baseline 和 diff artifact。

证据边界是明确的：

| Evidence | Status | 含义 |
|---|---|---|
| `STATIC` | `INFERRED` | 规则根据仓库内容推断出可移植性假设。 |
| `RUNTIME` | `VERIFIED` | 受限命令在已记录的主机上运行并产生运行时证据。 |

## 扫描范围

默认的受限发现流程包括 `SKILL.md`、`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`README.md`、`.github/**`、`.cursor/**`、`.claude/**`、`.codex/**`、`scripts/**`、package manifest 和 lockfile、Python metadata、Docker/Make 文件，以及常见的 Shell、Python、JavaScript、JSX、TypeScript、TSX 和 batch 扩展名（`.js`、`.mjs`、`.cjs`、`.jsx`、`.ts`、`.mts`、`.cts`、`.tsx`）。

`.git`、`node_modules`、`vendor`、`dist`、`build`、缓存、二进制文件和超大文件会被排除。

## 规则、严重级别与置信度

当前 registry 包含 49 条模块化规则，并使用稳定的 `AX-*` identifier。规则覆盖路径、Shell 命令与环境变量语法、quoting、Python、Node package script 和 Node/JS/TS AST 事实、文件系统、包管理器、外部工具、运行时假设及 Agent 配置。详见 [docs/RULES.md](docs/RULES.md)。

JavaScript 系列 source 会使用 Tree-sitter 做结构化解析。动态字符串和动态行为仍然属于静态推断。

Severity 为 `BLOCKER`、`ERROR`、`WARNING` 或 `INFO` 之一。Confidence 为 `HIGH`、`MEDIUM` 或 `LOW` 之一。低置信度假设会明确标记为低置信度，不会仅仅因为它不方便就升级为 blocker。

## 运行时验证

```bash
agent-xplat test .
```

`scan` 不会执行 target code。`test` 是显式且受限的：它可以在 timeout 限制下运行 allowlist 中的项目测试命令，并记录实际 host target、命令、exit code 和输出尾部。缺少命令时状态为 `INFERRED`，而不是 `VERIFIED`。一个主机的运行时证据不能证明整个矩阵。

发布验证记录了成功的 GitHub-hosted Windows、macOS 和 Linux jobs。每个 job 都记录自己的 `RUNTIME = VERIFIED` 证据；静态扫描仍为 `STATIC = INFERRED`。

## GitHub Actions 与 SARIF

```bash
agent-xplat init-ci
```

生成的 workflow 会在 `windows-latest`、`macos-latest` 和 `ubuntu-latest` 上运行。它会安装项目、运行测试、执行静态扫描、调用受控运行时验证、生成 JSON/SARIF/Markdown artifact、上传 artifact，并将 SARIF 上传到 Code Scanning。

仅仅在本地存在 workflow 文件，并不能证明 hosted jobs 已通过；在声明跨操作系统验证之前，仓库必须实际运行这些 jobs。

## 报告

```bash
agent-xplat scan .
agent-xplat scan . --format json --output agent-xplat.json
agent-xplat scan . --format sarif --output agent-xplat.sarif
agent-xplat report .
```

JSON 使用 `schema_version: 1.0` 进行版本化，供 Agent 和 CI 使用，并包含 `targets`、`scores`、`findings`、`baseline`、`contract`、`verification` 和 `summary`。SARIF 输出为 2.1.0 版本，包含 file、line、column、rule、level、message 和 help。Markdown 报告包含 executive summary、矩阵、blocking issues、warnings、assumptions、contract violations、受影响文件、建议修复、证据、ignored findings 和 baseline 状态。

## 安全修复

```bash
agent-xplat fix . --dry-run
agent-xplat fix .
```

只有确定性、高置信度且保持行为的修复才有资格自动应用。v1.0.1 会自动把 CRLF shebang 文件规范化为 LF。Shell 重写、路径重写、环境变量语法转换和依赖迁移仍只作为建议，因为仅凭静态文本无法证明它们等价。dry-run 会打印 unified patch，不会修改文件。

## 基线与差异

```bash
agent-xplat baseline
agent-xplat scan . --baseline-only
agent-xplat scan . --diff master
agent-xplat scan . --diff HEAD~1 --format markdown
```

Baseline 会区分 existing、new 和 resolved fingerprint。`--baseline-only` 会针对新增发现执行 gate。Diff mode 会从 Git reference 比较前后 score 与 issue fingerprint，不会执行 reference tree。

## 兼容性契约

`.agent-xplat.yml` 接受声明式支持范围与 requirements：

```yaml
supported:
  - windows-powershell
  - windows-git-bash
  - windows-wsl
  - macos-zsh
  - linux-bash
unsupported:
  - windows-cmd
requirements:
  python: ">=3.11"
  node: ">=22"
minimum_score: 85
fail_on:
  - BLOCKER
  - ERROR
```

也接受可选的 `agent-xplat:` wrapper。声明的 support 会与检测到的假设进行比较，并以 `VIOLATION` 报告；unsupported target 不会被当作契约失败。

### 配置与忽略规则

```bash
agent-xplat init
```

Schema 支持 `targets`、`exclude`、`ignore`、`minimum_score`、`fail_on`、`supported`、`unsupported`、`requirements`、`max_file_size` 和 `verification`。全局 suppression 使用 `ignore`。行级 marker 是显式且可审计的：

```text
# agent-xplat-ignore AX-SHELL-001
chmod +x scripts/render.sh
```

Ignored finding 仍会以 `ignored: true` 保留在 machine-readable output 中，summary 也会报告其数量。未知 key、target、severity、rule ID 和无效值都会以 exit code 2 失败。未使用的行级 suppression marker 会作为 suppression diagnostic 报告，而不会被静默接受。

## 面向 Agent 的使用方式

```bash
agent-xplat scan . --format json
```

Agent 应消费 `summary`、每个 target 的 `scores`、`findings` 和 `contract.violations`，不要解析 terminal decoration。

### CLI 命令

| Command | 用途 |
|---|---|
| `scan` | 推断跨操作系统可移植性问题 |
| `test` | 运行受控运行时验证 |
| `fix` | 规划并应用安全的确定性修复 |
| `report` | 写出 Markdown 可移植性报告 |
| `explain` | 解释一条可移植性规则 |
| `doctor` | 探测本地验证能力 |
| `baseline` | 写出当前发现的 baseline |
| `init` | 创建起始的 `.agent-xplat.yml` |
| `init-ci` | 创建三操作系统 GitHub Actions workflow |
| `badge` | 创建真实反映静态/运行时状态的 badge |

Root command 还支持 `--version`。Exit code 如下：

| Code | 含义 |
|---:|---|
| 0 | 没有触发已配置的可移植性 gate |
| 1 | 可移植性违规、契约违规或新的 diff regression |
| 2 | 配置、输入、Git reference 或命令参数无效 |
| 3 | 工具内部发生未预期错误 |

### Badge 与 doctor

```bash
agent-xplat badge
agent-xplat doctor
```

默认 badge 文案为 `Static Checked` 和 `Inference only`。`Cross-OS Verified` badge 必须有记录 Windows、macOS 和 Linux 验证证据的 verification artifact 支撑；静态扫描不会自动产生该 badge。`doctor` 只报告本地是否有 Git、Node、Python、Docker、PowerShell、Git Bash、WSL、Bash 和 zsh，不检查仓库健康状态。

## 安全模型

默认命令离线运行、相对于 target source 只读、不执行 target code、不收集 telemetry，也不会上传数据。`test` 是唯一可能执行选定 allowlist 项目测试命令的命令，并且不允许 shell operator，具有受限 timeout 和清晰的运行时证据记录。不存在 AI API、SaaS backend、credential upload 或隐藏网络路径。

## 架构

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。核心流程为：

```text
Config -> bounded discovery -> structured/text parsers -> rule registry
      -> target-specific findings -> suppression -> score/contract
      -> terminal / JSON / SARIF / Markdown / baseline / diff
```

## 限制

静态分析无法证明每一种 Shell 版本、已安装工具、文件系统策略、原生 binary、动态命令字符串或运行时行为。JavaScript 系列 source 已覆盖支持扩展名的结构化 AST 分析，但动态求值、生成代码、不支持的语法恢复和实际 subprocess 行为仍属于运行时问题。

Release workflow 已生成并有文档说明，但 hosted runner 证据必须来自用户自己的 GitHub 仓库。未来可以增加更多 runtime adapter 和经过独立审查的规则，同时保持公开 finding contract 不变。

## 参与贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，每次规则变更都添加 positive 和 negative fixture，运行 `python -m pytest -q`，并保持输出确定性。不要加入 telemetry、网络调用、secret 或机器特定路径。

## 发布与 PyPI

当前版本为 **v1.0.1**。package 已以 wheel 和 source distribution 形式发布到 [PyPI](https://pypi.org/project/agent-xplat/)，GitHub [Release v1.0.1](https://github.com/kwhi6693-web/agent-xplat/releases/tag/v1.0.1) 是对应的发布记录。

发布路径使用 GitHub Actions Trusted Publishing，即基于 OIDC 的发布流程，不需要长期有效的 PyPI token。[验证记录](docs/audit/verification-run.md) 说明了本地检查、托管 Windows/macOS/Linux 证据、package readback，以及 inferred 静态发现和 verified 运行时结果之间的边界。发布变更汇总在 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
