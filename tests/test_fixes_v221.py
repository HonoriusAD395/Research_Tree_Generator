# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
v2.2.1 修复项回归测试 / Regression tests for the v2.2.1 fixes

覆盖本次审计修复的每一个缺陷，防止回归：
  1. 撤销 MODIFY_PROPERTY 键名不对称（属性面板改 Costs 必须可撤销）
  2. _schedule_overlap_check 防抖失效（QTimer.singleShot 恒返回 None）
  3. update_from_unit 烧瓶图标恒假分支
  4. all_units 别名导致列表重复
  5. 清空数据/新建科技树必须清空撤销栈
  6. 按下即对齐导致的数据/视觉分叉
  7. draw_grid 与 sceneRect 原点对齐
  8. save_tech_tree 返回状态 + closeEvent 校验 + 脏位复位
  9. _extract_faction 不把时期当阵营
 10. i18n 键集对齐 + 语言菜单不反向
 11. 调试日志在 DEBUG=False 时必须短路（不得无条件组装 f-string）

运行 / Run:
    cd Research_Tree_Generator
    python -m unittest tests.test_fixes_v221 -v
"""

import io
import json
import os
import sys
import unittest

# 必须在导入 PyQt5 之前设置，保证无显示环境可运行
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtCore import QEvent, QPointF, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QApplication, QMessageBox

from src import main_window as mw_module
from src.debug import DEBUG, debug_print
from src.exporter import SetFileExporter
from src.main_window import MainWindow
from src.parser import SetFileParser, Unit
from src.tech_tree_canvas import TechTreeCanvas
from tests import make_test_dir, remove_test_dir, write_sample_sets

_app = QApplication.instance() or QApplication([])

# 在替换 mw_module.QMessageBox 之前抓取真实常量（Discard/Save 等是组合标志位，
# 不能凭记忆硬编码）。
_REAL_MSGBOX = QMessageBox


class StubMessageBox:
    """拦截所有模态弹窗，避免测试阻塞。"""

    instances = []

    def __init__(self):
        self.calls = []
        StubMessageBox.instances.append(self)

    def _record(self, kind, default):
        def fn(parent=None, title="", text="", *a, **kw):
            self.calls.append((kind, title, text))
            return default

        return fn

    def install(self, question_reply=None):
        self._saved = (mw_module.QMessageBox,)
        self.question_reply = _REAL_MSGBOX.Yes if question_reply is None else question_reply
        mw_module.QMessageBox = self
        return self

    def uninstall(self):
        (mw_module.QMessageBox,) = self._saved

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

    # 转发真实常量，使被替换后的 mw_module.QMessageBox.Xxx 仍可用
    Ok = _REAL_MSGBOX.Ok
    Yes = _REAL_MSGBOX.Yes
    No = _REAL_MSGBOX.No
    Save = _REAL_MSGBOX.Save
    Discard = _REAL_MSGBOX.Discard
    Cancel = _REAL_MSGBOX.Cancel


_YES = _REAL_MSGBOX.Yes
_SAVE = _REAL_MSGBOX.Save
_DISCARD = _REAL_MSGBOX.Discard


class CanvasTestCase(unittest.TestCase):
    """共享一个离屏画布的基类。"""

    def setUp(self):
        self.canvas = TechTreeCanvas()
        self.canvas.resize(800, 600)

    def tearDown(self):
        self.canvas.clear_canvas()

    def add(self, name, **kw):
        unit = Unit(name=name, **kw)
        self.canvas.add_unit_node(unit)
        return self.canvas.nodes[name]


# ══════════════════════════════════════════════════════════════════════
# 1. 撤销键名兼容
# ══════════════════════════════════════════════════════════════════════
class TestUndoPropertyKeyCompat(unittest.TestCase):
    """修复点 1：属性面板入口写 'property_name'，画布入口写 'property'，两者都必须能撤销。"""

    @staticmethod
    def resolve(data):
        """复刻 perform_undo 中的键解析表达式。"""
        return data.get('property', data.get('property_name', 'costs'))

    def test_panel_key(self):
        self.assertEqual(self.resolve(
            {'unit_name': 'u', 'property_name': 'costs', 'old_value': 4}), 'costs')

    def test_canvas_key(self):
        self.assertEqual(self.resolve(
            {'unit_name': 'u', 'property': 'costs', 'old_value': 4}), 'costs')

    def test_neither_key_falls_back(self):
        self.assertEqual(self.resolve({'unit_name': 'u', 'old_value': 4}), 'costs')

    def test_source_uses_get_not_indexing(self):
        """确认 perform_undo 不再直接下标取 'property'（原 KeyError 根因）。"""
        src = io.open(os.path.join(project_root, "src", "main_window.py"),
                      encoding="utf-8").read()
        self.assertNotIn("action.data['property']", src,
                         "perform_undo 仍用下标取 'property'，属性面板撤销会抛 KeyError")
        self.assertIn("action.data.get('property'", src)


# ══════════════════════════════════════════════════════════════════════
# 2. 防抖定时器
# ══════════════════════════════════════════════════════════════════════
class TestOverlapDebounce(CanvasTestCase):
    """修复点 2：原用 QTimer.singleShot（静态方法，恒返回 None），防抖从未生效。"""

    def test_timer_is_real_instance(self):
        self.add("a")
        self.assertIsInstance(self.canvas._overlap_timer, QTimer,
                              "_overlap_timer 不是 QTimer 实例，防抖会失效")

    def test_timer_is_single_shot(self):
        self.add("a")
        self.assertTrue(self.canvas._overlap_timer.isSingleShot())

    def test_timer_timeout_connected(self):
        self.add("a")
        t = self.canvas._overlap_timer
        self.assertGreater(t.receivers(t.timeout), 0, "timeout 未连接 check_node_overlaps")

    def test_scheduling_reuses_one_timer(self):
        """连续排程不得新建定时器实例（原实现每次都是新的 singleShot）。"""
        self.add("a")
        first = self.canvas._overlap_timer
        for _ in range(20):
            self.canvas._schedule_overlap_check()
        self.assertIs(self.canvas._overlap_timer, first)

    def test_burst_collapses_to_single_call(self):
        """同一次事件循环内的大量排程必须合并为一次检测，否则加载 N 节点退化为 O(N³)。"""
        calls = []
        original = self.canvas.check_node_overlaps
        self.canvas.check_node_overlaps = lambda: (calls.append(1), original())[1]
        try:
            self.canvas.preview_mode = True
            for _ in range(50):
                self.canvas._schedule_overlap_check()
            _app.processEvents()
            self.assertEqual(len(calls), 1, f"排程 50 次实际检测了 {len(calls)} 次")
        finally:
            self.canvas.check_node_overlaps = original

    def test_no_static_singleShot_call_in_source(self):
        """不得再「调用」静态 QTimer.singleShot（注释/文档中提及是允许的）。

        用 AST 只检查真实的 Call 节点，不会把注释或 docstring 里的文字误判为调用。
        """
        import ast
        path = os.path.join(project_root, "src", "tech_tree_canvas.py")
        source = io.open(path, encoding="utf-8").read()
        tree = ast.parse(source)
        offenders = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "singleShot"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "QTimer"):
                offenders.append(node.lineno)
        self.assertEqual(offenders, [],
                         f"仍存在对静态 QTimer.singleShot 的调用（返回 None）: 行 {offenders}")


# ══════════════════════════════════════════════════════════════════════
# 3. 烧瓶图标
# ══════════════════════════════════════════════════════════════════════
class TestFlaskIconUpdate(unittest.TestCase):
    """修复点 3：原先把 unit 赋给 self.unit 后才取 old type，比较恒为假。"""

    def setUp(self):
        self.canvas = TechTreeCanvas()
        self.canvas.resize(800, 600)
        self.node = self.add("u", unit_type="")

    def tearDown(self):
        self.canvas.clear_canvas()

    def add(self, name, **kw):
        self.canvas.add_unit_node(Unit(name=name, **kw))
        return self.canvas.nodes[name]

    def test_initially_no_flask(self):
        self.assertIsNone(self.node.flask_icon)

    def test_draws_flask_when_switching_to_tech(self):
        self.node.update_from_unit(Unit(name="u", unit_type="tech", costs=1))
        self.assertIsNotNone(self.node.flask_icon, "切到 tech 未绘制烧瓶图标")

    def test_clears_flask_when_switching_back(self):
        self.node.update_from_unit(Unit(name="u", unit_type="tech", costs=1))
        self.assertIsNotNone(self.node.flask_icon)
        self.node.update_from_unit(Unit(name="u", unit_type="", costs=1))
        self.assertIsNone(self.node.flask_icon, "切回普通未清除烧瓶图标")

    def test_idempotent_when_type_unchanged(self):
        self.node.update_from_unit(Unit(name="u", unit_type="", costs=5))
        self.assertIsNone(self.node.flask_icon)
        self.assertEqual(self.node.unit.costs, 5)

    def test_old_type_captured_before_overwrite(self):
        """源码层面确认：old_unit_type 必须在 self.unit = unit 之前取值。"""
        src = io.open(os.path.join(project_root, "src", "tech_tree_canvas.py"),
                      encoding="utf-8").read()
        start = src.index("def update_from_unit")
        body = src[start:start + 900]
        i_old = body.index("old_unit_type = getattr")
        i_assign = body.index("self.unit = unit")
        self.assertLess(i_old, i_assign,
                        "old_unit_type 在 self.unit = unit 之后才取值，分支恒假")


# ══════════════════════════════════════════════════════════════════════
# 4. 按下/释放时的位置同步（数据与视觉一致性）
# ══════════════════════════════════════════════════════════════════════
class TestDragPositionSync(CanvasTestCase):
    """修复点 6：按下时不再对齐；释放时无条件把像素位置写回 unit。"""

    def test_press_does_not_move_node(self):
        """按下阶段已移除预对齐，源码中不应再出现 aligned_x/aligned_y。"""
        src = io.open(os.path.join(project_root, "src", "tech_tree_canvas.py"),
                      encoding="utf-8").read()
        self.assertNotIn("aligned_x", src, "mousePressEvent 仍在按下时对齐网格")

    def test_release_snaps_and_writes_back(self):
        node = self.add("a", position_x=0.35, position_y=0.35)
        # 0.35 量纲 -> 140px / 70px，均非网格倍数（40/20）
        self.assertNotEqual(node.pos().x() % 40, 0)
        # 模拟拖动释放
        node.setSelected(True)
        self.canvas.is_dragging_nodes = True
        self.canvas.dragged_nodes_initial_positions = {
            "a": (node.pos().x(), node.pos().y())}
        self.canvas.dragged_units_initial_logical = {"a": (0.35, 0.35)}
        self.canvas.mouseReleaseEvent(
            _make_mouse_event(QEvent.MouseButtonRelease, QPointF(10, 10)))

        self.assertEqual(node.pos().x() % 40, 0, "释放后未吸附到 X 网格")
        self.assertEqual(node.pos().y() % 20, 0, "释放后未吸附到 Y 网格")
        # 关键：unit 必须与视觉位置一致
        self.assertAlmostEqual(node.unit.position_x, node.pos().x() / 40 * 0.1, places=6)
        self.assertAlmostEqual(node.unit.position_y, node.pos().y() / 20 * 0.1, places=6)

    def test_release_on_grid_keeps_data_consistent(self):
        """已在网格上的节点：数据必须仍然等于视觉位置（原实现在此分支不回写）。"""
        node = self.add("b", position_x=0.4, position_y=0.4)
        node.setSelected(True)
        self.canvas.is_dragging_nodes = True
        self.canvas.dragged_nodes_initial_positions = {
            "b": (node.pos().x(), node.pos().y())}
        self.canvas.dragged_units_initial_logical = {"b": (-1.0, -1.0)}  # 故意给错旧值
        self.canvas.mouseReleaseEvent(
            _make_mouse_event(QEvent.MouseButtonRelease, QPointF(10, 10)))
        self.assertAlmostEqual(node.unit.position_x, 0.4, places=6)
        self.assertAlmostEqual(node.unit.position_y, 0.4, places=6)

    def test_release_uses_snapshot_for_undo_old_value(self):
        """撤销用的 old_* 必须取按下时快照的 unit 逻辑坐标，而非像素反算。"""
        node = self.add("c", position_x=0.35, position_y=0.35)
        node.setSelected(True)
        self.canvas.is_dragging_nodes = True
        self.canvas.dragged_nodes_initial_positions = {"c": (140.0, 70.0)}
        self.canvas.dragged_units_initial_logical = {"c": (0.35, 0.35)}
        captured = {}
        self.canvas.batch_unit_position_changed.connect(
            lambda d: captured.update(d))
        self.canvas.mouseReleaseEvent(
            _make_mouse_event(QEvent.MouseButtonRelease, QPointF(10, 10)))
        self.assertIn("c", captured)
        self.assertAlmostEqual(captured["c"]["old_position_x"], 0.35, places=6)
        self.assertAlmostEqual(captured["c"]["old_position_y"], 0.35, places=6)
        self.assertAlmostEqual(captured["c"]["position_x"], 0.4, places=6)


def _make_mouse_event(event_type, pos):
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtCore import Qt
    return QMouseEvent(event_type, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


# ══════════════════════════════════════════════════════════════════════
# 5. 网格与场景矩形原点对齐
# ══════════════════════════════════════════════════════════════════════
class TestGridOriginAlignment(CanvasTestCase):
    """修复点 7：draw_grid 必须以 grid_origin_* 为原点，且 sceneRect 口径统一。"""

    def test_default_origin_is_zero(self):
        self.assertEqual((self.canvas.grid_origin_x, self.canvas.grid_origin_y), (0, 0))

    def test_scene_rect_starts_at_grid_origin(self):
        self.add("far", position_x=10.0, position_y=10.0)
        r = self.canvas.scene.sceneRect()
        self.assertEqual(r.left(), self.canvas.grid_origin_x)
        self.assertEqual(r.top(), self.canvas.grid_origin_y)

    def test_scene_rect_covers_all_nodes(self):
        node = self.add("n", position_x=5.0, position_y=5.0)
        r = self.canvas.scene.sceneRect()
        self.assertLessEqual(r.left(), node.pos().x())
        self.assertLessEqual(r.top(), node.pos().y())
        self.assertGreaterEqual(r.right(), node.pos().x() + node.width)
        self.assertGreaterEqual(r.bottom(), node.pos().y() + node.height)

    def test_origin_is_multiple_of_grid_size(self):
        self.add("far", position_x=10.0, position_y=10.0)
        self.assertEqual(self.canvas.grid_origin_x % 40, 0)
        self.assertEqual(self.canvas.grid_origin_y % 40, 0)

    def test_grid_items_lie_inside_scene_rect(self):
        """核心回归：网格线必须落在 sceneRect 内，否则可见区没有网格。

        容差说明：网格线由 1px 画笔绘制，QGraphicsLineItem.boundingRect() 会比端点
        各外扩 0.5px，故给 1px 容差；而原缺陷的错位量级是数千像素，仍能可靠捕获。
        """
        self.add("far", position_x=10.0, position_y=10.0)
        r = self.canvas.scene.sceneRect()
        self.assertTrue(self.canvas.grid_items, "网格项为空")
        from PyQt5.QtWidgets import QGraphicsTextItem
        lines = [i for i in self.canvas.grid_items
                 if not isinstance(i, QGraphicsTextItem)]
        self.assertTrue(lines, "没有网格线")
        tol = 1.0
        for item in lines:
            b = item.sceneBoundingRect()
            self.assertGreaterEqual(b.left() + tol, r.left(), "网格线在 sceneRect 左侧之外")
            self.assertGreaterEqual(b.top() + tol, r.top(), "网格线在 sceneRect 上方之外")
            self.assertLessEqual(b.right(), r.right() + tol, "网格线在 sceneRect 右侧之外")
            self.assertLessEqual(b.bottom(), r.bottom() + tol, "网格线在 sceneRect 下方之外")

    def test_clear_canvas_resets_origin(self):
        self.add("far", position_x=10.0, position_y=10.0)
        self.canvas.clear_canvas()
        self.assertEqual((self.canvas.grid_origin_x, self.canvas.grid_origin_y), (0, 0))
        self.assertEqual(self.canvas.scene.sceneRect().topLeft(), QPointF(0, 0))

    def test_scene_rect_stable_across_repeated_updates(self):
        """两个分支口径必须一致，重复更新不应让 sceneRect 抖动。"""
        node = self.add("n", position_x=3.0, position_y=3.0)
        self.canvas._update_scene_rect()
        first = self.canvas.scene.sceneRect()
        node.setPos(node.pos().x() + 1.0, node.pos().y())  # 微移，不触发大变化
        self.canvas._update_scene_rect()
        second = self.canvas.scene.sceneRect()
        self.assertEqual(first, second, "sceneRect 在不触发重绘的分支间发生抖动")


# ══════════════════════════════════════════════════════════════════════
# 6. 重叠检测行为与增量重绘
# ══════════════════════════════════════════════════════════════════════
class TestOverlapDetection(CanvasTestCase):

    def _build(self, positions):
        for name, (x, y) in positions.items():
            node = self.add(name, position_x=x, position_y=y)
            node.update_position()
        self.canvas.preview_mode = True

    def test_edit_mode_does_not_mark(self):
        self._build({"a": (0.0, 0.0), "b": (0.05, 0.0)})
        self.canvas.preview_mode = False
        self.canvas.check_node_overlaps()
        self.assertFalse(any(n.is_overlapping for n in self.canvas.nodes.values()))

    def test_overlapping_pair_marked(self):
        self._build({"a": (0.0, 0.0), "b": (0.05, 0.0), "far": (5.0, 5.0)})
        self.canvas.check_node_overlaps()
        self.assertTrue(self.canvas.nodes["a"].is_overlapping)
        self.assertTrue(self.canvas.nodes["b"].is_overlapping)
        self.assertFalse(self.canvas.nodes["far"].is_overlapping)

    def test_idempotent(self):
        self._build({"a": (0.0, 0.0), "b": (0.05, 0.0), "far": (5.0, 5.0)})
        self.canvas.check_node_overlaps()
        snap1 = {n: (v.is_overlapping, frozenset(v.highlighted_edges))
                 for n, v in self.canvas.nodes.items()}
        self.canvas.check_node_overlaps()
        snap2 = {n: (v.is_overlapping, frozenset(v.highlighted_edges))
                 for n, v in self.canvas.nodes.items()}
        self.assertEqual(snap1, snap2)

    def test_repaint_only_on_change(self):
        """增量重绘：第二轮检测时样式未变，不应再调用 set_pen_and_brush。"""
        self._build({"a": (0.0, 0.0), "b": (0.05, 0.0)})
        self.canvas.check_node_overlaps()
        repaints = []
        for name, node in self.canvas.nodes.items():
            original = node.set_pen_and_brush
            node.set_pen_and_brush = (lambda o: lambda: (repaints.append(1), o())[1])(original)
        self.canvas.check_node_overlaps()
        self.assertEqual(repaints, [],
                         "样式未变化却仍在重绘（增量判断失效）")


# ══════════════════════════════════════════════════════════════════════
# 7. MainWindow: 保存 / 脏位 / 关闭 / 撤销栈
# ══════════════════════════════════════════════════════════════════════
class TestMainWindowPersistence(unittest.TestCase):
    """修复点 4、5：脏位复位、closeEvent 校验保存结果、清空时清撤销栈。"""

    def setUp(self):
        self.stub = StubMessageBox().install()
        self.win = MainWindow()
        self.win.tech_tree_canvas.add_unit_node(Unit(name="a", costs=1))
        self.win.all_units = [Unit(name="a", costs=1)]
        self.tmp = make_test_dir()

    def tearDown(self):
        self.stub.uninstall()
        remove_test_dir(self.tmp)
        self.win.close = lambda *a, **k: None
        self.win.deleteLater()

    def _stub_file_dialog(self, path):
        saved = mw_module.QFileDialog

        class _FD:
            @staticmethod
            def getSaveFileName(*a, **k):
                return (path, "")

        mw_module.QFileDialog = _FD
        return saved

    def test_save_returns_true_and_resets_dirty(self):
        path = os.path.join(self.tmp, "out.set")
        saved = self._stub_file_dialog(path)
        try:
            self.win.has_unsaved_changes = True
            ok = self.win.save_tech_tree()
        finally:
            mw_module.QFileDialog = saved
        self.assertTrue(ok, "保存成功应返回 True")
        self.assertTrue(os.path.exists(path), "文件未写出")
        self.assertFalse(self.win.has_unsaved_changes,
                         "保存成功后未复位脏位（会导致每次关闭都提示未保存）")

    def test_save_cancelled_returns_false(self):
        saved = self._stub_file_dialog("")     # 用户取消
        try:
            ok = self.win.save_tech_tree()
        finally:
            mw_module.QFileDialog = saved
        self.assertFalse(ok, "取消保存应返回 False")

    def test_close_ignored_when_save_cancelled(self):
        """核心回归：保存对话框点取消后，窗口不得关闭。"""
        saved_dialog = self._stub_file_dialog("")
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _SAVE
        event = QCloseEvent()
        try:
            self.win.closeEvent(event)
        finally:
            mw_module.QFileDialog = saved_dialog
        self.assertFalse(event.isAccepted(), "取消保存后窗口仍被关闭（会静默丢数据）")

    def test_close_accepted_after_successful_save(self):
        path = os.path.join(self.tmp, "out2.set")
        saved = self._stub_file_dialog(path)
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _SAVE
        event = QCloseEvent()
        try:
            self.win.closeEvent(event)
        finally:
            mw_module.QFileDialog = saved
        self.assertTrue(event.isAccepted())

    def test_close_discard_accepts(self):
        self.win.has_unsaved_changes = True
        self.stub.question_reply = _DISCARD
        event = QCloseEvent()
        self.win.closeEvent(event)
        self.assertTrue(event.isAccepted())

    def test_close_clean_accepts_without_prompt(self):
        self.win.has_unsaved_changes = False
        event = QCloseEvent()
        self.win.closeEvent(event)
        self.assertTrue(event.isAccepted())
        self.assertEqual(self.stub.find("question"), [], "无更改时不应弹询问框")

    def test_clear_all_data_clears_undo_stack(self):
        self.win.undo_manager.push_action(
            mw_module.UndoAction(mw_module.UndoActionType.ADD_UNIT, {"unit_name": "a"}))
        self.assertGreater(self.win.undo_manager.get_stack_size(), 0)
        self.stub.question_reply = _YES
        self.win.clear_all_data()
        self.assertEqual(self.win.undo_manager.get_stack_size(), 0,
                         "清空数据后撤销栈未清空（仍能撤销出幽灵单位）")
        self.assertFalse(self.win.has_unsaved_changes)


# ══════════════════════════════════════════════════════════════════════
# 8. all_units 别名
# ══════════════════════════════════════════════════════════════════════
class TestAllUnitsAliasing(unittest.TestCase):
    """修复点 4：all_units 不得与 units 指向同一 list。"""

    def test_no_alias_in_source(self):
        src = io.open(os.path.join(project_root, "src", "main_window.py"),
                      encoding="utf-8").read()
        self.assertNotIn("self.all_units = self.units\n", src,
                         "all_units 仍与 units 别名，新建单位会出现重复行")
        self.assertNotIn("self.all_units = self.research_units\n", src)
        self.assertIn("self.all_units = list(self.units)", src)

    def test_add_new_unit_not_appended_twice(self):
        src = io.open(os.path.join(project_root, "src", "main_window.py"),
                      encoding="utf-8").read()
        start = src.index("def add_new_unit")
        body = src[start:start + 4000]
        self.assertNotIn("self.units.append(unit)", body,
                         "add_new_unit 仍同时向 units 与 all_units 追加（重复行根因）")

    def test_duplicate_name_check_covers_all_units(self):
        src = io.open(os.path.join(project_root, "src", "main_window.py"),
                      encoding="utf-8").read()
        self.assertIn("any(u.name == name for u in self.all_units)", src,
                      "重名检查未覆盖仅存在于 research 文件中的单位")


# ══════════════════════════════════════════════════════════════════════
# 9. parser: faction 提取
# ══════════════════════════════════════════════════════════════════════
class TestFactionExtraction(unittest.TestCase):
    """修复点 9：units_sov_era1960.set 不得被解析成 faction='sov_era1960'。"""

    def setUp(self):
        self.parser = SetFileParser()

    def test_units_file_with_era_suffix(self):
        self.assertEqual(self.parser._extract_faction("units_sov_era1960.set"), "sov")

    def test_units_file_plain(self):
        self.assertEqual(self.parser._extract_faction("units_gdr.set"), "gdr")

    def test_research_file(self):
        self.assertEqual(
            self.parser._extract_faction("unit_research_gerce2.set"), "gerce2")

    def test_unknown_pattern(self):
        self.assertEqual(self.parser._extract_faction("something_else.set"), "unknown")

    def test_real_file_if_present(self):
        """用合成样例端到端验证 faction 提取（不再依赖仓库内的 mod 文件）。"""
        tmp = make_test_dir()
        try:
            research, units = write_sample_sets(tmp)
            self.assertEqual(self.parser.parse_file(units)["faction"], "sample")
            self.assertEqual(self.parser.parse_file(research)["faction"], "sample")
        finally:
            remove_test_dir(tmp)


# ══════════════════════════════════════════════════════════════════════
# 10. i18n
# ══════════════════════════════════════════════════════════════════════
class TestI18n(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base = os.path.join(project_root, "src", "translations")
        cls.zh = json.loads(io.open(os.path.join(base, "zh_CN.json"),
                                    encoding="utf-8").read())
        cls.en = json.loads(io.open(os.path.join(base, "en_US.json"),
                                    encoding="utf-8").read())

    def test_key_sets_aligned(self):
        self.assertEqual(sorted(self.zh), sorted(self.en),
                         "中英键集不一致，会有一侧残留原文")

    def test_language_menu_not_swapped(self):
        self.assertEqual(self.zh["语言(&L)"], "语言(&L)")
        self.assertEqual(self.en["语言(&L)"], "Language(&L)")

    def test_placeholders_preserved(self):
        """带占位符的键，译文必须保留同名占位符，否则 .format() 抛 KeyError。"""
        import re
        mismatched = []
        for key, value in self.en.items():
            want = set(re.findall(r"\{(\w+)\}", key))
            got = set(re.findall(r"\{(\w+)\}", value))
            if want - got:
                mismatched.append((key[:40], sorted(want - got)))
        self.assertEqual(mismatched, [], f"英文译文缺失占位符: {mismatched[:5]}")

    def test_multiline_keys_real_newlines(self):
        key = "科技树有未保存的更改。\n\n是否保存后再退出？"
        self.assertIn(key, self.zh)
        self.assertIn(key, self.en)

    def test_all_source_keys_translated(self):
        """源码中出现的每个 tr() 字面量都必须在两个语言包里存在。"""
        import tokenize
        found = set()
        src_dir = os.path.join(project_root, "src")
        for fname in sorted(os.listdir(src_dir)):
            if not fname.endswith(".py"):
                continue
            with open(os.path.join(src_dir, fname), "rb") as f:
                toks = list(tokenize.tokenize(f.readline))
            for i, t in enumerate(toks):
                if t.type == tokenize.NAME and t.string == "tr":
                    j = i + 1
                    while j < len(toks) and toks[j].type in (tokenize.NL, tokenize.COMMENT):
                        j += 1
                    if j < len(toks) and toks[j].string == "(":
                        j += 1
                        parts = []
                        while j < len(toks) and toks[j].type in (tokenize.NL, tokenize.COMMENT):
                            j += 1
                        while j < len(toks) and toks[j].type == tokenize.STRING:
                            s = toks[j].string
                            q = s.find(s.lstrip("fFrRbB")[0])
                            if s[:q].lower().startswith("f"):
                                parts = []
                                break
                            parts.append(s[q + 1:-1])
                            j += 1
                            while j < len(toks) and toks[j].type in (tokenize.NL, tokenize.COMMENT):
                                j += 1
                        if parts:
                            found.add("".join(parts).replace("\\n", "\n").replace('\\"', '"'))
        missing_zh = sorted(k for k in found if k not in self.zh)
        missing_en = sorted(k for k in found if k not in self.en)
        self.assertEqual(missing_zh, [], f"缺中文翻译: {missing_zh[:5]}")
        self.assertEqual(missing_en, [], f"缺英文翻译: {missing_en[:5]}")

    def test_i18n_manager_loads(self):
        from src.i18n import get_i18n
        m = get_i18n()
        self.assertEqual(m.tr("全部"), "全部")
        self.assertEqual(m.tr("不存在的键应回退原文"), "不存在的键应回退原文")


# ══════════════════════════════════════════════════════════════════════
# 11. 调试日志短路
# ══════════════════════════════════════════════════════════════════════
class TestDebugShortCircuit(unittest.TestCase):
    """修复点：DEBUG=False 时不得组装 f-string，也不得无条件 flush。

    检测器基于 AST 做「结构级」判断：只有当一个 debug_print 处于
    `if debug.DEBUG:`（或 `if DEBUG:`）的作用域之内时才算受守卫。
    纯文本扫描会误判以下两种合法写法，故不可取：
      · `if debug.DEBUG:` 与调用之间隔了 for/if 等嵌套层
      · docstring 中把 QTimer.singleShot 当作文字提及
    """

    SRC_DIR = os.path.join(project_root, "src")

    @classmethod
    def _guarded_calls(cls, filename):
        """返回 (受守卫的调用, 未受守卫的调用)，元素为 (行号, 源码片段)。

        递归下降时必须把 guarded 标志传入所有子块（for/while/with/try/if 的 body
        与 orelse 等），否则 `if debug.DEBUG:` 下嵌套一层的调用会被误判为未守卫。
        """
        import ast
        path = os.path.join(cls.SRC_DIR, filename)
        source = io.open(path, encoding="utf-8").read()
        tree = ast.parse(source)
        lines = source.split("\n")
        guarded, unguarded = [], []

        def is_debug_guard(test):
            """识别 `debug.DEBUG` / `DEBUG`，以及复合条件 `debug.DEBUG and ...`。"""
            if (isinstance(test, ast.Attribute) and test.attr == "DEBUG"
                    and isinstance(test.value, ast.Name) and test.value.id == "debug"):
                return True
            if isinstance(test, ast.Name) and test.id == "DEBUG":
                return True
            if isinstance(test, ast.BoolOp):
                return any(is_debug_guard(v) for v in test.values)
            return False

        def is_debug_call(stmt):
            return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "debug_print")

        def walk(stmts, guarded):
            for stmt in stmts:
                if is_debug_call(stmt):
                    entry = (stmt.lineno, lines[stmt.lineno - 1].strip()[:70])
                    if guarded:
                        guarded_calls.append(entry)
                    else:
                        unguarded.append(entry)
                    continue
                # 计算本语句为子块带来的守卫增量
                child_guarded = guarded
                if isinstance(stmt, ast.If) and is_debug_guard(stmt.test):
                    child_guarded = True
                for field in ("body", "orelse", "finalbody"):
                    sub = getattr(stmt, field, None)
                    if isinstance(sub, list):
                        walk(sub, child_guarded)
                # with / try 的 handlers
                for handler in getattr(stmt, "handlers", []) or []:
                    walk(handler.body, child_guarded)

        guarded_calls = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(node.body, False)
        return guarded_calls, unguarded

    def test_default_debug_is_off(self):
        if os.environ.get("DEBUG") != "1":
            self.assertFalse(DEBUG)

    def test_canvas_has_guarded_debug_calls(self):
        """正向校验：确认检测器确实识别到了守卫块（避免检测器本身失效而误报通过）。"""
        guarded, _ = self._guarded_calls("tech_tree_canvas.py")
        self.assertGreater(len(guarded), 5,
                           "未识别到任何受守卫的 debug_print，检测器可能失效")

    def test_no_unguarded_debug_print_with_fstring(self):
        _, unguarded = self._guarded_calls("tech_tree_canvas.py")
        bad = [(ln, src) for ln, src in unguarded if "f\"" in src or "f'" in src]
        self.assertEqual(bad, [], f"存在未守卫的 f-string 调试输出: {bad[:5]}")

    def test_no_unconditional_stdout_flush(self):
        lines = io.open(os.path.join(self.SRC_DIR, "tech_tree_canvas.py"),
                        encoding="utf-8").read().split("\n")
        bad = []
        for i, line in enumerate(lines):
            if line.strip() in ("sys.stdout.flush()", "sys.stderr.flush()"):
                prev = lines[i - 1].strip() if i else ""
                if not prev.startswith("if sys."):
                    bad.append(i + 1)
        self.assertEqual(bad, [], f"存在无条件 flush: {bad}")

    def test_overlap_method_debug_prints_all_guarded(self):
        lines = io.open(os.path.join(self.SRC_DIR, "tech_tree_canvas.py"),
                        encoding="utf-8").read().split("\n")
        start = next(i for i, l in enumerate(lines)
                     if l.startswith("    def check_node_overlaps"))
        end = next(i for i, l in enumerate(lines)
                   if i > start and l.startswith("    def get_all_units"))
        _, unguarded = self._guarded_calls("tech_tree_canvas.py")
        bad = [(ln, src) for ln, src in unguarded if start + 1 <= ln <= end]
        self.assertEqual(bad, [], f"check_node_overlaps 内存在未守卫的调试输出: {bad[:5]}")

    def test_all_other_src_modules_guarded(self):
        """其余模块的 debug_print 也不得无条件组装 f-string。"""
        bad = []
        for fname in sorted(os.listdir(self.SRC_DIR)):
            if not fname.endswith(".py") or fname == "tech_tree_canvas.py":
                continue
            try:
                _, unguarded = self._guarded_calls(fname)
            except SyntaxError:
                continue
            for ln, src in unguarded:
                if "f\"" in src or "f'" in src:
                    bad.append((fname, ln, src))
        self.assertEqual(bad, [], f"其他模块存在未守卫的 f-string 调试输出: {bad[:5]}")


# ══════════════════════════════════════════════════════════════════════
# 12. 导出往返（确保本次改动未破坏核心链路）
# ══════════════════════════════════════════════════════════════════════
class TestExportRoundTrip(unittest.TestCase):

    def setUp(self):
        self.tmp = make_test_dir()

    def tearDown(self):
        remove_test_dir(self.tmp)

    def test_multi_parent_round_trip(self):
        units = [
            Unit(name="a", unit_type="tech", costs=0, requires=[], position_x=0.0, position_y=0.0),
            Unit(name="b", unit_type="tech", costs=1, requires=["a"], position_x=1.0, position_y=0.0),
            Unit(name="c", costs=2, requires=["a", "b"], position_x=2.0, position_y=0.0),
        ]
        # 注意：文件名必须含 'unit_research'，parser 按文件名判定格式，
        # 否则会被当作 units_*.set 解析（这是既有设计，见 parse_file）
        out = os.path.join(self.tmp, "unit_research_rt.set")
        SetFileExporter().export(units, "test", out)
        parsed = SetFileParser().parse_file(out)["units"]
        by_name = {u["name"]: u for u in parsed}
        self.assertEqual(len(parsed), 3, "往返后单位数量不符")
        self.assertEqual(by_name["a"]["unit_type"], "tech")
        self.assertEqual(by_name["c"]["unit_type"], "")
        self.assertEqual(by_name["c"]["requires"], ["a", "b"], "多父节点往返后丢失")
        self.assertEqual(by_name["c"]["costs"], 2)

    def test_research_file_detected_by_filename(self):
        """回归：说明 parse_file 的格式判定依赖文件名前缀。"""
        parser = SetFileParser()
        units = [Unit(name="x", unit_type="tech", costs=1, requires=[],
                      position_x=1.0, position_y=1.0)]
        good = os.path.join(self.tmp, "unit_research_ok.set")
        bad = os.path.join(self.tmp, "ok.set")
        SetFileExporter().export(units, "test", good)
        SetFileExporter().export(units, "test", bad)
        self.assertEqual(len(parser.parse_file(good)["units"]), 1)
        self.assertEqual(len(parser.parse_file(bad)["units"]), 0,
                         "无 unit_research 前缀的文件被误判为 research 文件")

    def test_real_file_round_trip_line_count(self):
        """用合成样例验证「保留格式」导出不改变行数。"""
        src_file, _units = write_sample_sets(self.tmp)
        parser = SetFileParser()
        data = parser.parse_file(src_file)
        units = [Unit.from_dict(u) for u in data["units"]]
        out = os.path.join(self.tmp, "unit_research_rt_real.set")
        SetFileExporter().export(units, data["faction"], out, src_file)
        n_src = len(io.open(src_file, encoding="utf-8").read().splitlines())
        n_out = len(io.open(out, encoding="utf-8").read().splitlines())
        self.assertEqual(n_src, n_out, "保留格式导出改变了行数（注释/空行丢失）")

    def test_comment_lines_preserved(self):
        src_file, _units = write_sample_sets(self.tmp)
        parser = SetFileParser()
        data = parser.parse_file(src_file)
        units = [Unit.from_dict(u) for u in data["units"]]
        out = os.path.join(self.tmp, "rt_cmt.set")
        SetFileExporter().export(units, data["faction"], out, src_file)
        orig = io.open(src_file, encoding="utf-8").read()
        new = io.open(out, encoding="utf-8").read()
        for marker in (";// REINFORCEMENTS", ";// DOCTRINE TECHS"):
            self.assertIn(marker, orig)
            self.assertIn(marker, new, f"注释 {marker} 丢失")


if __name__ == "__main__":
    unittest.main(verbosity=2)
