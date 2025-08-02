"""
UI基底コントローラー
"""

import streamlit as st
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..utils.logging_config import logger


class BaseUIController(ABC):
    """UI基底コントローラークラス"""
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    def render(self) -> Any:
        """画面描画の抽象メソッド"""
        pass
    
    def show_error(self, message: str, error: Exception = None):
        """エラー表示"""
        self.logger.error(message, error)
    
    def show_success(self, message: str):
        """成功メッセージ表示"""
        self.logger.success(message)
    
    def show_warning(self, message: str):
        """警告メッセージ表示"""
        self.logger.warning(message)
    
    def show_info(self, message: str):
        """情報メッセージ表示"""
        st.info(f"ℹ️ {message}")
    
    def render_with_error_handling(self) -> Any:
        """エラーハンドリング付きレンダリング"""
        try:
            return self.render()
        except Exception as e:
            self.show_error(f"{self.__class__.__name__}でエラーが発生", e)
            return None