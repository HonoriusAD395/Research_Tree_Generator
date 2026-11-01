# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
主窗口类
包含菜单栏、工具栏和主要布局
"""

import os
import re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QToolBar, QAction, QActionGroup,
    QFileDialog, QMessageBox, QLabel, QInputDialog, QShortcut,
    QDialog, QLineEdit, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QPen, QColor, QKeySequence

from src.unit_list_panel import UnitListPanel
from src.tech_tree_canvas import TechTreeCanvas
from src.property_panel import PropertyPanel
from src.parser import SetFileParser, Unit
from src.exporter import SetFileExporter
from src.undo_manager import UndoManager, UndoAction, UndoActionType
from src import debug
from src.debug import debug_print
from src.i18n import tr, i18n


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据
        self.parser = SetFileParser()
        self.exporter = SetFileExporter()
        self.research_file = None  # unit_research_*.set 文件路径
        self.units = []  # units_*.set 中的单位
        self.research_units = []  # unit_research_*.set 中的单位
        self.all_units = []  # 合并后的单位列表
        self.faction = ""
        
        # 初始化撤销管理器（最多50步）
        self.undo_manager = UndoManager(max_undo_steps=50)
        
        # 标记是否有未保存的更改
        self.has_unsaved_changes = False
        
        # 注册 Ctrl+Z 全局快捷键（QShortcut 不需要焦点）
        self.undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        self.undo_shortcut.activated.connect(self.perform_undo)
        
        # 注册 Ctrl+Y 全局快捷键（重做）
        # ✅ AI 生成: 恢复重做功能（v2.2.2），QShortcut 不需要焦点
        self.redo_shortcut = QShortcut(QKeySequence('Ctrl+Y'), self)
        self.redo_shortcut.activated.connect(self.perform_redo)
        
        # 初始化 UI
        self.init_ui()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_central_widget()
        
        # 设置窗口属性
        self.setWindowTitle(tr("科技树生成器") + " - Gates of Hell")
        self.setGeometry(100, 100, 1400, 900)
        
    def init_ui(self):
        """初始化 UI 样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QMenuBar {
                font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                font-size: 12px;
            }
            QMenuBar::item {
                font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                font-size: 12px;
            }
            QToolBar {
                background-color: #3c3f41;
                border-bottom: 1px solid #555;
                spacing: 5px;
                padding: 5px;
                font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                font-size: 12px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 5px;
                color: #bbbbbb;
                font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                font-size: 12px;
            }
            QToolButton:hover {
                background-color: #4e5254;
                border: 1px solid #6a6e71;
            }
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #3c3f41;
                color: #bbbbbb;
                border-bottom: 1px solid #555;
            }
            QMenuBar::item:selected {
                background-color: #4e5254;
            }
            QMenu {
                background-color: #3c3f41;
                color: #bbbbbb;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #4e5254;
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu(tr('文件(&F)'))
        
        # 导入 units.set 文件
        import_units_action = QAction(tr('导入 units_*.set 文件(&U)'), self)
        import_units_action.setShortcut('Ctrl+U')
        import_units_action.setStatusTip(tr('导入单位定义文件'))
        import_units_action.triggered.connect(self.import_units_file)
        file_menu.addAction(import_units_action)
        
        # 导入 unit_research.set 文件
        import_research_action = QAction(tr('导入 unit_research_*.set 文件(&R)'), self)
        import_research_action.setShortcut('Ctrl+R')
        import_research_action.setStatusTip(tr('导入科技树文件'))
        import_research_action.triggered.connect(self.import_research_file)
        file_menu.addAction(import_research_action)
        
        # 新建科技树
        new_research_action = QAction(tr('新建科技树(&N)'), self)
        new_research_action.setShortcut('Ctrl+N')
        new_research_action.setStatusTip(tr('创建新的科技树'))
        new_research_action.triggered.connect(self.new_research_tree)
        file_menu.addAction(new_research_action)
        
        # 清空所有数据
        clear_all_action = QAction(tr('清空所有数据(&C)'), self)
        clear_all_action.setShortcut('Ctrl+Shift+C')
        clear_all_action.setStatusTip(tr('清空导入的 units、research 和画布内容'))
        clear_all_action.triggered.connect(self.clear_all_data)
        file_menu.addAction(clear_all_action)
        
        file_menu.addSeparator()
        
        save_action = QAction(tr('保存科技树配置(&S)'), self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip(tr('保存为 unit_research.set 文件'))
        save_action.triggered.connect(self.save_tech_tree)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(tr('退出(&X)'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip(tr('退出应用程序'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu(tr('编辑(&E)'))
        
        # 新建单位
        new_unit_action = QAction(tr('➕ 新建单位(&N)'), self)
        new_unit_action.setShortcut('Ctrl+N')
        new_unit_action.setStatusTip(tr('手动添加新单位'))
        new_unit_action.triggered.connect(self.add_new_unit)
        edit_menu.addAction(new_unit_action)
        
        edit_menu.addSeparator()
        
        undo_action = QAction(tr('撤销(&U)'), self)
        # 不在这里设置快捷键，避免与 QShortcut 冲突
        undo_action.setStatusTip(tr('撤销上一步操作'))
        undo_action.triggered.connect(self.perform_undo)
        edit_menu.addAction(undo_action)
        
        # ✅ AI 生成: 恢复重做菜单项（快捷键统一由 QShortcut 处理，避免双重触发）
        redo_action = QAction(tr('重做(&R)'), self)
        # 不在这里设置快捷键，避免与 QShortcut 冲突
        redo_action.setStatusTip(tr('重做上一步操作'))
        redo_action.triggered.connect(self.perform_redo)
        edit_menu.addAction(redo_action)
        
        # 语言切换菜单
        lang_menu = menubar.addMenu(tr('语言(&L)'))
        
        lang_group = QActionGroup(self)
        
        zh_action = QAction('简体中文', self, checkable=True)
        zh_action.setChecked(i18n.get_current_language() == 'zh_CN')
        zh_action.triggered.connect(lambda: self.switch_language('zh_CN'))
        lang_group.addAction(zh_action)
        lang_menu.addAction(zh_action)
        
        en_action = QAction('English', self, checkable=True)
        en_action.setChecked(i18n.get_current_language() == 'en_US')
        en_action.triggered.connect(lambda: self.switch_language('en_US'))
        lang_group.addAction(en_action)
        lang_menu.addAction(en_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu(tr('帮助(&H)'))
        
        about_action = QAction(tr('关于(&A)'), self)
        about_action.setStatusTip(tr('显示关于信息'))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar(tr('主工具栏'))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 导入按钮
        import_units_btn = QAction(tr('导入 units_*.set'), self)
        import_units_btn.setStatusTip(tr('导入 units.set 文件'))
        import_units_btn.triggered.connect(self.import_units_file)
        toolbar.addAction(import_units_btn)
        
        import_research_btn = QAction(tr('导入 unit_research_*.set'), self)
        import_research_btn.setStatusTip(tr('导入 unit_research.set 文件'))
        import_research_btn.triggered.connect(self.import_research_file)
        toolbar.addAction(import_research_btn)
        
        # 选择资源文件夹（头像）
        select_resource_btn = QAction(tr('📂 选择资源'), self)
        select_resource_btn.setToolTip(tr('选择 Mod 文件夹加载头像，先选主 Mod，再选子 Mod 可叠加'))
        select_resource_btn.setStatusTip(tr('选择 Mod 文件夹加载头像，先选主 Mod，再选子 Mod 可叠加'))
        select_resource_btn.triggered.connect(self.select_resource_folder)
        toolbar.addAction(select_resource_btn)
        
        self.resource_label = QLabel(tr('未选择资源'))
        self.resource_label.setStyleSheet("color: #888888; padding: 0 5px; font-size: 11px;")
        toolbar.addWidget(self.resource_label)
        
        new_research_btn = QAction(tr('新建科技树'), self)
        new_research_btn.setStatusTip(tr('创建新的科技树'))
        new_research_btn.triggered.connect(self.new_research_tree)
        toolbar.addAction(new_research_btn)
        
        clear_all_btn = QAction(tr('清空所有数据'), self)
        clear_all_btn.setStatusTip(tr('清空导入的 units、research 和画布内容'))
        clear_all_btn.triggered.connect(self.clear_all_data)
        toolbar.addAction(clear_all_btn)
        
        toolbar.addSeparator()
        
        # 保存按钮
        save_btn = QAction(tr('💾 保存'), self)
        save_btn.setStatusTip(tr('保存科技树配置'))
        save_btn.triggered.connect(self.save_tech_tree)
        toolbar.addAction(save_btn)
        
        toolbar.addSeparator()
        
        # 新建单位按钮
        new_unit_btn = QAction(tr('➕ 新建单位'), self)
        new_unit_btn.setStatusTip(tr('手动添加新单位'))
        new_unit_btn.triggered.connect(self.add_new_unit)
        toolbar.addAction(new_unit_btn)
        
        toolbar.addSeparator()
        
        # 缩放功能
        zoom_in_btn = QAction(tr('🔍+'), self)
        zoom_in_btn.setStatusTip(tr('放大画布'))
        zoom_in_btn.triggered.connect(lambda: self.tech_tree_canvas.scale_view(1.2))
        toolbar.addAction(zoom_in_btn)
        
        zoom_out_btn = QAction(tr('🔍-'), self)
        zoom_out_btn.setStatusTip(tr('缩小画布'))
        zoom_out_btn.triggered.connect(lambda: self.tech_tree_canvas.scale_view(1/1.2))
        toolbar.addAction(zoom_out_btn)
        
        reset_zoom_btn = QAction(tr('🔍0'), self)
        reset_zoom_btn.setStatusTip(tr('重置缩放比例'))
        reset_zoom_btn.triggered.connect(lambda: self.tech_tree_canvas.scale_view(1.0, reset=True))
        toolbar.addAction(reset_zoom_btn)
        
        toolbar.addSeparator()
        
        # 编辑/预览模式切换按钮
        self.preview_mode_btn = QAction(tr('预览模式'), self)
        self.preview_mode_btn.setStatusTip(tr('切换到预览模式，检测节点距离过近'))
        self.preview_mode_btn.setCheckable(True)
        self.preview_mode_btn.setChecked(False)  # 默认编辑模式
        self.preview_mode_btn.setEnabled(False)  # 默认禁用（无节点时）
        
        self.preview_mode_btn.triggered.connect(self.toggle_preview_mode)
        toolbar.addAction(self.preview_mode_btn)
        
        # 设置按钮样式（禁用状态更明显）
        preview_mode_widget = toolbar.widgetForAction(self.preview_mode_btn)
        if preview_mode_widget:
            preview_mode_widget.setStyleSheet("""
                QToolButton:disabled {
                    background-color: #444444;
                    color: #777777;
                    border: 1px solid #555555;
                    padding: 3px 8px;
                }
            """)
        
        toolbar.addSeparator()
    
    def create_central_widget(self):
        """创建中央部件（三栏布局）"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 状态栏（显示操作提示）
        self.status_bar = QLabel(tr("就绪 | 请先导入 units_*.set 文件"))
        self.status_bar.setStyleSheet("""
            background-color: #2d5a3d;
            color: #ffffff;
            padding: 4px 15px;
            font-size: 11px;
            border-bottom: 1px solid #1e3d2f;
        """)
        self.status_bar.setMaximumHeight(28)  # 限制最大高度
        main_layout.addWidget(self.status_bar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：单位列表面板
        self.unit_list_panel = UnitListPanel()
        splitter.addWidget(self.unit_list_panel)
        
        # 中间：科技树画布
        self.tech_tree_canvas = TechTreeCanvas()
        splitter.addWidget(self.tech_tree_canvas)
        
        # 右侧：属性面板
        self.property_panel = PropertyPanel()
        splitter.addWidget(self.property_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)  # 左侧
        splitter.setStretchFactor(1, 3)  # 中间（最大）
        splitter.setStretchFactor(2, 1)  # 右侧
        
        # 设置初始宽度
        splitter.setSizes([250, 800, 300])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 创建中央部件容器
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        
        # 设置为中央部件
        self.setCentralWidget(central_widget)
        
        # 连接信号槽
        self.connect_signals()
    
    def connect_signals(self):
        """连接信号槽"""
        # ✅ AI 生成: 移除 unit_dropped 死连接 —— 该信号在全仓库无 emit，
        # 实际拖拽路径走画布 dropEvent -> unit_dropped_at_position
        # （连带移除只被该连接引用的 add_unit_to_canvas 处理器）
        
        # 单位列表 -> 画布：双击添加单位到左上角
        self.unit_list_panel.unit_double_clicked.connect(self.add_unit_to_canvas_top_left)
        
        # 画布 -> 主窗口：从列表拖拽单位到画布（新方式，带位置信息）
        self.tech_tree_canvas.unit_dropped_at_position.connect(self.add_unit_to_canvas_at_position)
        
        # 画布 -> 属性面板：选中单位
        self.tech_tree_canvas.unit_selected.connect(self.property_panel.load_unit)
        
        # 画布 -> 属性面板：更新单位位置坐标
        self.tech_tree_canvas.unit_position_changed.connect(self.update_unit_position_in_panel)
        
        # 画布 -> 主窗口：批量单位位置变化（用于撤销）
        self.tech_tree_canvas.batch_unit_position_changed.connect(self.update_unit_position_in_panel)
        
        # 画布 -> 主窗口：单位属性变更（双击修改 Costs）
        if hasattr(self.tech_tree_canvas, 'unit_property_changed'):
            self.tech_tree_canvas.unit_property_changed.connect(self.on_unit_property_changed)

        # 属性面板 -> 画布：更新单位属性
        self.property_panel.unit_updated.connect(self.update_unit_in_canvas)
        
        # 画布 -> 主窗口：删除单位时恢复状态
        self.tech_tree_canvas.unit_deleted.connect(self.on_unit_deleted_from_canvas)
        
        # 画布 -> 主窗口：删除单位用于撤销
        self.tech_tree_canvas.unit_delete_for_undo.connect(self.on_unit_delete_for_undo)
        
        # 场景 -> 主窗口：设置 requires 关系
        self.tech_tree_canvas.scene.requires_set.connect(self.on_requires_set)
        
        # 画布 -> 主窗口：状态消息
        self.tech_tree_canvas.status_message.connect(self.update_status_bar)
        
        # 画布 -> 主窗口：节点数量变化（更新预览模式按钮状态）
        self.tech_tree_canvas.node_count_changed.connect(self.on_node_count_changed)
        
        # 初始化按钮状态（默认无节点，禁用预览模式按钮）
        self.on_node_count_changed(0)
    
    def update_status_bar(self, message: str):
        """更新状态栏消息"""
        self.status_bar.setText(message)
    
    def on_node_count_changed(self, count: int):
        """节点数量变化时更新预览模式按钮状态"""
        if count == 0:
            # 无节点：禁用按钮
            self.preview_mode_btn.setEnabled(False)
            # 如果当前在预览模式，强制切换回编辑模式
            if self.preview_mode_btn.isChecked():
                self.preview_mode_btn.setChecked(False)
        else:
            # 有节点：启用按钮
            self.preview_mode_btn.setEnabled(True)
    
    def switch_language(self, language_code: str):
        """切换界面语言并自动重启"""
        # ✅ AI 生成: 已是当前语言时直接返回（点选当前语言不应触发重启）
        if language_code == i18n.get_current_language():
            return
        
        # ✅ AI 生成: os.execl 会直接替换进程、不经过 closeEvent，
        # 有未保存更改时必须先处理，否则切换语言会静默丢数据
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                tr('保存更改'),
                tr('切换语言将重启程序，且当前科技树有未保存的更改。\n\n是否保存后再切换？'),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                if not self.save_tech_tree():
                    return  # 保存取消或失败，中止切换
            elif reply == QMessageBox.Cancel:
                return  # 用户取消切换
            # Discard：用户明确放弃更改，继续切换
        
        i18n.set_language(language_code)
        
        # 显示提示信息
        QMessageBox.information(
            self,
            tr('语言切换'),
            tr('语言已切换为 {lang}。\n程序将自动重启以应用更改。').format(
                lang=i18n.get_available_languages()[language_code]
            )
        )
        
        # 自动重启程序
        import sys
        import os
        python = sys.executable
        if getattr(sys, 'frozen', False):
            # ✅ AI 生成: PyInstaller 打包后直接重启自身
            # （原实现 os.execl(python, python, script) 会把 exe 路径
            #  当作多余参数传给新进程，行为脆弱）
            os.execl(python, python)
        else:
            # 开发环境：用当前解释器重新运行 main.py
            script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
            script = os.path.abspath(script)
            os.execl(python, python, script)
    
    def import_units_file(self):
        """导入 units_*.set 文件（完整单位定义，支持多文件同时选择，叠加模式）"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr('导入 units.set 文件（可多选）'),
            '',
            tr('SET Files (*.set);;All Files (*)')
        )        
        if not file_paths:
            return
        
        total_added = 0
        total_skipped = 0
        total_errors = 0
        total_files_imported = 0  # ✅ 只统计实际成功导入的 unit_*.set 文件数
        first_faction = None
        
        # 已存在的名称集合（用于去重）
        existing_names = {unit.name for unit in self.units}
        
        for file_path in file_paths:
            # 验证文件类型
            if not self._validate_units_file(file_path):
                QMessageBox.warning(
                    self,
                    tr('文件类型错误'),
                    tr('文件 "{file}" 不是有效的 units_*.set 文件！\n\n'
                    'units_*.set 文件应包含完整的单位定义（如 side、cost、action 等）。\n'
                    '请选择正确的 units 文件。').format(file=os.path.basename(file_path))
                )
                total_errors += 1
                continue
            
            try:
                data = self.parser.parse_units_file(file_path)
                new_units = [Unit.from_dict(u) for u in data['units']]
                new_faction = data['faction']
                
                if first_faction is None:
                    first_faction = new_faction
                
                added = 0
                skipped = 0
                for new_unit in new_units:
                    if new_unit.name not in existing_names:
                        self.units.append(new_unit)
                        existing_names.add(new_unit.name)
                        added += 1
                    else:
                        skipped += 1
                
                total_added += added
                total_skipped += skipped
                total_files_imported += 1
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr('导入失败'),
                    tr('解析文件 "{file}" 时出错:\n{error}').format(
                        file=os.path.basename(file_path), error=str(e))
                )
                total_errors += 1
        
        if total_added == 0 and total_errors > 0:
            return  # 没有任何文件成功导入
        
        # 更新 faction 和文件路径
        self.faction = first_faction or self.faction
        
        # 重新合并
        if self.research_units:
            self.all_units = self.parser.merge_units(self.units, self.research_units)
        else:
            # ✅ AI 生成: 取副本而非别名，避免 all_units 与 units 指向同一 list
            # （别名会导致 add_new_unit 双向 append 产生重复行）
            self.all_units = list(self.units)
        
        # 更新单位列表
        self.unit_list_panel.load_units(self.all_units)
        
        self.update_status_bar(tr('已导入 {files} 个文件: +{added} 个单位 | 跳过: {skipped} 个 | 总计: {total} 个单位 | 阵营: {faction}').format(
            files=total_files_imported, added=total_added, skipped=total_skipped, total=len(self.units), faction=self.faction))
        
        QMessageBox.information(
            self,
            tr('导入成功'),
            tr('成功导入 {files} 个文件\n'
            '新增: {added} 个单位\n'
            '跳过（已存在）: {skipped} 个\n'
            '当前总计: {total} 个单位\n'
            '阵营: {faction}').format(
                files=total_files_imported, added=total_added, skipped=total_skipped,
                total=len(self.units), faction=self.faction))
    
    def import_research_file(self):
        """导入 unit_research_*.set 文件（科技树结构，覆盖模式）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr('导入 unit_research.set 文件'),
            '',
            tr('SET Files (*.set);;All Files (*)')
        )
        
        if file_path:
            # 验证文件类型
            if not self._validate_research_file(file_path):
                QMessageBox.warning(
                    self,
                    tr('文件类型错误'),
                    tr('这不是有效的 unit_research_*.set 文件！\n\n'
                    'unit_research_*.set 文件应包含科技树结构（如 { tech "..." requires "..." costs X position X X}）。\n'
                    '请选择正确的 research 文件。')
                )
                return
            
            try:
                # 【关键】覆盖模式：直接替换旧的 research 数据
                data = self.parser.parse_research_file(file_path)
                self.research_units = [Unit.from_dict(u) for u in data['units']]
                self.faction = data['faction']
                self.research_file = file_path
                
                # 如果已经有 units 文件，合并两者
                if self.units:
                    self.all_units = self.parser.merge_units(self.units, self.research_units)
                else:
                    # 只有 research 文件：所有单位都应标记为已部署
                    for u in self.research_units:
                        u.deployed = True
                        u.in_research = True
                    self.all_units = list(self.research_units)
                
                # 更新单位列表
                self.unit_list_panel.load_units(self.all_units)
                
                # 根据 research 文件生成科技树
                self.generate_tech_tree_from_research()
                
                self.update_status_bar(tr('已覆盖导入科技树: {count} 个节点 | 阵营: {faction}').format(
                    count=len(self.research_units), faction=self.faction))
                
                QMessageBox.information(
                    self,
                    tr('覆盖导入成功'),
                    tr('成功导入 {count} 个科技树节点\n'
                    '阵营: {faction}\n\n'
                    '注意：已覆盖之前的科技树数据').format(
                        count=len(self.research_units), faction=self.faction)
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr('导入失败'),
                    tr('解析文件时出错:\n{error}').format(error=str(e))
                )
    
    def new_research_tree(self):
        """新建科技树（清空画布，让用户从零开始构建）"""
        if not self.units:
            QMessageBox.warning(
                self,
                tr('警告'),
                tr('请先导入 units_*.set 文件！')
            )
            return
        
        # 清空画布
        self.tech_tree_canvas.clear_canvas()
        
        # 清空 research 数据
        self.research_units = []
        self.research_file = None
        
        # 重置所有单位的 deployed 状态
        for unit in self.units:
            unit.deployed = False
            unit.position_x = 0.0
            unit.position_y = 0.0
            # ✅ AI 生成: requires 统一为空列表（原为 ""，与 parser 的 list 契约不一致）
            unit.requires = []
        
        # ✅ AI 生成: 取副本而非别名
        self.all_units = list(self.units)
        # ✅ AI 生成: 新建科技树后旧撤销记录已无意义，清空撤销/重做栈
        self.undo_manager.clear()
        
        # 更新单位列表
        self.unit_list_panel.load_units(self.all_units)
        
        self.update_status_bar(tr('新建科技树 | {count} 个单位可用 | 请拖拽单位到画布开始构建').format(count=len(self.units)))
        
        QMessageBox.information(
            self,
            tr('新建成功'),
            tr('已清空科技树\n\n请从左侧列表拖拽单位到画布\n右键节点选择前置单位设置依赖关系')
        )
    
    def clear_all_data(self):
        """一键清空所有数据（units、research、画布）"""
        # 确认对话框
        reply = QMessageBox.question(
            self,
            tr('确认清空'),
            tr('确定要清空所有数据吗？\n\n'
            '这将清除：\n'
            '• 所有导入的 units_*.set 数据\n'
            '• 所有导入的 unit_research_*.set 数据\n'
            '• 画布上的所有节点和连线\n\n'
            '此操作不可撤销！'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 1. 清空画布
                self.tech_tree_canvas.clear_canvas()
                
                # 2. 清空 units 数据
                self.units = []
                
                # 3. 清空 research 数据
                self.research_units = []
                self.research_file = None
                
                # 4. 清空合并后的数据
                self.all_units = []
                
                # 5. 重置 faction
                self.faction = ""
                
                # 6. 更新单位列表面板
                self.unit_list_panel.load_units([])
                
                # ✅ AI 生成: 数据已清空，旧撤销记录引用的是已不存在的单位，必须清栈
                # （原实现提示"不可撤销"却未调用 undo_manager.clear()，导致仍能撤销出幽灵单位）
                self.undo_manager.clear()
                self.has_unsaved_changes = False
                
                # 7. 更新状态栏
                self.update_status_bar(tr('已清空所有数据 | 请导入 units_*.set 文件开始'))
                
                # 8. 显示成功消息
                QMessageBox.information(
                    self,
                    tr('清空成功'),
                    tr('已清空所有数据\n\n'
                    '请重新导入 units_*.set 和 unit_research_*.set 文件')
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr('清空失败'),
                    tr('清空数据时出错:\n{error}').format(error=str(e))
                )
    
    def toggle_preview_mode(self, checked):
        """切换编辑/预览模式"""
        if checked:
            # 预览模式：启用重叠检测
            self.preview_mode_btn.setText(tr('编辑模式'))
            self.preview_mode_btn.setStatusTip(tr('切换到编辑模式，不检测节点距离'))
            self.status_bar.setText(tr("预览模式 | 节点距离过近时边框变红"))
        else:
            # 编辑模式：禁用重叠检测
            self.preview_mode_btn.setText(tr('预览模式'))
            self.preview_mode_btn.setStatusTip(tr('切换到预览模式，检测节点距离过近'))
            self.status_bar.setText(tr("编辑模式 | 自由编辑，不检测节点距离"))
        
        # 更新预览模式状态
        self.update_preview_mode_status()
    
    def update_preview_mode_status(self):
        """更新预览模式状态到画布"""
        is_preview_mode = self.preview_mode_btn.isChecked()
        self.tech_tree_canvas.set_preview_mode(is_preview_mode)
    
    def generate_tech_tree_from_research(self):
        """
        根据 unit_research 文件生成科技树（自动部署到画布）
        """
        # 清空画布
        self.tech_tree_canvas.clear_canvas()
        
        # 添加所有 research 中的单位到画布
        for unit in self.research_units:
            # 查找完整的单位信息（如果有）
            full_unit = None
            for u in self.units:
                if u.name == unit.name:
                    full_unit = u
                    break
            
            if full_unit:
                # 更新完整单位的位置和 requires
                full_unit.position_x = unit.position_x
                full_unit.position_y = unit.position_y
                full_unit.requires = unit.requires
                # 使用 research.set 中的 costs（科技树节点 costs），覆盖 units.set 的默认值 4
                full_unit.costs = unit.costs
                full_unit.deployed = True
                self.tech_tree_canvas.add_unit_node(full_unit)
            else:
                # units 中不存在，只创建名称
                unit.deployed = True
                self.tech_tree_canvas.add_unit_node(unit)
        
        # 更新连线
        self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
        
        # ✅ 新增：检查节点重叠情况（三格内）
        # ✅ AI 生成: 补上 DEBUG 短路，原实现在 DEBUG=False 时仍无条件组装 f-string
        if debug.DEBUG:
            debug_print(f"\n=== [MainWindow] 准备调用 check_node_overlaps() ===")
            debug_print(f"=== [MainWindow] 节点数量: {len(self.tech_tree_canvas.nodes)} ===")
        try:
            self.tech_tree_canvas.check_node_overlaps()
            if debug.DEBUG:
                debug_print(f"=== [MainWindow] check_node_overlaps() 调用完成 ===\n")
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"=== [MainWindow] ERROR: check_node_overlaps() 异常: {e} ===")
            import traceback
            traceback.print_exc()
    
    def add_unit_to_canvas_at_position(self, unit: Unit):
        """
        从单位列表拖拽添加单位到画布（带位置信息）
        
        Args:
            unit: 单位对象，position_x 和 position_y 已设置为鼠标释放位置
        """
        # 检查是否已经部署
        if unit.deployed:
            QMessageBox.warning(
                self,
                tr('警告'),
                tr('单位 "{name}" 已经部署到画布上了！\n\n每个单位只能部署一次。').format(name=unit.name)
            )
            return
        
        # 标记为已部署
        unit.deployed = True
        
        # 添加到画布（会使用 unit.position_x 和 unit.position_y）
        self.tech_tree_canvas.add_unit_node(unit)
        
        # ✅ AI 生成: ADD_UNIT 同时快照 unit_data，供 perform_redo 恢复
        # （旧格式只有 unit_name，redo 时回退到 all_units 查找）
        undo_action = UndoAction(
            UndoActionType.ADD_UNIT,
            {'unit_name': unit.name, 'unit_data': unit.to_dict()}
        )
        self.undo_manager.push_action(undo_action)
        
        # 更新列表中的状态
        self.unit_list_panel.update_unit_status(unit.name, deployed=True)
        
        # 更新 all_units 列表（同时更新 units 列表）
        for u in self.all_units:
            if u.name == unit.name:
                u.deployed = True
                u.position_x = unit.position_x
                u.position_y = unit.position_y
                break
        
        for u in self.units:
            if u.name == unit.name:
                u.deployed = True
                u.position_x = unit.position_x
                u.position_y = unit.position_y
                break
        
        # 显示成功消息
        self.update_status_bar(tr('✅ 已添加单位 "{name}" 到位置 ({x}, {y})').format(
            name=unit.name, x=unit.position_x, y=unit.position_y))
        
        # 标记有未保存的更改
        self.has_unsaved_changes = True
    
    def add_unit_to_canvas_top_left(self, unit_data: dict):
        """
        双击单位列表，处理已部署和未部署单位
        - 未部署：添加到画布左上角
        - 已部署：视图居中到画布上的该单位
        
        Args:
            unit_data: 单位数据字典
        """
        from src.parser import Unit
        unit = Unit.from_dict(unit_data)
        
        # 检查是否已经部署
        if unit.deployed:
            # 已部署：查找画布上的节点并居中视图
            if unit.name in self.tech_tree_canvas.nodes:
                node = self.tech_tree_canvas.nodes[unit.name]
                # 计算节点中心位置
                from PyQt5.QtCore import QPointF
                node_center = node.pos() + QPointF(node.width / 2, node.height / 2)
                # 居中视图
                self.tech_tree_canvas.centerOn(node_center)
                
                # 视觉反馈：短暂高亮
                original_pen = node.pen()
                highlight_pen = QPen(QColor('#00FFFF'), 4)  # 青色
                node.setPen(highlight_pen)
                
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, lambda: node.setPen(original_pen))
                
                self.update_status_bar(tr('🎯 已定位到单位 "{name}"').format(name=unit.name))
            else:
                QMessageBox.warning(
                    self,
                    tr('警告'),
                    tr('单位 "{name}" 标记为已部署，但在画布上找不到！').format(name=unit.name)
                )
            return
        
        # 设置单位为左上角位置（0, 0）
        unit.position_x = 0
        unit.position_y = 0
        
        # 标记为已部署
        unit.deployed = True
        
        # 添加到画布
        self.tech_tree_canvas.add_unit_node(unit)
        
        # ✅ AI 生成: ADD_UNIT 同时快照 unit_data，供 perform_redo 恢复
        # （旧格式只有 unit_name，redo 时回退到 all_units 查找）
        undo_action = UndoAction(
            UndoActionType.ADD_UNIT,
            {'unit_name': unit.name, 'unit_data': unit.to_dict()}
        )
        self.undo_manager.push_action(undo_action)
        
        # 更新列表中的状态
        self.unit_list_panel.update_unit_status(unit.name, deployed=True)
        
        # 更新 all_units 列表（同时更新 units 列表）
        for u in self.all_units:
            if u.name == unit.name:
                u.deployed = True
                u.position_x = unit.position_x
                u.position_y = unit.position_y
                break
        
        for u in self.units:
            if u.name == unit.name:
                u.deployed = True
                u.position_x = unit.position_x
                u.position_y = unit.position_y
                break
        
        # 显示成功消息
        self.update_status_bar(tr('✅ 已添加单位 "{name}" 到左上角 (40, 40)').format(name=unit.name))
    
    def update_unit_in_canvas(self, unit_data: dict):
        """从属性面板更新单位"""
        # 获取当前画布上的节点（用于比较旧值）
        unit_name = unit_data.get('name', '')
        old_costs = None
        old_requires = None
        old_position_x = None
        old_position_y = None
        
        if unit_name in self.tech_tree_canvas.nodes:
            node = self.tech_tree_canvas.nodes[unit_name]
            old_costs = node.unit.costs
            old_requires = node.unit.requires.copy() if isinstance(node.unit.requires, list) else ([node.unit.requires] if node.unit.requires else [])
            # ✅ 关键修复：保存当前的 position，避免被 unit_data 中的错误 position 覆盖
            old_position_x = node.unit.position_x
            old_position_y = node.unit.position_y
        
        # ✅ 关键修复：使用当前的 position，而不是 unit_data 中的 position
        # 这样可以避免点击节点时 position 被错误地修改
        if old_position_x is not None and old_position_y is not None:
            unit_data['position_x'] = old_position_x
            unit_data['position_y'] = old_position_y
        
        # 更新节点
        unit = Unit.from_dict(unit_data)
        self.tech_tree_canvas.update_unit_node(unit)
        
        # 记录撤销操作（修改属性 - costs）
        if old_costs is not None and unit_data.get('costs') != old_costs:
            undo_action = UndoAction(
                UndoActionType.MODIFY_PROPERTY,
                {
                    'unit_name': unit_name,
                    'property_name': 'costs',
                    'old_value': old_costs,
                    'new_value': unit_data.get('costs')
                }
            )
            self.undo_manager.push_action(undo_action)
            
            # 标记有未保存的更改
            self.has_unsaved_changes = True
    
    def update_unit_position_in_panel(self, unit_data):
        """
        更新属性面板中的坐标显示（当节点被拖动时）
        支持单单位数据（旧格式）和批量数据（新格式：{name: data, ...}）
        
        Args:
            unit_data: 单个单位字典 或 批量字典 {unit_name: {name, position_x, position_y, old_position_x, old_position_y}, ...}
        """
        try:
            if debug.DEBUG:
                debug_print(f"[DEBUG UNDO] update_unit_position_in_panel called, type={type(unit_data)}")
            
            # 检测数据格式：批量数据（字典的value是字典，且包含name字段）
            is_batch = False
            if isinstance(unit_data, dict) and len(unit_data) > 0:
                # 检查是否是批量数据：key是unit_name，value是unit_data字典
                first_value = next(iter(unit_data.values()))
                if isinstance(first_value, dict) and 'name' in first_value and 'old_position_x' in first_value:
                    is_batch = True
                    if debug.DEBUG:
                        debug_print(f"[DEBUG UNDO] Detected batch format with {len(unit_data)} units")
            
            if is_batch:
                # 批量处理：遍历所有单位
                for name, data in unit_data.items():
                    if debug.DEBUG:
                        debug_print(f"[DEBUG UNDO] Processing unit: {name}, old=({data.get('old_position_x')}, {data.get('old_position_y')}), new=({data.get('position_x')}, {data.get('position_y')})")
                    self._process_single_unit_move(data)
            else:
                # 单个单位处理（兼容旧格式）
                if debug.DEBUG:
                    debug_print(f"[DEBUG UNDO] Processing single unit: {unit_data.get('name', 'unknown')}")
                self._process_single_unit_move(unit_data)
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] update_unit_position_in_panel failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_single_unit_move(self, unit_data: dict):
        """
        处理单个单位的位置移动
        
        Args:
            unit_data: 包含 name, position_x, position_y, old_position_x, old_position_y 的字典
        """
        if debug.DEBUG:
            debug_print(f"[DEBUG UNDO] _process_single_unit_move called for {unit_data.get('name')}")
        
        # 记录撤销操作（移动单位）- 只有位置真正改变时才记录
        if 'old_position_x' in unit_data and 'old_position_y' in unit_data:
            if debug.DEBUG:
                debug_print(f"[DEBUG UNDO] Has old_position: old=({unit_data['old_position_x']}, {unit_data['old_position_y']}), new=({unit_data['position_x']}, {unit_data['position_y']})")
            if (unit_data['position_x'] != unit_data['old_position_x'] or 
                unit_data['position_y'] != unit_data['old_position_y']):
                if debug.DEBUG:
                    debug_print(f"[DEBUG UNDO] Position changed! Creating undo action...")
                undo_action = UndoAction(
                    UndoActionType.MOVE_UNIT,
                    {
                        'unit_name': unit_data['name'],
                        'old_position_x': unit_data['old_position_x'],
                        'old_position_y': unit_data['old_position_y'],
                        'new_position_x': unit_data['position_x'],
                        'new_position_y': unit_data['position_y']
                    }
                )
                self.undo_manager.push_action(undo_action)
                if debug.DEBUG:
                    debug_print(f"[DEBUG UNDO] Undo action pushed. Stack size: {len(self.undo_manager.undo_stack)}")
                
                # 标记有未保存的更改
                self.has_unsaved_changes = True
            else:
                if debug.DEBUG:
                    debug_print(f"[DEBUG UNDO] Position unchanged, skipping undo record")
        
        # 只有当属性面板当前显示的是这个单位时才更新
        if self.property_panel.current_unit_data and \
           self.property_panel.current_unit_data.get('name') == unit_data['name']:
            # 更新坐标显示（阻止信号避免触发循环）
            self.property_panel.pos_x_spinbox.blockSignals(True)
            self.property_panel.pos_y_spinbox.blockSignals(True)
            self.property_panel.pos_x_spinbox.setValue(unit_data['position_x'])
            self.property_panel.pos_y_spinbox.setValue(unit_data['position_y'])
            self.property_panel.pos_x_spinbox.blockSignals(False)
            self.property_panel.pos_y_spinbox.blockSignals(False)
    
    def on_unit_deleted_from_canvas(self, unit_name: str):
        """处理从画布删除单位的事件"""
        # 更新 units 列表中的 deployed 状态
        for u in self.units:
            if u.name == unit_name:
                u.deployed = False
                break
        
        # 更新 all_units 列表中的 deployed 状态（确保拖拽检查时状态正确）
        for u in self.all_units:
            if u.name == unit_name:
                u.deployed = False
                break
        
        # 同步更新所有子节点的 requires（从该节点的数据中获取被修改的子节点信息）
        # 注意：这里 unit_name 只是被删除的节点名，子节点的 requires 已在 canvas 中更新
        # 需要同步到 all_units 和 units 列表
        if unit_name in self.tech_tree_canvas.nodes:
            # 节点还在画布中（不应该出现），跳过
            pass
        else:
            # 节点已被删除，找到所有以它为父节点的子节点并更新
            for u in self.all_units:
                if isinstance(u.requires, list):
                    if unit_name in u.requires:
                        u.requires.remove(unit_name)
                elif u.requires == unit_name:
                    u.requires = []
            
            for u in self.units:
                if isinstance(u.requires, list):
                    if unit_name in u.requires:
                        u.requires.remove(unit_name)
                elif u.requires == unit_name:
                    u.requires = []
        
        # 更新列表中的状态显示
        self.unit_list_panel.update_unit_status(unit_name, deployed=False)
        
        # 标记有未保存的更改
        self.has_unsaved_changes = True
    
    def on_unit_delete_for_undo(self, unit_data: dict):
        """处理删除单位用于撤销（记录操作）"""
        # 记录撤销操作（删除单位）
        undo_action = UndoAction(
            UndoActionType.DELETE_UNIT,
            {'unit_data': unit_data}
        )
        self.undo_manager.push_action(undo_action)
        
        # 标记有未保存的更改
        self.has_unsaved_changes = True
        
        if debug.DEBUG:
            debug_print(f"[UNDO] Recorded delete action for: {unit_data.get('name')}, stack size: {self.undo_manager.get_stack_size()}")
    
    def on_requires_set(self, child_name: str, parent_name: str):
        """
        处理设置 requires 关系（支持多个父节点）
        
        Args:
            child_name: 子节点名称
            parent_name: 父节点（前置）名称
        """
        # 直接从画布节点获取当前的 unit（确保 position 是最新的）
        if child_name in self.tech_tree_canvas.nodes:
            node = self.tech_tree_canvas.nodes[child_name]
            current_unit = node.unit
            
            # 确保 requires 是列表
            if not isinstance(current_unit.requires, list):
                current_unit.requires = [current_unit.requires] if current_unit.requires else []
            
            # 保存旧的前置关系
            old_requires = current_unit.requires.copy()
            
            # 检查是否已经存在该父节点
            if parent_name in current_unit.requires:
                self.update_status_bar(tr('⚠️ "{parent}" 已经是 "{child}" 的前置单位').format(
                    parent=parent_name, child=child_name))
                return
            
            # 添加新的父节点到列表
            current_unit.requires.append(parent_name)
            
            # 记录撤销操作（修改 requires）
            undo_action = UndoAction(
                UndoActionType.CHANGE_REQUIRES,
                {
                    'unit_name': child_name,
                    'old_requires': old_requires,
                    'new_requires': current_unit.requires.copy()
                }
            )
            self.undo_manager.push_action(undo_action)
            
            # 标记有未保存的更改
            self.has_unsaved_changes = True
            
            # 更新画布上的节点（不改变位置）
            node.update_from_unit(current_unit, update_pos=False)
            
            # 刷新连线（scene 是 TechTreeCanvas 的属性）
            self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
            
            # 同步更新所有数据源中的 requires
            for u in self.all_units:
                if u.name == child_name:
                    u.requires = current_unit.requires.copy()
                    break
            
            for u in self.units:
                if u.name == child_name:
                    u.requires = current_unit.requires.copy()
                    break
            
            # 更新状态栏
            self.update_status_bar(tr('✅ 已为 "{child}" 添加前置单位 "{parent}"').format(
                child=child_name, parent=parent_name))
            
            # 刷新左侧列表
            self.unit_list_panel.load_units(self.all_units)
    
    def on_unit_property_changed(self, unit_name: str, property_name: str, old_value, new_value):
        """
        处理单位属性变更（双击修改 Costs）
        
        Args:
            unit_name: 单位名称
            property_name: 属性名（如 'costs'）
            old_value: 旧值
            new_value: 新值
        """
        if property_name == 'costs':
            # 记录撤销操作
            undo_action = UndoAction(
                UndoActionType.MODIFY_PROPERTY,
                {
                    'unit_name': unit_name,
                    'property': 'costs',
                    'old_value': old_value,
                    'new_value': new_value
                }
            )
            self.undo_manager.push_action(undo_action)
            
            # 标记有未保存的更改
            self.has_unsaved_changes = True
            
            # 同步更新所有数据源
            for u in self.all_units:
                if u.name == unit_name:
                    u.costs = new_value
                    break
            
            for u in self.units:
                if u.name == unit_name:
                    u.costs = new_value
                    break
            
            # 更新状态栏
            self.update_status_bar(tr('✅ 已修改 "{name}" 的 Costs: {old} → {new}').format(
                name=unit_name, old=old_value, new=new_value))
            
            # 更新画布上的节点（不改变位置）
            if unit_name in self.tech_tree_canvas.nodes:
                node = self.tech_tree_canvas.nodes[unit_name]
                node.cost_text.setPlainText(f"Cost: {new_value}")
                node.set_pen_and_brush()
            
            # 更新属性面板（如果当前选中该单位）
            if self.property_panel.current_unit_data and \
               self.property_panel.current_unit_data.get('name') == unit_name:
                # 阻止信号避免触发位置重置
                self.property_panel.blockSignals(True)
                self.property_panel.costs_spinbox.setValue(new_value)
                self.property_panel.blockSignals(False)
    
    def add_new_unit(self):
        """手动添加新单位（带类型选择）"""
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('新建单位'))
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 单位名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel(tr('单位名称:'))
        name_input = QLineEdit()
        name_input.setPlaceholderText(tr('请输入单位名称'))
        # ✅ AI 生成: 限制单位名称只允许字母、数字、下划线、括号、连字符，禁止引号/花括号等破坏格式的字符
        from PyQt5.QtGui import QRegExpValidator
        from PyQt5.QtCore import QRegExp
        name_validator = QRegExpValidator(QRegExp(r'^[a-zA-Z0-9_()\[\]\-\.]+$'))
        name_input.setValidator(name_validator)
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
        
        # 单位类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel(tr('单位类型:'))
        type_combo = QComboBox()
        type_combo.addItems(['', 'tech'])  # 空表示单位，tech 表示科技
        type_combo.setToolTip(tr('空=普通单位，tech=科技节点'))
        type_layout.addWidget(type_label)
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(tr('确定'))
        cancel_btn = QPushButton(tr('取消'))
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            unit_type = type_combo.currentText()
            
            if not name:
                QMessageBox.warning(self, tr('警告'), tr('单位名称不能为空！'))
                return
            
            # ✅ AI 生成: 额外检查单位名称是否包含非法字符（防止验证器疏漏）
            if not re.match(r'^[a-zA-Z0-9_()\[\]\-\.]+$', name):
                QMessageBox.warning(
                    self,
                    tr('警告'),
                    tr('单位名称包含非法字符！\n\n只允许使用字母、数字、下划线、括号和连字符。')
                )
                return
            
            # ✅ AI 生成: 重名检查覆盖 all_units（含 research-only 单位），
            # 原实现只查 self.units，会漏掉仅存在于 research 文件中的单位
            if any(u.name == name for u in self.all_units):
                QMessageBox.warning(
                    self,
                    tr('警告'),
                    tr('单位 "{name}" 已经存在！').format(name=name)
                )
                return
            
            # 创建新单位
            unit = self.parser.add_custom_unit(name)
            unit.unit_type = unit_type  # 设置单位类型
            # ✅ AI 生成: parser.add_custom_unit 已向 self.parser.units 追加，
            # 此处只向展示用的 all_units 追加一次，避免同一 Unit 对象出现两次导致列表重复行
            self.all_units.append(unit)
            
            # ✅ 关键修复：不自动部署到画布，不设置 deployed=True
            # unit.deployed = False  # 默认就是不部署
            
            # ✅ 修复：刷新左侧单位列表时使用 all_units，确保显示所有单位
            self.unit_list_panel.load_units(self.all_units)
            
            type_desc = tr('科技') if unit_type == 'tech' else tr('单位')
            QMessageBox.information(
                self,
                tr('成功'),
                tr('已创建{type} "{name}"\n\n新单位已添加到单位列表，\n双击列表项或拖拽到画布即可部署。').format(
                    type=type_desc, name=name)
            )
    
    def select_resource_folder(self):
        """选择游戏资源文件夹（加载单位头像）"""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('选择游戏资源文件夹'),
            '',
            QFileDialog.ShowDirsOnly
        )
        
        if not folder:
            return
        
        from src.tech_tree_canvas import TechTreeCanvas
        mgr = TechTreeCanvas.portrait_manager
        mgr.load_folder(folder)
        
        # 刷新所有节点的头像
        self.tech_tree_canvas.refresh_portraits()
        
        # 更新状态显示
        self.resource_label.setText(tr('资源: {folder}').format(folder=os.path.basename(folder)))
        self.update_status_bar(tr('已加载资源文件夹: {folder}').format(folder=folder))
    
    def save_tech_tree(self) -> bool:
        """
        保存科技树配置
        
        Returns:
            True 表示确实写出成功；False 表示用户取消或写出失败
        """
        if not self.tech_tree_canvas.nodes:
            QMessageBox.warning(self, tr('警告'), tr('没有可保存的单位数据'))
            return False
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr('保存科技树配置'),
            f'unit_research_{self.faction}.set',
            tr('SET Files (*.set);;All Files (*)')
        )
        
        if not file_path:
            # ✅ AI 生成: 用户在保存对话框中取消，明确返回 False，避免 closeEvent 误判为已保存
            return False
        
        try:
            # 从画布获取最新的单位数据
            deployed_units = self.tech_tree_canvas.get_all_units()
            
            # 导出文件（传递原始文件路径以保留注释）
            original_file = getattr(self, 'research_file', None)
            self.exporter.export(deployed_units, self.faction, file_path, original_file)
            
            # 更新 all_units
            for deployed_unit in deployed_units:
                for u in self.all_units:
                    if u.name == deployed_unit.name:
                        u.position_x = deployed_unit.position_x
                        u.position_y = deployed_unit.position_y
                        u.requires = deployed_unit.requires
                        u.costs = deployed_unit.costs
                        break
            
            # ✅ AI 生成: 保存成功后复位脏位，修复"每次关闭都提示未保存"的问题
            # ✅ AI 生成: 记住本次输出路径，使后续保存可直接覆盖同一文件（保留注释）
            self.research_file = file_path
            self.has_unsaved_changes = False
            
            QMessageBox.information(
                self,
                tr('保存成功'),
                tr('已保存到:\n{path}').format(path=file_path)
            )
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('保存失败'),
                tr('导出文件时出错:\n{error}').format(error=str(e))
            )
            return False
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            tr('关于科技树生成器'),
            '<h2>' + tr('科技树生成器') + '</h2>'
            '<p>Gates of Hell ' + tr('模组开发工具') + '</p>'
            # ✅ AI 生成: 版本号与 main.py / Research_Tree_Generator.spec 保持一致（原为 2.1）
            '<p>' + tr('版本') + ': 2.2.2</p>'
            # ✅ 隐私处理：作者署名改用 GitHub 账号，不公开私人邮箱
            '<p>' + tr('作者') + ': HonoriusAD395</p>'
            '<p>GitHub: '
            '<a href="https://github.com/HonoriusAD395">'
            'https://github.com/HonoriusAD395</a></p>'
            '<p style="white-space: pre-wrap;">' + tr('作者：本软件在opencode+deepseek-v4-flash帮助下开发。\n'
            'deepseek-v4 1M上下文，纯爷们、真汉子、真便宜、默秒全。') + '</p>'
            '<hr>'
            # ✅ AI 披露：按 NOTICE 的标准声明，在界面内也明确告知
            '<p>' + tr('AI 生成声明：本软件源码与文档主要由 AI 编码助手生成，经人工审核；'
                       '按 MIT 许可「AS IS」提供，详见 NOTICE 文件。') + '</p>'
        )
    
    def keyPressEvent(self, event):
        """键盘事件 - 备用处理（主要使用 QShortcut）"""
        # 其他按键交给父类处理
        super().keyPressEvent(event)
    
    def perform_undo(self):
        """执行撤销操作"""
        if debug.DEBUG:
            debug_print(f"[UNDO] perform_undo called, can_undo: {self.undo_manager.can_undo()}")
        action = self.undo_manager.undo()
        
        if not action:
            self.update_status_bar(tr('⚠️ 没有可撤销的操作'))
            return
        
        if debug.DEBUG:
            debug_print(f"[UNDO] Performing undo for: {action}")
        
        try:
            if action.action_type == UndoActionType.ADD_UNIT:
                # 撤销添加单位 -> 删除该单位
                unit_name = action.data['unit_name']
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    # ✅ AI 生成: record_undo=False —— 撤销流程内部的删除不得再压
                    # DELETE_UNIT 撤销动作，否则 push_action 会清空重做栈（Ctrl+Y 失效）
                    self.tech_tree_canvas.on_item_deleted(node, record_undo=False)
                    self.update_status_bar(tr('↩️ 已撤销添加单位 "{name}"').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法撤销'))
            
            elif action.action_type == UndoActionType.DELETE_UNIT:
                # 撤销删除单位 -> 重新添加该单位
                unit_data = action.data['unit_data']
                
                # 先提取 removed_requires_children（避免传递给 Unit.from_dict）
                removed_children = unit_data.pop('removed_requires_children', [])
                
                unit = Unit.from_dict(unit_data)
                
                # 恢复 removed_requires_children（用于后续恢复子节点）
                unit_data['removed_requires_children'] = removed_children
                
                if debug.DEBUG:
                    debug_print(f"[UNDO] Restoring deleted unit: {unit.name}")
                self.tech_tree_canvas.add_unit_node(unit)
                
                # 恢复被删除节点时移除的子节点 requires 引用
                removed_children = unit_data.get('removed_requires_children', [])
                for child_info in removed_children:
                    child_name = child_info['unit_name']
                    old_requires = child_info['old_requires']
                    
                    if child_name in self.tech_tree_canvas.nodes:
                        child_node = self.tech_tree_canvas.nodes[child_name]
                        # 恢复旧的 requires
                        child_node.unit.requires = old_requires
                        # 更新文本显示
                        child_node.requires_value_text.setPlainText(child_node._format_requires_value(old_requires))
                        # 更新边框颜色
                        child_node.set_pen_and_brush()
                        
                        # 同步更新 all_units 和 units
                        for u in self.all_units:
                            if u.name == child_name:
                                u.requires = old_requires.copy() if isinstance(old_requires, list) else old_requires
                                break
                        for u in self.units:
                            if u.name == child_name:
                                u.requires = old_requires.copy() if isinstance(old_requires, list) else old_requires
                                break
                        
                        if debug.DEBUG:
                            debug_print(f"[UNDO] Restored requires for {child_name}: {old_requires}")
                
                # 更新连线
                self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
                
                # 更新列表状态
                self.unit_list_panel.update_unit_status(unit.name, deployed=True)
                
                # 更新 all_units
                for u in self.all_units:
                    if u.name == unit.name:
                        u.deployed = True
                        u.position_x = unit.position_x
                        u.position_y = unit.position_y
                        break
                
                # 更新 units 列表（重要！）
                for u in self.units:
                    if u.name == unit.name:
                        u.deployed = True
                        u.position_x = unit.position_x
                        u.position_y = unit.position_y
                        break
                
                if debug.DEBUG:
                    debug_print(f"[UNDO] Unit restored successfully")
                self.update_status_bar(tr('↩️ 已撤销删除单位 "{name}"').format(name=unit.name))
            
            elif action.action_type == UndoActionType.MOVE_UNIT:
                # 撤销移动单位 -> 恢复到旧位置
                unit_name = action.data['unit_name']
                old_pos_x = action.data['old_position_x']
                old_pos_y = action.data['old_position_y']
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    node.unit.position_x = old_pos_x
                    node.unit.position_y = old_pos_y
                    node.update_position()
                    
                    # 更新连线
                    self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
                    
                    # ✅ 新增：检查节点重叠情况（三格内）
                    self.tech_tree_canvas.check_node_overlaps()
                    
                    # 更新属性面板（如果当前选中的是这个单位）
                    if self.property_panel.current_unit_data and \
                       self.property_panel.current_unit_data.get('name') == unit_name:
                        self.property_panel.pos_x_spinbox.setValue(old_pos_x)
                        self.property_panel.pos_y_spinbox.setValue(old_pos_y)
                    
                    self.update_status_bar(tr('↩️ 已撤销移动单位 "{name}"').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法撤销'))
            
            elif action.action_type == UndoActionType.CHANGE_REQUIRES:
                # 撤销修改 requires -> 恢复旧的 requires
                unit_name = action.data['unit_name']
                old_requires = action.data['old_requires']
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    node.unit.requires = old_requires
                    
                    # 更新文本显示
                    node.requires_value_text.setPlainText(node._format_requires_value(old_requires))
                    
                    # 更新连线
                    self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
                    
                    # 更新属性面板
                    if self.property_panel.current_unit_data and \
                       self.property_panel.current_unit_data.get('name') == unit_name:
                        if isinstance(old_requires, list):
                            # ✅ AI 生成: 撤销 requires 恢复时使用空格分隔，与主逻辑保持一致
                            self.property_panel.requires_input.setText(' '.join(old_requires))
                        else:
                            self.property_panel.requires_input.setText(str(old_requires) if old_requires else '')
                    
                    self.update_status_bar(tr('↩️ 已撤销修改 "{name}" 的前置关系').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法撤销'))
            
            elif action.action_type == UndoActionType.MODIFY_PROPERTY:
                # 撤销修改属性 -> 恢复旧值
                unit_name = action.data['unit_name']
                # ✅ AI 生成: 兼容两种历史键名，修复属性面板改 Costs 后按 Ctrl+Z 抛 KeyError 的问题
                # 画布双击入口写入 'property'，属性面板入口写入 'property_name'，此处必须同时兼容
                property_name = action.data.get('property', action.data.get('property_name', 'costs'))
                old_value = action.data['old_value']
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    
                    if property_name == 'costs':
                        node.unit.costs = old_value
                        node.cost_text.setPlainText(f"Cost: {old_value}")
                        
                        # 更新属性面板
                        if self.property_panel.current_unit_data and \
                           self.property_panel.current_unit_data.get('name') == unit_name:
                            self.property_panel.costs_spinbox.setValue(old_value)
                        
                        # 同步更新所有数据源
                        for u in self.all_units:
                            if u.name == unit_name:
                                u.costs = old_value
                                break
                        
                        for u in self.units:
                            if u.name == unit_name:
                                u.costs = old_value
                                break
                    
                    self.update_status_bar(tr('↩️ 已撤销修改 "{name}" 的属性').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法撤销'))
            
            else:
                self.update_status_bar(tr('⚠️ 未知的操作类型: {type}').format(type=action.action_type))
        
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] Undo failed: {e}")
            import traceback
            traceback.print_exc()
            self.update_status_bar(tr('❌ 撤销失败: {error}').format(error=str(e)))
    
    def perform_redo(self):
        """执行重做操作（Ctrl+Y / 编辑菜单）"""
        if debug.DEBUG:
            debug_print(f"[REDO] perform_redo called, can_redo: {self.undo_manager.can_redo()}")
        action = self.undo_manager.redo()
        
        if not action:
            self.update_status_bar(tr('⚠️ 没有可重做的操作'))
            return
        
        if debug.DEBUG:
            debug_print(f"[REDO] Performing redo for: {action}")
        
        try:
            if action.action_type == UndoActionType.ADD_UNIT:
                # 重做添加单位 -> 重新添加该单位
                # ✅ AI 生成: 优先使用压栈时快照的 unit_data（重做语义 = 恢复为当初添加时的状态）；
                # 旧格式记录只有 unit_name 时回退到 all_units 查找
                unit_data = action.data.get('unit_data')
                if unit_data is None:
                    unit_data = next(
                        (u.to_dict() for u in self.all_units
                         if u.name == action.data.get('unit_name')),
                        None)
                if unit_data is None:
                    self.update_status_bar(tr('⚠️ 缺少单位数据，无法重做'))
                    return
                
                unit = Unit.from_dict(unit_data)
                unit.deployed = True
                self.tech_tree_canvas.add_unit_node(unit)
                
                # 同步列表状态（不走 add_unit_to_canvas，避免再次压栈清空重做栈）
                self.unit_list_panel.update_unit_status(unit.name, deployed=True)
                for u in self.all_units:
                    if u.name == unit.name:
                        u.deployed = True
                        break
                for u in self.units:
                    if u.name == unit.name:
                        u.deployed = True
                        break
                
                self.has_unsaved_changes = True
                self.update_status_bar(tr('↪️ 已重做添加单位 "{name}"').format(name=unit.name))
            
            elif action.action_type == UndoActionType.DELETE_UNIT:
                # 重做删除单位 -> 再次删除该单位
                # ✅ AI 生成: on_item_deleted 传 record_undo=False，
                # 否则会压入新的 DELETE_UNIT 撤销动作并清空重做栈（redo 链会断）
                unit_name = action.data['unit_data'].get('name')
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    self.tech_tree_canvas.on_item_deleted(node, record_undo=False)
                    self.has_unsaved_changes = True
                    self.update_status_bar(tr('↪️ 已重做删除单位 "{name}"').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法重做'))
            
            elif action.action_type == UndoActionType.MOVE_UNIT:
                # 重做移动单位 -> 移动到新位置
                unit_name = action.data['unit_name']
                new_pos_x = action.data['new_position_x']
                new_pos_y = action.data['new_position_y']
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    node.unit.position_x = new_pos_x
                    node.unit.position_y = new_pos_y
                    node.update_position()
                    
                    # 更新连线
                    self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
                    
                    # 检查节点重叠情况
                    self.tech_tree_canvas.check_node_overlaps()
                    
                    # 更新属性面板（如果当前选中的是这个单位）
                    if self.property_panel.current_unit_data and \
                       self.property_panel.current_unit_data.get('name') == unit_name:
                        self.property_panel.pos_x_spinbox.setValue(new_pos_x)
                        self.property_panel.pos_y_spinbox.setValue(new_pos_y)
                    
                    self.has_unsaved_changes = True
                    self.update_status_bar(tr('↪️ 已重做移动单位 "{name}"').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法重做'))
            
            elif action.action_type == UndoActionType.CHANGE_REQUIRES:
                # 重做修改 requires -> 设置新的 requires
                unit_name = action.data['unit_name']
                new_requires = action.data['new_requires']
                if not isinstance(new_requires, list):
                    new_requires = [new_requires] if new_requires else []
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    node.unit.requires = new_requires.copy()
                    
                    # 更新文本显示
                    node.requires_value_text.setPlainText(node._format_requires_value(new_requires))
                    node.set_pen_and_brush()
                    
                    # 更新连线
                    self.tech_tree_canvas.scene.update_edges(self.tech_tree_canvas.nodes)
                    
                    # 同步更新所有数据源
                    for u in self.all_units:
                        if u.name == unit_name:
                            u.requires = new_requires.copy()
                            break
                    for u in self.units:
                        if u.name == unit_name:
                            u.requires = new_requires.copy()
                            break
                    
                    # 更新属性面板
                    if self.property_panel.current_unit_data and \
                       self.property_panel.current_unit_data.get('name') == unit_name:
                        self.property_panel.requires_input.setText(' '.join(new_requires))
                    
                    self.has_unsaved_changes = True
                    self.update_status_bar(tr('↪️ 已重做修改 "{name}" 的前置关系').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法重做'))
            
            elif action.action_type == UndoActionType.MODIFY_PROPERTY:
                # 重做修改属性 -> 设置新值
                unit_name = action.data['unit_name']
                # ✅ AI 生成: 与 perform_undo 相同的双键名兼容（画布入口 'property'，属性面板入口 'property_name'）
                property_name = action.data.get('property', action.data.get('property_name', 'costs'))
                new_value = action.data['new_value']
                
                if unit_name in self.tech_tree_canvas.nodes:
                    node = self.tech_tree_canvas.nodes[unit_name]
                    
                    if property_name == 'costs':
                        node.unit.costs = new_value
                        node.cost_text.setPlainText(f"Cost: {new_value}")
                        
                        # 更新属性面板
                        if self.property_panel.current_unit_data and \
                           self.property_panel.current_unit_data.get('name') == unit_name:
                            self.property_panel.costs_spinbox.setValue(new_value)
                        
                        # 同步更新所有数据源
                        for u in self.all_units:
                            if u.name == unit_name:
                                u.costs = new_value
                                break
                        for u in self.units:
                            if u.name == unit_name:
                                u.costs = new_value
                                break
                    
                    self.has_unsaved_changes = True
                    self.update_status_bar(tr('↪️ 已重做修改 "{name}" 的属性').format(name=unit_name))
                else:
                    self.update_status_bar(tr('⚠️ 单位不存在，无法重做'))
            
            else:
                self.update_status_bar(tr('⚠️ 未知的操作类型: {type}').format(type=action.action_type))
        
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] Redo failed: {e}")
            import traceback
            traceback.print_exc()
            self.update_status_bar(tr('❌ 重做失败: {error}').format(error=str(e)))

    def _validate_units_file(self, file_path: str) -> bool:
        """
        验证 units 文件类型
        
        units_*.set 文件特征：
        - 包含完整的单位定义
        - 包含 side(...) period(...) 等关键字
        - 包含 {cost ...} {action ...} 等块
        - 不包含 { tech ... requires ... costs ... position ... }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含 units 文件特有的关键字
            has_side = 'side(' in content
            has_period = 'period(' in content or 'min_stage(' in content
            has_cost_block = bool(re.search(r'\{cost\s+\d+\}', content))
            
            # 检查是否包含 research 文件的特征（如果有则说明是 research 文件）
            has_tech_keyword = bool(re.search(r'\{\s*tech\s+', content))
            has_requires_keyword = bool(re.search(r'requires\s+"[^"]*"', content))
            
            # units 文件应该有 side/period，但不应该有 tech 关键字
            if has_side and not has_tech_keyword:
                return True
            
            # 如果只有 cost block 和 period，也认为是 units 文件
            if has_period and has_cost_block and not has_tech_keyword:
                return True
            
            # 如果同时包含 tech 和 requires，这很可能是 research 文件
            if has_tech_keyword and has_requires_keyword:
                return False
            
            # 如果文件名包含 'unit_research'，肯定不是 units 文件
            if 'unit_research' in os.path.basename(file_path):
                return False
            
            # 如果文件名包含 'units' 但没有 units 文件的特征，发出警告
            if 'units' in os.path.basename(file_path).lower():
                # 允许导入，但提示用户
                if debug.DEBUG:
                    debug_print(f"[WARNING] File '{file_path}' may not be a valid units file")
                return True  # 仍然允许导入
            
            return False
            
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] Failed to validate units file: {e}")
            return False
    
    def _validate_research_file(self, file_path: str) -> bool:
        """
        验证 research 文件类型
        
        unit_research_*.set 文件特征：
        - 包含 { tech "..." requires "..." costs X position X X}
        - 包含 {IconGap ...}
        - 不包含完整的单位定义（side、period、action 等）
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含 research 文件特有的关键字
            has_icon_gap = '{IconGap' in content
            has_tech_keyword = bool(re.search(r'\{\s*tech\s+', content))
            has_requires_keyword = bool(re.search(r'requires\s+"[^"]*"', content))
            has_position_keyword = bool(re.search(r'position\s+[\d.]+\s+[\d.]+', content))
            
            # 检查是否包含 units 文件的特征（如果有则说明是 units 文件）
            has_side = 'side(' in content
            has_period = 'period(' in content
            
            # research 文件应该有 tech/requires/position，但不应该有 side
            if has_tech_keyword and has_requires_keyword and not has_side:
                return True
            
            # 如果有 IconGap 和 tech，也认为是 research 文件
            if has_icon_gap and has_tech_keyword:
                return True
            
            # 如果文件名包含 'unit_research'，优先认为是 research 文件
            if 'unit_research' in os.path.basename(file_path):
                return True
            
            # 如果文件名包含 'units' 但没有 research 文件的特征，发出警告
            if 'units' in os.path.basename(file_path).lower() and not has_tech_keyword:
                return False
            
            return False
            
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] Failed to validate research file: {e}")
            return False
    
    def closeEvent(self, event: QEvent):
        """
        窗口关闭事件 - 提示保存
        """
        # 检查是否有未保存的更改
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                tr('保存更改'),
                tr('科技树有未保存的更改。\n\n是否保存后再退出？'),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # ✅ AI 生成: 只有真正写出成功才关闭；用户取消保存对话框或写出失败时留在窗口
                if self.save_tech_tree():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Discard:
                # 用户选择不保存
                event.accept()
            else:
                # 用户选择取消
                event.ignore()
        else:
            # 没有未保存的更改，直接关闭
            event.accept()
