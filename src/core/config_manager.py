"""
改善された設定管理システム
"""

import os
from typing import Optional
from dataclasses import dataclass

from ..utils.logging_config import logger


@dataclass
class EnhancedAppConfig:
    """拡張アプリケーション設定"""
    openai_api_key: str
    youtube_api_key: Optional[str]
    user_agent: str = "Newsletter-Generator/1.0 (Educational-Purpose)"
    youtube_channel_handle: str = "nichidaiichi"
    debug_mode: bool = False
    cache_enabled: bool = True
    cache_ttl_hours: int = 1
    
    @classmethod
    def from_env(cls) -> 'EnhancedAppConfig':
        """環境変数から設定を読み込み"""
        user_agent = os.getenv("USER_AGENT", "Newsletter-Generator/1.0 (Educational-Purpose)")
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        
        try:
            cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "1"))
        except ValueError:
            cache_ttl_hours = 1
            logger.warning("CACHE_TTL_HOURSの値が無効です。デフォルト値(1)を使用します")
        
        # Streamlit Cloud の場合は st.secrets から取得
        try:
            import streamlit as st
            openai_api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            youtube_api_key = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
        except:
            openai_api_key = os.getenv("OPENAI_API_KEY", "")
            youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        return cls(
            openai_api_key=openai_api_key,
            youtube_api_key=youtube_api_key,
            user_agent=user_agent,
            debug_mode=debug_mode,
            cache_enabled=cache_enabled,
            cache_ttl_hours=cache_ttl_hours,
        )
    
    def validate(self) -> bool:
        """設定の検証"""
        if not self.openai_api_key:
            logger.error("OpenAI APIキーが設定されていません")
            return False
        
        if len(self.openai_api_key) < 10:
            logger.error("OpenAI APIキーが無効な形式です")
            return False
        
        logger.info("設定の検証が完了しました")
        return True
    
    def to_dict(self) -> dict:
        """辞書形式での出力（デバッグ用・機密情報は隠す）"""
        return {
            "openai_api_key": "***HIDDEN***" if self.openai_api_key else None,
            "youtube_api_key": "***HIDDEN***" if self.youtube_api_key else None,
            "user_agent": self.user_agent,
            "youtube_channel_handle": self.youtube_channel_handle,
            "debug_mode": self.debug_mode,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_hours": self.cache_ttl_hours,
        }


class ConfigManager:
    """設定管理クラス"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[EnhancedAppConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_config(self) -> EnhancedAppConfig:
        """設定の取得"""
        if self._config is None:
            self._config = EnhancedAppConfig.from_env()
            
            if self._config.debug_mode:
                logger.debug(f"設定情報: {self._config.to_dict()}")
        
        return self._config
    
    def reload_config(self) -> EnhancedAppConfig:
        """設定の再読み込み"""
        self._config = None
        return self.get_config()


# グローバル設定管理インスタンス
config_manager = ConfigManager()