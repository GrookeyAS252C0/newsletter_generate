"""
統一ログシステム
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

import streamlit as st


class NewsletterLogger:
    """メルマガシステム用のログ管理クラス"""
    
    _instance: Optional['NewsletterLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'NewsletterLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """ログの設定"""
        self._logger = logging.getLogger('newsletter')
        self._logger.setLevel(logging.INFO)
        
        # 既存のハンドラーを削除
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        
        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # ファイルハンドラー（オプション）
        if os.path.exists('logs'):
            os.makedirs('logs', exist_ok=True)
        
        # デバッグモードの確認
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        if debug_mode:
            self._logger.setLevel(logging.DEBUG)
    
    def info(self, message: str):
        """情報ログ"""
        if self._logger:
            self._logger.info(message)
    
    def error(self, message: str, error: Exception = None):
        """エラーログとStreamlitエラー表示"""
        if self._logger:
            if error:
                self._logger.error(f"{message}: {str(error)}")
            else:
                self._logger.error(message)
        
        # Streamlitでもエラー表示
        st.error(f"❌ {message}")
        if error and os.getenv("DEBUG_MODE", "false").lower() == "true":
            import traceback
            st.error(f"詳細エラー: {traceback.format_exc()}")
    
    def warning(self, message: str):
        """警告ログ"""
        if self._logger:
            self._logger.warning(message)
        st.warning(f"⚠️ {message}")
    
    def success(self, message: str):
        """成功メッセージ"""
        if self._logger:
            self._logger.info(f"SUCCESS: {message}")
        st.success(f"✅ {message}")
    
    def debug(self, message: str):
        """デバッグログ"""
        if self._logger:
            self._logger.debug(message)
        
        # デバッグモードの場合のみStreamlitにも表示
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            st.info(f"🐛 DEBUG: {message}")


# グローバルログインスタンス
logger = NewsletterLogger()