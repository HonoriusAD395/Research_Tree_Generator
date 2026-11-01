# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
属性编辑面板
编辑选中单位的各项属性
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from src import debug
from src.debug import debug_print
from src.i18n import tr


class PropertyPanel(QWidget):
    """属性编辑面板"""
    
    # 信号：单位属性更新
    unit_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_unit_data = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(tr("⚙️ 属性编辑"))
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #bbbbbb;
            padding: 10px;
            background-color: #3c3f41;
        """)
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 内容部件
        content_widget = QWidget()
        self.form_layout = QFormLayout(content_widget)
        
        # 单位名称（只读，加粗放大显示，白色文字）
        self.name_label = QLabel(tr("未选择单位"))
        self.name_label.setStyleSheet("""
            color: #ffffff;
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
            background-color: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
        """)
        self.name_label.setWordWrap(True)  # 支持自动换行
        self.name_label.setMinimumHeight(30)
        self.form_layout.addRow(tr("名称:"), self.name_label)
        
        # 单位类型（可编辑下拉框，只有 tech 和空两种选择）
        self.type_combo = QComboBox()
        self.type_combo.addItems(['', 'tech'])  # 空表示单位，tech 表示科技
        self.type_combo.setEditable(False)  # 不允许手动输入
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                color: #00FF7F;
                border: 1px solid #555;
                padding: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.type_combo.currentTextChanged.connect(self.on_property_changed)
        self.form_layout.addRow(tr("类型:"), self.type_combo)
        
        # 阵营（只读）
        self.side_label = QLabel("-")
        self.side_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        self.form_layout.addRow(tr("阵营:"), self.side_label)
        
        self.form_layout.addItem(None)  # 分隔
        
        # Costs（可编辑）
        self.costs_spinbox = QSpinBox()
        self.costs_spinbox.setRange(0, 1000)  # 最高支持 1000
        self.costs_spinbox.setValue(1)
        self.costs_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
        """)
        self.costs_spinbox.valueChanged.connect(self.on_property_changed)
        self.form_layout.addRow(tr("Costs:"), self.costs_spinbox)
        
        # Position X（可编辑）
        self.pos_x_spinbox = QDoubleSpinBox()  # 使用支持小数的 SpinBox
        self.pos_x_spinbox.setRange(0, 100)  # 从 0 开始，不允许负数
        self.pos_x_spinbox.setValue(0)
        self.pos_x_spinbox.setDecimals(2)  # 保留两位小数
        self.pos_x_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
        """)
        self.pos_x_spinbox.valueChanged.connect(self.on_property_changed)
        self.form_layout.addRow(tr("Position X:"), self.pos_x_spinbox)
        
        # Position Y（可编辑）
        self.pos_y_spinbox = QDoubleSpinBox()  # 使用支持小数的 SpinBox
        self.pos_y_spinbox.setRange(0, 100)  # 从 0 开始，不允许负数
        self.pos_y_spinbox.setValue(0)
        self.pos_y_spinbox.setDecimals(2)  # 保留两位小数
        self.pos_y_spinbox.setSingleStep(0.1)  # 步进为 0.1
        self.pos_y_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
        """)
        self.pos_y_spinbox.valueChanged.connect(self.on_property_changed)
        self.form_layout.addRow(tr("Position Y:"), self.pos_y_spinbox)
        
        self.form_layout.addItem(None)  # 分隔
        
        # Requires（可编辑）
        self.requires_input = QLineEdit()
        self.requires_input.setPlaceholderText(tr("前置单位名称（可选）"))
        self.requires_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
        """)
        from PyQt5.QtGui import QRegExpValidator
        from PyQt5.QtCore import QRegExp
        # ✅ AI 生成: 禁止输入引号、逗号、花括号、反斜杠（这些字符会破坏 .set 文件格式）
        self.requires_input.setValidator(QRegExpValidator(QRegExp(r'^[^"\,\{\}\\\;]*$')))
        self.requires_input.textChanged.connect(self.on_property_changed)
        self.form_layout.addRow(tr("Requires:"), self.requires_input)
        
        self.form_layout.addItem(None)  # 分隔
        
        # Period（只读）
        self.period_label = QLabel("-")
        self.period_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        self.form_layout.addRow(tr("Period:"), self.period_label)
        
        # Min Stage（只读）
        self.stage_label = QLabel("-")
        self.stage_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        self.form_layout.addRow(tr("Min Stage:"), self.stage_label)
        
        # CP（只读）
        self.cp_label = QLabel("-")
        self.cp_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        self.form_layout.addRow(tr("CP:"), self.cp_label)
        
        # Tags（只读）
        self.tags_label = QLabel("-")
        self.tags_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        self.tags_label.setWordWrap(True)
        self.form_layout.addRow(tr("Tags:"), self.tags_label)
        
        content_widget.setLayout(self.form_layout)
        scroll.setWidget(content_widget)
        
        layout.addWidget(scroll)
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        reset_btn = QPushButton(tr("🔄 重置位置"))
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #4e5254;
                color: #ffffff;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5e61;
            }
        """)
        reset_btn.clicked.connect(self.reset_position)
        button_layout.addWidget(reset_btn)
        
        # 移除了自动计算按钮，保留手动输入 costs 功能
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_unit(self, unit_data: dict):
        """
        加载单位数据到表单
        
        Args:
            unit_data: 单位数据字典
        """
        if debug.DEBUG:
            debug_print(f"[DEBUG LOAD] Loading unit: {unit_data.get('name')}, position=({unit_data.get('position_x')}, {unit_data.get('position_y')}), requires={unit_data.get('requires')}")
        
        # ✅ AI 生成: 先保存旧数据，避免在设置控件值时触发 on_property_changed
        old_unit_data = self.current_unit_data
        
        # 填充只读字段
        self.name_label.setText(unit_data.get('name', 'Unknown'))
        # ✅ AI 生成: type_combo 用 blockSignals 防止切换节点时修改上个节点的 unit_type
        self.type_combo.blockSignals(True)
        unit_type = unit_data.get('unit_type', '')
        if unit_type == 'tech':
            self.type_combo.setCurrentText('tech')
        else:
            self.type_combo.setCurrentText('')  # 空表示单位
        self.type_combo.blockSignals(False)
        self.side_label.setText(unit_data.get('side', '-'))
        self.period_label.setText(unit_data.get('period', '-'))
        self.stage_label.setText(str(unit_data.get('min_stage', '-')))
        self.cp_label.setText(str(unit_data.get('cp', '-')))
        
        tags = unit_data.get('tags', [])
        self.tags_label.setText(', '.join(tags) if tags else '-')
        
        # 填充可编辑字段
        self.costs_spinbox.blockSignals(True)
        # 使用 unit_data 中的 costs（默认 4），如果不存在则使用 4
        self.costs_spinbox.setValue(unit_data.get('costs', 4))
        self.costs_spinbox.blockSignals(False)
        
        self.pos_x_spinbox.blockSignals(True)
        self.pos_x_spinbox.setValue(unit_data.get('position_x', 0))
        self.pos_x_spinbox.blockSignals(False)
        
        self.pos_y_spinbox.blockSignals(True)
        self.pos_y_spinbox.setValue(unit_data.get('position_y', 0))
        self.pos_y_spinbox.blockSignals(False)
        
        self.requires_input.blockSignals(True)
        # 兼容处理：requires 可能是字符串或列表
        requires_data = unit_data.get('requires', '')
        if isinstance(requires_data, list):
            # ✅ 使用空格分隔多个父节点
            self.requires_input.setText(' '.join(requires_data))
        else:
            self.requires_input.setText(requires_data)
        self.requires_input.blockSignals(False)
        
        # ✅ 关键修复：在所有控件设置完成后，才更新 current_unit_data
        import copy
        self.current_unit_data = copy.deepcopy(unit_data)
        
        if debug.DEBUG:
            debug_print(f"[DEBUG LOAD] Loaded successfully, current_unit_data position=({self.current_unit_data.get('position_x')}, {self.current_unit_data.get('position_y')}), requires={self.current_unit_data.get('requires')}")
    
    def on_property_changed(self):
        """属性变化时触发"""
        if not self.current_unit_data:
            return
        
        if debug.DEBUG:
            debug_print(f"[DEBUG CHANGE] on_property_changed called for {self.current_unit_data.get('name')}, position=({self.current_unit_data.get('position_x')}, {self.current_unit_data.get('position_y')}), costs={self.current_unit_data.get('costs')}")
        
        # 更新当前数据
        self.current_unit_data['costs'] = self.costs_spinbox.value()
        self.current_unit_data['position_x'] = self.pos_x_spinbox.value()
        self.current_unit_data['position_y'] = self.pos_y_spinbox.value()
        # 保存单位类型：'tech' 或 ''（空表示单位）
        self.current_unit_data['unit_type'] = self.type_combo.currentText()
        # 将空格分隔的字符串转换为列表（支持多父节点）
        requires_text = self.requires_input.text().strip()
        if requires_text:
            # ✅ 使用空格分隔多个父节点
            self.current_unit_data['requires'] = [r.strip() for r in requires_text.split() if r.strip()]
        else:
            self.current_unit_data['requires'] = []
        
        if debug.DEBUG:
            debug_print(f"[DEBUG CHANGE] Emitting unit_updated with position=({self.current_unit_data['position_x']}, {self.current_unit_data['position_y']}), costs={self.current_unit_data['costs']}, requires={self.current_unit_data['requires']}")
        
        # 发送更新信号
        self.unit_updated.emit(self.current_unit_data)
    
    def reset_position(self):
        """重置位置到默认值"""
        if not self.current_unit_data:
            return
        
        # 重置为 0,0
        self.pos_x_spinbox.setValue(0)
        self.pos_y_spinbox.setValue(0)
