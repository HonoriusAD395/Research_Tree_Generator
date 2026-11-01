# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
文件解析器模块
负责解析 .set 文件并提取单位信息
支持 units_*.set 和 unit_research_*.set 格式
"""

import re
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class Unit:
    """单位数据类"""
    name: str
    unit_type: str = ""  # 单位类型，只有 ''（空）和 'tech'
    side: str = ""
    costs: int = 4  # 默认值为 4（不使用 units.set 中的 MP costs）
    position_x: float = 0.0
    position_y: float = 0.0
    requires: list = field(default_factory=list)  # 前置单位列表（支持多个父节点）
    raw_definition: str = ""
    deployed: bool = False  # 是否已部署到画布
    in_research: bool = True  # 是否在 unit_research 文件中（用于标记显示）
    period: str = ""  # 时期，如 era1960
    squad_type: str = ""  # 单位分类，从 units_*.set 的括号内提取（如 squad_vehicle、offmap_support）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Unit':
        """从字典创建（忽略未知字段，保持向后兼容）"""
        # 获取 Unit 类的所有字段名
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        # 只提取有效字段
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class SetFileParser:
    """.set 文件解析器"""
    
    def __init__(self):
        self.units: List[Unit] = []
        self.faction: str = ""
        
    def parse_file(self, filepath: str) -> Dict:
        """
        解析 .set 文件（自动识别格式）
        
        Args:
            filepath: 文件路径
            
        Returns:
            包含 faction 和 units 的字典
        """
        basename = os.path.basename(filepath)
        
        # 根据文件名自动识别格式
        if 'unit_research' in basename:
            return self.parse_research_file(filepath)
        else:
            return self.parse_units_file(filepath)
    
    def parse_units_file(self, filepath: str) -> Dict:
        """
        解析 units_*.set 文件（完整单位定义）
        
        Args:
            filepath: 文件路径
            
        Returns:
            包含 faction 和 units 的字典
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除注释
        content = self._remove_comments(content)
        
        # 提取阵营信息
        self.faction = self._extract_faction(filepath)
        
        # 解析单位定义
        self.units = self._parse_units_definitions(content)
        
        return {
            'faction': self.faction,
            'units': [unit.to_dict() for unit in self.units]
        }
    
    def parse_research_file(self, filepath: str) -> Dict:
        """
        解析 unit_research_*.set 文件（科技树结构）
        
        Args:
            filepath: 文件路径
            
        Returns:
            包含 faction 和 units 的字典
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除注释
        content = self._remove_comments(content)
        
        # 提取阵营信息
        self.faction = self._extract_faction(filepath)
        
        # 解析科技树
        self.units = self._parse_research_tree(content)
        
        return {
            'faction': self.faction,
            'units': [unit.to_dict() for unit in self.units]
        }
    
    def _remove_comments(self, content: str) -> str:
        """
        移除 .set 文件中的注释（分号开头的行）
        
        Args:
            content: 原始文件内容
            
        Returns:
            移除注释后的内容
        """
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 去除行首空白后检查是否以分号开头
            stripped = line.strip()
            if not stripped.startswith(';'):
                # 保留非注释行，包括空行
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_faction(self, filepath: str) -> str:
        """从文件名提取阵营信息"""
        basename = os.path.basename(filepath)
        
        # 尝试多种模式
        patterns = [
            # ✅ AI 生成: 用 [a-z]+ 只取第一个下划线前的阵营名。
            # 原 \w+ 会把 units_sov_era1960.set 解析成 faction="sov_era1960"（把时期当阵营），
            # 导致默认导出文件名变成 unit_research_sov_era1960.set
            r'units_([a-z]+)',
            r'unit_research_(\w+)\.set',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, basename)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _parse_units_definitions(self, content: str) -> List[Unit]:
        """
        解析 units 定义格式（完整单位信息）
        
        格式: {"unit_name"
            ("type" side(sov) period(era1960) ...)
            {cost 1}{action "..."}
        }
        """
        units = []
        
        # 找到所有 {" 开始的位置（不再要求紧跟括号）
        unit_def_starts = [m.start() for m in re.finditer(r'\{"', content)]
        
        for start_pos in unit_def_starts:
            # 找到块的结束位置（匹配对应的 }
            brace_count = 0
            in_string = False
            end_pos = start_pos
            
            for i in range(start_pos, len(content)):
                char = content[i]
                
                if char == '"' and (i == 0 or content[i-1] != '\\'):
                    in_string = not in_string
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
            
            if end_pos <= start_pos:
                continue
            
            full_block = content[start_pos:end_pos]
            
            # 检查是否有 not_for_player_sale
            if 'not_for_player_sale' in full_block:
                nps_match = re.search(r'not_for_player_sale\s+(\d+)', full_block)
                if nps_match and nps_match.group(1) == '1':
                    continue  # 跳过
            
            # 提取名称
            name_match = re.match(r'\{"([^"]+)"', full_block)
            if not name_match:
                continue
            
            name = name_match.group(1)
            
            # 检查是否已经添加过
            if any(u.name == name for u in units):
                continue
            
            # ✅ AI 生成: 从名称结束之后搜索 properties（避免名称中如 con(sov) 的括号被误匹配）
            name_end = name_match.end()
            props_match = re.search(r'\(([^)]+)\)', full_block[name_end:])
            if not props_match:
                continue
            
            properties = props_match.group(1)
            
            # ✅ AI 生成: 提取 squad_type（括号内第一个引号中的词，如 squad_vehicle、offmap_support）
            squad_type = ""
            squad_match = re.match(r'\s*"([^"]+)"', properties)
            if squad_match:
                squad_type = squad_match.group(1)
            
            # 提取 side
            side_match = re.search(r'side\((\w+)\)', properties)
            side = side_match.group(1) if side_match else ""
            
            # ✅ 关键：units_*.set 的单位类型永远为空，以 unit_research_*.set 为准
            unit_type = ""
            
            # 提取 period
            period_match = re.search(r'period\((\w+)\)', properties)
            period = period_match.group(1) if period_match else ""
            
            # 提取 cost（可能有多个 {cost ...} 块，取第一个）
            # 注意：units.set 中的 costs 是 MP 系统的值，不使用，默认设为 4
            costs = 4  # 默认值
            
            unit = Unit(
                name=name,
                side=side,
                unit_type=unit_type,
                costs=costs,
                period=period,
                squad_type=squad_type,
                in_research=False  # 默认不在 research 中
            )
            units.append(unit)
        
        # ✅ AI 生成: 解析 conquest 格式 — ("type" ... side(xxx) ... name(yyy) ...)
        # unit_name = name + (suffix)，优先用 nation，没有则用 side
        existing_names = {u.name for u in units}
        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped.startswith('("') or 'name(' not in stripped:
                continue
            
            squad_type = ''
            m = re.match(r'\("([^"]+)"', stripped)
            if m:
                squad_type = m.group(1)
            side_match = re.search(r'side\((\w+)\)', stripped)
            nation_match = re.search(r'nation\((\w+)\)', stripped)
            name_match = re.search(r'name\(([^)]+)\)', stripped)
            
            if not squad_type or not side_match or not name_match:
                continue
            
            side = side_match.group(1)
            suffix = side
            if nation_match:
                suffix = nation_match.group(1)
            
            name = name_match.group(1) + '(' + suffix + ')'
            
            if name in existing_names:
                continue
            
            unit = Unit(
                name=name,
                side=side,
                unit_type="",
                costs=4,
                squad_type=squad_type,
                in_research=False
            )
            units.append(unit)
            existing_names.add(name)
        
        return units
    
    def _parse_research_tree(self, content: str) -> List[Unit]:
        """
        解析 unit_research 科技树格式
        
        支持格式：
        1. unit_research 格式: { tech "name" requires "req" costs 1 position x y}
        2. unit_research 格式: {"name" requires "req" costs 1 position x y}
        """
        units = []
        
        # 模式 1: { tech "name" requires "req" costs 1 position x y}
        tech_pattern = r'\{\s*tech\s+"([^"]+)"\s+requires\s+"([^"]*)"\s+costs\s+(\d+(?:\.\d+)?)\s+position\s+([\d.]+)\s+([\d.]+)\s*\}'
        for match in re.finditer(tech_pattern, content):
            req = match.group(2).strip()
            # ✅ 支持多父节点：空格分隔
            requires_list = [r.strip() for r in req.split() if r.strip()] if req else []
            unit = Unit(
                name=match.group(1),
                requires=requires_list,
                costs=int(float(match.group(3))),
                position_x=float(match.group(4)),
                position_y=float(match.group(5)),
                unit_type="tech",
                in_research=True
            )
            units.append(unit)
        
        # 模式 2: {"name" requires "req" costs 1 position x y}
        # ✅ 关键：非 tech 关键字的单位类型为空字符串
        unit_pattern = r'\{\s*"([^"]+)"\s+requires\s+"([^"]*)"\s+costs\s+(\d+(?:\.\d+)?)\s+position\s+([\d.]+)\s+([\d.]+)\s*\}'
        for match in re.finditer(unit_pattern, content):
            name = match.group(1)
            # 检查是否已经添加过（避免重复）
            if not any(u.name == name for u in units):
                req = match.group(2).strip()
                # ✅ 支持多父节点：空格分隔
                requires_list = [r.strip() for r in req.split() if r.strip()] if req else []
                unit = Unit(
                    name=name,
                    requires=requires_list,
                    costs=int(float(match.group(3))),
                    position_x=float(match.group(4)),
                    position_y=float(match.group(5)),
                    unit_type="",  # ✅ 非 tech 类型为空
                    in_research=True
                )
                units.append(unit)
        
        return units
    
    def merge_units(self, units_list: List[Unit], research_list: List[Unit]) -> List[Unit]:
        """
        合并两个单位列表
        
        Args:
            units_list: units_*.set 中的单位（完整信息）
            research_list: unit_research_*.set 中的单位（科技树结构）
            
        Returns:
            合并后的单位列表
        """
        # 创建字典便于查找
        units_dict = {u.name: u for u in units_list}
        
        # 标记哪些单位在 research 中
        research_names = set()
        
        # 处理 research 中的单位
        for research_unit in research_list:
            research_names.add(research_unit.name)
            
            if research_unit.name in units_dict:
                # 单位已存在，更新位置和 requires 信息
                existing = units_dict[research_unit.name]
                existing.position_x = research_unit.position_x
                existing.position_y = research_unit.position_y
                existing.requires = research_unit.requires
                # ✅ 关键：单位类型以 unit_research_*.set 为准，覆盖 units.set 的空类型
                existing.unit_type = research_unit.unit_type
                # 使用 research.set 中的 costs（科技树节点 costs），覆盖 units.set 的默认值 4
                existing.costs = research_unit.costs
                existing.in_research = True
                existing.deployed = True  # 在 research 中的单位自动部署
            else:
                # 单位不存在，自动创建（只创建名称）
                research_unit.in_research = True
                research_unit.deployed = True
                units_dict[research_unit.name] = research_unit
        
        # 标记不在 research 中的单位
        for unit in units_dict.values():
            if unit.name not in research_names:
                unit.in_research = False
        
        return list(units_dict.values())
    
    def add_custom_unit(self, name: str) -> Unit:
        """
        手动添加自定义单位
        
        Args:
            name: 单位名称
            
        Returns:
            创建的 Unit 对象
        """
        # ✅ 新建单位类型为空
        unit = Unit(name=name, unit_type="")
        self.units.append(unit)
        return unit
    
    def save_to_json(self, filepath: str):
        """保存解析结果为 JSON"""
        data = {
            'faction': self.faction,
            'units': [unit.to_dict() for unit in self.units]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"已保存到: {filepath}")
    
    def load_from_json(self, filepath: str) -> Dict:
        """从 JSON 加载数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.faction = data['faction']
        self.units = [Unit.from_dict(u) for u in data['units']]
        
        return data
