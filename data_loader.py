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
            'schedule_calendar_ids': ['nichidai1.haishin@gmail.com'],  # 行事予定用カレンダーID
            'event_calendar_ids': ['c38f50b10481248d05113108d0ba210e7edd5d60abe152ce319c595f011cb814@group.calendar.google.com'],     # 広報イベント用カレンダーID
            'event_keywords': ['説明会', '学校説明', '見学会', 'オープンキャンパス', '体験会', '相談会', '入試', '文化祭', '学園祭', 'オープンスクール'],
            'credentials_path': 'credentials.json',
            'token_path': 'token.json'
        }
        
        # Google Calendar サービスの初期化
        if self.use_google_calendar:
            try:
                self.calendar_service = GoogleCalendarService(
                    credentials_path=self.calendar_config['credentials_path'],
                    token_path=self.calendar_config['token_path']
                )
                st.success("📅 Google Calendar サービスを初期化しました")
            except Exception as e:
                st.error(f"❌ Google Calendar初期化に失敗: {e}")
                self.use_google_calendar = False
    
    def get_events_for_date(self, target_date: date) -> List[str]:
        """指定日のイベントを取得（「今日の日大一」用 - 行事予定カレンダー）"""
        events = []
        
        # Google Calendarから取得
        if self.use_google_calendar and self.calendar_service:
            try:
                calendar_ids = self.calendar_config.get('schedule_calendar_ids', [])
                st.info(f"📅 「今日の日大一」用イベント取得: カレンダー数={len(calendar_ids)}")
                
                if calendar_ids:
                    st.info(f"📅 {len(calendar_ids)}個の行事予定カレンダーから今日のイベントを取得中...")
                    calendar_events = self.calendar_service.get_events_for_date(target_date, calendar_ids)
                    events.extend(calendar_events)
                    st.success(f"📅 Google Calendar（行事予定）から {len(calendar_events)} 件のイベントを取得")
                else:
                    st.warning("⚠️ 行事予定用カレンダーIDが設定されていません（サイドバーで設定してください）")
                    st.info("💡 「今日の日大一」セクション用の行事予定カレンダーを選択してください")
            except Exception as e:
                st.error(f"❌ Google Calendarからの行事予定取得に失敗: {e}")
        else:
            st.info("📅 Google Calendar機能が無効です - CSVファイルから読み込みます")
        
        return events
    
    def get_events_within_month(self, target_date: date) -> List[EventInfo]:
        """指定日から2ヶ月以内のイベントを取得（「今後の学校説明会について」用 - 広報イベントカレンダー）"""
        events = []
        
        # Google Calendarから取得
        if self.use_google_calendar and self.calendar_service:
            try:
                calendar_ids = self.calendar_config.get('event_calendar_ids', [])
                keywords = self.calendar_config.get('event_keywords', [])
                
                st.info(f"🎉 「今後の学校説明会について」用イベント取得: カレンダー数={len(calendar_ids)}, キーワード数={len(keywords)}")
                
                if calendar_ids:
                    st.info(f"🎉 {len(calendar_ids)}個の広報イベントカレンダーから今後のイベントを取得中...")
                    st.info(f"🔍 検索キーワード: {', '.join(keywords)}")
                    calendar_events = self.calendar_service.get_events_within_month(
                        target_date, calendar_ids, keywords
                    )
                    events.extend(calendar_events)
                    st.success(f"📅 Google Calendar（広報イベント）から {len(calendar_events)} 件のイベントを取得")
                else:
                    st.warning("⚠️ 広報イベント用カレンダーIDが設定されていません（サイドバーで設定してください）")
                    st.info("💡 「今後の学校説明会について」セクション用の広報イベントカレンダーを選択してください")
            except Exception as e:
                st.error(f"❌ Google Calendarからの広報イベント取得に失敗: {e}")
        else:
            st.info("🎉 Google Calendar機能が無効です - CSVファイルから読み込みます")
        
        # 日付順でソート
        return sorted(events, key=lambda x: x.date)
    
    def get_available_calendars(self) -> List[dict]:
        """利用可能なカレンダーのリストを取得（設定用）"""
        if self.use_google_calendar and self.calendar_service:
            return self.calendar_service.get_calendar_list()
        return []
    
    def update_calendar_config(self, config: dict):
        """カレンダー設定を更新"""
        self.calendar_config.update(config)
        st.success("📅 カレンダー設定を更新しました")