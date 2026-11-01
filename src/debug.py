# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""调试工具"""
import os

from src.console import safe_print

DEBUG = False
if os.environ.get("DEBUG") == "1": DEBUG = True
def debug_print(*a, **k):
    # ✅ 走 safe_print：控制台编码不兼容时不得抛异常
    if DEBUG: safe_print(*a, **k)
# ✅ AI 生成: 供调用方提前短路，避免 f-string 在 DEBUG=False 时仍被求值
# 用法: if DEBUG: debug_print(f"...{expensive}...")
# 注意必须写成 `if debug.DEBUG:` 而非 `if DEBUG:`，否则 import 期快照不会随环境变量更新
