# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
科技树画布
支持节点拖拽、连线显示依赖关系
"""

from math import atan2, cos, sin, pi
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QGraphicsPixmapItem, QMenu, QApplication,
    QMessageBox, QShortcut, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QRegExp, QTimer
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, 
    QWheelEvent, QMouseEvent, QPolygonF, QKeySequence
)
from PyQt5.QtGui import QRegExpValidator

from src.parser import Unit
from src import debug
from src.debug import debug_print
from src.i18n import tr
from src.portrait_manager import PortraitManager


class TechTreeNode(QGraphicsRectItem):
    """科技树节点"""
    
    def __init__(self, unit: Unit, parent=None):
        super().__init__(parent)
        self.unit = unit
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            # 禁用 ItemIsMovable，使用自定义拖动逻辑避免冲突
            # QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        
        # 节点尺寸（0.6 x 0.6 量纲）
        # X: 0.6量纲 / 0.1 * 40px = 240px（6格）
        # Y: 0.6量纲 / 0.1 * 20px = 120px（3格，纵轴0.1量纲=20px）
        self.width = 240
        self.height = 120
        
        # 设置矩形
        self.setRect(0, 0, self.width, self.height)
        
        # 接受悬停事件
        self.setAcceptHoverEvents(True)
        
        # 设置 Z 值（节点在连线上方）
        self.setZValue(10)
        
        # 标记是否作为父节点被高亮
        self.highlighted_as_parent = False
        
        # 单边变色相关属性
        self.highlighted_edges = set()  # 需要高亮的边 {'top', 'bottom', 'left', 'right'}
        self.is_overlapping = False  # 是否重叠（全红）
        self.edge_items = []  # 存储高亮边线的 QGraphicsLineItem 列表
        
        # 保存拖动前的位置（用于撤销）
        self.old_position_x = unit.position_x
        self.old_position_y = unit.position_y
        
        # 样式
        self.set_pen_and_brush()
        
        # 节点尺寸 240×120，114:140 比例图像框
        self.img_w = 96   # 114:140 比例适配节点高度
        img_h = 118  # 96 * 140/114 ≈ 118
        self.image_box = QGraphicsRectItem(0, 1, self.img_w, img_h, self)
        self.image_box.setPen(QPen(QColor('#555555'), 1, Qt.DashLine))
        self.image_box.setBrush(QBrush(QColor('#2a2a2a')))
        self.portrait_item = QGraphicsPixmapItem(self)
        self.portrait_item.setVisible(False)
        
        # 右侧：Cost / Pos.X / Pos.Y（缩小字体，不超出矩形）
        Cost_font = QFont('Consolas', 16)
        Cost_font.setBold(True)
        tx = self.img_w + 5
        
        self.cost_text = QGraphicsTextItem(self)
        self.cost_text.setPlainText(f"Cost: {unit.costs}")
        self.cost_text.setDefaultTextColor(QColor('#d2b48c'))
        self.cost_text.setFont(Cost_font)
        self.cost_text.setPos(tx, 6)

        small_font = QFont('Consolas', 12)
        self.pos_x_text = QGraphicsTextItem(self)
        self.pos_x_text.setPlainText(f"Pos.X: {unit.position_x:g}")
        self.pos_x_text.setDefaultTextColor(QColor('#cccccc'))
        self.pos_x_text.setFont(small_font)
        self.pos_x_text.setPos(tx, 26)
        
        
        self.pos_y_text = QGraphicsTextItem(self)
        self.pos_y_text.setPlainText(f"Pos.Y: {unit.position_y:g}")
        self.pos_y_text.setDefaultTextColor(QColor('#cccccc'))
        self.pos_y_text.setFont(small_font)
        self.pos_y_text.setPos(tx, 46)
        
        # 矩形下方：单位名称 + Requires
        self.name_text = QGraphicsTextItem(self)
        self.name_text.setPlainText(unit.name)
        self.name_text.setDefaultTextColor(QColor('#ffffff'))
        font = QFont('Consolas', 15)
        font.setBold(True)
        self.name_text.setFont(font)
        self.name_text.setPos(0, self.height + 4)
        
        # Requires 分两色：标签 #f4a460，值 #d2b48c
        requires_font = QFont('Consolas', 14)
        self.requires_label_text = QGraphicsTextItem(self)
        self.requires_label_text.setPlainText('Requires: ')
        self.requires_label_text.setDefaultTextColor(QColor('#f4a460'))
        self.requires_label_text.setFont(requires_font)
        self.requires_label_text.setPos(0, self.height + 4 + 24)
        
        self.requires_value_text = QGraphicsTextItem(self)
        self.requires_value_text.setPlainText(self._format_requires_value(unit.requires))
        self.requires_value_text.setDefaultTextColor(QColor('#d2b48c'))
        self.requires_value_text.setFont(requires_font)
        self.requires_value_text.setPos(self.requires_label_text.boundingRect().width(), self.height + 4 + 24)
        
        # 添加烧瓶图标（科技单位标记）
        self.flask_icon = None
        if unit.unit_type == 'tech':
            self._draw_flask_icon()
        
        # 设置节点位置（从 unit 的 position_x/y 转换）
        self.update_position()
    
    def _draw_flask_icon(self):
        """
        绘制化学烧瓶图标（科技单位标记）
        
        化学烧瓶形状：锥形瓶身 + 圆柱形颈部 + 顶部开口
        放置在节点右上角
        """
        # 烧瓶尺寸和位置（相对于节点左上角）
        icon_size = 26  # 图标大小
        margin = 6      # 边距
        start_x = self.width - icon_size - margin  # 右上角
        start_y = margin
        
        # 计算烧瓶各部分尺寸
        neck_width = 8          # 颈部宽度
        neck_height = 8         # 颈部高度
        top_opening_y = start_y
        neck_bottom_y = start_y + neck_height
        body_bottom_y = start_y + icon_size
        
        # 颈部左右边界
        neck_left = start_x + (icon_size - neck_width) / 2
        neck_right = start_x + (icon_size + neck_width) / 2
        
        # 瓶底左右边界（比颈部宽）
        body_left = start_x + 2
        body_right = start_x + icon_size - 2
        
        pen = QPen(QColor('#4FC3F7'), 2)  # 浅蓝色
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        # 绘制烧瓶轮廓
        # 1. 顶部开口（横线）
        top_line = QGraphicsLineItem(
            neck_left, top_opening_y,
            neck_right, top_opening_y,
            self
        )
        top_line.setPen(pen)
        top_line.setZValue(11)
        
        # 2. 左颈部（竖线）
        left_neck = QGraphicsLineItem(
            neck_left, top_opening_y,
            neck_left, neck_bottom_y,
            self
        )
        left_neck.setPen(pen)
        left_neck.setZValue(11)
        
        # 3. 右颈部（竖线）
        right_neck = QGraphicsLineItem(
            neck_right, top_opening_y,
            neck_right, neck_bottom_y,
            self
        )
        right_neck.setPen(pen)
        right_neck.setZValue(11)
        
        # 4. 左侧锥形斜边（从颈部到底部）
        left_slope = QGraphicsLineItem(
            neck_left, neck_bottom_y,
            body_left, body_bottom_y - 2,
            self
        )
        left_slope.setPen(pen)
        left_slope.setZValue(11)
        
        # 5. 右侧锥形斜边（从颈部到底部）
        right_slope = QGraphicsLineItem(
            neck_right, neck_bottom_y,
            body_right, body_bottom_y - 2,
            self
        )
        right_slope.setPen(pen)
        right_slope.setZValue(11)
        
        # 6. 瓶底（横线）
        bottom_line = QGraphicsLineItem(
            body_left, body_bottom_y - 2,
            body_right, body_bottom_y - 2,
            self
        )
        bottom_line.setPen(pen)
        bottom_line.setZValue(11)
        
        # 7. 瓶身填充（使用多边形）
        from PyQt5.QtWidgets import QGraphicsPolygonItem
        flask_polygon = QPolygonF([
            QPointF(neck_left, neck_bottom_y),
            QPointF(neck_right, neck_bottom_y),
            QPointF(body_right, body_bottom_y - 2),
            QPointF(body_left, body_bottom_y - 2)
        ])
        fill_item = QGraphicsPolygonItem(flask_polygon, self)
        
        # 半透明填充
        fill_color = QColor('#4FC3F7')
        fill_color.setAlpha(80)
        fill_item.setBrush(QBrush(fill_color))
        # 无边框（使用空 QPen）
        no_pen = QPen()
        no_pen.setStyle(Qt.NoPen)
        fill_item.setPen(no_pen)
        fill_item.setZValue(10)
        
        # 保存引用以便后续清理
        self.flask_icon = {
            'top_line': top_line,
            'left_neck': left_neck,
            'right_neck': right_neck,
            'left_slope': left_slope,
            'right_slope': right_slope,
            'bottom_line': bottom_line,
            'fill': fill_item
        }
    
    def set_portrait(self, pixmap):
        """设置节点头像图片"""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(self.img_w, 118, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.portrait_item.setPixmap(scaled)
            x = (self.img_w - scaled.width()) / 2
            y = (118 - scaled.height()) / 2
            self.portrait_item.setPos(x, 1 + y)
            self.portrait_item.setVisible(True)
        else:
            self.portrait_item.setVisible(False)
    
    def update_position(self):
        """
        根据 unit.position_x 和 unit.position_y 更新节点在场景中的位置
        
        坐标转换：
        - position_x: 量纲值，每 0.1 = 40px
        - position_y: 量纲值，每 0.1 = 20px（纵轴像素为横轴的一半）
        
        ✅ AI 生成: 本文件原先定义了两个 update_position（后者覆盖前者），
        且内部设置一个早已失效的拖动标志类变量（itemChange 已无条件 return value），
        该标志写 6 处读 0 处，属死代码，现已连同重复定义一并移除。
        """
        grid_size_x = 40  # 横轴每0.1量纲 = 40px
        grid_size_y = 20  # 纵轴每0.1量纲 = 20px
        # 将量纲值转换为像素
        pixel_x = (self.unit.position_x / 0.1) * grid_size_x
        pixel_y = (self.unit.position_y / 0.1) * grid_size_y
        self.setPos(pixel_x, pixel_y)
    
    def _format_requires_value(self, requires) -> str:
        """格式化 requires 值部分（不含标签）"""
        if not requires:
            return "None"
        if isinstance(requires, list):
            if len(requires) == 0:
                return "None"
            elif len(requires) == 1:
                return requires[0]
            else:
                return ', '.join(requires)
        return requires if requires else "None"
    
    def set_pen_and_brush(self):
        """设置边框和填充颜色"""
        # 先清除高亮边线
        self.clear_edge_highlights()
        
        if self.is_overlapping:
            # 重叠：红色边框
            pen = QPen(QColor('#FF0000'), 2)
            self.setPen(pen)
            if self.unit.deployed:
                # 已部署：半透明红色
                color = QColor('#FF0000')
                color.setAlpha(128)
                self.setBrush(QBrush(color))
            elif self.unit.requires:
                # 有前置：红色填充
                self.setBrush(QBrush(QColor('#FF6666')))
            else:
                # 无前置：红色填充
                self.setBrush(QBrush(QColor('#FF6666')))
        elif self.highlighted_edges:
            # 有单边高亮：绘制红色边线
            # 先设置默认边框
            if self.unit.deployed:
                pen = QPen(QColor('#888888'), 2)
                color = QColor('#666666')
                color.setAlpha(128)
                brush = QBrush(color)
            elif self.unit.requires:
                pen = QPen(QColor('#3498DB'), 2)
                brush = QBrush(QColor('#2980B9'))
            else:
                pen = QPen(QColor('#2ECC71'), 2)
                brush = QBrush(QColor('#27AE60'))
            
            self.setPen(pen)
            self.setBrush(brush)
            
            # 绘制高亮的红色边线
            self._draw_highlighted_edges()
        else:
            # 正常状态
            if self.unit.deployed:
                # 已部署：半透明灰色
                pen = QPen(QColor('#888888'), 2)
                color = QColor('#666666')
                color.setAlpha(128)  # 设置透明度
                brush = QBrush(color)
            elif self.unit.requires:
                # 有前置：蓝色
                pen = QPen(QColor('#3498DB'), 2)
                brush = QBrush(QColor('#2980B9'))
            else:
                # 无前置：绿色
                pen = QPen(QColor('#2ECC71'), 2)
                brush = QBrush(QColor('#27AE60'))
            
            self.setPen(pen)
            self.setBrush(brush)
    
    def clear_edge_highlights(self):
        """清除所有高亮边线"""
        scene = self.scene()
        if scene:
            for edge_item in self.edge_items:
                scene.removeItem(edge_item)
        self.edge_items.clear()
    
    def _draw_highlighted_edges(self):
        """绘制高亮的红色边线（叠加在节点上方）"""
        if not self.highlighted_edges:
            return
        
        # 红色边线样式
        red_pen = QPen(QColor('#FF0000'), 3)
        
        # 获取节点在场景中的位置（关键修复：使用场景坐标）
        node_pos = self.pos()
        x1 = node_pos.x()
        y1 = node_pos.y()
        x2 = node_pos.x() + self.width
        y2 = node_pos.y() + self.height
        
        scene = self.scene()
        if not scene:
            return
        
        # 绘制上边
        if 'top' in self.highlighted_edges:
            line = QGraphicsLineItem(x1, y1, x2, y1)
            line.setPen(red_pen)
            line.setZValue(11)  # 在节点上方
            scene.addItem(line)
            self.edge_items.append(line)
        
        # 绘制下边
        if 'bottom' in self.highlighted_edges:
            line = QGraphicsLineItem(x1, y2, x2, y2)
            line.setPen(red_pen)
            line.setZValue(11)
            scene.addItem(line)
            self.edge_items.append(line)
        
        # 绘制左边
        if 'left' in self.highlighted_edges:
            line = QGraphicsLineItem(x1, y1, x1, y2)
            line.setPen(red_pen)
            line.setZValue(11)
            scene.addItem(line)
            self.edge_items.append(line)
        
        # 绘制右边
        if 'right' in self.highlighted_edges:
            line = QGraphicsLineItem(x2, y1, x2, y2)
            line.setPen(red_pen)
            line.setZValue(11)
            scene.addItem(line)
            self.edge_items.append(line)
    
    def update_from_unit(self, unit: Unit, update_pos: bool = True):
        """
        从 Unit 对象更新节点
        
        Args:
            unit: 单位对象
            update_pos: 是否更新位置（设置 requires 时不需要更新位置）
        """
        # ✅ AI 生成: 必须在覆盖 self.unit 之前取旧类型，否则 old==new 恒成立，
        # 导致 '' ↔ 'tech' 切换时烧瓶图标既不清除也不绘制（原实现的恒假分支）
        old_unit_type = getattr(self.unit, 'unit_type', '')
        new_unit_type = unit.unit_type
        
        self.unit = unit
        self.name_text.setPlainText(unit.name)
        self.cost_text.setPlainText(f"Cost: {unit.costs}")
        self.pos_x_text.setPlainText(f"Pos.X: {unit.position_x:g}")
        self.pos_y_text.setPlainText(f"Pos.Y: {unit.position_y:g}")
        
        # 更新 Requires 指示器
        self.requires_value_text.setPlainText(self._format_requires_value(unit.requires))
        
        # 更新烧瓶图标（科技单位标记）
        if old_unit_type != new_unit_type:
            # 单位类型发生变化，需要更新图标
            if self.flask_icon is not None:
                # 清除旧的烧瓶图标
                scene = self.scene()
                if scene:
                    for item in self.flask_icon.values():
                        scene.removeItem(item)
                self.flask_icon = None
            
            # 如果新类型是科技单位，绘制烧瓶图标
            if new_unit_type == 'tech':
                self._draw_flask_icon()
        
        self.set_pen_and_brush()
        
        # 强制刷新画布显示
        self.update()
        
        if update_pos:
            self.update_position()
    
    def itemChange(self, change, value):
        """处理项目变化"""
        if change == QGraphicsRectItem.ItemPositionChange:
            # ✅ 关键修复：完全跳过 itemChange 的网格对齐，避免意外修改位置
            # 网格对齐只在明确需要的地方进行（拖动释放、撤销恢复等）
            return value
        
        elif change == QGraphicsRectItem.ItemSelectedChange:
            if value:
                # 选中时高亮（金色边框）
                if self.unit.deployed:
                    pen = QPen(QColor('#FFA500'), 3)  # 橙色
                else:
                    pen = QPen(QColor('#FFD700'), 3)  # 金色
                self.setPen(pen)
                
                # 高亮父节点（通过视图访问 nodes 字典）
                requires_list = self.unit.requires if isinstance(self.unit.requires, list) else ([self.unit.requires] if self.unit.requires else [])
                if requires_list and self.scene() and self.scene().views():
                    view = self.scene().views()[0]
                    if hasattr(view, 'nodes'):
                        for req_name in requires_list:
                            if req_name in view.nodes:
                                parent_node = view.nodes[req_name]
                                parent_node.highlight_as_parent()
            else:
                # 取消选中时，不要直接恢复默认样式
                # 而是重新运行重叠检测，确保颜色正确
                if self.scene() and self.scene().views():
                    view = self.scene().views()[0]
                    if hasattr(view, 'check_node_overlaps'):
                        # 重新检测所有节点的重叠状态
                        view.check_node_overlaps()
                    
                    # ✅ AI 生成: 重置当前节点的边框颜色（编辑模式下 overlap check 无效）
                    self.set_pen_and_brush()
                    
                    # 取消所有节点的父节点高亮状态
                    if hasattr(view, 'nodes'):
                        for node in view.nodes.values():
                            node.unhighlight_as_parent()
        
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 拖动结束后更新连线和坐标显示"""
        super().mouseReleaseEvent(event)
        
        # 通知场景更新连线
        if self.scene():
            # 通过父视图获取 nodes 字典
            view = self.scene().views()[0] if self.scene().views() else None
            if view and hasattr(view, 'nodes'):
                view.scene.update_edges(view.nodes)
                
                # 更新场景大小以适应内容
                if hasattr(view, '_update_scene_rect'):
                    view._update_scene_rect()
                
                # ✅ 关键：禁用节点级别的 position_changed 信号发送
                # 统一由 TechTreeCanvas.mouseReleaseEvent 处理撤销逻辑
                # 避免重复记录和 old_position_x 数据过期问题
                # if hasattr(view, 'unit_position_changed'):
                #     unit_data = {...}
                #     view.unit_position_changed.emit(unit_data)
    
    def mouseDoubleClickEvent(self, event):
        """双击事件 - 修改 Costs 值"""
        # 检查是否在选择前置单位模式，如果是则不响应双击
        if hasattr(self.scene(), 'setting_requires_mode') and self.scene().setting_requires_mode:
            return
        
        # 使用自定义对话框实现输入限制
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        
        dialog = QDialog()
        dialog.setWindowTitle(tr('修改 Costs'))
        dialog.setFixedSize(350, 150)
        
        layout = QVBoxLayout()
        
        # 提示标签
        label = QLabel(tr('请输入 "{name}" 的新 Costs 值 (0-1000):').format(name=self.unit.name))
        layout.addWidget(label)
        
        # 输入框
        line_edit = QLineEdit()
        current_costs = str(self.unit.costs) if self.unit.costs is not None else ''
        line_edit.setText(current_costs)
        
        # 设置正则表达式验证器：只允许 0-1000 的整数
        reg_exp = QRegExp(r'^(1000|[1-9]\d{0,2}|0)$')
        validator = QRegExpValidator(reg_exp, line_edit)
        line_edit.setValidator(validator)
        
        layout.addWidget(line_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        ok_button = QPushButton(tr('确定'))
        cancel_button = QPushButton(tr('取消'))
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # 连接按钮信号
        result = {'value': None}
        
        def on_ok():
            text = line_edit.text()
            if text == '':
                QMessageBox.warning(dialog, tr('错误'), tr('Costs 不能为空！'))
                return
            value = int(text)
            if value < 0 or value > 1000:
                QMessageBox.warning(dialog, tr('错误'), tr('Costs 必须在 0-1000 之间！'))
                return
            result['value'] = value
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)
        
        # 按回车键确认
        line_edit.returnPressed.connect(on_ok)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted and result['value'] is not None:
            costs_value = result['value']
            
            # 保存旧值用于撤销
            old_costs = self.unit.costs
            
            # 更新单位数据
            self.unit.costs = costs_value
            
            # 更新显示文本
            self.cost_text.setPlainText(f"Cost: {costs_value}")
            
            # 发送属性变更信号（用于撤销）
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, 'unit_property_changed'):
                    view.unit_property_changed.emit(
                        self.unit.name,
                        'costs',
                        old_costs,
                        costs_value
                    )
    
    def hoverEnterEvent(self, event):
        """鼠标悬停进入事件"""
        super().hoverEnterEvent(event)
        
        # 检查场景是否在选择前置单位模式
        if hasattr(self.scene(), 'setting_requires_mode') and self.scene().setting_requires_mode:
            # 高亮显示（亮绿色边框）
            highlight_pen = QPen(QColor('#00FF00'), 4)  # 亮绿色，4像素宽
            highlight_pen.setStyle(Qt.DashLine)  # 虚线
            self.setPen(highlight_pen)
    
    def hoverLeaveEvent(self, event):
        """鼠标悬停离开事件"""
        super().hoverLeaveEvent(event)
        
        # 恢复原来的样式
        if hasattr(self.scene(), 'setting_requires_mode') and self.scene().setting_requires_mode:
            self.set_pen_and_brush()
    
    def highlight_as_parent(self):
        """高亮显示为父节点（当子节点被选中时）"""
        # 使用紫色边框表示父节点
        highlight_pen = QPen(QColor('#9B59B6'), 4)  # 紫色，4像素宽
        highlight_pen.setStyle(Qt.SolidLine)
        self.setPen(highlight_pen)
        self.highlighted_as_parent = True
    
    def unhighlight_as_parent(self):
        """取消父节点高亮"""
        # 只取消如果当前是父节点高亮状态
        if self.highlighted_as_parent:
            self.highlighted_as_parent = False
            # ✅ AI 生成: 始终恢复默认样式（重叠检测已在 itemChange 中执行）
            self.set_pen_and_brush()
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        try:
            menu = QMenu()
            
            # 如果正在设置 requires 模式，显示取消选项
            scene = self.scene()
            if not scene:
                return
            
            if scene.setting_requires_mode:
                cancel_action = menu.addAction("❌ 取消设置前置")
                action = menu.exec_(event.screenPos())
                if action == cancel_action:
                    scene.cancel_set_requires()
                return
            
            delete_action = menu.addAction(tr("🗑️ 删除节点"))
            menu.addSeparator()
            set_requires_action = menu.addAction(tr("🔗 选择前置单位"))
            
            action = menu.exec_(event.screenPos())
            
            if action == delete_action:
                # 发送删除信号（由场景处理）
                scene.item_deleted.emit(self)
            elif action == set_requires_action:
                # 进入设置 requires 模式
                scene.start_set_requires(self.unit.name)
        except Exception as e:
            pass


class TechTreeScene(QGraphicsScene):
    """科技树场景，管理连线和节点"""
    
    # 信号
    item_deleted = pyqtSignal(object)
    # 信号：完成设置 requires（子节点名称，父节点名称）
    requires_set = pyqtSignal(str, str)
    # 信号：状态消息（用于显示在状态栏）
    status_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.edges = []  # 存储连线
        self.setting_requires_mode = False  # 是否在选择前置单位模式
        self.requires_child_name = ""  # 正在设置 requires 的子节点
    
    def update_edges(self, nodes_dict: dict):
        """
        更新所有连线（支持多个父节点）
        
        Args:
            nodes_dict: {unit_name: TechTreeNode} 字典
        """
        # 清除旧连线
        for edge in self.edges:
            self.removeItem(edge)
        self.edges.clear()
        
        # 创建新连线（带箭头）
        pen = QPen(QColor('#E74C3C'), 2)  # 红色连线
        pen.setStyle(Qt.DashLine)
        
        for name, node in nodes_dict.items():
            # requires 现在是列表，支持多个父节点
            requires_list = node.unit.requires if isinstance(node.unit.requires, list) else ([node.unit.requires] if node.unit.requires else [])
            
            for req_name in requires_list:
                if req_name and req_name in nodes_dict:
                    parent_node = nodes_dict[req_name]
                    
                    # 计算智能连接点（从节点边缘最近点连接）
                    # start_pos: 父节点边缘（出口）
                    start_pos = self._get_connection_point(parent_node, node, is_start=True)
                    # end_pos: 子节点边缘（入口）
                    end_pos = self._get_connection_point(parent_node, node, is_start=False)
                    
                    # 创建连线
                    line = QGraphicsLineItem(
                        start_pos.x(), start_pos.y(),
                        end_pos.x(), end_pos.y()
                    )
                    line.setPen(pen)
                    line.setZValue(5)  # 连线在节点下方，确保不遮挡节点
                    self.addItem(line)
                    self.edges.append(line)
                    
                    # 添加箭头（指向子节点）
                    arrow_size = 14  # 箭头大小
                    # 计算角度
                    from math import atan2, cos, sin, pi
                    dx = end_pos.x() - start_pos.x()
                    dy = end_pos.y() - start_pos.y()
                    angle = atan2(dy, dx)
                    
                    # 计算箭头的两个点
                    arrow_p1 = QPointF(
                        end_pos.x() - arrow_size * cos(angle - pi / 6),
                        end_pos.y() - arrow_size * sin(angle - pi / 6)
                    )
                    arrow_p2 = QPointF(
                        end_pos.x() - arrow_size * cos(angle + pi / 6),
                        end_pos.y() - arrow_size * sin(angle + pi / 6)
                    )
                    
                    # 创建箭头多边形
                    arrow_polygon = QPolygonF([end_pos, arrow_p1, arrow_p2])
                    arrow_item = QGraphicsPolygonItem(arrow_polygon)
                    arrow_item.setBrush(QColor('#E74C3C'))
                    arrow_item.setPen(QPen(QColor('#E74C3C'), 1))  # 添加边框
                    arrow_item.setZValue(5)  # 箭头也在节点下方
                    self.addItem(arrow_item)
                    self.edges.append(arrow_item)
    
    def _get_connection_point(self, from_node, to_node, is_start: bool) -> QPointF:
        """
        计算两个节点之间的最佳连接点（从节点边缘）
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            is_start: 是否是起始点（True=父节点出口，False=子节点入口）
            
        Returns:
            连接点的坐标
        """
        # 获取两个节点的中心点
        from_center = from_node.pos() + QPointF(from_node.width / 2, from_node.height / 2)
        to_center = to_node.pos() + QPointF(to_node.width / 2, to_node.height / 2)
        
        # 计算方向向量
        dx = to_center.x() - from_center.x()
        dy = to_center.y() - from_center.y()
        
        # 根据相对位置决定从哪个边缘连接
        if is_start:
            # 起始节点（父节点）：从底部、右侧或左侧出去
            if abs(dy) > abs(dx):
                # 垂直方向更远，从顶部或底部
                if dy > 0:
                    # 目标在下方，从底部出去
                    return from_node.pos() + QPointF(from_node.width / 2, from_node.height)
                else:
                    # 目标在上方，从顶部出去
                    return from_node.pos() + QPointF(from_node.width / 2, 0)
            else:
                # 水平方向更远，从左侧或右侧
                if dx > 0:
                    # 目标在右侧，从右侧出去
                    return from_node.pos() + QPointF(from_node.width, from_node.height / 2)
                else:
                    # 目标在左侧，从左侧出去
                    return from_node.pos() + QPointF(0, from_node.height / 2)
        else:
            # 目标节点（子节点）：从顶部、左侧或右侧进入
            if abs(dy) > abs(dx):
                # 垂直方向更远，从顶部或底部进入
                if dy > 0:
                    # 来自上方，从顶部进入
                    return to_node.pos() + QPointF(to_node.width / 2, 0)
                else:
                    # 来自下方，从底部进入
                    return to_node.pos() + QPointF(to_node.width / 2, to_node.height)
            else:
                # 水平方向更远，从左侧或右侧进入
                if dx > 0:
                    # 来自左侧，从左侧进入
                    return to_node.pos() + QPointF(0, to_node.height / 2)
                else:
                    # 来自右侧，从右侧进入
                    return to_node.pos() + QPointF(to_node.width, to_node.height / 2)
    
    def start_set_requires(self, child_name: str):
        """
        开始设置 requires 关系
        
        Args:
            child_name: 子节点（需要设置前置的单位）名称
        """
        self.setting_requires_mode = True
        self.requires_child_name = child_name
        
        # 改变光标样式提示用户
        try:
            if self.views() and len(self.views()) > 0:
                self.views()[0].setCursor(Qt.CrossCursor)
        except Exception:
            pass
        
        # 发送状态消息
        self.status_message.emit(tr('🔗 正在为 "{name}" 选择前置单位 | 点击目标单位或按 ESC 取消').format(name=child_name))
    
    def cancel_set_requires(self):
        """取消设置 requires 模式"""
        self.setting_requires_mode = False
        child_name = self.requires_child_name
        self.requires_child_name = ""
        
        # 恢复光标
        try:
            if self.views() and len(self.views()) > 0:
                self.views()[0].unsetCursor()
        except Exception:
            pass
        
        # 发送取消消息
        if child_name:
            self.status_message.emit(tr('❌ 已取消为 "{name}" 设置前置单位 | 就绪').format(name=child_name))
    
    def complete_set_requires(self, parent_name: str):
        """
        完成设置 requires 关系
        
        Args:
            parent_name: 父节点（前置单位）名称
        """
        if self.requires_child_name and parent_name:
            # 发送信号通知主窗口更新
            self.requires_set.emit(self.requires_child_name, parent_name)
        
        # 退出模式
        self.cancel_set_requires()
        
        # 清除所有节点的悬停高亮状态
        try:
            if self.views() and len(self.views()) > 0:
                canvas = self.views()[0]
                if hasattr(canvas, 'nodes'):
                    for node in canvas.nodes.values():
                        node.set_pen_and_brush()
        except Exception:
            pass


class TechTreeCanvas(QGraphicsView):
    """科技树画布"""
    
    # 全局头像管理器
    portrait_manager = PortraitManager()
    
    # 信号：选中单位
    unit_selected = pyqtSignal(dict)
    # 信号：删除单位（传递单位名称）
    unit_deleted = pyqtSignal(str)
    # 信号：删除单位用于撤销（传递完整单位数据）
    unit_delete_for_undo = pyqtSignal(dict)
    # 信号：开始设置 requires 关系（传递子节点名称）
    start_set_requires = pyqtSignal(str)
    # 信号：状态消息（转发场景的信号）
    status_message = pyqtSignal(str)
    # 信号：单位位置变化（用于更新属性面板坐标）
    unit_position_changed = pyqtSignal(dict)
    # 信号：批量单位位置变化（用于撤销，格式：{unit_name: {name, position_x, position_y, old_position_x, old_position_y}, ...}）
    batch_unit_position_changed = pyqtSignal(dict)
    # 信号：从列表拖拽单位到画布（传递 Unit 对象，已包含位置信息）
    unit_dropped_at_position = pyqtSignal(object)
    # 信号：单位属性变更（用于撤销，参数：unit_name, property_name, old_value, new_value）
    unit_property_changed = pyqtSignal(str, str, object, object)
    # 信号：节点数量变化（用于更新工具栏按钮状态）
    node_count_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        # 场景
        self.scene = TechTreeScene()
        self.setScene(self.scene)
        
        # 节点字典 {unit_name: TechTreeNode}
        self.nodes = {}
        
        # 缩放级别（默认50%）
        self.zoom_level = 0.50
        
        # 双击/三击追踪
        self.last_click_time = 0
        self.last_click_node = None
        self.click_count = 0
        
        # 设置 requires 模式
        self.setting_requires_mode = False
        self.requires_child_name = ""  # 正在设置 requires 的子节点名称
        
        # 当前网格大小（用于跟踪是否需要重绘）
        self.current_grid_width = 3000
        self.current_grid_height = 2000
        # ✅ AI 生成: 网格/场景矩形原点，与 _update_scene_rect 保持一致
        self.grid_origin_x = 0
        self.grid_origin_y = 0
        
        # 预览模式标志（默认编辑模式）
        self.preview_mode = False
        
        # ✅ AI 生成: 追踪网格背景项，避免全场景清除重建
        self.grid_items = []
        
        # ✅ AI 生成: 重叠检测防抖定时器
        self._overlap_timer = None
        
        # 初始化
        self.init_canvas()
        self.setAcceptDrops(True)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 连接信号
        self.scene.item_deleted.connect(self.on_item_deleted)
        
        # 转发场景的状态消息信号
        self.scene.status_message.connect(self.status_message)
        
        # 强制设置焦点
        self.setFocus()
        
        # 注意：Ctrl+Z 快捷键由主窗口的 keyPressEvent 处理，这里不注册以避免冲突
    
    def init_canvas(self):
        """初始化画布"""
        # 设置渲染提示
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # 初始缩放 50%
        self.scale(0.50, 0.50)
        
        # 矩形框选相关
        self.is_selecting = False
        self.selection_start_pos = None
        self.selection_rect = None
        
        # 多节点拖动相关
        self.is_dragging_nodes = False
        self.drag_start_pos = None
        self.dragged_nodes_initial_positions = {}  # {node_name: (x, y)}
        # ✅ AI 生成: 按下时快照的 unit 逻辑坐标 {node_name: (position_x, position_y)}，供撤销使用
        self.dragged_units_initial_logical = {}
        
        # 中键拖动画布相关
        self.is_panning = False
        self.pan_start_pos = None
        
        # 使用 NoDrag 模式，完全由自定义鼠标事件处理（框选、选中、拖动）
        self.setDragMode(QGraphicsView.NoDrag)
        
        # 设置视口更新模式
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # ✅ 设置滚动条样式，使其更明显
        self.setStyleSheet("""
            QScrollBar:horizontal {
                border: 1px solid #555555;
                background: #2a2a2a;
                height: 14px;
                margin: 0px 14px 0px 14px;
            }
            QScrollBar::handle:horizontal {
                background: #4A90E2;
                min-width: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5BA3F5;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: #3a3a3a;
                width: 14px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #2a2a2a;
            }
            QScrollBar:vertical {
                border: 1px solid #555555;
                background: #2a2a2a;
                width: 14px;
                margin: 14px 0px 14px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4A90E2;
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5BA3F5;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: #3a3a3a;
                height: 14px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #2a2a2a;
            }
        """)
        
        # 背景色
        self.setBackgroundBrush(QColor('#1e1e1e'))
        
        # 绘制网格（初始大小）
        self.draw_grid()
        
        # 设置场景大小（从 0,0 开始）
        self.scene.setSceneRect(0, 0, 3000, 2000)
    
    def draw_grid(self):
        """绘制网格背景（含标尺）
        
        ✅ AI 生成: 网格以 grid_origin_x / grid_origin_y 为原点绘制，与 _update_scene_rect
        的 sceneRect 对齐。原实现恒从绝对坐标 (0,0) 起画，而 sceneRect 原点可能被设为
        min_x>0，导致内容远离原点时整个可见区没有网格与标尺。
        
        横轴每0.1量纲 = 40px，纵轴每0.1量纲 = 20px
        """
        grid_size_x = 40  # 横轴网格间距
        grid_size_y = 20  # 纵轴网格间距
        x0 = self.grid_origin_x
        y0 = self.grid_origin_y
        width = self.current_grid_width
        height = self.current_grid_height
        
        pen = QPen(QColor('#333333'), 1)
        
        # 标尺样式（放大字体）
        ruler_pen = QPen(QColor('#666666'), 1)
        ruler_font = QFont('Consolas', 12)  # 从 10 放大到 12
        
        # ✅ AI 生成: 新建 grid_items 列表（不清空旧引用，由调用方负责）
        self.grid_items = []
        
        # 垂直线 + 横向标尺（每格0.1量纲，40px）
        for x in range(0, width + 1, grid_size_x):
            abs_x = x0 + x
            # 网格线
            line = self.scene.addLine(abs_x, y0, abs_x, y0 + height, pen)
            line.setZValue(-1)  # 网格在最底层
            self.grid_items.append(line)
            
            # 标尺数字（只在主要刻度显示）
            if x % (grid_size_x * 10) == 0:  # 每10格（1.0量纲）显示数字
                ruler_value = abs_x / grid_size_x * 0.1  # 计算量纲值
                text = self.scene.addText(f'{ruler_value:.1f}', ruler_font)
                text.setDefaultTextColor(QColor('#888888'))
                text.setPos(abs_x + 2, y0 + 2)
                text.setZValue(-1)
                self.grid_items.append(text)
        
        # 水平线 + 纵向标尺（每格0.1量纲，20px）
        for y in range(0, height + 1, grid_size_y):
            abs_y = y0 + y
            # 网格线
            line = self.scene.addLine(x0, abs_y, x0 + width, abs_y, pen)
            line.setZValue(-1)  # 网格在最底层
            self.grid_items.append(line)
            
            # 标尺数字（只在主要刻度显示，每1.0量纲）
            if y % (grid_size_y * 10) == 0:  # 每10格（1.0量纲）显示数字
                ruler_value = abs_y / grid_size_y * 0.1  # 计算量纲值
                text = self.scene.addText(f'{ruler_value:.1f}', ruler_font)
                text.setDefaultTextColor(QColor('#888888'))
                text.setPos(x0 + 2, abs_y + 2)
                text.setZValue(-1)
                self.grid_items.append(text)
    
    def add_unit_node(self, unit: Unit):
        """
        添加单位节点
        
        Args:
            unit: 单位对象
        """
        if unit.name in self.nodes:
            # 节点已存在，更新
            self.nodes[unit.name].update_from_unit(unit)
        else:
            # 创建新节点
            node = TechTreeNode(unit)
            self.scene.addItem(node)
            self.nodes[unit.name] = node
            # 加载头像
            pixmap = self.portrait_manager.get_portrait(unit.name)
            if pixmap:
                node.set_portrait(pixmap)
            # 发送节点数量变化信号
            self.node_count_changed.emit(len(self.nodes))
        
        # 更新场景大小以适应内容
        self._update_scene_rect()
        
        # 更新连线
        self.scene.update_edges(self.nodes)
        
        # ✅ AI 生成: 防抖延迟重叠检测（避免重复 O(n²) 计算）
        self._schedule_overlap_check()
    
    def update_unit_node(self, unit: Unit, update_pos: bool = True):
        """
        更新单位节点
        
        Args:
            unit: 单位对象
            update_pos: 是否更新位置（默认True，设置requires时传False）
        """
        if unit.name in self.nodes:
            self.nodes[unit.name].update_from_unit(unit, update_pos=update_pos)
            # 更新连线
            self.scene.update_edges(self.nodes)
            
            # ✅ AI 生成: 防抖延迟重叠检测
            if update_pos:
                self._schedule_overlap_check()
    
    def refresh_portraits(self):
        """刷新所有节点的头像（资源文件夹切换后调用）"""
        for node in self.nodes.values():
            QApplication.processEvents()
            pixmap = self.portrait_manager.get_portrait(node.unit.name)
            node.set_portrait(pixmap)
    
    def clear_canvas(self):
        """清空画布"""
        # ✅ 先清除 edges 列表中的引用（避免访问已删除的 QGraphicsLineItem）
        self.scene.edges.clear()
        
        # 清空网格引用
        self.grid_items.clear()
        
        # 清空场景（会删除所有 items，包括 nodes 和 edges）
        self.scene.clear()
        
        # 清空 nodes 字典
        self.nodes.clear()
        
        # 发送节点数量变化信号（清空后为0）
        self.node_count_changed.emit(0)
        
        # 恢复默认场景大小
        self.current_grid_width = 3000
        self.current_grid_height = 2000
        # ✅ AI 生成: 同步复位网格原点，否则 draw_grid 会在旧原点绘制
        self.grid_origin_x = 0
        self.grid_origin_y = 0
        self.scene.setSceneRect(0, 0, 3000, 2000)
        
        # 重新绘制网格
        self.draw_grid()
    
    def _update_scene_rect(self):
        """更新场景大小以适应所有节点（扩展网格和标尺）

        ✅ AI 生成: 统一两个分支的 sceneRect 口径（原 1267/1274 两处算法不同，
        导致场景尺寸在分支间抖动），并让 sceneRect 原点与网格原点严格一致。
        """
        grid_size_base = 40  # 网格基准间距，sceneRect 与网格均按此对齐
        
        if not self.nodes:
            # 没有节点，使用默认大小
            self.grid_origin_x = 0
            self.grid_origin_y = 0
            self.current_grid_width = 3000
            self.current_grid_height = 2000
            self.scene.setSceneRect(0, 0, 3000, 2000)
            return
        
        # 计算所有节点的边界（不依赖 itemsBoundingRect，避免包含网格线）
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for node in self.nodes.values():
            pos = node.pos()
            min_x = min(min_x, pos.x())
            min_y = min(min_y, pos.y())
            max_x = max(max_x, pos.x() + node.width)
            max_y = max(max_y, pos.y() + node.height)
        
        # 添加边距（至少 500px）
        margin = 500
        min_x = max(0, min_x - margin)
        min_y = max(0, min_y - margin)
        max_x = max(3000, max_x + margin)  # 至少保持 3000 宽度
        max_y = max(2000, max_y + margin)  # 至少保持 2000 高度
        
        # ✅ AI 生成: 网格/场景矩形原点向下对齐到网格间距的整数倍，
        # 保证标尺读数仍是 0.1 量纲的整齐倍数
        origin_x = (int(min_x) // grid_size_base) * grid_size_base
        origin_y = (int(min_y) // grid_size_base) * grid_size_base
        
        # ✅ AI 生成: 统一口径 —— span = 从原点到最大边的距离，向上取整到 grid 倍数
        span_x = max_x - origin_x
        span_y = max_y - origin_y
        new_width = int(((span_x // grid_size_base) + 1) * grid_size_base)
        new_height = int(((span_y // grid_size_base) + 1) * grid_size_base)
        
        # ✅ AI 生成: 原点变化同样需要重绘网格，否则网格会与场景错位
        origin_changed = (origin_x != self.grid_origin_x) or (origin_y != self.grid_origin_y)
        
        # ✅ AI 生成: 只有当大小变化超过 200px 时才重绘网格（避免频繁重绘）
        if origin_changed or abs(new_width - self.current_grid_width) > 200 or abs(new_height - self.current_grid_height) > 200:
            self.grid_origin_x = origin_x
            self.grid_origin_y = origin_y
            self.current_grid_width = new_width
            self.current_grid_height = new_height
            
            # 仅移除旧网格项，保留所有节点和连线
            for item in self.grid_items:
                try:
                    self.scene.removeItem(item)
                except Exception:
                    pass
            self.grid_items.clear()
            
            # 更新场景大小并重新绘制网格（两个分支口径完全一致）
            self.scene.setSceneRect(origin_x, origin_y, new_width, new_height)
            self.draw_grid()
            
            # 重新创建连线（节点已保留，只需刷新连线）
            self.scene.update_edges(self.nodes)
        else:
            # 不需要重绘网格，只更新场景大小（与重绘分支口径一致）
            self.scene.setSceneRect(origin_x, origin_y, new_width, new_height)
    
    def set_preview_mode(self, enabled: bool):
        """
        设置预览模式
        
        Args:
            enabled: True=预览模式（启用检测），False=编辑模式（禁用检测）
        """
        self.preview_mode = enabled
        
        if not enabled:
            # 切换到编辑模式，清除所有高亮
            for node in self.nodes.values():
                # 清除标志位
                node.is_overlapping = False
                node.highlighted_edges.clear()
                # 清除视觉元素并重新设置样式
                node.clear_edge_highlights()
                node.set_pen_and_brush()
        else:
            # 切换到预览模式，立即检测一次
            self.check_node_overlaps()
    
    def _schedule_overlap_check(self):
        """
        ✅ AI 生成: 防抖延迟重叠检测（多次调用合并为一次）

        性能修复：原实现用 `self._overlap_timer = QTimer.singleShot(0, ...)`，
        而 PyQt5 的 QTimer.singleShot 是静态方法、恒返回 None，导致 `stop()` 分支永不执行、
        每个节点各排一次单次定时器 → 加载 N 个节点的总代价退化为 O(N³)。
        现改为持有真正的 QTimer 实例并 setSingleShot(True)，把同一次事件循环内的
        多次调用合并为一次检测。
        """
        if self._overlap_timer is None:
            self._overlap_timer = QTimer(self)
            self._overlap_timer.setSingleShot(True)
            self._overlap_timer.timeout.connect(self.check_node_overlaps)
        self._overlap_timer.stop()
        self._overlap_timer.start(0)

    def check_node_overlaps(self):
        """
        检查节点重叠/相邻情况，实现单边变色效果
        
        - 节点真正重叠：节点全红（is_overlapping = True）
        - 水平或垂直方向相邻 ≤ 2格：对应方向的边变红
        - 无附近节点：边框正常颜色
        
        判断逻辑：
        - 检查每对节点的边界框
        - 如果重叠：标记为重叠
        - 如果水平间隙 ≤ 2格（80px）：标记左右边
        - 如果垂直间隙 ≤ 2格（40px）：标记上下边
        
        注意：仅在预览模式下执行检测
        """
        # 仅在预览模式下执行检测
        if not self.preview_mode:
            return
        
        try:
            # ✅ AI 生成: 全部调试输出统一用 `if debug.DEBUG:` 短路，
            # 避免 DEBUG=False 时仍付出 f-string 组装与 stdout.flush() 的开销
            if debug.DEBUG:
                debug_print("\n=== [Overlap] check_node_overlaps() START ===")
                debug_print(f"=== [Overlap] 节点数量: {len(self.nodes)} ===")
            
            if len(self.nodes) < 2:
                if debug.DEBUG:
                    debug_print("=== [Overlap] 节点数量不足，跳过检测 ===")
                return
            
            grid_size_x = 40  # 横轴每0.1量纲 = 40px
            grid_size_y = 20  # 纵轴每0.1量纲 = 20px
                
            # 2格的像素距离
            threshold_x = 2 * grid_size_x  # 80px（横向2格）
            threshold_y = 2 * grid_size_y  # 40px（纵向2格）
                
            # 记录每个节点的边高亮情况 {node_name: {'top', 'bottom', 'left', 'right'}}
            node_edge_highlights = {name: set() for name in self.nodes}
            # 记录每个节点是否重叠
            node_overlapping = set()
                
            # 检查每对节点
            node_names = list(self.nodes.keys())
            if debug.DEBUG:
                debug_print(f"=== [Overlap] 开始检测 {len(node_names)} 个节点 ===")
        
            # 调试：输出 reinforcement_stage 节点的位置
            if debug.DEBUG:
                for name in node_names:
                    if 'reinforcement_stage' in name:
                        node = self.nodes[name]
                        pos = node.pos()
                        debug_print(f"  节点 {name}: pos=({pos.x():.1f}, {pos.y():.1f}), rect=[{pos.x():.1f}, {pos.x()+node.width:.1f}, {pos.y():.1f}, {pos.y()+node.height:.1f}]")
        
            for i, name_a in enumerate(node_names):
                node_a = self.nodes[name_a]
                pos_a = node_a.pos()
                
                # 计算节点A边界框
                a_left = pos_a.x()
                a_right = pos_a.x() + node_a.width
                a_top = pos_a.y()
                a_bottom = pos_a.y() + node_a.height
                
                for j, name_b in enumerate(node_names):
                    if i >= j:
                        continue  # 跳过自己和重复检查
                        
                    node_b = self.nodes[name_b]
                    pos_b = node_b.pos()
                        
                    # 计算节点B边界框
                    b_left = pos_b.x()
                    b_right = pos_b.x() + node_b.width
                    b_top = pos_b.y()
                    b_bottom = pos_b.y() + node_b.height
                        
                    # 检查是否重叠（边界框相交）
                    is_overlapping_boxes = (a_right > b_left and a_left < b_right and
                                            a_bottom > b_top and a_top < b_bottom)
                    
                    is_fully_overlapping = False
                    if is_overlapping_boxes:
                        # 计算重叠量
                        overlap_x = min(a_right, b_right) - max(a_left, b_left)
                        overlap_y = min(a_bottom, b_bottom) - max(a_top, b_top)
                        
                        # 只要重叠量≥1格就视为完全重叠（横40px，纵20px）
                        if overlap_x >= grid_size_x and overlap_y >= grid_size_y:
                            node_overlapping.add(name_a)
                            node_overlapping.add(name_b)
                            is_fully_overlapping = True
                    
                    # 如果不是完全重叠，计算间隙并检测边框
                    if not is_fully_overlapping:
                        # 计算水平方向间隙
                        if a_right <= b_left:
                            gap_x = b_left - a_right  # B在A右侧
                            a_edge_h = 'right'
                            b_edge_h = 'left'
                        elif b_right <= a_left:
                            gap_x = a_left - b_right  # B在A左侧
                            a_edge_h = 'left'
                            b_edge_h = 'right'
                        else:
                            gap_x = -1  # 水平方向重叠，不标记边
                            a_edge_h = None
                            b_edge_h = None
                            
                        # 计算垂直方向间隙
                        if a_bottom <= b_top:
                            gap_y = b_top - a_bottom  # B在A下方
                            a_edge_v = 'bottom'
                            b_edge_v = 'top'
                        elif b_bottom <= a_top:
                            gap_y = a_top - b_bottom  # B在A上方
                            a_edge_v = 'top'
                            b_edge_v = 'bottom'
                        else:
                            gap_y = -1  # 垂直方向重叠，不标记边
                            a_edge_v = None
                            b_edge_v = None
                        
                        # 调试：输出 reinforcement_stage 节点对的详细信息
                        if debug.DEBUG and ('reinforcement_stage' in name_a or 'reinforcement_stage' in name_b):
                            if 'reinforcement_stage_4' in name_a or 'reinforcement_stage_5' in name_a or \
                               'reinforcement_stage_4' in name_b or 'reinforcement_stage_5' in name_b:
                                debug_print(f"\n=== [Overlap] 关键节点对: {name_a} <-> {name_b} ===")
                                debug_print(f"  节点A [{a_left:.1f}, {a_right:.1f}] x [{a_top:.1f}, {a_bottom:.1f}]")
                                debug_print(f"  节点B [{b_left:.1f}, {b_right:.1f}] x [{b_top:.1f}, {b_bottom:.1f}]")
                                debug_print(f"  gap_x = {gap_x if gap_x >= 0 else '重叠'}")
                                debug_print(f"  gap_y = {gap_y if gap_y >= 0 else '重叠'}")
                        
                        # 水平方向间隙 ≤ 2格：标记左右边
                        # 条件：垂直方向必须有显著重叠（≥节点高度的1/6）
                        if gap_x >= 0 and gap_x <= threshold_x and a_edge_h and b_edge_h:
                            # 检查垂直方向重叠程度
                            if gap_y == -1:
                                # 垂直方向重叠：计算实际重叠量
                                vertical_overlap = min(a_bottom, b_bottom) - max(a_top, b_top)
                                # 只有重叠量≥节点高度的1/6时才标记水平边
                                if vertical_overlap >= node_a.height / 6:
                                    if debug.DEBUG:
                                        debug_print(f"=== [Overlap] ✓ 水平: {name_a}({a_edge_h}) <-> {name_b}({b_edge_h}), gap_x={gap_x:.1f}px, overlap_y={vertical_overlap:.1f}px ===")
                                    node_edge_highlights[name_a].add(a_edge_h)
                                    node_edge_highlights[name_b].add(b_edge_h)
                                else:
                                    if debug.DEBUG:
                                        debug_print(f"=== [Overlap] ✗ 水平未标记(垂直重叠不足): {name_a} <-> {name_b}, gap_x={gap_x:.1f}px, overlap_y={vertical_overlap:.1f}px ===")
                            else:
                                # 垂直方向有间隙（不重叠）：不标记水平边
                                if debug.DEBUG:
                                    debug_print(f"=== [Overlap] ✗ 水平未标记(垂直有间隙): {name_a} <-> {name_b}, gap_x={gap_x:.1f}px, gap_y={gap_y:.1f}px ===")
                        
                        # 垂直方向间隙 ≤ 2格：标记上下边
                        # 条件：水平方向必须有显著重叠（≥节点宽度的1/6）
                        if gap_y >= 0 and gap_y <= threshold_y and a_edge_v and b_edge_v:
                            # 检查水平方向重叠程度
                            if gap_x == -1:
                                # 水平方向重叠：计算实际重叠量
                                horizontal_overlap = min(a_right, b_right) - max(a_left, b_left)
                                # 只有重叠量≥节点宽度的1/6时才标记垂直边
                                if horizontal_overlap >= node_a.width / 6:
                                    if debug.DEBUG:
                                        debug_print(f"=== [Overlap] ✓ 垂直: {name_a}({a_edge_v}) <-> {name_b}({b_edge_v}), gap_y={gap_y:.1f}px, overlap_x={horizontal_overlap:.1f}px ===")
                                    node_edge_highlights[name_a].add(a_edge_v)
                                    node_edge_highlights[name_b].add(b_edge_v)
                                else:
                                    if debug.DEBUG:
                                        debug_print(f"=== [Overlap] ✗ 垂直未标记(水平重叠不足): {name_a} <-> {name_b}, gap_y={gap_y:.1f}px, overlap_x={horizontal_overlap:.1f}px ===")
                            else:
                                # 水平方向有间隙（不重叠）：不标记垂直边
                                if debug.DEBUG:
                                    debug_print(f"=== [Overlap] ✗ 垂直未标记(水平有间隙): {name_a} <-> {name_b}, gap_y={gap_y:.1f}px, gap_x={gap_x:.1f}px ===")
            
            # 调试：输出高亮统计信息
            highlighted_count = sum(1 for edges in node_edge_highlights.values() if edges)
            overlapping_count = len(node_overlapping)
            if debug.DEBUG:
                debug_print(f"=== [Overlap] 检测完成: {len(self.nodes)}个节点, {highlighted_count}个单边高亮, {overlapping_count}个重叠 ===")
        
                # 调试：输出所有被高亮的节点及其高亮边
                debug_print("\n=== [Overlap] 被高亮的节点列表 ===")
                for name, edges in node_edge_highlights.items():
                    if edges:
                        node = self.nodes[name]
                        pos = node.pos()
                        debug_print(f"  {name}: 边={edges}, pos=({pos.x():.1f}, {pos.y():.1f})")
                debug_print("================================\n")
            
            # 应用高亮效果
            # ✅ AI 生成: 先快照旧的样式状态，仅对真正变化的节点重绘
            prev_overlapping = {name: node.is_overlapping for name, node in self.nodes.items()}
            prev_edges = {name: set(node.highlighted_edges) for name, node in self.nodes.items()}
            for name, node in self.nodes.items():
                if name in node_overlapping:
                    # 节点重叠：全红
                    node.is_overlapping = True
                    node.highlighted_edges = set()
                else:
                    # 应用单边高亮
                    node.is_overlapping = False
                    node.highlighted_edges = node_edge_highlights[name]
                    
                # ✅ AI 生成: 仅在样式真正变化时才重绘，避免每轮检测对全部节点做 O(N) 次
                # scene.removeItem/addItem（高亮边线重建）造成的分配抖动
                if (node.is_overlapping != prev_overlapping.get(name)) or \
                   (node.highlighted_edges != prev_edges.get(name)):
                    node.set_pen_and_brush()
            
            if debug.DEBUG:
                debug_print("=== [Overlap] check_node_overlaps() END ===\n")
            
        except Exception as e:
            import sys
            import traceback
            error_msg = f"\n{'='*60}\n[Overlap] 发生异常: {e}\n{'='*60}\n"
            if debug.DEBUG:
                debug_print(error_msg)
            traceback.print_exc()
            if sys.stdout:
                sys.stdout.flush()
            if sys.stderr:
                sys.stderr.flush()
    
    def get_all_units(self) -> list:
        """获取所有单位的最新数据"""
        units = []
        for node in self.nodes.values():
            units.append(node.unit)
        return units
    
    def on_item_deleted(self, item, record_undo=True):
        """处理节点删除
        
        Args:
            item: 要删除的 TechTreeNode
            record_undo: 是否记录撤销动作（True=用户操作；撤销/重做流程
                内部调用时应传 False，否则内部删除会再次压栈并清空重做栈）
        """
        if item.unit.name in self.nodes:
            unit_name = item.unit.name
            
            # 找到所有以该节点为父节点的子节点，并移除该父节点
            removed_requires_children = []  # 记录被修改的子节点
            for child_name, child_node in list(self.nodes.items()):
                if child_name == unit_name:
                    continue  # 跳过自己
                
                child_requires = child_node.unit.requires
                if isinstance(child_requires, list):
                    if unit_name in child_requires:
                        # 保存旧值
                        old_requires = child_requires.copy()
                        # 移除该父节点
                        child_requires.remove(unit_name)
                        # 更新显示
                        child_node.requires_value_text.setPlainText(child_node._format_requires_value(child_requires))
                        # 更新边框颜色
                        child_node.set_pen_and_brush()
                        # 记录
                        removed_requires_children.append({
                            'unit_name': child_name,
                            'old_requires': old_requires,
                            'new_requires': child_requires.copy()
                        })
                elif child_requires == unit_name:
                    # 单个字符串的情况
                    old_requires = [child_requires]
                    child_node.unit.requires = []
                    child_node.requires_value_text.setPlainText(child_node._format_requires_value([]))
                    # 更新边框颜色
                    child_node.set_pen_and_brush()
                    removed_requires_children.append({
                        'unit_name': child_name,
                        'old_requires': old_requires,
                        'new_requires': []
                    })
            
            # 保存单位数据用于撤销（在删除之前）
            unit_data = {
                'name': item.unit.name,
                'costs': item.unit.costs,
                'position_x': item.unit.position_x,
                'position_y': item.unit.position_y,
                'requires': item.unit.requires if isinstance(item.unit.requires, list) else ([item.unit.requires] if item.unit.requires else []),
                'deployed': True,
                'removed_requires_children': removed_requires_children  # 附加子节点信息
            }
            
            # ✅ 先从字典和场景中删除节点
            del self.nodes[unit_name]
            self.scene.removeItem(item)
            
            # 发送节点数量变化信号
            self.node_count_changed.emit(len(self.nodes))
            
            # ✅ 再更新连线（此时节点已移除，不会生成残留连线）
            self.scene.update_edges(self.nodes)
            
            # 发送删除信号，通知主窗口更新状态（包含完整数据）
            self.unit_deleted.emit(unit_name)
            
            # ✅ AI 生成: 发送撤销数据信号。撤销(ADD_UNIT)/重做(DELETE_UNIT)流程内部
            # 调用时传 record_undo=False：内部删除不得再压 DELETE_UNIT 动作，
            # 否则 push_action 会清空重做栈，导致 Ctrl+Y 链条断裂
            if record_undo and hasattr(self, 'unit_delete_for_undo'):
                self.unit_delete_for_undo.emit(unit_data)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件 - 必须实现以支持拖拽"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽释放事件 - 将单位添加到鼠标位置"""
        if not event.mimeData().hasText():
            return
        
        import json
        try:
            # 解析单位数据
            unit_data = json.loads(event.mimeData().text())
            
            # 转换为场景坐标
            scene_pos = self.mapToScene(event.pos())
            
            # 发送信号到主窗口，传递单位和位置
            from src.parser import Unit
            unit = Unit.from_dict(unit_data)
            
            # 设置单位为鼠标释放的位置（转换为量纲值）
            grid_size_x = 40  # 横轴每0.1量纲 = 40px
            grid_size_y = 20  # 纵轴每0.1量纲 = 20px
            pixel_x = round(scene_pos.x() / grid_size_x) * grid_size_x
            pixel_y = round(scene_pos.y() / grid_size_y) * grid_size_y
            
            # 确保位置不为负
            pixel_x = max(0, pixel_x)
            pixel_y = max(0, pixel_y)
            
            # 将像素坐标转换为量纲坐标
            # X: 每格40px = 0.1量纲, Y: 每格20px = 0.1量纲
            unit.position_x = (pixel_x / grid_size_x) * 0.1
            unit.position_y = (pixel_y / grid_size_y) * 0.1
            
            # 发送信号（包含位置信息）
            self.unit_dropped_at_position.emit(unit)
            
            event.acceptProposedAction()
        except Exception:
            event.ignore()
    
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮缩放"""
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl + 滚轮缩放
            delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            
            event.accept()
        else:
            super().wheelEvent(event)
    
    def zoom_in(self):
        """放大"""
        self.zoom_level *= 1.1
        self.scale(1.1, 1.1)
    
    def zoom_out(self):
        """缩小"""
        self.zoom_level /= 1.1
        self.scale(1 / 1.1, 1 / 1.1)
    
    def reset_zoom(self):
        """重置缩放"""
        self.zoom_level = 1.0
        self.resetTransform()
    
    def scale_view(self, factor: float, reset: bool = False):
        """
        缩放画布
        
        Args:
            factor: 缩放比例（>1 放大，<1 缩小，=1 配合 reset=True 重置）
            reset: 是否重置缩放
        """
        if reset:
            self.reset_zoom()
        else:
            self.zoom_level *= factor
            self.scale(factor, factor)
    
    def keyPressEvent(self, event):
        """键盘事件 - 支持 Ctrl+Z / Space / Escape / Delete"""
        # 空格键：选中节点后按空格 = 选择前置单位（右键-选择前置单位 的快捷键）
        if event.key() == Qt.Key_Space:
            event.accept()
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, TechTreeNode):
                    self.scene.start_set_requires(item.unit.name)
                    return
            return
        
        # ESC 键取消设置 requires 模式
        if event.key() == Qt.Key_Escape:
            if self.scene.setting_requires_mode:
                self.scene.cancel_set_requires()
                return
        
        # Delete 键删除选中的节点
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, TechTreeNode):
                    self.on_item_deleted(item)
        
        # Ctrl+Z：撤销（备用，主要使用 QShortcut）
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
            parent = self.parent()
            depth = 0
            while parent and not hasattr(parent, 'perform_undo'):
                parent = parent.parent()
                depth += 1
                if depth > 10:
                    break
            if parent and hasattr(parent, 'perform_undo'):
                parent.perform_undo()
                event.accept()
                return
        
        # 其他按键交给父类处理
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 支持 Shift + 框选和多节点拖动"""
        try:
            # 中键按下：开始拖动画布
            if event.button() == Qt.MiddleButton:
                self.is_panning = True
                self.pan_start_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
            
            if event.button() == Qt.LeftButton:
                # 如果正在设置 requires 模式，处理前置单位选择
                if self.scene.setting_requires_mode:
                    # 转换为场景坐标
                    scene_pos = self.mapToScene(event.pos())
                    
                    # 遍历所有节点，找到被点击的节点
                    clicked_node = None
                    for name, node in self.nodes.items():
                        if node.boundingRect().translated(node.pos()).contains(scene_pos):
                            clicked_node = node
                            break
                    
                    if clicked_node:
                        # 点击了某个节点，设置为前置单位
                        parent_name = clicked_node.unit.name
                        
                        # 检查是否选择了自己
                        if parent_name == self.scene.requires_child_name:
                            from PyQt5.QtWidgets import QMessageBox
                            QMessageBox.warning(
                                self,
                                tr('错误'),
                                tr('不能将单位的前置设置为自己！')
                            )
                            return
                        
                        # 完成设置
                        self.scene.complete_set_requires(parent_name)
                    else:
                        # 点击空白处，取消设置
                        self.scene.cancel_set_requires()
                    return
                
                # 检查是否点击在节点上
                scene_pos = self.mapToScene(event.pos())
                item = self.scene.itemAt(scene_pos, self.transform())
                
                # 查找 TechTreeNode
                node = None
                if isinstance(item, TechTreeNode):
                    node = item
                elif item and isinstance(item.parentItem(), TechTreeNode):
                    node = item.parentItem()
                
                if node:
                    # 点击在节点上
                    
                    # 如果按住 Shift，添加到当前选区（不清除其他选中）
                    if event.modifiers() & Qt.ShiftModifier:
                        node.setSelected(not node.isSelected())
                    else:
                        # 否则清除其他选中，只选中当前节点
                        if not node.isSelected():
                            for n in self.nodes.values():
                                n.setSelected(False)
                            node.setSelected(True)
                    
                    # 发送单位选中信号，更新属性面板
                    unit_dict = node.unit.to_dict()
                    self.unit_selected.emit(unit_dict)
                    
                    # 记录拖动开始状态（用于多节点同步移动）
                    self.is_dragging_nodes = True
                    self.drag_start_pos = event.pos()
                    self.dragged_nodes_initial_positions = {}
                    
                    # ✅ AI 生成: 只记录节点的真实初始位置，不再在按下时就对齐到网格。
                    # 原实现会在 mousePressEvent 里 setPos 对齐但不写回 unit.position_*，
                    # 且该位移永远进不了撤销栈（释放时 old==new 被跳过），
                    # 导致"画在 0.4、数据仍是 0.35"的静默数据/视觉分叉。
                    # 网格吸附统一在 mouseReleaseEvent 中完成并同步写回 unit。
                    # ✅ AI 生成: 同时快照 unit 的逻辑坐标，供撤销记录使用真实旧值
                    self.dragged_units_initial_logical = {}
                    for name, n in self.nodes.items():
                        if n.isSelected():
                            self.dragged_nodes_initial_positions[name] = (n.pos().x(), n.pos().y())
                            self.dragged_units_initial_logical[name] = (n.unit.position_x, n.unit.position_y)
                    
                    if debug.DEBUG:
                        debug_print(f"[DEBUG UNDO] Drag start: {len(self.dragged_nodes_initial_positions)} nodes recorded: {list(self.dragged_nodes_initial_positions.keys())}")
                    
                    event.accept()  # ✅ 拦截事件，防止Qt默认行为干扰
                else:
                    # 点击在空白处，开始矩形框选
                    self.is_selecting = True
                    self.selection_start_pos = event.pos()
                    
                    # 创建选择矩形
                    self.selection_rect = QGraphicsRectItem()
                    pen = QPen(QColor('#3498DB'), 2)
                    pen.setStyle(Qt.DashLine)
                    self.selection_rect.setPen(pen)
                    
                    brush_color = QColor('#3498DB')
                    brush_color.setAlpha(30)
                    brush = QBrush(brush_color)
                    self.selection_rect.setBrush(brush)
                    self.selection_rect.setZValue(1000)
                    
                    start_scene = self.mapToScene(event.pos())
                    self.selection_rect.setRect(start_scene.x(), start_scene.y(), 0, 0)
                    
                    self.scene.addItem(self.selection_rect)
            else:
                super().mousePressEvent(event)
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] mousePressEvent failed: {e}")
            import traceback
            traceback.print_exc()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 更新选择矩形或拖动节点"""
        try:
            # 中键拖动：平移画布
            if self.is_panning and event.buttons() & Qt.MiddleButton:
                if self.pan_start_pos:
                    delta = event.pos() - self.pan_start_pos
                    self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                    self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
                    self.pan_start_pos = event.pos()
                event.accept()
                return
            
            if self.is_selecting and self.selection_rect:
                # 更新矩形大小
                start_scene = self.mapToScene(self.selection_start_pos)
                end_scene = self.mapToScene(event.pos())
                
                from PyQt5.QtCore import QRectF
                rect = QRectF(start_scene, end_scene).normalized()
                self.selection_rect.setRect(rect)
                
                event.accept()
            elif self.is_dragging_nodes and event.buttons() & Qt.LeftButton:
                # 手动处理多节点拖动
                try:
                    if self.drag_start_pos and self.dragged_nodes_initial_positions:
                        # ✅ 关键修复：计算鼠标移动的偏移量，考虑缩放因子
                        # 需要将视图坐标转换为场景坐标
                        delta_pixel_x = (event.pos().x() - self.drag_start_pos.x()) / self.zoom_level
                        delta_pixel_y = (event.pos().y() - self.drag_start_pos.y()) / self.zoom_level
                                        
                        # ✅ 移除拖动激活阈值，让节点立即跟随鼠标，解决不跟手问题
                        # if abs(delta_pixel_x) < 5 and abs(delta_pixel_y) < 5:
                        #     event.accept()
                        #     return
                        
                        # ✅ 拖动过程中不做网格对齐，直接跟随鼠标
                        # 网格对齐只在 mouseReleaseEvent 中进行
                        
                        # 移动所有选中的节点
                        for name, (init_x, init_y) in self.dragged_nodes_initial_positions.items():
                            if name in self.nodes:
                                node = self.nodes[name]
                                # ✅ 基于初始位置 + 原始偏移量（不对齐）
                                new_x = init_x + delta_pixel_x
                                new_y = init_y + delta_pixel_y
                                
                                # 确保不为负
                                new_x = max(0, new_x)
                                new_y = max(0, new_y)
                                
                                # ✅ 性能优化：使用 prepareGeometryChange + 直接设置位置
                                # 避免不必要的重绘
                                node.prepareGeometryChange()
                                node.setPos(new_x, new_y)
                        
                        # ✅ 性能优化：拖动过程中不更新连线，只在释放时更新
                        # self.scene.update_edges(self.nodes)
                    
                    event.accept()
                except Exception as e:
                    if debug.DEBUG:
                        debug_print(f"[ERROR DRAG] Exception in mouseMoveEvent: {e}")
                    import traceback
                    traceback.print_exc()
                    event.accept()
            else:
                super().mouseMoveEvent(event)
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] mouseMoveEvent failed: {e}")
            super().mouseMoveEvent(event)
    
    def snap_logical_to_grid(self, position_x: float, position_y: float):
        """
        把量纲坐标吸附到网格（0.1 量纲 = 1 格）。

        ✅ AI 生成: 直接在量纲域取整，避免像素域浮点噪声导致吸附方向不确定
        （0.35 → 0.4 而不是 0.3）。返回值保证为非负且是 0.1 的整数倍。

        Args:
            position_x: 逻辑坐标 X（量纲）
            position_y: 逻辑坐标 Y（量纲）

        Returns:
            (grid_x, grid_y) 以 0.1 量纲为单位的整格坐标
        """
        gx = max(0, int(round(position_x * 10)))
        gy = max(0, int(round(position_y * 10)))
        return gx / 10.0, gy / 10.0

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - 完成框选或节点拖动"""
        try:
            # 中键释放：结束拖动画布
            if event.button() == Qt.MiddleButton:
                self.is_panning = False
                self.pan_start_pos = None
                self.setCursor(Qt.ArrowCursor)
                event.accept()
                return
            
            if debug.DEBUG:
                debug_print(f"[DEBUG MOUSE] mouseReleaseEvent called, is_dragging={self.is_dragging_nodes}, is_selecting={self.is_selecting}")
            if self.is_dragging_nodes:
                
                # 对所有选中的节点进行网格吸附
                # ✅ AI 生成: 无条件把画布像素位置同步回 unit 逻辑坐标。
                # 原实现只在「吸附改变了像素位置」时才写回 unit，导致单击未拖动
                # 或吸附结果恰等于当前位置时，unit 仍保留旧值 → 导出与画布不一致。
                # 吸附是幂等的：位置未变时写回同一个值，因此不会误置脏位。
                for name, node in self.nodes.items():
                    if node.isSelected():
                        # ✅ AI 生成: 通过对「量纲值」取整来吸附，而不是对像素取整。
                        # 原实现 round(px / 40) 在网格边界上受浮点噪声影响方向不可预测：
                        # 0.35 量纲对应 139.99999999999997px，round(3.4999…) 得 3 而非 4，
                        # 于是吸附到 0.3（反直觉）。改为先把量纲值四舍五入到 0.1 的整数倍
                        # （0.35 → 0.4），彻底消除该边界不确定性。
                        snapped_gx, snapped_gy = self.snap_logical_to_grid(
                            node.unit.position_x, node.unit.position_y)
                        snapped_x = snapped_gx * 400.0   # 1.0 量纲 = 400px
                        snapped_y = snapped_gy * 200.0   # 1.0 量纲 = 200px
                        
                        if abs(snapped_x - node.pos().x()) > 1e-6 or abs(snapped_y - node.pos().y()) > 1e-6:
                            node.setPos(snapped_x, snapped_y)
                        
                        # ✅ AI 生成: 无论是否发生吸附，都把吸附后的量纲值同步到 unit
                        node.unit.position_x = snapped_gx
                        node.unit.position_y = snapped_gy
                
                # 更新连线
                self.scene.update_edges(self.nodes)
                
                # ✅ 关键修复：拖动完成后更新场景大小，确保画布自动扩展
                self._update_scene_rect()
                
                # ✅ 新增：检查节点重叠（三格内）
                if debug.DEBUG:
                    debug_print("=" * 60)
                    debug_print("[Canvas] mouseReleaseEvent: 拖动完成，准备检测重叠")
                    debug_print(f"[Canvas] 当前节点数: {len(self.nodes)}")
                    debug_print("=" * 60)
                
                # 调用重叠检测
                self.check_node_overlaps()
                
                if debug.DEBUG:
                    debug_print("=" * 60)
                    debug_print("[Canvas] check_node_overlaps() 执行完毕")
                    debug_print("=" * 60)
                
                # 发送批量位置变化信号（包含新旧位置，用于撤销）
                # ✅ 关键：必须在清空 dragged_nodes_initial_positions 之前收集数据！
                position_changes = {}
                # ✅ AI 生成: old_* 取按下时快照的 unit 真实逻辑坐标，
                # 而不是由像素反算（像素在按下时可能已被旧版本对齐过，会失真）
                for name, node in self.nodes.items():
                    if node.isSelected():
                        old_pos = self.dragged_nodes_initial_positions.get(name)
                        if old_pos:
                            old_logical = self.dragged_units_initial_logical.get(name)
                            if old_logical:
                                old_x, old_y = old_logical
                            else:
                                grid_size_x = 40
                                grid_size_y = 20
                                old_x = (old_pos[0] / grid_size_x) * 0.1
                                old_y = (old_pos[1] / grid_size_y) * 0.1
                            
                            position_changes[name] = {
                                'name': name,
                                'position_x': node.unit.position_x,
                                'position_y': node.unit.position_y,
                                'old_position_x': old_x,
                                'old_position_y': old_y
                            }
                
                if position_changes:
                    if debug.DEBUG:
                        debug_print(f"[DEBUG UNDO] Emitting batch signal for {len(position_changes)} units: {list(position_changes.keys())}")
                    self.batch_unit_position_changed.emit(position_changes)
                
                # ✅ 最后才清空拖动初始位置记录
                self.is_dragging_nodes = False
                self.drag_start_pos = None
                self.dragged_nodes_initial_positions = {}
                self.dragged_units_initial_logical = {}
                
                event.accept()
            elif self.is_selecting and event.button() == Qt.LeftButton:
                # 结束框选
                self.is_selecting = False
                
                if self.selection_rect:
                    # 获取选择矩形
                    selection_rect = self.selection_rect.rect()
                    
                    # 如果没有按 Shift，清除之前的选中
                    if not (event.modifiers() & Qt.ShiftModifier):
                        for node in self.nodes.values():
                            node.setSelected(False)
                    
                    # 选中在矩形内的所有节点
                    from PyQt5.QtCore import QRectF, QSizeF
                    for name, node in self.nodes.items():
                        node_rect = QRectF(node.pos(), QSizeF(node.width, node.height))
                        if selection_rect.intersects(node_rect):
                            node.setSelected(True)
                    
                    # 移除选择矩形
                    self.scene.removeItem(self.selection_rect)
                    self.selection_rect = None
                    
                    # 发送选中信号
                    if self.scene.selectedItems():
                        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, TechTreeNode)]
                        if selected_nodes:
                            self.unit_selected.emit(selected_nodes[0].unit.to_dict())
                
                event.accept()
            else:
                super().mouseReleaseEvent(event)
        except Exception as e:
            if debug.DEBUG:
                debug_print(f"[ERROR] mouseReleaseEvent failed: {e}")
            import traceback
            traceback.print_exc()
            # 确保清理状态，避免卡住
            self.is_selecting = False
            self.is_dragging_nodes = False
            self.drag_start_pos = None
            self.dragged_nodes_initial_positions = {}
            self.dragged_units_initial_logical = {}
            if self.selection_rect:
                try:
                    self.scene.removeItem(self.selection_rect)
                except:
                    pass
                self.selection_rect = None
