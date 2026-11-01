# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
文件导出器模块
负责生成 unit_research_*.set 文件
支持实际的 .set 文件格式，保留原始注释和格式
"""

import os
import re
import shutil
from typing import List, Dict, Tuple
from src.parser import Unit


class SetFileExporter:
    """.set 文件导出器"""
    
    def __init__(self):
        self.icon_gap = 30
    
    # ✅ AI 生成: 原子写入 + 自动备份。
    # 原实现直接 open(output_path, 'w')，且输出路径常等于原文件：
    # 写入中途异常（断电/崩溃/磁盘错误）会把用户的 mod 源文件直接损坏。
    # 现改为：① 先把现有文件复制为 .bak；② 写同目录临时文件；③ os.replace 原子替换。
    # os.replace 在 Windows 上对已存在目标是原子替换，任一环节失败原文件都保持完好。
    def _write_file_safely(self, output_path: str, content: str):
        """安全写出文件：备份现有文件 → 临时文件 → 原子替换"""
        if os.path.exists(output_path):
            try:
                shutil.copy2(output_path, output_path + '.bak')
            except OSError:
                pass  # 备份失败不阻断保存（.bak 只是额外保险）
        
        tmp_path = output_path + '.rtg_tmp'
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(tmp_path, output_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise
    
    def export(self, units: List[Unit], faction: str, output_path: str, original_file_path: str = None):
        """
        导出科技树配置文件（保留原始注释和格式）
        
        Args:
            units: 单位列表
            faction: 阵营名称
            output_path: 输出文件路径
            original_file_path: 原始文件路径（可选，用于保留注释）
        """
        lines = []  # 初始化 lines 列表
        
        if original_file_path:
            # 如果有原始文件，读取并更新
            self._export_with_original_format(units, faction, output_path, original_file_path)
            return output_path
        else:
            # 否则使用简单导出
            return self._export_simple(units, faction, output_path)
    
    def _format_tech_line(self, unit: Unit) -> str:
        """
        格式化 tech 单位行
        
        Args:
            unit: 单位对象
            
        Returns:
            格式化的行字符串
        """
        # ✅ 支持多父节点：用空格连接
        if isinstance(unit.requires, list):
            requires = ' '.join(unit.requires) if unit.requires else ""
        else:
            requires = unit.requires if unit.requires else ""
        costs = unit.costs
        pos_x = unit.position_x
        pos_y = unit.position_y
        
        # 格式化位置（如果是整数则不显示小数）
        pos_x_str = f"{pos_x:g}"
        pos_y_str = f"{pos_y:g}"
        
        # ✅ AI 生成: 统一 tab 数量，与 _format_unit_line_preserve_style 保持一致
        line = f'\t{{ tech "{unit.name}"\t\trequires "{requires}"\t\tcosts {costs}  position {pos_x_str} {pos_y_str}}}'
        
        return line
    
    def _format_unit_line(self, unit: Unit, faction: str) -> str:
        """
        格式化单位行
        
        Args:
            unit: 单位对象
            faction: 阵营名称
            
        Returns:
            格式化的行字符串
        """
        # ✅ 支持多父节点：用空格连接
        if isinstance(unit.requires, list):
            requires_str = ' '.join(unit.requires) if unit.requires else ""
        else:
            requires_str = unit.requires if unit.requires else ""
        costs = unit.costs
        pos_x = unit.position_x
        pos_y = unit.position_y
        
        # 格式化位置
        pos_x_str = f"{pos_x:g}"
        pos_y_str = f"{pos_y:g}"
        
        line = f'\t{{"{unit.name}"\t\trequires "{requires_str}"\t\t\t\tcosts {costs}  position {pos_x_str} {pos_y_str}}}'
        
        return line
    
    def _export_simple(self, units: List[Unit], faction: str, output_path: str):
        """
        简单导出（不保留原始注释）
        """
        lines = []
        
        # 文件头
        lines.append(f"{{IconGap {self.icon_gap}}}")
        lines.append("")
        lines.append(f";// 自动生成 - 科技树配置文件")
        lines.append(f";// 阵营: {faction}")
        lines.append(f";// 单位数量: {len(units)}")
        lines.append("")
        
        # 按类型分组
        techs = [u for u in units if u.unit_type == "tech"]
        doctrines = [u for u in units if "doctrine" in u.name.lower() or "sov_" in u.name.lower()]
        radios = [u for u in units if "radio" in u.name.lower()]
        others = [u for u in units if u.unit_type not in ["tech", "custom"]]
        
        # 过滤掉 doctrines 中已经在 techs 中的
        doctrines = [u for u in doctrines if u not in techs]
        # 过滤掉 radios 中已经在 techs 或 doctrines 中的
        radios = [u for u in radios if u not in techs and u not in doctrines]
        # ✅ AI 生成: others 排除已出现在前三个分组中的单位（用 name 判重，Unit 不可 hash）
        already_grouped_names = {u.name for u in techs + doctrines + radios}
        others = [u for u in others if u.name not in already_grouped_names]
        
        # 输出 tech 类型（reinforcement, defense 等）
        if techs:
            lines.append(";// REINFORCEMENTS & TECH LEVELS")
            for unit in techs:
                line = self._format_tech_line(unit)
                lines.append(line)
            lines.append("")
        
        # 输出 doctrine 类型
        if doctrines:
            lines.append(";// DOCTRINE TECHS")
            for unit in doctrines:
                line = self._format_unit_line(unit, faction)
                lines.append(line)
            lines.append("")
        
        # 输出 radio 类型
        if radios:
            lines.append(";// RADIO & OFFMAP SUPPORTS")
            for unit in radios:
                line = self._format_unit_line(unit, faction)
                lines.append(line)
            lines.append("")
        
        # 输出其他单位
        if others:
            lines.append(";//---UNITS---")
            for unit in others:
                line = self._format_unit_line(unit, faction)
                lines.append(line)
            lines.append("")
        
        # 写入文件（原子写 + 备份）
        content = "\n".join(lines)
        self._write_file_safely(output_path, content)
        
        print(f"已导出到: {output_path}")
        return output_path
    
    def _export_with_original_format(self, units: List[Unit], faction: str, output_path: str, original_file_path: str):
        """
        保留原始格式和注释的导出
        
        Args:
            units: 单位列表
            faction: 阵营名称
            output_path: 输出文件路径
            original_file_path: 原始文件路径
        """
        try:
            # 读取原始文件
            with open(original_file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # 创建单位名称到 Unit 对象的映射
            units_dict = {unit.name: unit for unit in units}
            
            # 处理每一行
            result_lines = []
            # ✅ AI 生成: positions 块状态机。{positions ...} 块内的行形如
            # {"unit_name" x y}，会被 _parse_unit_line 误判为单位定义行；
            # 若该单位恰在 units_dict（画布上存在），会被重写为完整的
            # requires/costs/position 行，破坏 positions 块语法。
            # 进入该块后所有行原样保留，直到顶格的闭合 '}' 为止。
            in_positions_block = False
            for line in original_lines:
                stripped = line.strip()
                
                if in_positions_block:
                    result_lines.append(line.rstrip('\n'))
                    if stripped == '}':
                        in_positions_block = False
                    continue
                
                if stripped.startswith('{positions'):
                    in_positions_block = True
                    result_lines.append(line.rstrip('\n'))
                    continue
                
                # 检查是否是注释行或空行，直接保留
                if stripped.startswith(';') or stripped.startswith('//') or not stripped:
                    result_lines.append(line.rstrip('\n'))
                    continue
                
                # 检查是否是单位定义行
                unit_match = self._parse_unit_line(stripped)
                if unit_match:
                    unit_name = unit_match['name']
                    
                    # 如果该单位在我们的列表中，更新它
                    if unit_name in units_dict:
                        unit = units_dict[unit_name]
                        new_line = self._format_unit_line_preserve_style(unit, line)
                        result_lines.append(new_line)
                        # 从字典中移除，标记为已处理
                        del units_dict[unit_name]
                    else:
                        # 单位不在当前列表中，保留原样（可能是被删除的单位）
                        result_lines.append(line.rstrip('\n'))
                else:
                    # 非单位行（如 IconGap），保留原样
                    result_lines.append(line.rstrip('\n'))
            
            # 添加新增的单位（不在原始文件中的）
            if units_dict:
                result_lines.append("")
                result_lines.append(f";// 新增单位")
                for unit in units_dict.values():
                    new_line = self._format_unit_line_new(unit)
                    result_lines.append(new_line)
            
            # 写入文件（原子写 + 备份）
            content = "\n".join(result_lines)
            self._write_file_safely(output_path, content)
            
            print(f"已导出到: {output_path} (保留原始格式)")
            return output_path
            
        except Exception as e:
            print(f"保留格式导出失败: {e}，使用简单导出")
            # 如果失败，回退到简单导出
            return self._export_simple(units, faction, output_path)
    
    def _parse_unit_line(self, line: str) -> dict:
        """
        解析单位行，提取单位名称
        
        Args:
            line: 单位行字符串
            
        Returns:
            包含 name 的字典，如果不是单位行则返回 None
        """
        # 匹配 tech 格式: { tech "name" requires ... }
        tech_match = re.match(r'\{\s*tech\s+"([^"]+)"', line)
        if tech_match:
            return {'name': tech_match.group(1), 'is_tech': True}
        
        # 匹配普通单位格式: {"name" requires ... }
        unit_match = re.match(r'\{\s*"([^"]+)"', line)
        if unit_match:
            return {'name': unit_match.group(1), 'is_tech': False}
        
        return None
    
    def _format_unit_line_preserve_style(self, unit: Unit, original_line: str) -> str:
        """
        格式化单位行，保持原始行的样式（缩进、空格等）
        
        Args:
            unit: 单位对象
            original_line: 原始行字符串
            
        Returns:
            格式化后的行
        """
        # 提取原始行的前导空白
        leading_whitespace = ''
        for char in original_line:
            if char in [' ', '\t']:
                leading_whitespace += char
            else:
                break
        
        # 判断是否是 tech 类型（优先使用 unit.unit_type）
        is_tech = unit.unit_type == 'tech'
        
        # 如果 unit_type 为空，尝试从原始行判断
        if not is_tech:
            is_tech = '{ tech ' in original_line
        
        # 获取 requires 字符串
        requires_list = unit.requires if isinstance(unit.requires, list) else ([unit.requires] if unit.requires else [])
        # ✅ 支持多父节点：用空格连接
        requires_str = ' '.join(requires_list) if requires_list else ""
        
        # 格式化位置
        pos_x_str = f"{unit.position_x:g}"
        pos_y_str = f"{unit.position_y:g}"
        
        if is_tech:
            # Tech 格式: { tech "name" requires "req" costs N position x y}
            new_line = f'{leading_whitespace}{{ tech "{unit.name}"\t\trequires "{requires_str}"\t\tcosts {unit.costs}  position {pos_x_str} {pos_y_str}}}'
        else:
            # 普通单位格式: {"name" requires "req" costs N position x y}
            new_line = f'{leading_whitespace}{{"{unit.name}"\t\trequires "{requires_str}"\t\t\t\tcosts {unit.costs}  position {pos_x_str} {pos_y_str}}}'
        
        return new_line
    
    def _format_unit_line_new(self, unit: Unit) -> str:
        """
        格式化新单位的行（没有原始行参考）
        
        Args:
            unit: 单位对象
            
        Returns:
            格式化后的行
        """
        requires_list = unit.requires if isinstance(unit.requires, list) else ([unit.requires] if unit.requires else [])
        # ✅ AI 生成: 新单位支持多父节点导出（空格连接），不再只取第一个
        requires_str = ' '.join(requires_list) if requires_list else ""
        
        pos_x_str = f"{unit.position_x:g}"
        pos_y_str = f"{unit.position_y:g}"
        
        # 根据 unit_type 决定格式
        if unit.unit_type == 'tech':
            return f'\t{{ tech "{unit.name}"\t\trequires "{requires_str}"\t\tcosts {unit.costs}  position {pos_x_str} {pos_y_str}}}'
        else:
            return f'\t{{"{unit.name}"\t\trequires "{requires_str}"\t\t\t\tcosts {unit.costs}  position {pos_x_str} {pos_y_str}}}'
