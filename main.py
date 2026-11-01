# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
科技树生成器 - 主程序入口
Tech Tree Generator for Gates of Hell
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from src.console import configure_stdio
from src.main_window import MainWindow


def main():
    """应用程序入口"""
    # ✅ 先把标准输出切到 UTF-8：Windows 控制台默认是 GBK/cp1252，
    # 直接输出中文会抛 UnicodeEncodeError，导致导出/解析流程因一行日志崩溃。
    configure_stdio()

    # 设置全局异常处理（防止闪退）
    def exception_hook(exc_type, exc_value, exc_traceback):
        import traceback
        error_msg = f"{exc_type.__name__}: {exc_value}\n\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}"
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, '程序错误', error_msg)
    
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    app.setApplicationName("科技树生成器")
    app.setApplicationVersion('2.2.2')
    app.setOrganizationName("GoH Modding Tools")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
