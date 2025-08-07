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
        
        # Streamlit Cloud環境の判定
        is_streamlit_cloud = hasattr(st, 'secrets')
        
        # 既存のトークンファイルをチェック（ローカル環境のみ）
        if not is_streamlit_cloud and os.path.exists(self.token_path):
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
                # Streamlit Cloudの場合はst.secretsから読み込む
                credentials_data = None
                
                # 個別設定からの読み込みを優先
                if (hasattr(st, 'secrets') and 
                    'GOOGLE_SERVICE_TYPE' in st.secrets and 
                    'GOOGLE_PRIVATE_KEY' in st.secrets):
                    try:
                        credentials_data = {
                            "type": st.secrets['GOOGLE_SERVICE_TYPE'],
                            "project_id": st.secrets['GOOGLE_PROJECT_ID'],
                            "private_key_id": st.secrets['GOOGLE_PRIVATE_KEY_ID'],
                            "private_key": st.secrets['GOOGLE_PRIVATE_KEY'],
                            "client_email": st.secrets['GOOGLE_CLIENT_EMAIL'],
                            "client_id": st.secrets['GOOGLE_CLIENT_ID'],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['GOOGLE_CLIENT_EMAIL'].replace('@', '%40')}"
                        }
                        st.info("✅ Streamlit secrets（個別設定）から認証情報を読み込みました")
                    except Exception as e:
                        st.error(f"❌ Streamlit secrets（個別設定）からの読み込みに失敗: {e}")
                
                # 個別設定がない場合は従来のJSON形式を試行
                elif hasattr(st, 'secrets') and 'GOOGLE_CREDENTIALS' in st.secrets:
                    try:
                        credentials_raw = st.secrets['GOOGLE_CREDENTIALS']
                        # 文字列の場合はJSONパース、辞書の場合はそのまま使用
                        if isinstance(credentials_raw, str):
                            # 改行やスペースを正規化してからパース
                            credentials_clean = credentials_raw.replace('\n', '').replace('  ', ' ').strip()
                            credentials_data = json.loads(credentials_clean)
                        else:
                            # すでに辞書形式の場合
                            credentials_data = credentials_raw
                        st.info("✅ Streamlit secrets（JSON形式）から認証情報を読み込みました")
                    except Exception as e:
                        st.error(f"❌ Streamlit secrets（JSON形式）からの読み込みに失敗: {e}")
                        st.error(f"デバッグ情報: {type(st.secrets['GOOGLE_CREDENTIALS'])}")
                        # 生データを表示してデバッグ
                        if hasattr(st, 'secrets'):
                            raw_data = str(st.secrets['GOOGLE_CREDENTIALS'])[:200] + "..."
                            st.error(f"生データ(最初200文字): {raw_data}")
                
                # ローカルファイルから読み込む
                if not credentials_data and os.path.exists(self.credentials_path):
                    try:
                        with open(self.credentials_path, 'r') as f:
                            credentials_data = json.load(f)
                        st.info("✅ ローカルファイルから認証情報を読み込みました")
                    except Exception as e:
                        st.error(f"❌ ローカルファイルの読み込みに失敗: {e}")
                
                if not credentials_data:
                    st.error("❌ 認証情報が見つかりません")
                    st.error("ローカル環境: credentials.jsonをプロジェクトルートに配置してください")
                    st.error("Streamlit Cloud: SecretsにGOOGLE_CREDENTIALSを設定してください")
                    raise FileNotFoundError("認証情報が見つかりません")
                
                try:
                    # is_streamlit_cloud変数は既に定義済み
                    
                    if is_streamlit_cloud:
                        # Streamlit Cloud: 必ずサービスアカウント認証を使用
                        if 'type' in credentials_data and credentials_data['type'] == 'service_account':
                            from google.oauth2 import service_account
                            creds = service_account.Credentials.from_service_account_info(
                                credentials_data, scopes=self.SCOPES)
                            st.success("✅ サービスアカウント認証を完了しました")
                        else:
                            st.error("❌ Streamlit Cloudではサービスアカウント認証が必要です")
                            st.error("OAuth2認証情報ではなく、サービスアカウントキーを使用してください")
                            st.error(f"取得した認証情報のtype: {credentials_data.get('type', 'unknown')}")
                            raise ValueError("サービスアカウント認証が必要です")
                    else:
                        # ローカル環境: OAuth2フロー
                        flow = InstalledAppFlow.from_client_config(
                            credentials_data, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                        st.success("✅ 新しい認証を完了しました")
                except Exception as e:
                    st.error(f"❌ 認証フローに失敗: {e}")
                    if hasattr(st, 'secrets'):
                        st.error("💡 Streamlit Cloudではサービスアカウントキー（JSON）が必要です")
                        st.error("Google Cloud Console > IAM > サービスアカウントでキーを作成してください")
                        # デバッグ情報を追加
                        if credentials_data:
                            st.error(f"認証情報の内容確認:")
                            st.error(f"- type: {credentials_data.get('type', 'missing')}")
                            st.error(f"- project_id: {credentials_data.get('project_id', 'missing')}")
                            st.error(f"- client_email: {credentials_data.get('client_email', 'missing')}")
                    raise
            
            # トークンを保存（OAuth2認証の場合のみ）
            if not is_streamlit_cloud:  # ローカル環境でのOAuth2認証の場合のみ保存
                try:
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                    st.info(f"💾 認証トークンを保存しました: {self.token_path}")
                except Exception as e:
                    st.warning(f"⚠️ トークン保存に失敗: {e}")
            else:
                st.info("🔐 サービスアカウント認証はトークン保存不要です")
        
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
            
            st.info("🔍 アクセス可能なカレンダー一覧:")
            for calendar in calendar_list.get('items', []):
                calendar_info = {
                    'id': calendar['id'],
                    'summary': calendar.get('summary', ''),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False)
                }
                calendars.append(calendar_info)
                
                # デバッグ情報として表示
                st.info(f"📋 {calendar_info['summary']} (ID: {calendar_info['id'][:20]}...)")
            
            st.success(f"📅 {len(calendars)}個のカレンダーを取得しました")
            
            # 設定されているカレンダーIDとの照合
            st.info("🔍 設定されているカレンダーIDの確認:")
            target_ids = ['nichidai1.haishin@gmail.com', 'c38f50b10481248d05113108d0ba210e7edd5d60abe152ce319c595f011cb814@group.calendar.google.com']
            for target_id in target_ids:
                found = any(cal['id'] == target_id for cal in calendars)
                status = "✅ 見つかりました" if found else "❌ アクセスできません"
                st.info(f"- {target_id[:40]}... : {status}")
            
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
        """指定日から2ヶ月以内のイベントを全て取得（キーワードフィルタリング削除）"""
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
                st.info(f"📅 カレンダー '{calendar_id[:20]}...' から今後60日間の全イベントを取得中...")
                
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                calendar_events = events_result.get('items', [])
                processed_events = 0
                
                st.info(f"🔍 APIから {len(calendar_events)} 件のイベントを取得、全て処理中...")
                
                for event in calendar_events:
                    event_title = event.get('summary', '無題のイベント')
                    
                    # キーワードフィルタリングを削除 - 全てのイベントを取得
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
                        processed_events += 1
                        st.success(f"✅ 取得: {event_title} ({event_date})")
                    else:
                        st.warning(f"⚠️ 期間外: {event_title} ({event_date})")
                
                st.success(f"✅ カレンダーから {processed_events} 件の全イベントを取得")
                
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