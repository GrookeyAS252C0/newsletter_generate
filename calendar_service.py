"""
Google Calendar API サービス
"""

import os
import json
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

try:
    import streamlit as st
except ImportError:
    class DummySt:
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    st = DummySt()

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    st.error("Google API関連のライブラリがインストールされていません")
    st.error("pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2")
    raise

from config import EventInfo
from utils import DateUtils


class GoogleCalendarService:
    """Google Calendar APIを使用してイベント情報を取得 - 無効化済み"""
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """
        Google Calendar サービスを初期化（無効化済み）
        """
        self.service = None
        st.warning("⚠️ Google Calendar機能は無効化されています")
    
    def _authenticate(self):
        """Google Calendar APIの認証を行う（無効化済み）"""
        pass
    
    def get_calendar_list(self) -> List[Dict[str, str]]:
        """利用可能なカレンダーのリストを取得（無効化済み）"""
        st.info("📅 Google Calendar機能は無効化されています")
        return []
    
    def get_events_for_date(self, target_date: date, calendar_ids: List[str]) -> List[str]:
        """指定日のイベントを取得（行事予定用）- 無効化済み"""
        st.info("📅 Google Calendar機能は無効化されています")
        return []
    
    def get_events_within_month(self, target_date: date, calendar_ids: List[str], 
                               event_keywords: List[str] = None) -> List[EventInfo]:
        """指定日から2ヶ月以内のイベントを取得（学校説明会等の広報イベント用）- 無効化済み"""
        st.info("📅 Google Calendar機能は無効化されています")
        return []
    
    def search_events_by_keywords(self, start_date: date, end_date: date, 
                                 keywords: List[str], calendar_ids: List[str]) -> List[EventInfo]:
        """キーワードでイベントを検索 - 無効化済み"""
        st.info("📅 Google Calendar機能は無効化されています")
        return []