"""
サイドバー管理コントローラー
"""

import streamlit as st
from datetime import date
from typing import Dict, Optional, Tuple

from .base_controller import BaseUIController
from ..utils.logging_config import logger
from utils import DateUtils


class SidebarController(BaseUIController):
    """サイドバー設定管理"""
    
    def __init__(self):
        super().__init__()
    
    def render(self) -> Tuple[date, Optional[int], bool, Dict]:
        """サイドバーの描画"""
        st.sidebar.header("⚙️ メルマガ設定")
        
        # 発行日設定
        publish_date = self._render_date_settings()
        
        # 発行No.設定
        manual_issue_number = self._render_issue_number_settings(publish_date)
        
        # Google Calendar設定
        calendar_config = self._render_calendar_settings()
        
        # 天気予報設定
        self._render_weather_settings()
        
        # 生成ボタン
        generate_button = self._render_generate_button()
        
        return publish_date, manual_issue_number, generate_button, calendar_config
    
    def _render_date_settings(self) -> date:
        """発行日設定の描画"""
        st.sidebar.subheader("📅 発行日設定")
        
        today = DateUtils.get_today_jst()
        publish_date = st.sidebar.date_input(
            "メールマガジン発行日",
            value=today,
            help="天気予報を取得したい日付を選択してください"
        )
        
        formatted_date = f"{publish_date.year}年{publish_date.month}月{publish_date.day}日" + DateUtils.get_japanese_weekday(publish_date)
        st.sidebar.success(f"📆 発行日: {formatted_date}")
        
        return publish_date
    
    def _render_issue_number_settings(self, publish_date: date) -> Optional[int]:
        """発行No.設定の描画"""
        st.sidebar.subheader("📄 発行No.設定")
        
        auto_issue_number = DateUtils.get_issue_number(publish_date)
        
        # 日曜日の場合の警告表示
        if publish_date.weekday() == 6:
            st.sidebar.warning("⚠️ 日曜日は通常発行しません")
        
        use_manual_issue_number = st.sidebar.checkbox(
            "発行No.を手動設定",
            value=publish_date.weekday() == 6,
            help="チェックすると発行No.を手動で入力できます"
        )
        
        manual_issue_number = None
        if use_manual_issue_number:
            manual_issue_number = st.sidebar.number_input(
                "発行No.",
                min_value=1,
                value=auto_issue_number,
                step=1,
                help="発行No.を手動で入力してください"
            )
            st.sidebar.success(f"📄 手動設定: No.{manual_issue_number}")
        else:
            st.sidebar.info(f"📄 自動計算: No.{auto_issue_number} (2025年4月3日基準・日曜除く)")
        
        return manual_issue_number
    
    def _render_calendar_settings(self) -> Dict:
        """Google Calendar設定の描画"""
        st.sidebar.subheader("📅 Google Calendar設定")
        
        # 強制的にGoogle Calendar を有効化
        use_google_calendar = True
        st.sidebar.success("✅ Google Calendar機能は常に有効です")
        
        calendar_config = {
            'use_google_calendar': use_google_calendar,
            'schedule_calendar_ids': ['nichidai1.haishin@gmail.com'],
            'event_calendar_ids': ['c38f50b10481248d05113108d0ba210e7edd5d60abe152ce319c595f011cb814@group.calendar.google.com'],
            # キーワードフィルタリングを削除 - 全てのイベントを取得
            'credentials_path': 'credentials.json',
            'token_path': 'token.json'
        }
        
        st.sidebar.info("📅 学校行事: nichidai1.haishin@gmail.com")
        st.sidebar.info("🎉 広報行事: c38f...cb814@group.calendar.google.com")  
        st.sidebar.info("📧 認証: survey-app-service@nichidai-survey-app.iam.gserviceaccount.com")
        st.sidebar.success("🔄 キーワードフィルタリング無し - 全イベント取得")
        
        return calendar_config
    
    def _render_weather_settings(self):
        """天気予報設定の描画"""
        st.sidebar.subheader("🌐 天気予報設定")
        st.sidebar.info("📍 対象地域: 墨田区（東京地方）")
        
        st.sidebar.markdown("**🎯 データ取得優先度**")
        st.sidebar.info("📅 当日データを最優先で取得")
        st.sidebar.info("⚠️ 当日データが取得不可時は翌日データで代替・明示")
        
        st.sidebar.markdown("**📊 データソース（気象庁互換API）**")
        st.sidebar.code("https://weather.tsukumijima.net/api/forecast?city=130010", language="text")
        st.sidebar.success("✅ 気象庁互換APIから公式データを取得")
    
    def _render_generate_button(self) -> bool:
        """生成ボタンの描画"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🚀 メルマガ生成")
        
        generate_button = st.sidebar.button(
            "🔄 メルマガを生成",
            type="primary",
            use_container_width=True,
            help="設定した内容でメルマガを生成します"
        )
        
        return generate_button