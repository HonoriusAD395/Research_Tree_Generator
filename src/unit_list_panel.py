# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
单位列表面板
显示所有可用单位，支持拖拽到画布
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, 
    QTreeWidgetItem, QGroupBox, QLineEdit, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor
from src.i18n import tr


class UnitListPanel(QWidget):
    """单位列表面板"""
    
    # ✅ AI 生成: 移除 unit_dropped 死信号（全仓库无 emit，实际拖拽走
    # startDrag -> QDrag -> 画布 dropEvent -> unit_dropped_at_position）
    # 信号：单位被双击（添加到画布左上角）
    unit_double_clicked = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.units = []
        self.filtered_units = []  # 筛选后的单位列表
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(tr("📋 单位列表"))
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #bbbbbb;
            padding: 10px;
            background-color: #3c3f41;
        """)
        layout.addWidget(title_label)
        
        # 搜索和筛选区域
        filter_layout = QVBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr('🔍 搜索单位名称...'))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #bbbbbb;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        # ✅ AI 生成: 分类筛选下拉框
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                color: #bbbbbb;
                border: 1px solid #555;
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #bbbbbb;
                selection-background-color: #4e5254;
            }
        """)
        self.category_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_combo)
        
        # 筛选复选框
        self.filter_undeployed = QCheckBox(tr('仅显示未部署单位'))
        self.filter_undeployed.setStyleSheet("""
            QCheckBox {
                color: #bbbbbb;
                background-color: #3c3f41;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        self.filter_undeployed.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_undeployed)
        
        layout.addLayout(filter_layout)
        
        # 单位树形列表
        self.unit_tree = QTreeWidget()
        self.unit_tree.setHeaderLabels([tr('单位名称'), tr('科技'), tr('状态')])
        self.unit_tree.setColumnWidth(0, 150)
        self.unit_tree.setColumnWidth(1, 40)
        self.unit_tree.setColumnWidth(2, 40)
        self.unit_tree.setDragEnabled(True)
        self.unit_tree.setSelectionMode(QTreeWidget.SingleSelection)
        
        # 设置样式
        self.unit_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
                color: #bbbbbb;
                outline: none;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3c3f41;
            }
            QTreeWidget::item:selected {
                background-color: #4e5254;
            }
            QTreeWidget::item:hover {
                background-color: #3c3f41;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #555;
            }
        """)
        
        # 连接拖拽事件
        self.unit_tree.setDragEnabled(True)
        self.unit_tree.setAcceptDrops(False)
        
        # 重写 startDrag 方法
        original_start_drag = self.unit_tree.startDrag
        def custom_start_drag(supported_actions):
            self.startDrag(supported_actions)
        self.unit_tree.startDrag = custom_start_drag
        
        # 连接双击事件
        self.unit_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.unit_tree)
        
        # 统计信息
        self.stats_label = QLabel(tr("单位数: 0"))
        self.stats_label.setStyleSheet("""
            color: #888888;
            padding: 5px;
            font-size: 11px;
        """)
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
    
    def _build_category_list(self, units: list) -> list:
        """从单位列表提取所有分类，tech 单位归入 '🔬 科技单位'"""
        categories = set()
        for u in units:
            if u.unit_type == 'tech':
                categories.add('🔬 科技单位')
            elif u.squad_type:
                categories.add(u.squad_type)
            else:
                categories.add(tr('📦 其他单位'))
        return sorted(categories)
    
    def load_units(self, units: list):
        """
        加载单位列表
        
        Args:
            units: 单位对象列表
        """
        self.units = units
        self.filtered_units = units
        self.apply_filters()
    
    def apply_filters(self):
        """应用筛选条件并刷新显示"""
        search_text = self.search_input.text().lower().strip()
        only_undeployed = self.filter_undeployed.isChecked()
        selected_category = self.category_combo.currentText()
        
        # 筛选单位
        filtered = []
        for unit in self.units:
            if search_text and search_text not in unit.name.lower():
                continue
            if only_undeployed and unit.deployed:
                continue
            
            # ✅ AI 生成: 分类筛选
            if selected_category and selected_category != tr('全部'):
                unit_cat = self._get_unit_category(unit)
                if unit_cat != selected_category:
                    continue
            
            filtered.append(unit)
        
        self.filtered_units = filtered
        self._rebuild_category_combo(filtered)
        self._render_tree(filtered)
    
    def _get_unit_category(self, unit) -> str:
        """获取单位所属分类名称"""
        if unit.unit_type == 'tech':
            return '🔬 科技单位'
        elif unit.squad_type:
            return unit.squad_type
        else:
            return tr('📦 其他单位')
    
    def _rebuild_category_combo(self, filtered_units: list):
        """重建分类下拉框（基于当前筛选后单位）"""
        # 保存当前选中项
        current_text = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        
        # 优先使用全部未筛选时的分类（保持下拉框稳定）
        all_categories = self._build_category_list(self.units)
        self.category_combo.addItem(tr('全部'))
        for cat in all_categories:
            self.category_combo.addItem(cat)
        
        # 恢复选中项
        idx = self.category_combo.findText(current_text)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)
    
    def _render_tree(self, units: list):
        """渲染树形列表，按 squad_type 分组"""
        self.unit_tree.clear()
        
        # 按分类分组
        tech_units = [u for u in units if u.unit_type == 'tech']
        grouped = {}
        for u in units:
            if u.unit_type == 'tech':
                continue  # 单独处理
            cat = u.squad_type if u.squad_type else tr('📦 其他单位')
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(u)
        
        # 创建分类标题（排序：科技优先，其余按名称）
        category_items = {}
        
        if tech_units:
            item = QTreeWidgetItem(self.unit_tree, ['🔬 ' + tr('科技单位')])
            item.setExpanded(True)
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setForeground(0, Qt.cyan)
            category_items['🔬 科技单位'] = item
        
        for cat in sorted(grouped.keys()):
            item = QTreeWidgetItem(self.unit_tree, [cat])
            item.setExpanded(True)
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setForeground(0, Qt.green)
            category_items[cat] = item
        
        # 添加科技单位
        for unit in tech_units:
            cat_item = category_items.get('🔬 科技单位')
            if not cat_item:
                continue
            unit_item = QTreeWidgetItem(cat_item)
            unit_item.setText(0, unit.name)
            unit_item.setText(1, '🔬')
            self._set_unit_status(unit_item, unit)
            unit_item.setData(0, Qt.UserRole, unit.to_dict())
            unit_item.setForeground(0, Qt.cyan)
        
        # 添加各单位到对应分类
        for cat, unit_list in sorted(grouped.items()):
            cat_item = category_items.get(cat)
            if not cat_item:
                continue
            for unit in sorted(unit_list, key=lambda u: u.name):
                unit_item = QTreeWidgetItem(cat_item)
                unit_item.setText(0, unit.name)
                unit_item.setText(1, '')
                self._set_unit_status(unit_item, unit)
                unit_item.setData(0, Qt.UserRole, unit.to_dict())
        
        # 更新统计
        deployed_count = sum(1 for u in units if u.deployed)
        research_count = sum(1 for u in units if u.in_research)
        self.stats_label.setText(tr('显示: {show} | 总数: {total} | 已部署: {deployed} | 科技树: {research}').format(
            show=len(units), total=len(self.units), deployed=deployed_count, research=research_count))
    
    def _set_unit_status(self, unit_item: QTreeWidgetItem, unit):
        """设置单位的状态列和颜色"""
        if not unit.in_research:
            status_text = '⚠️'
            unit_item.setText(2, status_text)
            unit_item.setForeground(0, Qt.darkYellow)
            unit_item.setForeground(2, Qt.red)
        elif unit.deployed:
            status_text = '✅'
            unit_item.setText(2, status_text)
            unit_item.setForeground(0, Qt.gray)
        else:
            status_text = '❌'
            unit_item.setText(2, status_text)
            if unit.requires:
                unit_item.setForeground(0, Qt.yellow)
            else:
                unit_item.setForeground(0, Qt.green)
    
    def update_unit_status(self, unit_name: str, deployed: bool):
        """
        更新单位的部署状态
        
        Args:
            unit_name: 单位名称
            deployed: 是否已部署
        """
        root = self.unit_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category = root.child(i)
            for j in range(category.childCount()):
                item = category.child(j)
                if item.text(0) == unit_name:
                    unit_data = item.data(0, Qt.UserRole)
                    if unit_data:
                        unit_data['deployed'] = deployed
                        item.setData(0, Qt.UserRole, unit_data)
                        in_research = unit_data.get('in_research', True)
                    else:
                        in_research = True
                    
                    if deployed:
                        item.setText(2, '✅')
                        item.setForeground(0, Qt.green)
                    elif not in_research:
                        item.setText(2, '⚠️')
                        item.setForeground(0, Qt.darkYellow)
                        item.setForeground(2, Qt.red)
                    else:
                        item.setText(2, '❌')
                        requires_data = unit_data.get('requires') if unit_data else None
                        has_requires = False
                        if isinstance(requires_data, list):
                            has_requires = len(requires_data) > 0
                        elif requires_data:
                            has_requires = True
                        if has_requires:
                            item.setForeground(0, Qt.yellow)
                        else:
                            item.setForeground(0, Qt.green)
                    break
    
    def startDrag(self, supported_actions):
        """开始拖拽（使用 Qt 标准拖拽系统）"""
        selected_items = self.unit_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        unit_data = item.data(0, Qt.UserRole)
        
        if not unit_data:
            return
        
        import json
        mime_data = QMimeData()
        mime_data.setText(json.dumps(unit_data))
        
        drag = QDrag(self.unit_tree)
        drag.setMimeData(mime_data)
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor('#2b2b2b'))
        painter = QPainter(pixmap)
        painter.setPen(QColor('#ffffff'))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, unit_data.get('name', 'Unit')[:10])
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        drag.exec_(Qt.CopyAction)
    
    def on_item_double_clicked(self, item, column):
        """
        双击单位项事件
        
        Args:
            item: 被双击的树形项
            column: 被点击的列索引
        """
        unit_data = item.data(0, Qt.UserRole)
        if not unit_data:
            return
        
        if not isinstance(unit_data, dict) or 'name' not in unit_data:
            return
        
        self.unit_double_clicked.emit(unit_data)
