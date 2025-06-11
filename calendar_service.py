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
    """Google Calendar APIを使用してイベント情報を取得"""
    
    # 必要な権限スコープ
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """
        Google Calendar サービスを初期化
        
        Args:
            credentials_path: OAuth2クライアント認証情報ファイルのパス
            token_path: 認証トークン保存ファイルのパス
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Calendar APIの認証を行う"""
        creds = None
        
        # 既存のトークンファイルをチェック
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                st.info("✅ 既存の認証トークンを読み込みました")
            except Exception as e:
                st.warning(f"⚠️ 既存トークンの読み込みに失敗: {e}")
                creds = None
        
        # トークンが無効または期限切れの場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    st.info("🔄 認証トークンを更新しました")
                except Exception as e:
                    st.warning(f"⚠️ トークン更新に失敗: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    st.error(f"❌ 認証情報ファイルが見つかりません: {self.credentials_path}")
                    st.error("Google Cloud Consoleでcredentials.jsonを取得し、プロジェクトルートに配置してください")
                    raise FileNotFoundError(f"認証情報ファイルが見つかりません: {self.credentials_path}")
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    st.success("✅ 新しい認証を完了しました")
                except Exception as e:
                    st.error(f"❌ 認証フローに失敗: {e}")
                    raise
            
            # トークンを保存
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                st.info(f"💾 認証トークンを保存しました: {self.token_path}")
            except Exception as e:
                st.warning(f"⚠️ トークン保存に失敗: {e}")
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            st.success("✅ Google Calendar API接続完了")
        except Exception as e:
            st.error(f"❌ Google Calendar API接続に失敗: {e}")
            raise
    
    def get_calendar_list(self) -> List[Dict[str, str]]:
        """利用可能なカレンダーのリストを取得"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'summary': calendar.get('summary', ''),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False)
                })
            
            st.success(f"📅 {len(calendars)}個のカレンダーを取得しました")
            return calendars
            
        except HttpError as e:
            st.error(f"❌ カレンダーリスト取得エラー: {e}")
            return []
    
    def get_events_for_date(self, target_date: date, calendar_ids: List[str]) -> List[str]:
        """指定日のイベントを取得（行事予定用）"""
        events = []
        
        # 日本時間での当日の開始・終了時刻を設定
        jst = timezone(timedelta(hours=9))
        
        # 当日の00:00:00から23:59:59まで（日本時間）
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=jst)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=jst)
        
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()
        
        st.info(f"🕐 検索時間範囲（日本時間）: {start_time} ～ {end_time}")
        
        for calendar_id in calendar_ids:
            try:
                st.info(f"📅 カレンダー '{calendar_id[:20]}...' から {target_date} のイベントを検索中...")
                
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                calendar_events = events_result.get('items', [])
                
                # デバッグ情報：取得されたイベントの詳細を表示
                st.info(f"🔍 APIから {len(calendar_events)} 件のイベントを取得")
                
                for event in calendar_events:
                    event_title = event.get('summary', '無題のイベント')
                    start = event.get('start', {})
                    
                    # イベントの実際の日付をチェック
                    event_actual_date = None
                    
                    if 'dateTime' in start:
                        # 時刻指定のイベント
                        event_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                        event_actual_date = event_datetime.date()
                        
                        # 指定日と一致するかチェック
                        if event_actual_date == target_date:
                            time_str = event_datetime.astimezone(jst).strftime('%H:%M')
                            events.append(f"{time_str} {event_title}")
                            st.success(f"✅ マッチ: {event_title} ({event_actual_date})")
                        else:
                            st.warning(f"⚠️ 日付不一致: {event_title} (取得日: {event_actual_date}, 指定日: {target_date})")
                            
                    elif 'date' in start:
                        # 終日イベント
                        event_actual_date = datetime.fromisoformat(start['date']).date()
                        
                        # 指定日と一致するかチェック
                        if event_actual_date == target_date:
                            events.append(event_title)
                            st.success(f"✅ マッチ: {event_title} ({event_actual_date})")
                        else:
                            st.warning(f"⚠️ 日付不一致: {event_title} (取得日: {event_actual_date}, 指定日: {target_date})")
                    else:
                        st.warning(f"⚠️ 日付情報なし: {event_title}")
                
                st.success(f"✅ カレンダーから最終的に {len([e for e in events if e not in events[:-len(calendar_events)]])} 件のイベントを追加")
                
            except HttpError as e:
                st.warning(f"⚠️ カレンダー '{calendar_id[:20]}...' のイベント取得エラー: {e}")
                continue
        
        st.info(f"📊 最終結果: {target_date} に {len(events)} 件のイベント")
        return events
    
    def get_events_within_month(self, target_date: date, calendar_ids: List[str], 
                               event_keywords: List[str] = None) -> List[EventInfo]:
        """指定日から2ヶ月以内のイベントを取得（学校説明会等の広報イベント用）"""
        if event_keywords is None:
            event_keywords = ['説明会', '見学会', 'オープンキャンパス', '体験会', '相談会', '入試', '文化祭', '学園祭']
        
        events = []
        end_date = target_date + timedelta(days=60)
        
        # 日本時間での検索期間を設定
        jst = timezone(timedelta(hours=9))
        
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=jst)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=jst)
        
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()
        
        st.info(f"🕐 検索期間（日本時間）: {start_time} ～ {end_time}")
        
        for calendar_id in calendar_ids:
            try:
                st.info(f"📅 カレンダー '{calendar_id[:20]}...' から今後60日間のイベントを検索中...")
                
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                calendar_events = events_result.get('items', [])
                matched_events = 0
                
                st.info(f"🔍 APIから {len(calendar_events)} 件のイベントを取得、キーワードフィルタリング中...")
                
                for event in calendar_events:
                    event_title = event.get('summary', '無題のイベント')
                    event_description = event.get('description', '')
                    
                    # キーワードマッチング
                    keyword_matched = any(keyword in event_title for keyword in event_keywords) or \
                                    any(keyword in event_description for keyword in event_keywords)
                    
                    if keyword_matched:
                        # イベント日時を取得
                        start = event.get('start', {})
                        event_date = None
                        display_title = event_title
                        
                        if 'dateTime' in start:
                            # 時刻指定のイベント
                            event_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                            event_date = event_datetime.date()
                            time_str = event_datetime.astimezone(jst).strftime('%H:%M')
                            display_title = f"{time_str} {event_title}"
                        elif 'date' in start:
                            # 終日イベント
                            event_date = datetime.fromisoformat(start['date']).date()
                        
                        if event_date and target_date <= event_date <= end_date:
                            date_display = f"{event_date.month}月{event_date.day}日" + DateUtils.get_japanese_weekday(event_date)
                            events.append(EventInfo(
                                date=event_date,
                                event=display_title,
                                date_str=date_display
                            ))
                            matched_events += 1
                            st.success(f"✅ マッチ: {event_title} ({event_date})")
                        else:
                            st.warning(f"⚠️ 期間外: {event_title} ({event_date})")
                    else:
                        st.info(f"💡 キーワード不一致: {event_title}")
                
                st.success(f"✅ カレンダーから {matched_events} 件の関連イベントを取得")
                
            except HttpError as e:
                st.warning(f"⚠️ カレンダー '{calendar_id[:20]}...' のイベント取得エラー: {e}")
                continue
        
        # 日付順でソート
        sorted_events = sorted(events, key=lambda x: x.date)
        st.info(f"📊 最終結果: {len(sorted_events)} 件のイベント（{target_date} ～ {end_date}）")
        return sorted_events
    
    def search_events_by_keywords(self, start_date: date, end_date: date, 
                                 keywords: List[str], calendar_ids: List[str]) -> List[EventInfo]:
        """キーワードでイベントを検索"""
        events = []
        
        start_time = datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z'
        end_time = datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z'
        
        for calendar_id in calendar_ids:
            for keyword in keywords:
                try:
                    st.info(f"🔍 キーワード '{keyword}' でカレンダー '{calendar_id[:20]}...' を検索中...")
                    
                    events_result = self.service.events().list(
                        calendarId=calendar_id,
                        timeMin=start_time,
                        timeMax=end_time,
                        q=keyword,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    calendar_events = events_result.get('items', [])
                    
                    for event in calendar_events:
                        event_title = event.get('summary', '無題のイベント')
                        
                        # イベント日時を取得
                        start = event.get('start', {})
                        event_date = None
                        
                        if 'dateTime' in start:
                            event_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                            event_date = event_datetime.date()
                            time_str = event_datetime.strftime('%H:%M')
                            display_title = f"{time_str} {event_title}"
                        elif 'date' in start:
                            event_date = datetime.fromisoformat(start['date']).date()
                            display_title = event_title
                        
                        if event_date:
                            date_display = f"{event_date.month}月{event_date.day}日" + DateUtils.get_japanese_weekday(event_date)
                            event_info = EventInfo(
                                date=event_date,
                                event=display_title,
                                date_str=date_display
                            )
                            
                            # 重複を避ける
                            if event_info not in events:
                                events.append(event_info)
                    
                    st.success(f"✅ キーワード '{keyword}' で {len(calendar_events)} 件見つかりました")
                    
                except HttpError as e:
                    st.warning(f"⚠️ キーワード検索エラー: {e}")
                    continue
        
        return sorted(events, key=lambda x: x.date)