@echo off
REM SPDX-FileCopyrightText: 2026 HonoriusAD395
REM SPDX-License-Identifier: MIT
REM AI-Generated: 本脚本由 AI 编码助手生成，经人工审核。详见 NOTICE 文件。

chcp 65001 >nul
echo ========================================
echo   科技树生成器 - Gates of Hell
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 正在检查依赖...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动程序...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)
