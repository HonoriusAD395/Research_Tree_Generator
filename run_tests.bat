@echo off
REM SPDX-FileCopyrightText: 2026 HonoriusAD395
REM SPDX-License-Identifier: MIT
REM AI-Generated: 本脚本由 AI 编码助手生成，经人工审核。详见 NOTICE 文件。

chcp 65001 >nul
REM 运行单元测试 / Run unit tests
echo ========================================
echo Running Unit Tests
echo 运行单元测试
echo ========================================
echo.

cd /d "%~dp0"

REM 统一用 PYTHONUTF8 避免 Windows 控制台 GBK 下 emoji/中文输出报错
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo [1/5] 多父节点解析/导出 (test_multi_parent_nodes.py, 20 tests)...
python -m unittest tests.test_multi_parent_nodes
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Multi-parent tests FAILED! / 多父节点测试失败！
    echo ========================================
    pause
    exit /b 1
)
echo.

echo [2/5] 撤销与导出逻辑 (test_undo_export.py, 20 tests)...
python -m unittest tests.test_undo_export
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Undo/export tests FAILED! / 撤销/导出测试失败！
    echo ========================================
    pause
    exit /b 1
)
echo.

echo [3/5] v2.2.1 修复项回归 (test_fixes_v221.py, 61 tests)...
python -m unittest tests.test_fixes_v221
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo v2.2.1 regression tests FAILED! / v2.2.1 回归测试失败！
    echo ========================================
    pause
    exit /b 1
)
echo.

echo [4/5] v2.2.2 修复项回归 (test_fixes_v222.py, 34 tests)...
python -m unittest tests.test_fixes_v222
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo v2.2.2 regression tests FAILED! / v2.2.2 回归测试失败！
    echo ========================================
    pause
    exit /b 1
)
echo.

echo [5/5] 模块导入 + 解析器 + i18n 自检 (test_imports.py)...
python test_imports.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Self-check FAILED! / 自检失败！
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo All tests passed! (135 unit tests + self-check)
echo 所有测试通过！(135 个单元测试 + 自检)
echo ========================================
echo.
pause
