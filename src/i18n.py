# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
i18n 翻译模块
支持中文和英文双语切换
"""

import json
import os
from typing import Dict
from PyQt5.QtCore import QObject


class I18nManager(QObject):
    """国际化翻译管理器
    
    ✅ AI 生成: 移除语言切换信号与翻译重载方法 —— 语言切换改为重启生效后，
    两者均无调用方（属死代码）。
    """
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        'zh_CN': '简体中文',
        'en_US': 'English'
    }
    
    def __init__(self):
        super().__init__()
        self._current_language = 'zh_CN'  # 默认语言：中文
        self._translations = {}  # 当前语言的翻译字典
        self._translation_files = {}  # 所有翻译字典
        self._load_language_config()  # 加载保存的语言配置
        self._load_translations()
    
    def _get_config_path(self):
        """获取配置文件路径"""
        import sys
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'language_config.json')
    
    def _load_language_config(self):
        """加载语言配置"""
        config_path = self._get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    lang = config.get('language', 'zh_CN')
                    if lang in self.SUPPORTED_LANGUAGES:
                        self._current_language = lang
            except Exception as e:
                print(f"Failed to load language config: {e}")
    
    def _save_language_config(self):
        """保存语言配置"""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'language': self._current_language}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save language config: {e}")
    
    def _load_translations(self):
        """加载所有翻译文件"""
        # 获取翻译文件目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        translations_dir = os.path.join(base_dir, 'translations')
        
        # 尝试从打包目录加载
        if not os.path.exists(translations_dir):
            import sys
            if getattr(sys, 'frozen', False):
                # PyInstaller 打包后
                base_dir = sys._MEIPASS
                translations_dir = os.path.join(base_dir, 'translations')
        
        # 加载所有翻译文件
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            lang_file = os.path.join(translations_dir, f'{lang_code}.json')
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self._translation_files[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load {lang_file}: {e}")
                    self._translation_files[lang_code] = {}
            else:
                self._translation_files[lang_code] = {}
        
        # 设置当前语言的翻译
        self._translations = self._translation_files.get(self._current_language, {})
    
    def set_language(self, language_code: str):
        """
        切换语言（需要重启软件生效）
        
        Args:
            language_code: 语言代码，如 'zh_CN', 'en_US'
        """
        if language_code in self.SUPPORTED_LANGUAGES:
            self._current_language = language_code
            self._save_language_config()  # 保存配置
            print(f"Language switched to: {language_code} (restart required)")
        else:
            print(f"Unsupported language: {language_code}")
    
    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self._current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """获取可用的语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def tr(self, text: str) -> str:
        """
        翻译文本
        
        Args:
            text: 原文本（通常是中文）
            
        Returns:
            翻译后的文本，如果没有对应翻译则返回原文本
        """
        return self._translations.get(text, text)


# 全局单例实例
# 使用简单工厂模式确保单例
_i18n_instance = None

def get_i18n():
    """获取 i18n 单例实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    return _i18n_instance

i18n = get_i18n()


# 便捷函数
def tr(text: str) -> str:
    """翻译文本的便捷函数"""
    return i18n.tr(text)


def set_language(language_code: str):
    """切换语言的便捷函数"""
    i18n.set_language(language_code)


def get_current_language() -> str:
    """获取当前语言的便捷函数"""
    return i18n.get_current_language()
