# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
撤销管理器
支持 Ctrl+Z 撤销最近操作，限制撤销数量以保证性能
"""

from enum import Enum
from typing import Any, Dict, Optional
from src import debug
from src.debug import debug_print


class UndoActionType(Enum):
    """撤销操作类型"""
    ADD_UNIT = "add_unit"           # 添加单位
    DELETE_UNIT = "delete_unit"     # 删除单位
    MOVE_UNIT = "move_unit"         # 移动单位
    CHANGE_REQUIRES = "change_requires"  # 修改前置关系
    MODIFY_PROPERTY = "modify_property"  # 修改属性（costs等）


class UndoAction:
    """单个撤销操作"""
    
    def __init__(self, action_type: UndoActionType, data: Dict[str, Any]):
        self.action_type = action_type
        self.data = data
    
    def __repr__(self):
        return f"UndoAction(type={self.action_type.value}, data={self.data})"


class UndoManager:
    """
    撤销管理器
    
    功能：
    - 记录用户操作
    - 支持撤销（Ctrl+Z）
    - 限制撤销栈大小以优化性能
    """
    
    def __init__(self, max_undo_steps: int = 50):
        """
        初始化撤销管理器
        
        Args:
            max_undo_steps: 最大撤销步数，默认50步
        """
        self.max_undo_steps = max_undo_steps
        self.undo_stack = []  # 撤销栈
        self.redo_stack = []  # 重做栈（可选扩展）
    
    def push_action(self, action: UndoAction):
        """
        推送一个操作到撤销栈
        
        Args:
            action: 要记录的操作
        """
        # 添加到撤销栈
        self.undo_stack.append(action)
        
        # 如果超过限制，移除最早的操作
        if len(self.undo_stack) > self.max_undo_steps:
            removed = self.undo_stack.pop(0)
            if debug.DEBUG:
                debug_print(f"[UNDO] Removed oldest action from stack: {removed}")
        
        # 清空重做栈（新操作使重做无效）
        self.redo_stack.clear()
        
        if debug.DEBUG:
            debug_print(f"[UNDO] Pushed action: {action}, stack size: {len(self.undo_stack)}")
    
    def undo(self) -> Optional[UndoAction]:
        """
        撤销最近的操作
        
        Returns:
            被撤销的操作，如果栈为空则返回 None
        """
        if not self.undo_stack:
            if debug.DEBUG:
                debug_print("[UNDO] Stack is empty, nothing to undo")
            return None
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if debug.DEBUG:
            debug_print(f"[UNDO] Undid action: {action}, remaining: {len(self.undo_stack)}")
        return action
    
    def redo(self) -> Optional[UndoAction]:
        """
        重做最近撤销的操作（可选功能）
        
        Returns:
            被重做的操作，如果栈为空则返回 None
        """
        if not self.redo_stack:
            if debug.DEBUG:
                debug_print("[REDO] Stack is empty, nothing to redo")
            return None
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if debug.DEBUG:
            debug_print(f"[REDO] Redid action: {action}, stack size: {len(self.undo_stack)}")
        return action
    
    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return len(self.redo_stack) > 0
    
    def clear(self):
        """清空所有撤销历史"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        if debug.DEBUG:
            debug_print("[UNDO] Cleared all undo history")
    
    def get_stack_size(self) -> int:
        """获取当前撤销栈大小"""
        return len(self.undo_stack)
