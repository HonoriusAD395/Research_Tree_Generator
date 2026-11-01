# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
Research Tree Generator 单元测试包
Unit test package for Research Tree Generator
"""

import os
import shutil
import uuid

# ✅ AI 生成: 测试临时根目录。
# 默认 tempfile 会落到系统 TEMP 目录（如 %TEMP%\...），
# 在受限/沙箱环境下该系统目录可能不可写（sandbox 拒绝 workspace 外的写操作），
# 导致文件写盘类用例报 PermissionError 而非真实断言失败。
# 这里把临时根目录解析到项目内，跟随工作区可写性；仍可用环境变量覆盖。
_TEMP_ROOT = os.environ.get(
    "RTG_TEST_TMP",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".test_tmp"),
)


def make_test_dir(prefix: str = "rtg_") -> str:
    """创建一个测试用临时目录（位于项目内，随工作区可写）。

    注意：不要改用 tempfile.mkdtemp()。mkdtemp 会把目录权限收紧为 0700，
    在受限 ACL（如沙箱/受管环境）下反而导致后续写入被拒绝；
    os.makedirs 使用默认继承权限，行为更可预期。
    """
    os.makedirs(_TEMP_ROOT, exist_ok=True)
    path = os.path.join(_TEMP_ROOT, f"{prefix}{uuid.uuid4().hex[:12]}")
    os.makedirs(path, exist_ok=True)
    return path


def remove_test_dir(path: str) -> None:
    """清理测试临时目录；清理失败不应影响测试结论。"""
    shutil.rmtree(path, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────────
# 合成样例数据 / Synthetic sample data
#
# ⚠️ 为什么由代码生成而不是提交现成的 .set 文件：
#    真实的 mod 配置文件属于第三方作品，不适合随开源仓库分发。
#    下面这些是**为本项目测试自建的最小样例**，只保留解析器需要的语法结构，
#    不含任何游戏资源或第三方 mod 的内容。
# ──────────────────────────────────────────────────────────────────────

SAMPLE_RESEARCH_NAME = "unit_research_sample.set"
SAMPLE_UNITS_NAME = "units_sample_era1960.set"

SAMPLE_RESEARCH_SET = """{IconGap 30}

;// {"Squad/unit/entity/tech name" requires "other squad/unit/entity/tech" Position column, row}

;// REINFORCEMENTS & DEFENSE LEVELS
	{ tech "reinforcement_stage_1"		requires ""		costs 0  position 0.4 0.1}
	{ tech "reinforcement_stage_2"		requires "reinforcement_stage_1"		costs 1  position 1.4 0.1}
	{ tech "reinforcement_stage_3"		requires "reinforcement_stage_1 reinforcement_stage_2"		costs 2  position 2.4 0.1}

;// DOCTRINE TECHS
	{ tech "defense_level_1"		requires "reinforcement_stage_2"		costs 1  position 7 0.1}
	{ tech "defense_level_2"		requires "reinforcement_stage_3 defense_level_1"		costs 5  position 8 0.1}

;// RADIO & OFFMAP SUPPORTS
	{"sample_barrage_light"		requires "reinforcement_stage_2"				costs 2  position 1.7 36.2}
	{"sample_barrage_medium"		requires "sample_barrage_light"				costs 3  position 2.6 36.2}
"""

SAMPLE_UNITS_SET = """;SDL

;////////////////// INSTRUCTIONS //////////////////
;Buttons go as follows, displayed in-game in this order:
; inf1       - infantry squads
; vehicles   - vehicles, armoured cars, supplies
; TEMP: 测试用最小样例，仅保留解析器需要的字段
;//////////////////////////////////////////////////

;_________________________________________________
;|        	Default Strategic Abilities           |
;|________________________________________________|

;//Artillery Supports

{"sample_barrage_light"
	("offmap_support" side(sov) min_stage(1) max_stage(99) cw(0) cp(0) vehicle(sample_gun) crew(sample_crew:0))
	{cost 1}{action "airstrike:sample_light"}{condition "sample_radio"}
}

{"sample_squad_vehicle"
	("squad_vehicle" side(sov) period(era1960) min_stage(1))
	{cost 12}{action "spawn:sample_squad_vehicle"}
}

("squad_with4types_conquest" side(sov) name(sample_conscript_con) min_stage(1) max_stage(99))

("squad_with4types_conquest_warsaw" nation(gdr) side(sov) name(sample_kda) min_stage(1) max_stage(99))
"""


def write_sample_sets(directory: str) -> tuple:
    """把合成样例写入目录，返回 (research_path, units_path)。

    文件名刻意包含 `unit_research` / `units` 前缀，因为 parser.parse_file()
    依据文件名判断格式（见 parser._extract_faction 与 parse_file）。
    """
    os.makedirs(directory, exist_ok=True)
    research = os.path.join(directory, SAMPLE_RESEARCH_NAME)
    units = os.path.join(directory, SAMPLE_UNITS_NAME)
    with open(research, "w", encoding="utf-8", newline="\n") as f:
        f.write(SAMPLE_RESEARCH_SET)
    with open(units, "w", encoding="utf-8", newline="\n") as f:
        f.write(SAMPLE_UNITS_SET)
    return research, units
