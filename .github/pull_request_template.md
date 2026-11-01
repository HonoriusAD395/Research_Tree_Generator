## 变更内容 / What changed

<!-- 一句话说明改了什么 / One-line summary -->

## 关联 Issue / Related issue

<!-- Closes #123 -->

## ⚠️ AI 使用声明（必填，勾选一项） / AI Usage Disclosure (required)

> 规则见 [CONTRIBUTING.md](../CONTRIBUTING.md#6-️-ai-使用披露要求--ai-usage-disclosure--required)。
> 未填写本节的 PR 会被要求补充后才进入评审。

- [ ] `none` —— 完全手写 / fully hand-written
- [ ] `partial` —— 部分片段由 AI 生成，已人工修改 / some AI-generated parts, human-edited
- [ ] `substantial` —— 主体由 AI 生成，已人工审阅与测试 / mainly AI-generated, human-reviewed

**AI 工具 / AI tools**：

**人工审核方式 / How reviewed**：

## 测试 / Testing

- [ ] `python test_imports.py` 通过 / passes
- [ ] `python -m unittest discover -s tests` 通过 / passes
- [ ] 涉及 UI 的改动已人工冒烟 / UI changes smoke-tested manually
- [ ] 新增或修复都附带了测试 / tests added or updated

## 检查项 / Checklist

- [ ] 新文件带 `SPDX-License-Identifier` 与 `AI-Generated` 头部
- [ ] 用户可见文案走 `tr()`，中英语言包键集一致
- [ ] 未改变 `.set` 导出格式（空格分隔多父节点、保留注释、`{positions}` 块不动）
- [ ] 未提交 `dist/` `build/` `__pycache__` `.test_tmp` 或任何二进制/第三方素材
- [ ] 如有破坏性变更，已在描述中说明

## 其他说明 / Notes

<!-- 兼容性、迁移、已知限制 / compatibility, migration, known limitations -->
