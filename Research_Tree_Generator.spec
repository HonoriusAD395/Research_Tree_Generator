# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # ✅ 2026-09 清理：过时文档（QUICKSTART.md / 使用说明.md）已删除，同步从打包数据中移除
        # ✅ 2026-11 开源整理：LONG_TERM_MEMORY.md 是内部开发知识库，不随发布包分发
        ('README.md', '.'),
        ('INSTALL.md', '.'),
        ('src/translations', 'translations'),  # 翻译资源文件
    ],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'encodings'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Research_Tree_Generator_v2.2.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Research_Tree_Generator_v2.2.2',
)
