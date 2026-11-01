# 单元测试说明 / Unit Testing Guide

## 📁 测试文件结构 / Test File Structure

```
tests/
├── __init__.py                      # 包初始化 + 测试临时目录工具（make_test_dir / remove_test_dir）
├── test_multi_parent_nodes.py       # 多父节点功能测试（20 个测试）
├── test_undo_export.py              # 撤销/导出逻辑测试（20 个测试）
├── test_fixes_v221.py              # v2.2.1 修复项回归测试（61 个测试）
├── test_fixes_v222.py              # v2.2.2 修复项回归测试（34 个测试）
└── README_TESTS.md                  # 本说明
```

> **运行方式 / How to run**
> ```bash
> cd Research_Tree_Generator
> python -m unittest discover -s tests          # 全部 135 个测试
> python -m unittest discover -s tests -v       # 带用例名
> python -m unittest tests.test_fixes_v221      # 只跑 v2.2.1 回归测试
> python -m unittest tests.test_fixes_v222      # 只跑 v2.2.2 回归测试
> python test_imports.py                        # 模块导入 + 解析器 + i18n 键集自检
> run_tests.bat                                 # 一键跑全部 + 自检
> ```
>
> **临时目录 / Temp dirs**：测试在项目内 `.test_tmp/` 下创建临时目录（可用环境变量
> `RTG_TEST_TMP` 覆盖），不写系统 TEMP，因此可在受限/沙箱环境中运行。
> 清理失败不会计为测试失败。
>
> **无显示环境 / Headless**：`test_fixes_v221.py` / `test_fixes_v222.py` 会自行设置
> `QT_QPA_PLATFORM=offscreen`，可直接在无图形界面的环境（CI）运行。

---

## English Summary

> The detailed sections below are written in Chinese; this section gives English
> readers everything needed to run and understand the suite.

### Structure

| File | Tests | Purpose |
|------|-------|---------|
| `test_multi_parent_nodes.py` | 20 | Multi-parent parsing, export, round-trip |
| `test_undo_export.py` | 20 | Undo manager, export deduplication, tab consistency |
| `test_fixes_v221.py` | 61 | Regression tests for every v2.2.1 fix |
| `test_fixes_v222.py` | 34 | Regression tests for every v2.2.2 fix |
| `__init__.py` | — | Temp-dir helpers and synthetic sample fixtures |

**Total: 135 tests.**

### Running

```bash
cd Research_Tree_Generator
python -m unittest discover -s tests       # all 135 tests
python -m unittest discover -s tests -v    # with test names
python test_imports.py                     # imports + parser + i18n key parity
run_tests.bat                              # everything, one click
```

### Design notes

- **Temp directories**: created under the project's `.test_tmp/` (override with
  `RTG_TEST_TMP`), never the system TEMP, so the suite runs in restricted/sandboxed
  environments. Cleanup failures are ignored and never fail a test.
- **Headless**: the regression suites set `QT_QPA_PLATFORM=offscreen` themselves and
  run fine in CI with no display.
- **No third-party fixtures**: real `.set` samples were removed for licensing reasons;
  `write_sample_sets()` generates minimal synthetic files at runtime.
- **Test data lives in code**, so the suite has no external file dependencies.

---

## test_fixes_v221.py 覆盖内容 / What the regression suite covers

该文件是针对 v2.2.1 审计修复的回归保护，每个测试类对应一个已修复缺陷：

| 测试类 | 保护的修复点 |
|--------|-------------|
| `TestUndoPropertyKeyCompat` | 撤销 `MODIFY_PROPERTY` 键名兼容（原 `property`/`property_name` 不对称 → KeyError） |
| `TestOverlapDebounce` | `_schedule_overlap_check` 防抖（原 `QTimer.singleShot` 恒返回 None → O(N³)） |
| `TestFlaskIconUpdate` | `update_from_unit` 烧瓶图标（原 old/new 比较恒假） |
| `TestDragPositionSync` | 拖动释放后画布与 `unit.position_*` 一致（原按下即对齐造成静默偏移） |
| `TestGridOriginAlignment` | `draw_grid` 与 `sceneRect` 原点对齐（原恒从绝对 (0,0) 起画） |
| `TestOverlapDetection` | 重叠检测语义与增量重绘 |
| `TestMainWindowPersistence` | 保存返回状态、脏位复位、`closeEvent` 校验保存结果、清空时清撤销栈 |
| `TestAllUnitsAliasing` | `all_units` 不得与 `units` 别名（防列表重复行） |
| `TestFactionExtraction` | `units_sov_era1960.set` → faction `sov`（原把时期当阵营） |
| `TestI18n` | 中英键集对齐、语言菜单不反向、占位符一致、源码 key 全覆盖 |
| `TestDebugShortCircuit` | DEBUG=False 时不得组装 f-string / 无条件 flush（AST 结构级检测） |
| `TestExportRoundTrip` | 多父节点往返、真实文件行数不变、注释保留 |

---

## test_fixes_v222.py 覆盖内容 / What the v2.2.2 regression suite covers

该文件是针对 v2.2.2 本轮修改的回归保护：

| 测试类 | 保护的修复点 |
|--------|-------------|
| `TestRedoAddUnit` | ADD_UNIT 压栈快照 `unit_data`；撤销添加后重做栈不被清空；添加→撤销→重做往返 |
| `TestRedoDeleteUnit` | 删除（含子节点 requires 清理）→ 撤销（恢复子引用）→ 重做（再次清理）且不污染撤销栈 |
| `TestRedoMoveAndProperty` | MOVE / CHANGE_REQUIRES / MODIFY_PROPERTY（`property` 与 `property_name` 双键名）重做 |
| `TestRedoWiring` | Ctrl+Y 快捷键、重做菜单项、`perform_redo` 为活代码且覆盖五类动作、`record_undo=False` 恰好 2 处 |
| `TestExporterSafeWrite` | 覆盖保存生成 `.bak`、首次保存无 `.bak`、`os.replace` 失败时原文件完好且无临时残留 |
| `TestPositionsBlockPreserved` | `{positions}` 块内的单位行不被改写为完整定义行，块内不注入 requires/costs |
| `TestLanguageSwitchGuard` | 无未保存更改直接重启；有更改时 Save/Discard/Cancel 分支；保存取消不重启；同语言 no-op |
| `TestDeadCodeRemoval` | 重复 `update_position`、`is_being_dragged`、`unit_dropped`、`units_file`、`export_positions_only` 等死代码不得回潮 |

---

## 🧪 测试内容 / Test Coverage

### test_multi_parent_nodes.py

包含 **20 个单元测试**，覆盖多父节点功能的各个方面：

#### 1. TestMultiParentNodeParsing (7 个测试)
测试解析器读取多父节点的功能

- `test_parse_single_parent` - 单个父节点解析
- `test_parse_two_parents` - 两个父节点解析
- `test_parse_three_parents` - 三个父节点解析
- `test_parse_no_parent` - 无父节点解析
- `test_parse_mixed_units` - 混合单位类型解析
- `test_parse_with_extra_spaces` - 多余空格处理
- `test_parse_real_file` - 真实文件解析

#### 2. TestMultiParentNodeExporting (6 个测试)
测试导出器保存多父节点的功能

- `test_export_single_parent` - 单个父节点导出
- `test_export_two_parents` - 两个父节点导出
- `test_export_three_parents` - 三个父节点导出
- `test_export_no_parent` - 无父节点导出
- `test_export_preserve_style_two_parents` - 保留格式导出
- `test_export_full_file_round_trip` - 完整文件往返测试

#### 3. TestPropertyPanelMultiParent (4 个测试)
测试属性面板的字符串/列表转换

- `test_requires_string_to_list` - 字符串转列表
- `test_requires_list_to_string` - 列表转字符串
- `test_empty_requires` - 空值处理
- `test_requires_with_extra_spaces` - 多余空格处理

#### 4. TestUnitClassMultiParent (3 个测试)
测试 Unit 类的多父节点支持

- `test_unit_from_dict_with_list_requires` - 从字典创建
- `test_unit_to_dict_with_list_requires` - 转换为字典
- `test_unit_default_requires` - 默认值测试

---

## 🚀 运行测试 / Running Tests

### 方法 1: 使用批处理脚本（推荐）

```bash
cd 你放置项目的路径\Research_Tree_Generator
run_tests.bat
```

### 方法 2: 使用 unittest 命令行

```bash
cd 你放置项目的路径\Research_Tree_Generator
python -m unittest tests.test_multi_parent_nodes -v
```

参数说明：
- `-v`: 详细输出模式，显示每个测试的名称和结果

### 方法 3: 运行特定测试类

```bash
# 只运行解析器测试
python -m unittest tests.test_multi_parent_nodes.TestMultiParentNodeParsing -v

# 只运行导出器测试
python -m unittest tests.test_multi_parent_nodes.TestMultiParentNodeExporting -v
```

### 方法 4: 运行单个测试

```bash
# 运行特定的测试方法
python -m unittest tests.test_multi_parent_nodes.TestMultiParentNodeParsing.test_parse_two_parents -v
```

### 方法 5: 使用 pytest（需安装）

```bash
pip install pytest
cd 你放置项目的路径\Research_Tree_Generator
python -m pytest tests/test_multi_parent_nodes.py -v
```

---

## 📊 查看测试结果 / Viewing Results

### 成功输出示例

```
test_parse_two_parents (tests.test_multi_parent_nodes.TestMultiParentNodeParsing.test_parse_two_parents)
测试两个父节点解析 / Test two parent nodes parsing ... ok
test_export_full_file_round_trip (tests.test_multi_parent_nodes.TestMultiParentNodeExporting.test_export_full_file_round_trip)
测试完整文件往返（导入→导出）/ Test full file round-trip ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.018s

OK
```

### 失败输出示例

```
test_example (tests.test_multi_parent_nodes.TestExample.test_example)
测试示例 ... FAIL

======================================================================
FAIL: test_example (tests.test_multi_parent_nodes.TestExample.test_example)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "...", line XX, in test_example
    self.assertEqual(result, expected)
AssertionError: 'actual' != 'expected'

----------------------------------------------------------------------
Ran 20 tests in 0.020s

FAILED (failures=1)
```

---

## 🔍 测试文件说明 / Test Files Description

### test_multi_parent_nodes.py

**主要功能**:
- 测试多父节点的解析、导出、转换等核心功能
- 验证边界情况（空值、单值、多值、多余空格）
- 使用真实文件进行集成测试

**依赖模块**:
- `parser.SetFileParser` - 解析器
- `parser.Unit` - 单位数据类
- `exporter.SetFileExporter` - 导出器

**测试数据**:
- 使用临时目录创建测试文件
- 真实文件类用例改用 `tests/__init__.py` 里 `write_sample_sets()` 生成的**合成样例**
  （仓库不存放任何第三方 mod 的 `.set` 文件）
- 自动清理测试产生的临时文件

---

## 📝 添加新测试 / Adding New Tests

### 测试模板

```python
class TestNewFeature(unittest.TestCase):
    """测试新功能 / Test new feature"""
    
    def setUp(self):
        """设置测试环境 / Set up test environment"""
        # 初始化代码
    
    def tearDown(self):
        """清理测试环境 / Clean up test environment"""
        # 清理代码
    
    def test_example(self):
        """测试示例 / Test example"""
        # 测试代码
        self.assertEqual(result, expected)
```

### 常用断言方法

- `self.assertEqual(a, b)` - 验证 a 等于 b
- `self.assertIsInstance(obj, type)` - 验证对象类型
- `self.assertIn(item, list)` - 验证元素在列表中
- `self.assertTrue(condition)` - 验证条件为真
- `self.assertFalse(condition)` - 验证条件为假

---

## 🎯 最佳实践 / Best Practices

### 1. 测试命名规范
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头
- 使用描述性名称说明测试内容

### 2. 测试独立性
- 每个测试应该独立运行
- 使用 `setUp()` 和 `tearDown()` 管理测试环境
- 避免测试之间的依赖关系

### 3. 测试覆盖率
- 覆盖正常情况
- 覆盖边界情况（空值、最大值、最小值）
- 覆盖异常情况

### 4. 双语注释
- 所有测试都使用中英文双语注释
- 便于国际化团队协作

---

## 🐛 故障排除 / Troubleshooting

### 问题 1: ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'parser'`

**解决**: 确保在项目根目录运行测试，或检查 `sys.path` 设置

### 问题 2: 测试文件找不到

**错误**: `Failed to import test module`

**解决**: 确保 `tests/__init__.py` 文件存在

### 问题 3: 真实文件测试失败

**错误**: `test_parse_real_file` 失败

**解决**: 该类用例已改为使用合成样例。若失败，先确认能正常导入
`tests.write_sample_sets`，再检查 `parser.parse_research_file` 是否改动过格式正则。

---

## 📈 持续改进 / Continuous Improvement

### 未来测试计划

- [ ] 添加 UI 交互测试
- [ ] 添加性能测试
- [ ] 添加更多边界情况测试
- [ ] 集成 CI/CD 自动化测试
- [ ] 增加代码覆盖率到 90%+

---

**最后更新**: 2026-09-19  
**维护者**: Research Tree Generator Team

---

> **AI 生成声明**：本测试套件与说明文档主要由 AI 编码助手生成，经人工审核。
> 测试通过不代表代码无缺陷。详见 [../NOTICE](../NOTICE)。
>
> **AI disclosure**: this test suite and guide are primarily generated by AI coding
> assistants under human review. Passing tests do not imply absence of defects.
> See [../NOTICE](../NOTICE).
