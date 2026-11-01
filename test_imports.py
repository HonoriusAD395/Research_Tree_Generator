# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
快速自检脚本 / Quick self-check

验证所有模块可导入，并用仓库中真实存在的示例 .set 文件跑一遍解析器。
可安全用于 CI（无阻塞式 input()，失败以退出码 1 结束）。
"""

import io
import os
import sys

# ✅ 修复：Windows 控制台默认 GBK，输出 ✅/emoji 会抛 UnicodeEncodeError
for _stream in ("stdout", "stderr"):
    _s = getattr(sys, _stream, None)
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ✅ 修复：覆盖全部 src 模块（原实现漏了 undo_manager / i18n / portrait_manager / debug）
MODULES = [
    ('PyQt5', 'PyQt5 核心库'),
    ('src.parser', '文件解析器'),
    ('src.exporter', '文件导出器'),
    ('src.undo_manager', '撤销管理器'),
    ('src.i18n', '国际化'),
    ('src.debug', '调试工具'),
    ('src.portrait_manager', '头像管理器'),
    ('src.unit_list_panel', '单位列表面板'),
    ('src.tech_tree_canvas', '科技树画布'),
    ('src.property_panel', '属性编辑面板'),
    ('src.main_window', '主窗口'),
]

# 解析器测试改用 tests/__init__.py 在临时目录生成的合成样例，
# 仓库内不再存放任何第三方 mod 的 .set 文件。


def test_imports() -> bool:
    """测试所有模块导入"""
    print("=" * 50)
    print("  科技树生成器 - 模块导入测试")
    print("=" * 50)
    print()

    success_count = 0
    fail_count = 0

    for module_name, description in MODULES:
        try:
            __import__(module_name)
            print(f"✅ {description:20} [{module_name}]")
            success_count += 1
        except Exception as e:                      # ✅ 修复：原只捕 ImportError，其他异常直接崩溃脚本
            print(f"❌ {description:20} [{module_name}]")
            print(f"   错误: {type(e).__name__}: {e}")
            fail_count += 1

    print()
    print("=" * 50)
    print(f"  测试结果: {success_count} 成功, {fail_count} 失败")
    print("=" * 50)

    if fail_count:
        print()
        print("⚠️  检测到缺失的依赖，请运行:")
        print("   pip install -r requirements.txt")
        return False

    print()
    print("🎉 所有模块导入成功！可以运行 main.py 启动程序")
    return True


def test_parser() -> bool:
    """用合成样例测试解析器与合并逻辑

    ⚠️ 样例由 tests/__init__.py 在临时目录中生成，仓库内不存放任何第三方 mod 文件。
    """
    print()
    print("=" * 50)
    print("  解析器功能测试")
    print("=" * 50)
    print()

    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from tests import make_test_dir, remove_test_dir, write_sample_sets
        from src.parser import SetFileParser, Unit

        tmp = make_test_dir()
        try:
            sample_research, sample_units = write_sample_sets(tmp)
            parser = SetFileParser()
            data = parser.parse_file(sample_research)

            print(f"📂 解析合成样例: {os.path.basename(sample_research)}")
            print(f"   阵营: {data['faction']}")
            print(f"   节点数量: {len(data['units'])}")
            print()
            for unit in data['units'][:3]:
                print(f"   - {unit['name']} (类型: {unit['unit_type']!r}, "
                      f"costs: {unit['costs']}, requires: {unit['requires']})")

            assert data['units'], "解析结果为空"
            assert all(isinstance(u['requires'], list)
                       for u in data['units']), "requires 必须是列表"

            # units_*.set 与合并逻辑
            units_data = parser.parse_file(sample_units)
            print()
            print(f"📂 解析合成样例: {os.path.basename(sample_units)}")
            print(f"   阵营: {units_data['faction']}")
            print(f"   单位数量: {len(units_data['units'])}")
            merged = parser.merge_units(
                [Unit.from_dict(u) for u in units_data['units']],
                [Unit.from_dict(u) for u in data['units']],
            )
            print(f"   合并后: {len(merged)} 个单位")
            assert merged, "合并结果为空"

            # 多父节点往返
            assert any(len(u['requires']) > 1 for u in data['units']), \
                "样例应包含多父节点，否则测试无意义"
        finally:
            remove_test_dir(tmp)

        print()
        print("✅ 解析器测试通过")
        return True

    except Exception as e:
        print(f"❌ 解析器测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_i18n() -> bool:
    """验证两种语言键集完全对齐"""
    print()
    print("=" * 50)
    print("  国际化键集一致性测试")
    print("=" * 50)
    print()

    try:
        import json
        from src.i18n import get_i18n

        base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'src', 'translations')
        zh = json.load(io.open(os.path.join(base, 'zh_CN.json'), encoding='utf-8'))
        en = json.load(io.open(os.path.join(base, 'en_US.json'), encoding='utf-8'))

        only_zh = sorted(set(zh) - set(en))
        only_en = sorted(set(en) - set(zh))

        print(f"   zh_CN.json: {len(zh)} 键")
        print(f"   en_US.json: {len(en)} 键")
        if only_zh:
            print(f"   ⚠️ 仅中文: {only_zh[:5]}")
        if only_en:
            print(f"   ⚠️ 仅英文: {only_en[:5]}")

        assert not only_zh and not only_en, "两种语言键集不一致"
        assert get_i18n().tr('全部') is not None

        print()
        print("✅ 国际化键集一致")
        return True

    except Exception as e:
        print(f"❌ 国际化测试失败: {type(e).__name__}: {e}")
        return False


if __name__ == '__main__':
    ok_imports = test_imports()
    ok_parser = test_parser() if ok_imports else False
    ok_i18n = test_i18n() if ok_imports else False

    all_ok = ok_imports and ok_parser and ok_i18n
    print()
    print("=" * 50)
    print(f"  总体结果: {'✅ 全部通过' if all_ok else '❌ 存在失败项'}")
    print("=" * 50)
    # ✅ 修复：去掉阻塞式 input()，改为退出码，便于 CI 使用
    sys.exit(0 if all_ok else 1)
