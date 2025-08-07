"""
メインUIコントローラー
"""

import streamlit as st
from typing import Optional

from .base_controller import BaseUIController
from .sidebar_controller import SidebarController
from .content_controller import ContentController
from ..core.config_manager import config_manager
from ..utils.logging_config import logger
from ..utils.cache_manager import cache_manager as cache

# 既存のNewsletterGeneratorをインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from newsletter_generator import NewsletterGenerator


class MainUIController(BaseUIController):
    """メインUIコントローラー"""
    
    def __init__(self):
        super().__init__()
        self.config = config_manager.get_config()
        self.sidebar_controller = SidebarController()
        self.content_controller = ContentController()
        self.generator: Optional[NewsletterGenerator] = None
        self.calendar_config: Optional[dict] = None
        self._last_calendar_config: Optional[dict] = None
    
    def render(self):
        """画面描画の実装"""
        return self.run()
    
    def run(self):
        """メインUI実行"""
        logger.info("メインUIコントローラー開始")
        
        try:
            # ページ設定
            self._setup_page()
            
            # 設定検証
            if not self._validate_config():
                return
            
            # サイドバー設定
            publish_date, manual_issue_number, generate_button, self.calendar_config = self.sidebar_controller.render_with_error_handling()
            
            # NewsletterGenerator の初期化
            self._initialize_generator()
            
            # メインコンテンツ表示
            self.content_controller.render_event_preview(publish_date, self.generator)
            
            # メルマガ生成処理
            if generate_button:
                logger.info("メルマガ生成ボタンが押されました")
                self.content_controller.render_newsletter_generation(publish_date, manual_issue_number, self.generator)
            
            # 古いキャッシュのクリーンアップ（バックグラウンド処理）
            self._cleanup_cache()
            
        except Exception as e:
            self.show_error("メインUI実行中にエラーが発生", e)
            raise
        
        logger.info("メインUIコントローラー完了")
    
    def _setup_page(self):
        """ページ設定"""
        st.set_page_config(
            page_title="メルマガ「一日一知」生成",
            page_icon="📧",
            layout="wide"
        )
        
        st.title("📧 メルマガ「一日一知」生成")
        st.markdown("指定した発行日の天気予報と行事・イベント情報をメールマガジン用の文章として生成します。")
    
    def _validate_config(self) -> bool:
        """設定の検証"""
        if not self.config.validate():
            st.markdown("""
            **設定方法:**
            1. プロジェクトルートに `.env` ファイルを作成
            2. 以下の内容を記載:
            ```
            OPENAI_API_KEY=your_api_key_here
            YOUTUBE_API_KEY=your_youtube_api_key_here  # オプション
            DEBUG_MODE=false                           # オプション
            CACHE_ENABLED=true                         # オプション
            CACHE_TTL_HOURS=1                         # オプション
            ```
            """)
            return False
        
        # APIキー設定済みを表示
        st.sidebar.success("✅ OpenAI APIキーが設定されています")
        
        return True
    
    def _initialize_generator(self):
        """NewsletterGeneratorの初期化"""
        if not self.generator or self.calendar_config != self._last_calendar_config:
            logger.info("NewsletterGenerator を初期化中...")
            
            try:
                # 旧形式のAppConfigに変換
                from config import AppConfig
                old_config = AppConfig(
                    openai_api_key=self.config.openai_api_key,
                    youtube_api_key=self.config.youtube_api_key,
                    user_agent=self.config.user_agent,
                    youtube_channel_handle=self.config.youtube_channel_handle
                )
                
                self.generator = NewsletterGenerator(old_config, self.calendar_config)
                self._last_calendar_config = self.calendar_config.copy() if self.calendar_config else None
                
                logger.info("NewsletterGenerator 初期化完了")
                
            except Exception as e:
                self.show_error("NewsletterGeneratorの初期化に失敗", e)
    
    def _cleanup_cache(self):
        """キャッシュクリーンアップ"""
        if self.config.cache_enabled:
            try:
                cache.clear_old_cache(max_age_hours=24)  # 24時間以上古いキャッシュを削除
            except Exception as e:
                logger.warning(f"キャッシュクリーンアップエラー: {e}")


def main():
    """メイン関数"""
    try:
        controller = MainUIController()
        controller.run()
    except Exception as e:
        logger.error("アプリケーション実行中にエラーが発生", e)
        st.error("❌ アプリケーション実行中にエラーが発生しました。詳細はログを確認してください。")