"""
データアクセス層（Google Calendar専用版）
"""

from datetime import date
from typing import List

try:
    import streamlit as st
except ImportError:
    # Streamlitが無い環境での実行をサポート
    class DummySt:
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
    st = DummySt()

from config import EventInfo
from calendar_service import GoogleCalendarService


class EventDataService:
    """イベントデータの管理を担当（Google Calendar専用）"""
    
    def __init__(self, use_google_calendar: bool = True, calendar_config: dict = None):
        """
        Args:
            use_google_calendar: Google Calendarを使用するかどうか
            calendar_config: Google Calendar設定
        """
        self.use_google_calendar = use_google_calendar
        self.calendar_service = None
        
        # Google Calendar設定のデフォルト値
        self.calendar_config = calendar_config or {
            'schedule_calendar_ids': [],  # 行事予定用カレンダーID
            'event_calendar_ids': [],     # 広報イベント用カレンダーID
            'event_keywords': ['説明会', '見学会', 'オープンキャンパス', '体験会', '相談会', '入試', '文化祭', '学園祭', 'オープンスクール'],
            'credentials_path': 'credentials.json',
            'token_path': 'token.json'
        }
        
        # Google Calendar サービスの初期化（無効化済み）
        if self.use_google_calendar:
            st.warning("⚠️ Google Calendar機能は無効化されています")
            self.use_google_calendar = False
    
    def get_events_for_date(self, target_date: date) -> List[str]:
        """指定日のイベントを取得（「今日の日大一」用 - 行事予定カレンダー）"""
        events = []
        
        # Google Calendar機能は無効化済み
        st.info("📅 Google Calendar機能は無効化されています - CSVファイルから読み込みます")
        
        return events
    
    def get_events_within_month(self, target_date: date) -> List[EventInfo]:
        """指定日から2ヶ月以内のイベントを取得（「今後の学校説明会について」用 - 広報イベントカレンダー）"""
        events = []
        
        # Google Calendar機能は無効化済み
        st.info("🎉 Google Calendar機能は無効化されています - CSVファイルから読み込みます")
        
        # 日付順でソート
        return sorted(events, key=lambda x: x.date)
    
    def get_available_calendars(self) -> List[dict]:
        """利用可能なカレンダーのリストを取得（設定用）- 無効化済み"""
        st.info("📅 Google Calendar機能は無効化されています")
        return []
    
    def update_calendar_config(self, config: dict):
        """カレンダー設定を更新"""
        self.calendar_config.update(config)
        st.success("📅 カレンダー設定を更新しました")