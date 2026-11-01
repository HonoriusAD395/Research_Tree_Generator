# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
撤销和导出逻辑单元测试
Unit tests for undo and export logic

测试内容 / Test Coverage:
1. UndoManager 推入/弹出/溢出/清空
2. 导出器重复防止和格式一致性
3. 撤销 requires 恢复分隔符
4. 新单位导出多父节点支持
"""

import unittest
import sys
import os
import tempfile
import shutil

from tests import make_test_dir, remove_test_dir

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from undo_manager import UndoManager, UndoAction, UndoActionType
from exporter import SetFileExporter
from parser import Unit


class TestUndoManagerCore(unittest.TestCase):
    """测试 UndoManager 核心功能 / Test UndoManager core functionality"""

    def setUp(self):
        self.mgr = UndoManager(max_undo_steps=50)

    def test_push_and_undo(self):
        """测试推入和撤销 / Test push and undo"""
        action = UndoAction(UndoActionType.ADD_UNIT, {'unit_name': 'test'})
        self.mgr.push_action(action)
        self.assertTrue(self.mgr.can_undo())
        popped = self.mgr.undo()
        self.assertIsNotNone(popped)
        self.assertEqual(popped.action_type, UndoActionType.ADD_UNIT)
        self.assertEqual(popped.data['unit_name'], 'test')

    def test_undo_empty_stack(self):
        """测试空栈撤销返回 None / Test undo on empty stack returns None"""
        self.assertFalse(self.mgr.can_undo())
        self.assertIsNone(self.mgr.undo())

    def test_undo_overflow(self):
        """✅ AI 生成: 测试撤销栈溢出淘汰最旧操作 / Test overflow evicts oldest action"""
        for i in range(60):
            action = UndoAction(UndoActionType.ADD_UNIT, {'unit_name': f'unit_{i}'})
            self.mgr.push_action(action)
        self.assertEqual(self.mgr.get_stack_size(), 50)
        first_remaining = self.mgr.undo()
        self.assertEqual(first_remaining.data['unit_name'], 'unit_59')

    def test_redo_after_undo(self):
        """测试撤销后重做 / Test redo after undo"""
        action = UndoAction(UndoActionType.MOVE_UNIT, {'unit_name': 'test'})
        self.mgr.push_action(action)
        self.mgr.undo()
        self.assertTrue(self.mgr.can_redo())
        redone = self.mgr.redo()
        self.assertIsNotNone(redone)
        self.assertEqual(redone.action_type, UndoActionType.MOVE_UNIT)

    def test_new_action_clears_redo(self):
        """✅ AI 生成: 新操作清空重做栈 / Test new action clears redo stack"""
        self.mgr.push_action(UndoAction(UndoActionType.ADD_UNIT, {'unit_name': 'a'}))
        self.mgr.undo()
        self.mgr.push_action(UndoAction(UndoActionType.DELETE_UNIT, {'unit_name': 'b'}))
        self.assertFalse(self.mgr.can_redo())

    def test_clear(self):
        """测试清空撤销栈 / Test clear"""
        self.mgr.push_action(UndoAction(UndoActionType.ADD_UNIT, {'unit_name': 't'}))
        self.mgr.clear()
        self.assertFalse(self.mgr.can_undo())
        self.assertFalse(self.mgr.can_redo())
        self.assertEqual(self.mgr.get_stack_size(), 0)

    def test_all_action_types(self):
        """✅ AI 生成: 测试所有撤销操作类型 / Test all undo action types"""
        types = [
            (UndoActionType.ADD_UNIT, {'unit_name': 'a'}),
            (UndoActionType.DELETE_UNIT, {'unit_name': 'b', 'unit_data': {'name': 'b'}}),
            (UndoActionType.MOVE_UNIT, {'unit_name': 'c', 'old_position_x': 0, 'old_position_y': 0}),
            (UndoActionType.CHANGE_REQUIRES, {'unit_name': 'd', 'old_requires': [], 'new_requires': ['p']}),
            (UndoActionType.MODIFY_PROPERTY, {'unit_name': 'e', 'property': 'costs', 'old_value': 4, 'new_value': 5}),
        ]
        for action_type, data in types:
            self.mgr.push_action(UndoAction(action_type, data))
        self.assertEqual(self.mgr.get_stack_size(), 5)
        for action_type, data in reversed(types):
            popped = self.mgr.undo()
            self.assertEqual(popped.action_type, action_type)
            self.assertEqual(popped.data['unit_name'], data['unit_name'])


class TestUndoManagerOverflow(unittest.TestCase):
    """✅ AI 生成: 测试不同 max_undo_steps 的行为 / Test different max_undo_steps"""

    def test_small_stack(self):
        """测试小栈容量 / Test small stack capacity"""
        mgr = UndoManager(max_undo_steps=3)
        for i in range(5):
            mgr.push_action(UndoAction(UndoActionType.ADD_UNIT, {'unit_name': f'u{i}'}))
        self.assertEqual(mgr.get_stack_size(), 3)
        self.assertEqual(mgr.undo().data['unit_name'], 'u4')
        self.assertEqual(mgr.undo().data['unit_name'], 'u3')
        self.assertEqual(mgr.undo().data['unit_name'], 'u2')
        self.assertIsNone(mgr.undo())

    def test_no_overflow(self):
        """测试不超过容量时正常行为 / Test normal behavior within capacity"""
        mgr = UndoManager(max_undo_steps=10)
        for i in range(5):
            mgr.push_action(UndoAction(UndoActionType.ADD_UNIT, {'unit_name': f'u{i}'}))
        self.assertEqual(mgr.get_stack_size(), 5)


class TestExportDuplicatePrevention(unittest.TestCase):
    """✅ AI 生成: 测试导出重复防止 / Test export duplicate prevention"""

    def setUp(self):
        self.exporter = SetFileExporter()
        self.test_dir = make_test_dir()

    def tearDown(self):
        remove_test_dir(self.test_dir)

    def _count_occurrences_in_export(self, units, name):
        output = os.path.join(self.test_dir, 'test.set')
        self.exporter._export_simple(units, 'test', output)
        with open(output, 'r', encoding='utf-8') as f:
            content = f.read()
        count = 0
        for line in content.split('\n'):
            if f'"{name}"' in line or name in line:
                if '{' in line and '}' in line:
                    count += 1
        return count

    def test_no_duplicate_for_doctrine_and_radio(self):
        """✅ AI 生成: 同时匹配 doctrine 和 radio 的单位只导出一次 / Unit matching both doctrine and radio exports once"""
        unit = Unit(name='sov_radio_doctrine_1', unit_type='', costs=2)
        count = self._count_occurrences_in_export([unit], 'sov_radio_doctrine_1')
        self.assertEqual(count, 1,
                         f"Unit should appear once but found {count} times")

    def test_no_duplicate_for_tech_and_doctrine(self):
        """✅ AI 生成: 同时匹配 tech 和 doctrine 的单位只导出一次 / Unit matching both tech and doctrine exports once"""
        unit = Unit(name='doctrine_tech_1', unit_type='tech', costs=1)
        count = self._count_occurrences_in_export([unit], 'doctrine_tech_1')
        self.assertEqual(count, 1,
                         f"Tech unit with doctrine name should appear once but found {count} times")

    def test_mixed_categories_no_duplicate(self):
        """✅ AI 生成: 混合类别无重复导出 / Mixed categories with no duplicates"""
        units = [
            Unit(name='reinforcement_stage_1', unit_type='tech', costs=1),
            Unit(name='sov_radio_support', unit_type='', costs=3),
            Unit(name='doctrine_armor', unit_type='', costs=4),
            Unit(name='regular_infantry', unit_type='', costs=2),
        ]
        output = os.path.join(self.test_dir, 'mix.set')
        self.exporter._export_simple(units, 'test', output)
        with open(output, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith(';') and not l.strip().startswith('//') and not l.strip().startswith('{IconGap')]

        unit_lines = [l for l in lines if l.startswith('{') and l.endswith('}')]
        names_in_export = []
        for line in unit_lines:
            for u in units:
                if f'"{u.name}"' in line:
                    names_in_export.append(u.name)
                    break

        from collections import Counter
        counts = Counter(names_in_export)
        duplicates = [name for name, c in counts.items() if c > 1]
        self.assertEqual(len(duplicates), 0,
                         f"Duplicate units found: {duplicates}")


class TestExportNewUnitMultiParent(unittest.TestCase):
    """✅ AI 生成: 测试新单位导出多父节点支持 / Test new unit export multi-parent support"""

    def setUp(self):
        self.exporter = SetFileExporter()

    def test_tech_with_two_parents(self):
        """测试科技新单位两个父节点 / Test new tech unit with two parents"""
        unit = Unit(name='new_tech', requires=['parent1', 'parent2'], costs=3,
                    position_x=1.0, position_y=0.0, unit_type='tech')
        line = self.exporter._format_unit_line_new(unit)
        self.assertIn('requires "parent1 parent2"', line,
                      f"Expected space-separated parents, got: {line}")

    def test_unit_with_three_parents(self):
        """测试普通新单位三个父节点 / Test new normal unit with three parents"""
        unit = Unit(name='new_unit', requires=['a', 'b', 'c'], costs=5,
                    position_x=2.0, position_y=1.0, unit_type='')
        line = self.exporter._format_unit_line_new(unit)
        self.assertIn('requires "a b c"', line,
                      f"Expected space-separated parents, got: {line}")

    def test_tech_with_single_parent(self):
        """测试新单位单个父节点 / Test new unit with single parent"""
        unit = Unit(name='single', requires=['only_parent'], costs=1,
                    position_x=0.0, position_y=0.0, unit_type='tech')
        line = self.exporter._format_unit_line_new(unit)
        self.assertIn('requires "only_parent"', line)

    def test_tech_with_no_parent(self):
        """测试新单位无父节点 / Test new unit with no parent"""
        unit = Unit(name='root_unit', requires=[], costs=0,
                    position_x=0.0, position_y=0.0, unit_type='tech')
        line = self.exporter._format_unit_line_new(unit)
        self.assertIn('requires ""', line)


class TestExportTabConsistency(unittest.TestCase):
    """✅ AI 生成: 测试导出 tab 一致性 / Test export tab consistency"""

    def setUp(self):
        self.exporter = SetFileExporter()

    def test_tech_line_vs_preserve_style(self):
        """测试 _format_tech_line 和 preserve style 的 costs tab 数量一致 / Test tab count consistency for tech costs"""
        unit = Unit(name='test', requires=['parent'], costs=3,
                    position_x=1.0, position_y=0.0, unit_type='tech')
        simple_line = self.exporter._format_tech_line(unit)
        original = '\t{ tech "test"\t\trequires "old"\t\tcosts 1  position 1 0}'
        preserve_line = self.exporter._format_unit_line_preserve_style(unit, original)

        # 提取 costs 前的 tab 数
        def count_tabs_before(line, keyword):
            idx = line.find(keyword)
            before = line[:idx]
            tab_count = 0
            for ch in reversed(before):
                if ch == '\t':
                    tab_count += 1
                elif ch != ' ':
                    break
            return tab_count

        simple_tabs = count_tabs_before(simple_line, 'costs')
        preserve_tabs = count_tabs_before(preserve_line, 'costs')
        self.assertEqual(simple_tabs, preserve_tabs,
                         f"Tab count mismatch: simple={simple_tabs}, preserve={preserve_tabs}")

    def test_normal_unit_tabs(self):
        """测试普通单位两种格式 tab 一致 / Test tab consistency for normal units"""
        unit = Unit(name='normal', requires=['p'], costs=2,
                    position_x=0.0, position_y=0.0, unit_type='')
        simple_line = self.exporter._format_unit_line(unit, 'test')
        original = '\t{"normal"\t\trequires "p"\t\t\t\tcosts 2  position 0 0}'
        preserve_line = self.exporter._format_unit_line_preserve_style(unit, original)

        def count_tabs_before(line, keyword):
            idx = line.find(keyword)
            before = line[:idx]
            tab_count = 0
            for ch in reversed(before):
                if ch == '\t':
                    tab_count += 1
                elif ch != ' ':
                    break
            return tab_count

        simple_tabs = count_tabs_before(simple_line, 'costs')
        preserve_tabs = count_tabs_before(preserve_line, 'costs')
        new_line = self.exporter._format_unit_line_new(unit)
        new_tabs = count_tabs_before(new_line, 'costs')
        self.assertEqual(simple_tabs, preserve_tabs,
                         f"Tab mismatch: simple={simple_tabs}, preserve={preserve_tabs}")
        self.assertEqual(simple_tabs, new_tabs,
                         f"Tab mismatch: simple={simple_tabs}, new={new_tabs}")


class TestExportWithOriginalFormatMultiParent(unittest.TestCase):
    """✅ AI 生成: 测试保留格式导出多父节点 / Test preserve format export with multi-parent"""

    def setUp(self):
        self.exporter = SetFileExporter()
        self.test_dir = make_test_dir()

    def tearDown(self):
        remove_test_dir(self.test_dir)

    def test_preserve_format_with_two_parents(self):
        """测试保留格式两个父节点 / Test preserve format with two parents"""
        unit = Unit(name='defense_level_2',
                    requires=['reinforcement_stage_3', 'defense_level_1'],
                    costs=4, position_x=4.0, position_y=0.0, unit_type='tech')
        original_line = '\t{ tech "defense_level_2"\t\trequires "reinforcement_stage_3 defense_level_1"\t\tcosts 4  position 4 0}'
        result = self.exporter._format_unit_line_preserve_style(unit, original_line)
        self.assertIn('requires "reinforcement_stage_3 defense_level_1"', result)

    def test_round_trip_full_file(self):
        """测试完整文件往返一致性 / Test full file round-trip consistency"""
        input_file = os.path.join(self.test_dir, 'input.set')
        output_file = os.path.join(self.test_dir, 'output.set')

        original = '''{IconGap 28}

;// REINFORCEMENTS & TECH LEVELS
\t{ tech "reinforcement_stage_2"\t\trequires "reinforcement_stage_1"\t\tcosts 1  position 1 0}
\t{ tech "reinforcement_stage_3"\t\trequires "reinforcement_stage_2 squad_officer_con(ger)"\t\tcosts 2  position 2 0}

;// UNITS
\t{"squad_officer_con(ger)"\t\trequires "reinforcement_stage_2"\t\t\t\tcosts 2  position 3 0}
'''
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(original)

        from parser import SetFileParser
        parser = SetFileParser()
        data = parser.parse_research_file(input_file)
        units = [Unit.from_dict(u) for u in data['units']]

        self.exporter.export(units, 'test', output_file, input_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('requires "reinforcement_stage_2 squad_officer_con(ger)"', content)
        self.assertIn('requires "reinforcement_stage_2"', content)
        self.assertIn(';// REINFORCEMENTS & TECH LEVELS', content)
        self.assertIn(';// UNITS', content)


if __name__ == '__main__':
    unittest.main(verbosity=2)
