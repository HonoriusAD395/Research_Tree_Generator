# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
控制台输出安全封装 / Console output safety

为什么需要 / Why this exists
---------------------------
Windows 控制台默认编码可能是 GBK (cp936) 或 cp1252。直接 ``print()`` 中文会抛
``UnicodeEncodeError``，让**导出/解析流程因为一行日志而崩溃**。打包为 windowed
exe 时 ``sys.stdout`` 还可能为 ``None``，``print()`` 会再抛 ``AttributeError``。

Windows consoles default to GBK (cp936) or cp1252. A plain ``print()`` of non-ASCII
text raises ``UnicodeEncodeError``, crashing the export/parse flow over a log line.
In a windowed PyInstaller build ``sys.stdout`` may also be ``None``.

``safe_print()`` 统一兜住这两种情况：输出失败只影响日志，绝不影响主流程。
``safe_print()`` contains both cases: a failed write must never break the main flow.
"""

import sys


def configure_stdio() -> None:
    """尽力把标准输出切到 UTF-8 并容错，失败也不抛出。"""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def safe_print(*args, **kwargs) -> None:
    """在编码不兼容或 stdout 缺失时也不会抛异常的 print。"""
    stream = kwargs.get("file", sys.stdout)
    if stream is None:
        return

    try:
        print(*args, **kwargs)
        return
    except (UnicodeEncodeError, OSError, ValueError):
        pass

    # 退路：按目标流编码做有损转换后直接写
    try:
        encoding = getattr(stream, "encoding", None) or "utf-8"
        text = " ".join(str(a) for a in args)
        end = kwargs.get("end", "\n")
        stream.write(text.encode(encoding, "replace").decode(encoding, "replace") + end)
    except Exception:
        # 日志失败不得影响业务
        pass
