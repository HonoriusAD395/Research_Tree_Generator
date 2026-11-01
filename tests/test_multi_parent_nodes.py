# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
多父节点功能单元测试
Test suite for multi-parent node support

测试内容 / Test Coverage:
1. 解析器读取多父节点 / Parser reading multi-parent nodes
2. 导出器保存多父节点 / Exporter saving multi-parent nodes
3. 属性面板输入输出 / Property panel input/output
4. 往返一致性 / Round-trip consistency
"""

import unittest
import sys
import os
import tempfile
import shutil

from tests import make_test_dir, remove_test_dir, write_sample_sets

# 添加项目根目录和 src 目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from parser import SetFileParser, Unit
from exporter import SetFileExporter


class TestMultiParentNodeParsing(unittest.TestCase):
    """测试多父节点解析功能 / Test multi-parent node parsing"""
    
    def setUp(self):
        """设置测试环境 / Set up test environment"""
        self.parser = SetFileParser()
        self.test_dir = make_test_dir()
    
    def tearDown(self):
        """清理测试环境 / Clean up test environment"""
        remove_test_dir(self.test_dir)
    
    def test_parse_single_parent(self):
        """测试单个父节点解析 / Test single parent node parsing"""
        content = '''
{IconGap 28}
\t{ tech "child_unit" requires "parent_unit" costs 1 position 1 0}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].name, "child_unit")
        self.assertIsInstance(units[0].requires, list)
        self.assertEqual(units[0].requires, ["parent_unit"])
    
    def test_parse_two_parents(self):
        """测试两个父节点解析 / Test two parent nodes parsing"""
        content = '''
{IconGap 28}
\t{ tech "defense_level_2" requires "reinforcement_stage_3 defense_level_1" costs 4 position 4 0}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].name, "defense_level_2")
        self.assertIsInstance(units[0].requires, list)
        self.assertEqual(len(units[0].requires), 2)
        self.assertEqual(units[0].requires[0], "reinforcement_stage_3")
        self.assertEqual(units[0].requires[1], "defense_level_1")
    
    def test_parse_three_parents(self):
        """测试三个父节点解析 / Test three parent nodes parsing"""
        content = '''
{IconGap 28}
\t{"unit_name" requires "parent1 parent2 parent3" costs 2 position 5 3}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].name, "unit_name")
        self.assertIsInstance(units[0].requires, list)
        self.assertEqual(len(units[0].requires), 3)
        self.assertEqual(units[0].requires, ["parent1", "parent2", "parent3"])
    
    def test_parse_no_parent(self):
        """测试无父节点解析 / Test no parent node parsing"""
        content = '''
{IconGap 28}
\t{ tech "root_unit" requires "" costs 0 position 0 0}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].name, "root_unit")
        self.assertIsInstance(units[0].requires, list)
        self.assertEqual(units[0].requires, [])
    
    def test_parse_mixed_units(self):
        """测试混合单位解析（tech和普通单位）/ Test mixed units parsing"""
        content = '''
{IconGap 28}
\t{ tech "tech_unit" requires "parent1 parent2" costs 1 position 1 0}
\t{"normal_unit" requires "parent3 parent4" costs 2 position 2 0}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 2)
        
        # 检查 tech 单位
        tech_unit = next(u for u in units if u.name == "tech_unit")
        self.assertEqual(tech_unit.unit_type, "tech")
        self.assertEqual(tech_unit.requires, ["parent1", "parent2"])
        
        # 检查普通单位
        normal_unit = next(u for u in units if u.name == "normal_unit")
        self.assertEqual(normal_unit.unit_type, "")
        self.assertEqual(normal_unit.requires, ["parent3", "parent4"])
    
    def test_parse_with_extra_spaces(self):
        """测试多余空格的解析 / Test parsing with extra spaces"""
        content = '''
{IconGap 28}
\t{ tech "unit" requires "parent1   parent2    parent3" costs 1 position 1 0}
'''
        units = self.parser._parse_research_tree(content)
        
        self.assertEqual(len(units), 1)
        # 应该去除多余空格
        self.assertEqual(units[0].requires, ["parent1", "parent2", "parent3"])
    
    def test_parse_real_file(self):
        """测试解析真实文件 / Test parsing real file

        ⚠️ 使用 tests/__init__.py 生成的合成样例，不再依赖仓库内的第三方 mod 文件。
        """
        research, _units = write_sample_sets(self.test_dir)
        data = self.parser.parse_research_file(research)
        units_dict = {u['name']: u for u in data['units']}

        self.assertIn('defense_level_2', units_dict, "样例缺少 defense_level_2")
        requires = units_dict['defense_level_2']['requires']
        self.assertIsInstance(requires, list)
        self.assertEqual(requires, ['reinforcement_stage_3', 'defense_level_1'])

        self.assertIn('reinforcement_stage_3', units_dict)
        self.assertEqual(units_dict['reinforcement_stage_3']['requires'],
                         ['reinforcement_stage_1', 'reinforcement_stage_2'])


class TestMultiParentNodeExporting(unittest.TestCase):
    """测试多父节点导出功能 / Test multi-parent node exporting"""
    
    def setUp(self):
        """设置测试环境 / Set up test environment"""
        self.exporter = SetFileExporter()
        self.test_dir = make_test_dir()
    
    def tearDown(self):
        """清理测试环境 / Clean up test environment"""
        remove_test_dir(self.test_dir)
    
    def test_export_single_parent(self):
        """测试单个父节点导出 / Test single parent node export"""
        unit = Unit(
            name="child",
            requires=["parent"],
            costs=1,
            position_x=1.0,
            position_y=0.0,
            unit_type="tech"
        )
        
        line = self.exporter._format_tech_line(unit)
        
        self.assertIn('requires "parent"', line)
        self.assertNotIn('requires "parent "', line)  # 不应有多余空格
    
    def test_export_two_parents(self):
        """测试两个父节点导出 / Test two parent nodes export"""
        unit = Unit(
            name="defense_level_2",
            requires=["reinforcement_stage_3", "defense_level_1"],
            costs=4,
            position_x=4.0,
            position_y=0.0,
            unit_type="tech"
        )
        
        line = self.exporter._format_tech_line(unit)
        
        self.assertIn('requires "reinforcement_stage_3 defense_level_1"', line)
    
    def test_export_three_parents(self):
        """测试三个父节点导出 / Test three parent nodes export"""
        unit = Unit(
            name="complex_unit",
            requires=["parent1", "parent2", "parent3"],
            costs=5,
            position_x=6.0,
            position_y=3.0,
            unit_type=""
        )
        
        line = self.exporter._format_unit_line(unit, "test")
        
        self.assertIn('requires "parent1 parent2 parent3"', line)
    
    def test_export_no_parent(self):
        """测试无父节点导出 / Test no parent node export"""
        unit = Unit(
            name="root",
            requires=[],
            costs=0,
            position_x=0.0,
            position_y=0.0,
            unit_type="tech"
        )
        
        line = self.exporter._format_tech_line(unit)
        
        self.assertIn('requires ""', line)
    
    def test_export_preserve_style_two_parents(self):
        """测试保留格式导出两个父节点 / Test preserve style export with two parents"""
        unit = Unit(
            name="test_unit",
            requires=["parent_a", "parent_b"],
            costs=3,
            position_x=2.0,
            position_y=1.0,
            unit_type="tech"
        )
        
        original_line = '\t{ tech "test_unit"\t\trequires "old_parent"\t\tcosts 1  position 1 0}'
        new_line = self.exporter._format_unit_line_preserve_style(unit, original_line)
        
        self.assertIn('requires "parent_a parent_b"', new_line)
    
    def test_export_full_file_round_trip(self):
        """测试完整文件往返（导入→导出）/ Test full file round-trip"""
        # 创建测试文件
        test_input = os.path.join(self.test_dir, 'test_input.set')
        test_output = os.path.join(self.test_dir, 'test_output.set')
        
        original_content = '''{IconGap 28}
\t{ tech "unit1" requires "parent1 parent2" costs 1 position 1 0}
\t{"unit2" requires "parent3 parent4 parent5" costs 2 position 2 0}
'''
        
        with open(test_input, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # 解析
        parser = SetFileParser()
        data = parser.parse_research_file(test_input)
        units = [Unit.from_dict(u) for u in data['units']]
        
        # 导出
        self.exporter.export(units, 'test', test_output, test_input)
        
        # 读取导出文件
        with open(test_output, 'r', encoding='utf-8') as f:
            exported_content = f.read()
        
        # 验证多父节点被正确保存
        self.assertIn('requires "parent1 parent2"', exported_content)
        self.assertIn('requires "parent3 parent4 parent5"', exported_content)


class TestPropertyPanelMultiParent(unittest.TestCase):
    """测试属性面板多父节点处理 / Test property panel multi-parent handling"""
    
    def test_requires_string_to_list(self):
        """测试 requires 字符串转列表 / Test requires string to list conversion"""
        # 模拟属性面板的转换逻辑
        requires_text = "parent1 parent2 parent3"
        requires_list = [r.strip() for r in requires_text.split() if r.strip()]
        
        self.assertEqual(requires_list, ["parent1", "parent2", "parent3"])
    
    def test_requires_list_to_string(self):
        """测试 requires 列表转字符串 / Test requires list to string conversion"""
        requires_list = ["parent1", "parent2", "parent3"]
        requires_string = ' '.join(requires_list)
        
        self.assertEqual(requires_string, "parent1 parent2 parent3")
    
    def test_empty_requires(self):
        """测试空 requires 处理 / Test empty requires handling"""
        requires_text = ""
        requires_list = [r.strip() for r in requires_text.split() if r.strip()] if requires_text else []
        
        self.assertEqual(requires_list, [])
    
    def test_requires_with_extra_spaces(self):
        """测试带多余空格的 requires / Test requires with extra spaces"""
        requires_text = "parent1   parent2    parent3"
        requires_list = [r.strip() for r in requires_text.split() if r.strip()]
        
        self.assertEqual(requires_list, ["parent1", "parent2", "parent3"])


class TestUnitClassMultiParent(unittest.TestCase):
    """测试 Unit 类的多父节点支持 / Test Unit class multi-parent support"""
    
    def test_unit_from_dict_with_list_requires(self):
        """测试从字典创建 Unit（requires 为列表）/ Test Unit from dict with list requires"""
        data = {
            'name': 'test_unit',
            'requires': ['parent1', 'parent2'],
            'costs': 3,
            'position_x': 1.0,
            'position_y': 0.0,
            'unit_type': 'tech'
        }
        
        unit = Unit.from_dict(data)
        
        self.assertEqual(unit.name, 'test_unit')
        self.assertIsInstance(unit.requires, list)
        self.assertEqual(unit.requires, ['parent1', 'parent2'])
    
    def test_unit_to_dict_with_list_requires(self):
        """测试 Unit 转字典（requires 为列表）/ Test Unit to dict with list requires"""
        unit = Unit(
            name='test_unit',
            requires=['parent1', 'parent2'],
            costs=3,
            position_x=1.0,
            position_y=0.0,
            unit_type='tech'
        )
        
        data = unit.to_dict()
        
        self.assertEqual(data['name'], 'test_unit')
        self.assertIsInstance(data['requires'], list)
        self.assertEqual(data['requires'], ['parent1', 'parent2'])
    
    def test_unit_default_requires(self):
        """测试 Unit 默认 requires / Test Unit default requires"""
        unit = Unit(name='test')
        
        self.assertIsInstance(unit.requires, list)
        self.assertEqual(unit.requires, [])


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
