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

from config import AppConfig, WeatherInfo, EventInfo, YouTubeVideo
from data_loader import EventDataService
from weather_service import WeatherService
from youtube_service import YouTubeService
from utils import DateUtils

# 学校統合システムは削除済み


class NewsletterFormatter:
    """メルマガの整形を担当"""
    
    @staticmethod
    def format_weather_for_newsletter(weather_info: WeatherInfo, target_date: date, 
                                    heartwarming_message: str, moon_age: float = None, moon_phase_name: str = None) -> str:
        """天気情報をメルマガ用の文章に整形（月齢情報付き）"""
        formatted_date = f"{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
        
        # 月齢情報の表示部分を作成
        moon_info = ""
        if moon_age is not None and moon_phase_name:
            moon_info = f"\n\n【月齢：{moon_age:.1f}日（{moon_phase_name}）】"
        
        return f"""
{formatted_date}の天気は{weather_info.天気概況}です。気温は{weather_info.気温}となる予想です。
湿度は{weather_info.湿度}で、風は{weather_info.風速}となっています。
降水確率は{weather_info.降水確率}となっており、全体的に{weather_info.快適具合}一日になりそうです。{moon_info}

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
    
    @staticmethod
    def format_youtube_for_newsletter(videos: List[YouTubeVideo]) -> str:
        """
        YouTube動画情報をメルマガ用にフォーマット
        動画タイトルとURLを表示（発行日と完全一致するもののみ）
        """
        if not videos:
            return "本日の日付が含まれるYouTube動画は見つかりませんでした。"
        
        formatted_videos = []
        for i, video in enumerate(videos[:3]):  # 最大3つまで表示
            formatted_videos.append(f"・{video.title}")
            formatted_videos.append(f"  {video.url}")
            if i < len(videos) - 1:
                formatted_videos.append("")  # 動画間に空行
        
        return "\n".join(formatted_videos)
    


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
        
        # YouTube APIが利用可能かチェック
        if config.youtube_api_key:
            try:
                self.youtube_service = YouTubeService(config.youtube_api_key)
            except Exception as e:
                st.warning(f"YouTube APIの初期化に失敗: {e}")
                self.youtube_service = None
        else:
            self.youtube_service = None
            
        self.formatter = NewsletterFormatter()
        
        # 学校統合システムは削除済み



    
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
        
        # 2. 天気情報を取得・処理（複合API使用・当日優先）
        st.info("🌤️ Step 3: 天気情報の取得（当日データ最優先）")
        
        # 2-1. 気象庁互換APIで基本天気データ取得（当日優先）
        st.info(f"🌡️ {target_date.strftime('%Y年%m月%d日')}の天気データを優先取得中...")
        weather_data = self.weather_service.load_weather_data(target_date)
        
        # 2-2. Open-Meteo APIで湿度データを補完
        humidity_data = self.weather_service.get_humidity_data(target_date)
        
        # 2-3. Open-Meteo APIで風速データを補完
        wind_data = self.weather_service.get_wind_data(target_date)
        
        # 2-4. すべてのデータを統合
        combined_weather_data = self.weather_service.merge_weather_data(weather_data, humidity_data, wind_data)
        
        weather_info = None
        weather_text = ""
        
        if combined_weather_data:
            weather_info = self.weather_service.extract_weather_info(combined_weather_data, target_date)
            if weather_info:
                heartwarming_message = self.weather_service.generate_heartwarming_message(weather_info, target_date)
                # 月齢データを取得
                moon_age = self.weather_service.latest_moon_age
                moon_phase_name = None
                if moon_age is not None:
                    moon_phase_name = self.weather_service.get_moon_phase_name(moon_age)
                weather_text = self.formatter.format_weather_for_newsletter(
                    weather_info, target_date, heartwarming_message, moon_age, moon_phase_name
                )
        # データ取得状況をユーザーに明示
        if "当日データ取得不可" in combined_weather_data:
            st.warning("⚠️ 当日の天気データが取得できないため、代替データで補完しました")
        elif "当日データなし" in combined_weather_data:
            st.info("📅 当日の気温データは発表時刻により未発表です")
        else:
            st.success("✅ 当日の天気情報を正常に取得しました")
        
        st.info("✅ 天気情報取得完了")
        
        # 3. YouTube動画情報を取得（発行日と完全一致するもののみ）
        st.info("📹 Step 4: YouTube動画情報の取得（発行日と完全一致、YYYY\\MM/DDパターン含む）")
        youtube_videos = []
        if self.youtube_service:
            try:
                youtube_videos = self.youtube_service.search_videos_by_date(target_date)
                if youtube_videos:
                    st.info(f"✅ 発行日と一致するYouTube動画: {len(youtube_videos)} 件")
                else:
                    st.info(f"✅ {target_date.strftime('%Y年%m月%d日')}の動画は見つかりませんでした")
            except Exception as e:
                st.warning(f"YouTube動画の取得に失敗: {e}")
        else:
            st.info("YouTube APIが設定されていないため、動画情報をスキップします")
        
        # 4. 発行No.の決定
        issue_number = manual_issue_number if manual_issue_number is not None else DateUtils.get_issue_number(target_date)
        
        # 5. メルマガを生成
        st.info("📧 Step 5: メルマガコンテンツの生成")
        newsletter_content = self._generate_newsletter_content(
            weather_text, schedule_events, event_events, youtube_videos, 
            target_date, issue_number
        )
        st.success("✅ メルマガ生成完了！")
        
        return {
            'content': newsletter_content,
            'weather_info': weather_info,
            'weather_text': weather_text,
            'schedule_events': schedule_events,
            'event_events': event_events,
            'youtube_videos': youtube_videos,
            'metadata': {
                'target_date': target_date,
                'formatted_date': f"{target_date.year}年{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date),
                'issue_number': issue_number,
                'is_manual_issue_number': manual_issue_number is not None,
                'weekday': DateUtils.get_japanese_weekday_full(target_date),
                'character_count': len(newsletter_content)
            }
        }
    
    def _generate_newsletter_content(self, weather_text: str, schedule_events, 
                                   event_events, youtube_videos: List[YouTubeVideo],
                                   target_date: date, issue_number: int) -> str:
        """Jinja2テンプレートを使用してメルマガコンテンツを生成"""
        template = Template(self._get_newsletter_template())
        
        formatted_date = f"{target_date.year}年{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
        weekday = DateUtils.get_japanese_weekday_full(target_date)
        weekday_theme = DateUtils.get_weekday_theme(target_date)
        
        # データの適切なフォーマッティング
        schedule_text = self.formatter.format_schedule_for_newsletter(schedule_events)
        event_text = self.formatter.format_events_for_newsletter(event_events)
        
        youtube_text = self.formatter.format_youtube_for_newsletter(youtube_videos)
        
        # 生成日時（日本時間）を取得
        generated_time = DateUtils.get_now_jst()
        generated_timestamp = generated_time.strftime('%Y年%m月%d日 %H:%M:%S')
        
        return template.render(
            発行日=formatted_date,
            発行No=issue_number,
            生成日時=generated_timestamp,
            weather=weather_text,
            schedule=schedule_text,
            event=event_text,
            youtube=youtube_text,
            曜日=weekday,
            曜日テーマ=weekday_theme,
            曜日補足=""
        )
    
    def _get_newsletter_template(self) -> str:
        """メルマガテンプレートを取得"""
        return """『一日一知』日大一を毎日少しずつ知る学校案内 {{ 発行日 }}, No.{{ 発行No }}
生成日時: {{ 生成日時 }} (JST)

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

4. YouTube動画情報
-----
{{ youtube }}
-----

5. 今日の学校案内（{{ 曜日 }}曜日のテーマ：{{ 曜日テーマ }}）
-----
{% if 曜日補足 %}
{{ 曜日補足 }}
{% endif %}
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