# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
v2.2.2 修复项回归测试 / Regression tests for the v2.2.2 fixes

覆盖本轮修改，防止回归：
  1. 重做功能恢复（Ctrl+Y + 菜单项），五类动作均可 undo → redo 往返
  2. 撤销 ADD_UNIT 不再压入 DELETE_UNIT（否则 push_action 清空重做栈）
  3. exporter 原子写入 + .bak 备份（写失败时原文件不被破坏）
  4. {positions} 块在保留格式导出中不被破坏
  5. 语言切换前的未保存数据保护（Save/Discard/Cancel）+ frozen execl 修复
  6. 死代码清理回归（重复 update_position、is_being_dragged、unit_dropped 等）

运行 / Run:
    cd Research_Tree_Generator
    python -m unittest tests.test_fixes_v222 -v
"""

import io
import os
import sys
import unittest
from unittest import mock

# 必须在导入 PyQt5 之前设置，保证无显示环境可运行
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMessageBox

from src import main_window as mw_module
from src.exporter import SetFileExporter
from src.main_window import MainWindow
from src.parser import Unit
from src.undo_manager import UndoAction, UndoActionType
from tests import make_test_dir, remove_test_dir

_app = QApplication.instance() or QApplication([])

_REAL_MSGBOX = QMessageBox


class StubMessageBox:
    """拦截所有模态弹窗，避免测试阻塞（与 test_fixes_v221 同模式）。"""

    def __init__(self):
        self.calls = []
        self.question_reply = _REAL_MSGBOX.Ok

    def install(self, question_reply=None):
        self._saved = (mw_module.QMessageBox,)
        self.question_reply = _REAL_MSGBOX.Yes if question_reply is None else question_reply
        mw_module.QMessageBox = self
        return self

    def uninstall(self):
        (mw_module.QMessageBox,) = self._saved

    def _record(self, kind, default):
        def fn(parent=None, title="", text="", *a, **kw):
            self.calls.append((kind, title, text))
            return default
        return fn

    @property
    def information(self):
        return self._record("information", _REAL_MSGBOX.Ok)

    @property
    def warning(self):
        return self._record("warning", _REAL_MSGBOX.Ok)

    @property
    def critical(self):
        return self._record("critical", _REAL_MSGBOX.Ok)

    @property
    def question(self):
        return self._record("question", self.question_reply)

    def find(self, kind):
        return [c for c in self.calls if c[0] == kind]

    Ok = _REAL_MSGBOX.Ok
    Yes = _REAL_MSGBOX.Yes
    No = _REAL_MSGBOX.No
    Save = _REAL_MSGBOX.Save
    Discard = _REAL_MSGBOX.Discard
    Cancel = _REAL_MSGBOX.Cancel


def _src(filename):
    return io.open(os.path.join(project_root, "src", filename), encoding="utf-8").read()


# ══════════════════════════════════════════════════════════════════════
# 1. 重做功能（MainWindow 级往返）
# ══════════════════════════════════════════════════════════════════════
class RedoTestCase(unittest.TestCase):
    """MainWindow + 拦截弹窗的共享基类。"""

    def setUp(self):
        self.stub = StubMessageBox().install()
        self.win = MainWindow()
        self.tmp = make_test_dir()

    def tearDown(self):
        self.stub.uninstall()
        remove_test_dir(self.tmp)
        self.win.close = lambda *a, **k: None
        self.win.deleteLater()


class TestRedoAddUnit(RedoTestCase):

    def test_add_action_records_unit_data(self):
        """ADD_UNIT 压栈必须快照 unit_data（redo 恢复的数据来源）。"""
        unit = Unit(name="a", costs=3, position_x=1.0, position_y=2.0)
        self.win.add_unit_to_canvas_at_position(unit)
        action = self.win.undo_manager.undo_stack[-1]
        self.assertEqual(action.data['unit_name'], 'a')
        self.assertIn('unit_data', action.data, "ADD_UNIT 未快照 unit_data，redo 无法恢复")
        self.assertEqual(action.data['unit_data']['costs'], 3)

    def test_undo_add_keeps_redo_available(self):
        """核心回归：撤销添加时内部删除不得再压 DELETE_UNIT ——
        否则 push_action 会清空重做栈，Ctrl+Y 立即失效。"""
        self.win.add_unit_to_canvas_at_position(Unit(name="a", costs=1))
        self.assertEqual(self.win.undo_manager.get_stack_size(), 1)

        self.win.perform_undo()
        self.assertNotIn("a", self.win.tech_tree_canvas.nodes)
        self.assertEqual(self.win.undo_manager.get_stack_size(), 0,
                         "撤销添加又压入了新动作（会清空重做栈）")
        self.assertTrue(self.win.undo_manager.can_redo(),
                        "撤销添加后重做栈被清空，redo 链断裂")

    def test_redo_add_roundtrip(self):
        """添加 → 撤销 → 重做，节点与数据完整恢复。"""
        unit = Unit(name="a", costs=3, position_x=1.0, position_y=2.0)
        self.win.add_unit_to_canvas_at_position(unit)
        self.assertIn("a", self.win.tech_tree_canvas.nodes)

        self.win.perform_undo()
        self.assertNotIn("a", self.win.tech_tree_canvas.nodes)

        self.win.perform_redo()
        nodes = self.win.tech_tree_canvas.nodes
        self.assertIn("a", nodes, "redo 后节点未恢复")
        self.assertTrue(nodes["a"].unit.deployed)
        self.assertEqual(nodes["a"].unit.costs, 3)
        self.assertAlmostEqual(nodes["a"].unit.position_x, 1.0)
        self.assertAlmostEqual(nodes["a"].pos().x(), 1.0 / 0.1 * 40, places=4)
        # redo 后可以继续 undo（动作回到撤销栈）
        self.assertTrue(self.win.undo_manager.can_undo())
        self.assertFalse(self.win.undo_manager.can_redo())


class TestRedoDeleteUnit(RedoTestCase):

    def test_delete_undo_redo_roundtrip_with_children(self):
        """删除带子引用的节点 → 撤销（恢复子 requires）→ 重做（再次移除）。"""
        canvas = self.win.tech_tree_canvas
        canvas.add_unit_node(Unit(name="parent", costs=1))
        canvas.add_unit_node(Unit(name="child", costs=1, requires=["parent"]))

        # 用户删除 parent（真实路径：记录 DELETE_UNIT）
        canvas.on_item_deleted(canvas.nodes["parent"])
        self.assertNotIn("parent", canvas.nodes)
        self.assertEqual(canvas.nodes["child"].unit.requires, [],
                         "删除父节点后子节点 requires 未清理")

        # 撤销删除：parent 恢复，子引用恢复
        self.win.perform_undo()
        self.assertIn("parent", canvas.nodes)
        self.assertEqual(canvas.nodes["child"].unit.requires, ["parent"],
                         "撤销删除后子节点 requires 未恢复")

        # 重做删除：parent 再次删除，子引用再次清理，且不得污染撤销栈
        self.win.perform_redo()
        self.assertNotIn("parent", canvas.nodes, "redo 后父节点未删除")
        self.assertEqual(canvas.nodes["child"].unit.requires, [],
                         "redo 删除后子节点 requires 未再次清理")
        # redo() 会把动作放回撤销栈，故此时栈大小应为 1；
        # 若内部删除又压了一次 DELETE_UNIT，则会变成 2
        self.assertEqual(self.win.undo_manager.get_stack_size(), 1,
                         "redo 后栈内应只有被重做的动作本身（若为 2 则内部删除污染了撤销栈）")
        self.assertTrue(self.win.undo_manager.can_undo())


class TestRedoMoveAndProperty(RedoTestCase):

    def test_redo_move_unit(self):
        canvas = self.win.tech_tree_canvas
        canvas.add_unit_node(Unit(name="m", costs=1, position_x=0.0, position_y=0.0))
        self.win.undo_manager.push_action(UndoAction(UndoActionType.MOVE_UNIT, {
            'unit_name': 'm',
            'old_position_x': 0.0, 'old_position_y': 0.0,
            'new_position_x': 2.5, 'new_position_y': 1.5,
        }))

        self.win.perform_undo()
        self.assertAlmostEqual(canvas.nodes["m"].unit.position_x, 0.0)

        self.win.perform_redo()
        node = canvas.nodes["m"]
        self.assertAlmostEqual(node.unit.position_x, 2.5)
        self.assertAlmostEqual(node.unit.position_y, 1.5)
        # 视觉位置必须与数据同源（2.5 量纲 = 1000px）
        self.assertAlmostEqual(node.pos().x(), 2.5 / 0.1 * 40, places=4)
        self.assertAlmostEqual(node.pos().y(), 1.5 / 0.1 * 20, places=4)

    def test_redo_change_requires(self):
        canvas = self.win.tech_tree_canvas
        canvas.add_unit_node(Unit(name="c", costs=1))
        self.win.undo_manager.push_action(UndoAction(UndoActionType.CHANGE_REQUIRES, {
            'unit_name': 'c',
            'old_requires': [],
            'new_requires': ['p1', 'p2'],
        }))

        self.win.perform_undo()
        self.assertEqual(canvas.nodes["c"].unit.requires, [])

        self.win.perform_redo()
        self.assertEqual(canvas.nodes["c"].unit.requires, ['p1', 'p2'],
                         "redo 后 requires 未恢复为新值")
        self.assertIn('p1, p2', canvas.nodes["c"].requires_value_text.toPlainText())

    def test_redo_modify_property_canvas_key(self):
        """画布入口写入 'property' 键，redo 必须兼容。"""
        canvas = self.win.tech_tree_canvas
        canvas.add_unit_node(Unit(name="u", costs=4))
        self.win.undo_manager.push_action(UndoAction(UndoActionType.MODIFY_PROPERTY, {
            'unit_name': 'u', 'property': 'costs',
            'old_value': 4, 'new_value': 9,
        }))
        self.win.perform_undo()
        self.assertEqual(canvas.nodes["u"].unit.costs, 4)
        self.win.perform_redo()
        self.assertEqual(canvas.nodes["u"].unit.costs, 9)
        self.assertIn('9', canvas.nodes["u"].cost_text.toPlainText())

    def test_redo_modify_property_panel_key(self):
        """属性面板入口写入 'property_name' 键，redo 必须兼容（与 undo 的双键名对称）。"""
        canvas = self.win.tech_tree_canvas
        canvas.add_unit_node(Unit(name="u", costs=4))
        self.win.undo_manager.push_action(UndoAction(UndoActionType.MODIFY_PROPERTY, {
            'unit_name': 'u', 'property_name': 'costs',
            'old_value': 4, 'new_value': 7,
        }))
        self.win.perform_undo()
        self.win.perform_redo()
        self.assertEqual(canvas.nodes["u"].unit.costs, 7,
                         "redo 未兼容 'property_name' 键名")


class TestRedoWiring(unittest.TestCase):
    """源码级确认：快捷键 / 菜单 / 函数本体已恢复。"""

    def test_ctrl_y_shortcut_registered(self):
        src = _src("main_window.py")
        self.assertIn("QShortcut(QKeySequence('Ctrl+Y'), self)", src,
                      "Ctrl+Y 快捷键未注册")

    def test_redo_menu_action_present(self):
        src = _src("main_window.py")
        self.assertIn("tr('重做(&R)')", src, "重做菜单项缺失")
        self.assertIn("redo_action.triggered.connect(self.perform_redo)", src)

    def test_perform_redo_is_live_code(self):
        src = _src("main_window.py")
        line = "    def perform_redo(self):"
        self.assertIn(line, src, "perform_redo 不是活代码（仍被注释）")
        idx = src.index(line)
        # 函数体必须处理全部五种动作类型（函数较长，窗口取足）
        body = src[idx:idx + 12000]
        for t in ("UndoActionType.ADD_UNIT", "UndoActionType.DELETE_UNIT",
                  "UndoActionType.MOVE_UNIT", "UndoActionType.CHANGE_REQUIRES",
                  "UndoActionType.MODIFY_PROPERTY"):
            self.assertIn(t, body, f"perform_redo 缺少 {t} 分支")

    def test_record_undo_false_used_in_undo_and_redo(self):
        """undo(ADD) 与 redo(DELETE) 都必须用 record_undo=False 调用内部删除。"""
        src = _src("main_window.py")
        self.assertEqual(src.count("on_item_deleted(node, record_undo=False)"), 2,
                         "record_undo=False 应恰好出现 2 处（undo ADD 与 redo DELETE）")


# ══════════════════════════════════════════════════════════════════════
# 2. exporter 原子写入 + 备份
# ══════════════════════════════════════════════════════════════════════
class TestExporterSafeWrite(unittest.TestCase):

    def setUp(self):
        self.exporter = SetFileExporter()
        self.tmp = make_test_dir()

    def tearDown(self):
        remove_test_dir(self.tmp)

    def _unit(self, costs=1):
        return Unit(name="a", unit_type="tech", costs=costs,
                    requires=[], position_x=0.0, position_y=0.0)

    def test_overwrite_creates_bak_with_old_content(self):
        target = os.path.join(self.tmp, "unit_research_bak.set")
        self.exporter._export_simple([self._unit(costs=1)], "t", target)
        first = io.open(target, encoding="utf-8").read()

        self.exporter._export_simple([self._unit(costs=9)], "t", target)
        second = io.open(target, encoding="utf-8").read()

        self.assertIn("costs 9", second)
        self.assertTrue(os.path.exists(target + ".bak"), "覆盖保存未生成 .bak 备份")
        self.assertEqual(io.open(target + ".bak", encoding="utf-8").read(), first,
                         ".bak 备份内容不是旧版本")
        self.assertFalse(os.path.exists(target + ".rtg_tmp"), "临时文件残留")

    def test_new_file_has_no_bak(self):
        target = os.path.join(self.tmp, "unit_research_new.set")
        self.exporter._export_simple([self._unit()], "t", target)
        self.assertTrue(os.path.exists(target))
        self.assertFalse(os.path.exists(target + ".bak"),
                         "首次保存不应生成 .bak（没有旧文件可备份）")

    def test_write_failure_keeps_original_intact(self):
        """os.replace 失败（如磁盘错误）时原文件必须保持完好，临时文件清理。"""
        target = os.path.join(self.tmp, "unit_research_keep.set")
        self.exporter._export_simple([self._unit(costs=1)], "t", target)
        original = io.open(target, encoding="utf-8").read()

        with mock.patch("os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.exporter._export_simple([self._unit(costs=9)], "t", target)

        self.assertEqual(io.open(target, encoding="utf-8").read(), original,
                         "写出失败后原文件被破坏（非原子写入）")
        self.assertFalse(os.path.exists(target + ".rtg_tmp"),
                         "写出失败后临时文件未清理")


# ══════════════════════════════════════════════════════════════════════
# 3. {positions} 块保护
# ══════════════════════════════════════════════════════════════════════
class TestPositionsBlockPreserved(unittest.TestCase):

    def setUp(self):
        self.exporter = SetFileExporter()
        self.tmp = make_test_dir()

    def tearDown(self):
        remove_test_dir(self.tmp)

    def _original(self):
        return (
            "{IconGap 28}\n"
            "\n"
            ";// UNITS\n"
            '\t{"a"\t\trequires ""\t\t\t\tcosts 1  position 0 0}\n'
            '\t{"b"\t\trequires "a"\t\t\t\tcosts 2  position 1 0}\n'
            "\n"
            "{positions\n"
            '\t\t{"a" 0 0}\n'
            '\t\t{"b" 1 0}\n'
            '\t\t{"c" 2 0}\n'
            "\t}\n"
        )

    def test_positions_block_lines_untouched(self):
        """positions 块内形如 {"a" x y} 的行不得被改写为 requires/costs 行。"""
        in_file = os.path.join(self.tmp, "unit_research_pos.set")
        out_file = os.path.join(self.tmp, "unit_research_pos_out.set")
        io.open(in_file, "w", encoding="utf-8", newline="").write(self._original())

        units = [
            Unit(name="a", costs=5, requires=[], position_x=0.0, position_y=0.0),
            Unit(name="b", costs=2, requires=["a"], position_x=1.0, position_y=0.0),
            Unit(name="c", costs=1, requires=[], position_x=2.0, position_y=0.0),
        ]
        self.exporter.export(units, "t", out_file, in_file)
        out = io.open(out_file, encoding="utf-8").read()

        # 主块正常更新
        self.assertIn("costs 5", out, "主块单位行未被更新")
        # positions 块三行原样保留
        for line in ('\t\t{"a" 0 0}', '\t\t{"b" 1 0}', '\t\t{"c" 2 0}'):
            self.assertIn(line, out, f"positions 行被改写: {line}")
        # positions 块内不得被注入 requires/costs
        pos_section = out[out.index("{positions"):]
        pos_block = pos_section[:pos_section.index("\t}")]
        self.assertNotIn("requires", pos_block, "positions 块被注入了 requires")
        self.assertNotIn("costs", pos_block, "positions 块被注入了 costs")
        # c 是新单位，应追加到新增单位区（既有行为）
        self.assertIn(";// 新增单位", out)

    def test_positions_only_unit_not_rewritten(self):
        """仅存在于 positions 块且在画布上的单位，其 positions 行必须原样保留。"""
        in_file = os.path.join(self.tmp, "unit_research_pos2.set")
        out_file = os.path.join(self.tmp, "unit_research_pos2_out.set")
        io.open(in_file, "w", encoding="utf-8", newline="").write(self._original())

        # 画布上只有 c（主块中没有它的行）
        units = [Unit(name="c", costs=1, requires=[], position_x=2.0, position_y=0.0)]
        self.exporter.export(units, "t", out_file, in_file)
        out = io.open(out_file, encoding="utf-8").read()

        self.assertIn('\t\t{"c" 2 0}', out,
                      "仅在 positions 块中的单位行被改写（破坏块语法）")
        pos_section = out[out.index("{positions"):]
        pos_block = pos_section[:pos_section.index("\t}")]
        self.assertNotIn("requires", pos_block)


# ══════════════════════════════════════════════════════════════════════
# 4. 语言切换的未保存数据保护
# ══════════════════════════════════════════════════════════════════════
class TestLanguageSwitchGuard(RedoTestCase):
    """os.execl 直接替换进程、不经过 closeEvent —— 必须先处理未保存更改。"""

    def _switch(self, code='en_US'):
        """在 mock 保护下执行切换：不真正重启、不写 language_config.json。"""
        with mock.patch("os.execl") as execl, \
                mock.patch.object(mw_module.i18n, "set_language") as set_lang:
            self.win.switch_language(code)
        return execl, set_lang

    def test_same_language_is_noop(self):
        execl, set_lang = self._switch(mw_module.i18n.get_current_language())
        execl.assert_not_called()
        set_lang.assert_not_called()
        self.assertEqual(self.stub.find("question"), [])

    def test_unsaved_cancel_aborts_switch(self):
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _REAL_MSGBOX.Cancel
        execl, set_lang = self._switch()
        set_lang.assert_not_called()
        execl.assert_not_called()

    def test_unsaved_save_cancelled_aborts_switch(self):
        """选择"保存"但保存对话框取消 → 不得重启（数据还在画布上）。"""
        self.win.tech_tree_canvas.add_unit_node(Unit(name="a", costs=1))
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _REAL_MSGBOX.Save

        saved_fd = mw_module.QFileDialog

        class _FD:
            @staticmethod
            def getSaveFileName(*a, **k):
                return ("", "")  # 用户取消保存对话框

        mw_module.QFileDialog = _FD
        try:
            execl, set_lang = self._switch()
        finally:
            mw_module.QFileDialog = saved_fd
        set_lang.assert_not_called()
        execl.assert_not_called()

    def test_unsaved_discard_restarts(self):
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _REAL_MSGBOX.Discard
        execl, set_lang = self._switch()
        set_lang.assert_called_once_with("en_US")
        execl.assert_called_once()

    def test_clean_state_restarts_without_prompt(self):
        self.win.has_unsaved_changes = False
        execl, set_lang = self._switch()
        self.assertEqual(self.stub.find("question"), [],
                         "无未保存更改时不应弹询问框")
        set_lang.assert_called_once_with("en_US")
        execl.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# 5. 死代码清理回归（源码级）
# ══════════════════════════════════════════════════════════════════════
class TestDeadCodeRemoval(unittest.TestCase):

    def test_single_update_position_definition(self):
        src = _src("tech_tree_canvas.py")
        self.assertEqual(src.count("def update_position"), 1,
                         "update_position 必须只定义一次（原重复定义后者覆盖前者）")

    def test_is_being_dragged_removed(self):
        src = _src("tech_tree_canvas.py")
        self.assertNotIn("is_being_dragged", src,
                         "is_being_dragged（写 6 读 0 的死代码）仍存在")

    def test_unit_dropped_dead_signal_removed(self):
        panel = _src("unit_list_panel.py")
        window = _src("main_window.py")
        self.assertNotIn("unit_dropped = pyqtSignal", panel,
                         "死信号 unit_dropped 仍在声明")
        self.assertNotIn("unit_dropped.connect", window,
                         "死信号 unit_dropped 仍有连接")

    def test_dead_handler_add_unit_to_canvas_removed(self):
        self.assertNotIn("def add_unit_to_canvas(self", _src("main_window.py"),
                         "只被死信号引用的 add_unit_to_canvas 处理器仍在")

    def test_units_file_removed(self):
        self.assertNotIn("self.units_file", _src("main_window.py"),
                         "只写不读的 self.units_file 仍存在")

    def test_export_positions_only_removed(self):
        self.assertNotIn("def export_positions_only", _src("exporter.py"),
                         "无 UI 入口的 export_positions_only 仍存在")

    def test_edit_property_menu_item_removed(self):
        self.assertNotIn("✏️ 编辑属性", _src("tech_tree_canvas.py"),
                         "无处理分支的『编辑属性』菜单项仍存在")

    def test_on_undo_shortcut_removed(self):
        self.assertNotIn("def on_undo_shortcut", _src("tech_tree_canvas.py"))

    def test_canvas_load_units_removed(self):
        self.assertNotIn("def load_units", _src("tech_tree_canvas.py"),
                         "画布的死方法 load_units 仍存在（面板的同名方法是活代码）")

    def test_rebuild_ui_removed(self):
        self.assertNotIn("def rebuild_ui", _src("property_panel.py"))
        self.assertNotIn("def rebuild_ui", _src("unit_list_panel.py"))

    def test_i18n_dead_members_removed(self):
        src = _src("i18n.py")
        self.assertNotIn("language_changed", src)
        self.assertNotIn("def reload_translations", src)

    def test_on_item_deleted_has_record_undo_param(self):
        src = _src("tech_tree_canvas.py")
        self.assertIn("def on_item_deleted(self, item, record_undo=True)", src,
                      "on_item_deleted 缺少 record_undo 参数（redo 依赖它避免污染撤销栈）")


if __name__ == "__main__":
    unittest.main(verbosity=2)
