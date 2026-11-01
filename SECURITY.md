# 安全策略 / Security Policy

**项目 / Project**: Research Tree Generator / 科技树生成器
**适用版本 / Versions**: 2.2.x
**最后更新 / Last updated**: 2026-11-01

---

## 支持的版本 / Supported Versions

| 版本 / Version | 安全更新 / Security Updates |
|----------------|-----------------------------|
| `2.2.x` | ✅ 支持 / Supported |
| `< 2.2` | ❌ 不再支持 / Unsupported |

我们只为最新发布线提供安全修复。旧版本请先升级再报告问题。

Only the latest release line receives security fixes. Please upgrade before reporting.

---

## 报告漏洞 / Reporting a Vulnerability

### 请勿公开披露 / Do not disclose publicly

**不要**在公开 Issue、Discussion、社交平台或模组社区里描述漏洞细节。
公开披露会使用户在补丁可用之前暴露于风险。

**Do not** describe the vulnerability in public issues, discussions, social media or
modding communities. Public disclosure puts users at risk before a fix exists.

### 首选渠道 / Preferred channel

1. 打开本仓库的 **Security** 标签页 / Open the repository's **Security** tab
2. 点击 **Report a vulnerability**（私有漏洞报告）/ Click **Report a vulnerability**
3. 按下方清单填写 / Fill in the checklist below

若该入口不可用（仓库未启用私有报告），请开一个**不含技术细节**的 Issue，
只说明"有安全问题需要私下沟通"，维护者会提供后续渠道。

If private reporting is unavailable, open an issue **without technical details**
stating that you need a private channel; the maintainer will follow up.

### 报告内容清单 / What to include

请尽量提供：

- **受影响版本**（如 `2.2.2`）与运行方式（源码 / Release 打包版）
- **操作系统**与 Python / PyQt5 版本
- **复现步骤**（最小化、可重复）
- **影响评估**：能做什么（读取本地文件、覆盖文件、崩溃、拒绝服务、路径穿越等）
- **PoC**：样本 `.set` 文件、`.pak` / TGA 图片，或触发脚本
- **是否已公开**：是否已告知他人或在别处讨论过
- 可选：希望如何署名，或要求**匿名**

Please provide:

- **Affected version** (e.g. `2.2.2`) and how you run it (source / packaged release)
- **OS** plus Python / PyQt5 versions
- **Reproduction steps** (minimal and repeatable)
- **Impact**: what an attacker can do (read local files, overwrite files, crash,
  denial of service, path traversal, etc.)
- **PoC**: a sample `.set` file, `.pak` / TGA image, or trigger script
- **Disclosure status**: whether you already told anyone or discussed it elsewhere
- Optional: how you want to be credited, or a request to stay **anonymous**

匿名的请求会被尊重，不会在公告中泄露你的身份。

Anonymity requests are respected; your identity will not appear in the advisory.

---

## 响应流程与时限 / Response Process

以下为**尽力而为**的目标，非合同承诺。

Best-effort targets, not contractual commitments.

| 阶段 / Stage | 目标时间 / Target |
|--------------|-------------------|
| 确认收到 / Acknowledgement | 3 个工作日内 / within 3 business days |
| 初步评估 / Initial assessment | 7 个工作日内 / within 7 business days |
| 修复或缓解 / Fix or mitigation | 严重问题 30 天内，其余按排期 / critical within 30 days, others scheduled |
| 协调披露 / Coordinated disclosure | 修复发布后，或双方约定的 90 天内 / after the fix ships, or within 90 days by agreement |

我们会同步进展；如果你在时限内没有收到回复，可以再发一次提醒。

We keep you posted; if you get no reply within the target window, please ping again.

---

## 影响范围 / Scope

### 属于范围 / In scope

- 本仓库的全部源码（`src/`、`main.py`、`test_imports.py`）
- 构建产物（`Research_Tree_Generator.spec`、`run.bat`、`run_tests.bat`、CI 工作流）
- 解析逻辑（`.set` 文本、`{positions}` 块、Conquest 行）
- 资源加载逻辑（`portrait_manager`：文件夹、`.pak`(zip)、TGA 解码）
- 导出逻辑（临时文件、`.bak` 备份、原子替换、路径处理）

- All source in this repository (`src/`, `main.py`, `test_imports.py`)
- Build assets (`Research_Tree_Generator.spec`, `run.bat`, `run_tests.bat`, CI workflow)
- Parsing logic (`.set` text, `{positions}` blocks, Conquest lines)
- Resource loading (`portrait_manager`: folders, `.pak` (zip), TGA decoding)
- Export logic (temp file, `.bak` backup, atomic replace, path handling)

### 不属于范围 / Out of scope

- **游戏本体**与**第三方 mod** 的任何问题（请找对应发行方）
- 上游依赖漏洞（PyQt5 / Qt / Python）——请报给上游，我们跟进升级
- 用户本机环境、杀毒软件误报、非官方二次打包版本
- 纯理论、无实际影响路径的报告
- 社会工程、物理接触、已有管理员权限前提下的问题

- Any issue in the **game itself** or in **third-party mods** (contact their publishers)
- Upstream dependency flaws (PyQt5 / Qt / Python) — report upstream; we track upgrades
- Local environment issues, antivirus false positives, unofficial repackages
- Purely theoretical reports with no real impact path
- Social engineering, physical access, or anything requiring prior admin rights

---

## 安全相关的设计说明 / Security-Relevant Design

帮助报告者快速定位风险面。

Helps researchers focus on the actual attack surface.

| 方面 / Aspect | 现状 / Current state |
|---------------|----------------------|
| 网络 / Network | **无任何网络功能**，不发送数据、不检查更新 / **No network features at all**; no telemetry, no update checks |
| 代码执行 / Code execution | 不执行 `.set`、`.pak`、图片中的任何内容；只做文本/二进制解析 / Never executes content from `.set`, `.pak` or images; parsing only |
| 外部输入 / External input | 解析不可信文本与图片路径，为主要攻击面 / Parsing untrusted text and image paths is the main surface |
| 文件写入 / File writes | 导出使用「临时文件 + `os.replace` 原子替换」，并自动生成 `.bak` 备份；写失败时原文件保持不变 / Export uses temp file + `os.replace` and writes a `.bak`; on failure the original stays intact |
| 路径处理 / Path handling | 用户选择的资源目录会拼接子路径（潜在路径穿越关注点）/ User-chosen resource folders are joined with sub-paths (path-traversal concern) |
| 图片解码 / Image decoding | 自研 TGA 解码（类型 2/10、24/32 位），存在畸形输入风险 / Custom TGA decoder (types 2/10, 24/32-bit) is exposed to malformed input |
| 依赖面 / Dependencies | 仅 PyQt5（运行时）；打包版内置 Python 运行时 / Only PyQt5 at runtime; the packaged build bundles Python |

---

## 关于 AI 生成代码 / On AI-Generated Code

本项目的源码、测试与文档**主要由 AI 编码助手生成**（详见 [NOTICE](NOTICE)）。
这对安全报告有两层含义：

1. **不要因为"是 AI 写的"而降低报告门槛**。我们按**实际影响**评估，而不是按作者是
   人还是模型。报告时无需证明代码由 AI 生成。
2. **AI 生成代码更容易存在边界条件缺陷**（异常路径、畸形输入、状态同步）。
   因此以下类型的报告对我们特别有价值：

This project's source, tests and docs are **primarily generated by AI coding
assistants** (see [NOTICE](NOTICE)). Two implications for security reports:

1. **Never lower your reporting bar because "AI wrote it".** We triage by **actual
   impact**, not by whether a human or a model wrote the line. You do not need to
   prove AI involvement.
2. **AI-generated code is more prone to edge-case defects** (error paths, malformed
   input, state synchronisation). Reports of the following kinds are especially
   valuable:

- 畸形或超大的 `.set` / `.pak` / TGA 输入导致的崩溃、越界、内存增长
- 正则回溯、超大文件导致的拒绝服务
- 导出过程中的路径穿越或意外覆盖
- 撤销/重做、多父节点等状态机在极端序列下的不一致

- Crashes, out-of-bounds access or memory growth from malformed/oversized
  `.set` / `.pak` / TGA input
- Regex backtracking or oversized files causing denial of service
- Path traversal or accidental overwrite during export
- State-machine inconsistencies (undo/redo, multi-parent) under extreme sequences

已采取的缓解措施（不构成保证）：

- 135 项单元测试 + 导入自检 + 导出往返一致性测试
- 关键缺陷的根因记录与回归测试（见 `LONG_TERM_MEMORY.md` §9）
- 发布前人工验收与冒烟测试

Mitigations already in place (not a guarantee):

- 135 unit tests + import self-check + export round-trip consistency tests
- Root-cause notes and regression tests for key defects (`LONG_TERM_MEMORY.md` §9)
- Manual acceptance and smoke testing before release

> **不承诺**：AI 生成代码不存在漏洞。测试通过不等于代码安全。
>
> **No guarantee**: AI-generated code is not vulnerability-free. Passing tests does
> not mean the code is secure.

---

## 披露政策 / Disclosure Policy

- 我们采用**协调披露**：修复发布后再公开细节。
- 默认在安全公告中署名报告者；**要求匿名者会被尊重**。
- 我们不提供漏洞赏金（无资金支持），但会在 Release Notes 中致谢（经你同意）。
- 若我们 90 天内未响应，你可自行决定披露；请提前告知。

- We follow **coordinated disclosure**: details go public after the fix ships.
- Reporters are credited by default; **anonymity is respected**.
- We offer no bug bounty (no funding) but will thank you in Release Notes (with consent).
- If we do not respond within 90 days, you may disclose on your own; please notify us first.

---

## 联系方式 / Contact

- 首选：GitHub **Security → Report a vulnerability**
- 次选：开不含细节的 Issue 请求私下渠道
- 请**不要**通过公开渠道发送漏洞细节

- Preferred: GitHub **Security → Report a vulnerability**
- Fallback: open an issue without details to request a private channel
- **Never** send vulnerability details through public channels

---

> 本文件与项目一同按 [MIT](LICENSE) 分发，不构成任何担保。详见 [NOTICE](NOTICE)。
> 本文档由 AI 编码助手生成，经人工审核。
>
> Distributed with the project under [MIT](LICENSE), with no warranty. See [NOTICE](NOTICE).
> This document was produced with AI assistance and human review.
