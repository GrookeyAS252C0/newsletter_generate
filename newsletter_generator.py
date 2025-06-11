"""
メルマガ生成のビジネスロジック（Google Calendar専用版）
"""
from langchain_openai import ChatOpenAI

import time
from datetime import date
from typing import List, Dict, Any, Optional

try:
    import streamlit as st
except ImportError:
    class DummySt:
        def spinner(self, msg): 
            class DummySpinner:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return DummySpinner()
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def expander(self, title, expanded=False):
            class DummyExpander:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def write(self, msg): print(f"EXPANDER: {msg}")
                def code(self, content, language=None): print(f"CODE: {content}")
            return DummyExpander()
    st = DummySt()

try:
    from jinja2 import Template
except ImportError:
    raise ImportError("jinja2がインストールされていません: pip install jinja2")

from config import AppConfig, WeatherInfo, EventInfo
from data_loader import EventDataService
from weather_service import WeatherService
from utils import DateUtils


class NewsletterFormatter:
    """メルマガの整形を担当"""
    
    @staticmethod
    def format_weather_for_newsletter(weather_info: WeatherInfo, target_date: date, 
                                    heartwarming_message: str) -> str:
        """天気情報をメルマガ用の文章に整形"""
        formatted_date = f"{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
        
        return f"""
{formatted_date}の天気は{weather_info.天気概況}です。気温は{weather_info.気温}となる予想です。
湿度は{weather_info.湿度}で、風は{weather_info.風速}となっています。
降水確率は{weather_info.降水確率}となっており、全体的に{weather_info.快適具合}一日になりそうです。

{heartwarming_message}
""".strip()
    
    @staticmethod
    def format_schedule_for_newsletter(schedule_events: List[str]) -> str:
        """行事予定をメルマガ用にフォーマット（「今日の日大一」セクション用）"""
        if not schedule_events:
            return "今日はおやすみです。"
        
        # 時刻順にソートされたイベントを整形
        formatted_events = []
        for event in schedule_events:
            # 既に時刻が含まれている場合はそのまま、そうでなければ追加
            formatted_events.append(f"・{event}")
        
        return "\n".join(formatted_events)
    
    @staticmethod
    def format_events_for_newsletter(event_events: List[EventInfo]) -> str:
        """イベント情報をメルマガ用にフォーマット（「今後の学校説明会について」セクション用）"""
        if not event_events:
            return "現在、2ヶ月以内に予定されている学校説明会等のイベントはございません。最新情報は学校ホームページをご確認ください。"
        
        # 日付順に整理されたイベントを整形
        formatted_events = []
        for event in event_events:
            formatted_events.append(f"・{event.date_str}: {event.event}")
        
        return "\n".join(formatted_events)
    


class NewsletterGenerator:
    """メルマガ生成の中核処理を担当（Google Calendar専用版）"""
    
    def __init__(self, config: AppConfig, calendar_config: dict = None):
        self.config = config
        
        # Google Calendar専用のEventDataService
        self.event_service = EventDataService(
            use_google_calendar=calendar_config.get('use_google_calendar', True) if calendar_config else True,
            calendar_config=calendar_config or {}
        )
        
        self.weather_service = WeatherService(config.openai_api_key)
        self.formatter = NewsletterFormatter()



    
    def generate_newsletter(self, target_date: date, manual_issue_number: Optional[int] = None) -> Dict[str, Any]:
        """メルマガを生成（Google Calendar専用版）"""
        
        st.info("🔄 メルマガ生成開始...")
        
        # 1. 行事予定とイベント情報を取得（Google Calendar専用）
        st.info("📅 Step 1: 行事予定の取得（「今日の日大一」用）")
        schedule_events = self.event_service.get_events_for_date(target_date)
        st.info(f"✅ 行事予定取得完了: {len(schedule_events)} 件")
        
        st.info("🎉 Step 2: 広報イベントの取得（「今後の学校説明会について」用・2ヶ月以内）")
        event_events = self.event_service.get_events_within_month(target_date)
        st.info(f"✅ 広報イベント取得完了: {len(event_events)} 件")
        
        # 2. 天気情報を取得・処理（複数ソース）
        st.info("🌤️ Step 3: 天気情報の取得")
        weather_urls = [self.config.weather_url, self.config.additional_weather_url]
        weather_data = self.weather_service.load_weather_data(weather_urls)
        weather_info = None
        weather_text = ""
        
        if weather_data:
            weather_info = self.weather_service.extract_weather_info(weather_data, target_date)
            if weather_info:
                heartwarming_message = self.weather_service.generate_heartwarming_message(weather_info, target_date)
                weather_text = self.formatter.format_weather_for_newsletter(weather_info, target_date, heartwarming_message)
        st.info("✅ 天気情報取得完了")
        
        # 3. 発行No.の決定
        issue_number = manual_issue_number if manual_issue_number is not None else DateUtils.get_issue_number(target_date)
        
        # 4. メルマガを生成
        st.info("📧 Step 4: メルマガコンテンツの生成")
        newsletter_content = self._generate_newsletter_content(
            weather_text, schedule_events, event_events, target_date, issue_number
        )
        st.success("✅ メルマガ生成完了！")
        
        return {
            'content': newsletter_content,
            'weather_info': weather_info,
            'weather_text': weather_text,
            'schedule_events': schedule_events,
            'event_events': event_events,
            'metadata': {
                'target_date': target_date,
                'formatted_date': f"{target_date.year}年{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date),
                'issue_number': issue_number,
                'is_manual_issue_number': manual_issue_number is not None,
                'weekday': DateUtils.get_japanese_weekday_full(target_date),
                'character_count': len(newsletter_content)
            }
        }
    
    def _generate_newsletter_content(self, weather_text: str, schedule_events: List[str], 
                                   event_events: List[EventInfo], target_date: date, issue_number: int) -> str:
        """Jinja2テンプレートを使用してメルマガコンテンツを生成"""
        template = Template(self._get_newsletter_template())
        
        formatted_date = f"{target_date.year}年{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
        weekday = DateUtils.get_japanese_weekday_full(target_date)
        weekday_theme = DateUtils.get_weekday_theme(target_date)
        
        schedule_text = self.formatter.format_schedule_for_newsletter(schedule_events)
        event_text = self.formatter.format_events_for_newsletter(event_events)
        
        return template.render(
            発行日=formatted_date,
            発行No=issue_number,
            weather=weather_text,
            schedule=schedule_text,
            event=event_text,
            曜日=weekday,
            曜日テーマ=weekday_theme
        )
    
    def _get_newsletter_template(self) -> str:
        """メルマガテンプレートを取得"""
        return """『一日一知』日大一を毎日少しずつ知る学校案内 {{ 発行日 }}, No.{{ 発行No }}

日本大学第一中学・高等学校にご関心をお寄せいただき、誠にありがとうございます。「メルマガ『一日一知』日大一を毎日少しずつ知る学校案内」にお申込みいただいた皆様に、今日の日大一の様子をお伝えします。

1. 本日の墨田区横網の天気
-----
{{ weather }}
-----

2. 今日の日大一
-----
{{ schedule }}
-----

3. 今後の学校説明会について
-----
以下の日程で実施予定となっております。メルマガを通して「来校型イベント」に興味を持っていただけましたら、以下のURLからお申し込みいただければ幸いです。
中学受験：https://mirai-compass.net/usr/ndai1j/event/evtIndex.jsf
高校受験：https://mirai-compass.net/usr/ndai1h/event/evtIndex.jsf
{{ event }}
-----

4. 今日の学校案内（{{ 曜日 }}曜日のテーマ：{{ 曜日テーマ }}）
-----

-----

今回のメルマガは以上となります。

ご不明な点やご質問がございましたら、お気軽にお問い合わせください（03-3625-0026）。

{% if 曜日 == '土' %}来週も日大一の"ひと知り"をお届けします。{% else %}明日も日大一の"ひと知り"をお届けします。{% endif %}

日本大学第一中学・高等学校　入試広報部
※「メルマガ『一日一知』日大一を毎日少しずつ知る学校案内」の受信を停止したい場合は、以下の手順を実行してください：
・日大一のホームページから、ミライコンパスの「マイページ」にログインする
・「ログイン情報変更」（スマートフォンの場合は三本線のメニュー）を選択する
・「メール受信設定変更」を選択する
・「ログイン情報変更」のチェックボックスを解除する"""