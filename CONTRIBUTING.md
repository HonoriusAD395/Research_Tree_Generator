# 贡献指南 / Contributing Guide

感谢你愿意改进科技树生成器。本文说明开发流程、代码规范，以及**最重要的一条**：
提交前必须声明是否使用了 AI 生成内容。

Thanks for improving Research Tree Generator. This guide covers the workflow, coding
standards, and **the most important requirement**: you must disclose whether your
contribution used AI generation.

---

## 目录 / Contents

1. [行为准则](#1-行为准则--code-of-conduct)
2. [开发环境](#2-开发环境--development-setup)
3. [提交前检查清单](#3-提交前检查清单--pre-submit-checklist)
4. [代码规范](#4-代码规范--coding-standards)
5. [提交信息规范](#5-提交信息规范--commit-messages)
6. [⚠️ AI 使用披露要求](#6-️-ai-使用披露要求--ai-usage-disclosure--required)
7. [Pull Request 流程](#7-pull-request-流程--pull-request-process)
8. [许可证与素材](#8-许可证与素材--license-and-assets)

---

## 1. 行为准则 / Code of Conduct

- 对事不对人；技术分歧用数据和复现说话
- 不提交他人的版权素材（游戏资源、第三方 mod 文件）
- 不公开他人隐私信息
- 安全问题走 [SECURITY.md](SECURITY.md)，**不要**发公开 Issue

---

## 2. 开发环境 / Development Setup

```bash
git clone https://github.com/HonoriusAD395/Research_Tree_Generator.git
cd Research_Tree_Generator

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python test_imports.py                  # 自检
python -m unittest discover -s tests    # 全部测试
python main.py                          # 运行 GUI
```

要求：Python 3.7+、PyQt5。开发时 `debug.py` 的 `DEBUG` 由环境变量 `DEBUG=1` 打开。

---

## 3. 提交前检查清单 / Pre-submit Checklist

提交 PR 前**必须**全部通过：

```bash
[ ] python test_imports.py                # exit 0
[ ] python -m unittest discover -s tests  # Ran N tests, OK
[ ] 中英文语言包键集一致（test_imports.py 会断言）
[ ] 新增/修复都附带了测试
[ ] 用户可见文本都走 tr()，没有硬编码
[ ] 未提交 dist/ build/ __pycache__ .test_tmp 或任何二进制
```

CI 会跑同样的命令；本地不通过就别开 PR。

---

## 4. 代码规范 / Coding Standards

### 4.1 文件头（必须保留） / File Header (required)

每个新增的 `.py` / `.bat` / `.spec` / `.yml` 文件都要带标准头：

Every new `.py` / `.bat` / `.spec` / `.yml` file must carry the standard header:

```python
# SPDX-FileCopyrightText: <年份> <你的署名或 GitHub 账号>
# SPDX-License-Identifier: MIT
# AI-Generated: <none | partial | substantial> — 说明是否使用了 AI
```

`.bat` 用 `REM`，`.yml` / `.spec` 用 `#`。已有文件请**不要删除**头部。

Use `REM` in `.bat`, `#` in `.yml` / `.spec`. **Do not delete** the header from
existing files.

### 4.2 国际化（i18n） / Internationalization

- 所有用户可见字符串必须经 `tr()` 包装
- 新增文案必须**同时**加入 `src/translations/zh_CN.json` 与 `en_US.json`
- key 是**完整中文模板字符串**（含 `{placeholder}`），带占位符的译文必须保留同名占位符
- `test_imports.py` 会断言两侧键集完全一致

- All user-visible strings must be wrapped in `tr()`
- New text must be added to **both** `zh_CN.json` and `en_US.json`
- The key is the **complete Chinese template string** (including `{placeholder}`);
  translations must keep the same placeholders
- `test_imports.py` asserts that both key sets are identical

```python
# ✅ 正确
QMessageBox.information(self, tr('导入成功'),
                        tr('成功导入 {count} 个单位').format(count=n))

# ❌ 错误：硬编码、无 tr()
QMessageBox.information(self, '导入成功', '成功导入 %d 个单位' % n)
```

### 4.3 领域规则（容易被改坏） / Domain Rules (easy to break)

| 规则 | 说明 |
|------|------|
| **多父节点用空格分隔** | 内部是 `list`，`.set` 里是 `"parent1 parent2"`；**不要用逗号** |
| **导出保留原格式** | 注释、空行、缩进都要保留；只改数据行 |
| **`{positions}` 块不可改写** | 块内是 `{"unit" x y}`，不是完整定义 |
| **单位类型以 research 文件为准** | `units_*.set` 的 `unit_type` 恒为空 |
| **`requires` 恒为 list** | 不要写成 `""` 或 `None` |
| **导出必须原子写** | 临时文件 + `os.replace` + `.bak`，不要直接覆盖 |

- **Space-separated multi-parents**: internally a `list`, in `.set` it is
  `"parent1 parent2"` — never use commas
- **Preserve export formatting**: keep comments, blank lines and indentation;
  only rewrite data lines
- **`{positions}` blocks are read-only**: entries inside are `{"unit" x y}`, not
  full unit definitions
- **Unit type comes from the research file**: `unit_type` is always empty in `units_*.set`
- **`requires` is always a list**: never `""` or `None`
- **Atomic export**: temp file + `os.replace` + `.bak`; never overwrite directly

### 4.4 其他 / Misc

- 遵循 PEP 8；函数加类型提示与文档字符串
- 新增依赖需在 `requirements.txt` 说明理由（当前只允许 PyQt5）
- 不要把调试输出直接 `print`；用 `debug_print()` 并以 `if debug.DEBUG:` 短路
- 不要吞异常（`except: pass`），至少记录

- Follow PEP 8; add type hints and docstrings
- Justify any new dependency in `requirements.txt` (currently only PyQt5 is allowed)
- Do not `print` debug output directly; use `debug_print()` guarded by `if debug.DEBUG:`
- Do not swallow exceptions (`except: pass`); log at minimum

---

## 5. 提交信息规范 / Commit Messages

格式 / Format：

```
<类型>: <简短说明>
<type>: <short summary>

<可选正文：为什么改、影响范围>
<optional body: why, and what it affects>

<必填 trailer：AI 使用声明>
<required trailer: AI disclosure>
AI-Assisted: none | partial | substantial
AI-Tools: <工具名，如 none / Copilot / Claude / DeepSeek / 本地模型>
AI-Reviewed-by: <你的账号>
```

类型 / Types：`feat` / `fix` / `docs` / `test` / `refactor` / `perf` / `chore`。

示例 / Example：

```
fix: 修复撤销属性面板改 Costs 时抛 KeyError

压栈用 'property_name'、撤销读 'property'，键名不一致。
改为两种键名都兼容，并补回归测试。

AI-Assisted: substantial
AI-Tools: DeepSeek
AI-Reviewed-by: your-github-name
```

---

## 6. ⚠️ AI 使用披露要求 / AI Usage Disclosure — REQUIRED

> **硬性要求**：任何 PR 都必须声明是否使用了 AI 生成内容。未声明的 PR 会被要求
> 补充后才进入评审。

### 6.1 为什么要声明 / Why disclose

- 使用者需要知道代码的生成方式，才能评估可靠性与审查成本（见 [NOTICE](NOTICE)）
- AI 生成代码更容易出现边界条件缺陷，评审与测试投入需要相应调整
- 这也是本项目自身对外的披露方式——贡献者遵循同一标准

- Users need to know how code was produced to judge reliability and review cost
  (see [NOTICE](NOTICE))
- AI-generated code tends to have more edge-case defects, so review and testing
  effort must be adjusted accordingly
- This is also how this project discloses its own AI usage — contributors follow
  the same standard

### 6.2 三级声明 / Three disclosure levels

| 级别 | 含义 |
|------|------|
| `none` | 完全手写，未使用任何 AI 辅助 |
| `partial` | 部分片段（补全、查文档示例、生成测试骨架）由 AI 产出，人工改写并理解 |
| `substantial` | 主体逻辑由 AI 生成，人工审阅、修改、测试 |

| Level | Meaning |
|-------|---------|
| `none` | Fully hand-written, no AI assistance |
| `partial` | Some snippets (completions, doc examples, test skeletons) AI-produced, then human-edited and understood |
| `substantial` | Main logic AI-generated, human-reviewed, modified and tested |

**无法判断时选更高一级。** 隐瞒不构成合规。

**When in doubt, pick the higher level.** Non-disclosure is not compliance.

### 6.3 PR 描述模板（直接复制）

```markdown
## 变更内容
<!-- 一句话说明改了什么 -->

## 关联 Issue
<!-- Closes #123 -->

## AI 使用声明（必填，勾选一项）
- [ ] `none` —— 完全手写
- [ ] `partial` —— 部分片段由 AI 生成，已人工修改
- [ ] `substantial` —— 主体由 AI 生成，已人工审阅与测试

AI 工具：
人工审核方式：

## 测试
<!-- 新增/修改了哪些测试，如何验证 -->
- [ ] `python test_imports.py` 通过
- [ ] `python -m unittest discover -s tests` 通过
- [ ] 涉及 UI 的改动已人工冒烟

## 其他说明
<!-- 兼容性、迁移、已知限制 -->
```

### 6.4 评审会额外关注什么 / What reviewers look at

- 边界条件：空值、超大输入、畸形 `.set` / TGA / `.pak`
- 是否改写 `.set` 格式（空格分隔、`{positions}` 块）
- i18n 键是否两侧齐全
- 是否有**理解不了就提交**的代码块（AI 产物必须能被解释）

- Edge cases: empty values, oversized input, malformed `.set` / TGA / `.pak`
- Whether the `.set` format is altered (space separation, `{positions}` blocks)
- Whether i18n keys exist on both sides
- Whether there is code the author **cannot explain** (AI output must be explainable)

---

## 7. Pull Request 流程 / Pull Request Process

1. Fork 本仓库，从 `main` 开分支：`fix/undo-keyerror`、`feat/xxx`
2. 小步提交，每个提交只做一件事
3. 补齐测试与文档（README / INSTALL / 必要时 LONG_TERM_MEMORY）
4. 按第 6 节填写 AI 使用声明
5. 通过 CI 后请求评审；维护者可能要求补测试或拆分 PR
6. 合并方式：squash merge，保留清晰的最终提交信息

**不接受**：移除许可证/披露文件、提交第三方版权素材、引入网络功能或遥测、
静默改变导出格式（会破坏用户现有 mod 文件）。

---

## 8. 许可证与素材 / License and Assets

- 本项目采用 [MIT](LICENSE)。提交即表示你同意以 MIT 分发你的贡献。
- 提交的文件头保留 `SPDX-License-Identifier: MIT`。
- **不要提交**：游戏本体资源、第三方 mod 的 `.set` / `.pak` / 图片、抓取的用户数据。
- 测试数据请用**合成样例**：参考 `tests/__init__.py` 的 `write_sample_sets()`。
- 若确需引入外部素材，必须在 PR 中说明来源与授权，并在 [NOTICE](NOTICE) 登记。

---

## 有疑问？ / Questions

- 功能与用法：先读 [README](README.md)、[INSTALL](INSTALL.md)
- 安全问题：走 [SECURITY.md](SECURITY.md)，**不要**公开 Issue
- 其他：开 Issue 讨论，说明版本与复现步骤

感谢贡献 🙏 / Thanks for contributing

---

> 本文档由 AI 编码助手生成，经人工审核，按 [MIT](LICENSE) 分发。详见 [NOTICE](NOTICE)。
> This guide was produced with AI assistance and human review, distributed under
> [MIT](LICENSE). See [NOTICE](NOTICE).
