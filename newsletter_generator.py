"""
メルマガ生成のビジネスロジック（Google Calendar専用版）
"""
from langchain_openai import ChatOpenAI
from langchain.document_loaders import YoutubeLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

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

from config import AppConfig, WeatherInfo, YouTubeVideo, EventInfo
from data_loader import EventDataService
from weather_service import WeatherService
from youtube_service import YouTubeService
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
    
    @staticmethod
    def format_youtube_for_newsletter(videos: List[YouTubeVideo]) -> str:
        """
        メルマガ用の YouTube 表示
        ─ タイトル
        ─ URL
        ─ 100 文字以内キャッチコピー
        """
        if not videos:
            return "本日の YouTube 投稿は見つかりませんでした。"

        v = videos[0]
        teaser = getattr(v, "teaser", "")
        lines = [v.title, v.url]
        if teaser:
            lines.append(teaser)
        return "\n".join(lines)


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

    def _generate_video_teaser(self, video: YouTubeVideo) -> tuple[str, str, str]:
        """
        YouTube動画から字幕を取得し、要約とキャッチコピーを生成する
        ・要約 (summary)
        ・キャッチコピー (teaser, 100 字以内)
        ・字幕全文 (transcript)
        を返す。言語は ja→en の順でフォールバック。
        """
        st.info(f"🎞️ 字幕を取得する動画: {video.title} ({video.url})")

        def _load_transcript_with_retry() -> str:
            """
            字幕を複数の言語でリトライしながら取得する
            効率化：成功した時点で即座に返却
            """
            # 効率的な順序で言語を試行（デバッグ情報を参考に調整）
            language_combinations = [
                ["ja"],           # 日本語（最も成功率が高い）
                [],               # 言語指定なし（デフォルト）
                ["en"],           # 英語
                ["ja-JP"],        # 日本語（地域指定）
                ["en-US"],        # 英語（米国）
            ]
            
            tries = 3
            
            for lang_list in language_combinations:
                lang_str = str(lang_list) if lang_list else "デフォルト"
                st.info(f"🌐 言語設定 {lang_str} で字幕取得を試行中...")
                
                for attempt in range(tries):
                    try:
                        # パターン1: 提供されたシンプルなコードパターン（日本語のみ）
                        if lang_list == ["ja"] and attempt == 0:
                            st.info("📝 提供されたコードパターンで試行中...")
                            try:
                                loader = YoutubeLoader.from_youtube_url(video.url, language=["ja"])
                                
                                # 提供されたリトライパターンを実装
                                for i in range(3):
                                    try:
                                        movie_content = loader.load()[0].page_content
                                        if movie_content and len(movie_content.strip()) > 10:
                                            st.success(f"✅ 提供パターンで字幕取得成功! (文字数: {len(movie_content)})")
                                            return movie_content  # 即座に返却
                                        break
                                    except Exception as e:
                                        if i + 1 == 3:
                                            st.warning(f"提供パターン失敗: {e}")
                                            break
                                        time.sleep(2)
                                        continue
                            except Exception as e:
                                st.warning(f"提供パターン初期化失敗: {e}")
                        
                        # パターン2: 標準的な方法
                        try:
                            if lang_list:
                                loader = YoutubeLoader.from_youtube_url(video.url, language=lang_list)
                            else:
                                loader = YoutubeLoader.from_youtube_url(video.url)
                                
                            docs = loader.load()
                            if docs and len(docs) > 0:
                                content = docs[0].page_content.strip()
                                if content and len(content) > 10:
                                    st.success(f"✅ 字幕取得成功 (言語: {lang_str}, 試行: {attempt + 1}, 文字数: {len(content)})")
                                    return content  # 即座に返却
                                else:
                                    st.warning(f"⚠️ 字幕データが短すぎます (言語: {lang_str}, 文字数: {len(content)})")
                            else:
                                st.warning(f"⚠️ 空のドキュメント (言語: {lang_str}, 試行: {attempt + 1})")
                                
                        except Exception as e:
                            error_msg = str(e)
                            
                            # 特定のエラーで早期終了判定
                            if "No transcripts were found" in error_msg:
                                st.warning(f"📝 この言語設定では字幕が見つかりません: {lang_str}")
                                break  # この言語設定では字幕がないので次の言語へ
                            elif "Video unavailable" in error_msg:
                                st.error(f"🚫 動画が利用できません")
                                return ""  # 完全に諦める
                            elif "Private video" in error_msg:
                                st.error(f"🚫 非公開動画です")
                                return ""  # 完全に諦める
                            elif attempt + 1 == tries:
                                st.warning(f"❌ 字幕取得失敗 (言語: {lang_str}): {error_msg}")
                            else:
                                st.info(f"🔄 リトライ中 (言語: {lang_str}, 試行: {attempt + 1})")
                                time.sleep(1)  # リトライ間隔を短縮
                                
                    except Exception as outer_e:
                        st.error(f"🚫 予期しないエラー (言語: {lang_str}, 試行: {attempt + 1}): {outer_e}")
                        if attempt + 1 == tries:
                            break
            
            st.warning("🚫 すべての言語設定で字幕取得に失敗しました")
            return ""

        # 字幕を取得
        transcript_text = _load_transcript_with_retry()
        
        # 字幕が取得できた場合はデバッグをスキップ
        if not transcript_text:
            # デバッグ情報を表示（字幕取得に失敗した場合のみ）
            self._debug_youtube_video_info(video.url)
        else:
            st.success(f"🎯 字幕取得完了: {len(transcript_text)} 文字")
        
        if not transcript_text:
            st.warning("📜 字幕が取得できませんでした。動画の説明文から情報を生成します。")
            # 字幕が取得できない場合は、動画タイトルのみでキャッチコピーを生成
            return self._generate_teaser_from_title_only(video.title)

        # LLMモデル初期化
        llm = ChatOpenAI(
            openai_api_key=self.config.openai_api_key,
            model_name="gpt-4o-mini",
            temperature=0.2,
        )

        # 要約生成
        summary = ""
        try:
            from langchain.docstore.document import Document
            docs = [Document(page_content=transcript_text)]
            
            summary = load_summarize_chain(llm, chain_type="stuff").run(docs).strip()
            st.success("📝 要約生成完了")
            
        except Exception as e:
            st.warning(f"⚠️ 要約生成に失敗: {e}")
            # 要約に失敗した場合は、字幕の最初の1000文字を使用
            summary = transcript_text[:1000] if transcript_text else ""

        # キャッチコピー生成
        teaser = ""
        try:
            if summary:
                prompt = PromptTemplate(
                    input_variables=["title", "summary"],
                    template=(
                        "あなたはYouTube動画を紹介するコピーライターです。\n"
                        "次のタイトルと内容概要を参考に、読者が思わず動画を見たくなる"
                        "日本語キャッチコピー（100文字以内）を1行で作成してください。\n\n"
                        "タイトル: {title}\n"
                        "概要: {summary}\n\n"
                        "キャッチコピー:"
                    ),
                )
                teaser = (
                    LLMChain(llm=llm, prompt=prompt)
                    .run({"title": video.title, "summary": summary})
                    .strip()[:100]
                )
            else:
                teaser = self._generate_teaser_from_title_only(video.title)[0]
            
            st.success("🎯 キャッチコピー生成完了")
            
        except Exception as e:
            st.warning(f"⚠️ キャッチコピー生成に失敗: {e}")
            teaser = "最新動画をチェック！"

        return teaser or "最新動画をチェック！", summary, transcript_text

    def _debug_youtube_video_info(self, video_url: str):
        """デバッグ用：動画の字幕情報を調査"""
        try:
            st.info("🔍 動画の字幕情報をデバッグ中...")
            
            # まずURLの形式をチェック
            if "youtube.com/watch?v=" not in video_url and "youtu.be/" not in video_url:
                st.error("🚫 無効なYouTube URLです")
                return
            
            # 動画IDを抽出
            try:
                if "youtube.com/watch?v=" in video_url:
                    video_id = video_url.split("watch?v=")[1].split("&")[0]
                elif "youtu.be/" in video_url:
                    video_id = video_url.split("youtu.be/")[1].split("?")[0]
                else:
                    st.error("🚫 動画IDを抽出できません")
                    return
                
                st.info(f"📹 動画ID: {video_id}")
            except Exception as e:
                st.error(f"🚫 動画ID抽出エラー: {str(e)}")
                return
            
            # 複数の方法で字幕取得を試行
            methods = [
                {"name": "基本ローダー", "add_video_info": False},
                {"name": "動画情報付きローダー", "add_video_info": True},
                {"name": "言語指定なしローダー", "add_video_info": False, "no_language": True}
            ]
            
            for method in methods:
                try:
                    st.info(f"🔧 {method['name']}で試行中...")
                    
                    if method.get("no_language"):
                        # 言語指定を一切しない
                        loader = YoutubeLoader.from_youtube_url(
                            video_url,
                            add_video_info=method["add_video_info"]
                        )
                    else:
                        loader = YoutubeLoader.from_youtube_url(
                            video_url,
                            add_video_info=method["add_video_info"]
                        )
                    
                    docs = loader.load()
                    if docs:
                        content_length = len(docs[0].page_content) if docs[0].page_content else 0
                        st.success(f"✅ {method['name']}で成功: {content_length} 文字")
                        
                        # メタデータがあれば表示
                        if hasattr(docs[0], 'metadata') and docs[0].metadata:
                            with st.expander(f"📊 {method['name']} - メタデータ詳細"):
                                st.json(docs[0].metadata)
                        
                        # 内容の一部をプレビュー
                        if content_length > 0:
                            preview = docs[0].page_content[:200] + "..." if content_length > 200 else docs[0].page_content
                            with st.expander(f"👁️ {method['name']} - 内容プレビュー"):
                                st.text(preview)
                        
                        return  # 成功したら終了
                    else:
                        st.warning(f"⚠️ {method['name']}: 空のドキュメント")
                        
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ {method['name']}エラー: {error_msg}")
                    
                    # 特定のエラーメッセージをチェック
                    if "HTTP Error 400" in error_msg:
                        st.info("💡 HTTP 400エラー: YouTubeサーバーがリクエストを拒否しました")
                    elif "HTTP Error 403" in error_msg:
                        st.info("💡 HTTP 403エラー: アクセスが禁止されています（地域制限・年齢制限など）")
                    elif "No transcripts were found" in error_msg:
                        st.info("💡 この動画には字幕が存在しません")
                    elif "Video unavailable" in error_msg:
                        st.info("💡 動画が利用できません（非公開・削除済み）")
                    elif "Subtitles are disabled" in error_msg:
                        st.info("💡 この動画では字幕が無効になっています")
                    elif "Private video" in error_msg:
                        st.info("💡 非公開動画です")
                    
            # 全ての方法が失敗した場合
            st.error("🚫 すべての方法で字幕取得に失敗しました")
            
            # 代替手段の提案
            st.info("💡 代替手段:")
            st.markdown("""
            - 別の動画で試してみてください
            - 動画に実際に字幕があるかブラウザで確認してください
            - 動画が公開設定になっているか確認してください
            - しばらく時間をおいてから再試行してください
            """)
                    
        except Exception as e:
            st.error(f"🔍 デバッグ中に予期しないエラー: {str(e)}")

    def _generate_teaser_from_title_only(self, title: str) -> tuple[str, str, str]:
        """
        タイトルのみからキャッチコピーを生成する（フォールバック用）
        """
        try:
            llm = ChatOpenAI(
                openai_api_key=self.config.openai_api_key,
                model_name="gpt-4o-mini",
                temperature=0.2,
            )
            
            prompt = PromptTemplate(
                input_variables=["title"],
                template=(
                    "次のYouTube動画タイトルだけを参考に、"
                    "日本語キャッチコピー（100文字以内）を作成してください。\n\n"
                    "タイトル: {title}\n\n"
                    "キャッチコピー:"
                ),
            )
            teaser = (
                LLMChain(llm=llm, prompt=prompt)
                .run({"title": title})
                .strip()[:100]
            )
            
            return teaser or "最新動画をチェック！", "", ""
            
        except Exception as e:
            st.warning(f"⚠️ タイトルベースのキャッチコピー生成に失敗: {e}")
            return "最新動画をチェック！", "", ""
    
    def generate_newsletter(self, target_date: date, manual_channel_id: Optional[str] = None, 
                          manual_issue_number: Optional[int] = None) -> Dict[str, Any]:
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
        
        # 3. YouTube動画を検索（ボタン押下時のみ）
        st.info("📺 Step 4: YouTube動画の検索")
        youtube_videos = []
        if self.youtube_service:
            with st.spinner(f"📺 YouTube動画を検索中..."):
                youtube_videos = self.youtube_service.search_videos_by_date(target_date, manual_channel_id)
        st.info(f"✅ YouTube動画検索完了: {len(youtube_videos)} 件")
        
        # 3.5 先頭動画からコピーと要約を生成
        youtube_teaser, youtube_summary, youtube_transcript = "", "", ""
        if youtube_videos:
            youtube_teaser, youtube_summary, youtube_transcript = self._generate_video_teaser(youtube_videos[0])
            setattr(youtube_videos[0], "teaser", youtube_teaser)
            setattr(youtube_videos[0], "summary", youtube_summary)
            setattr(youtube_videos[0], "transcript", youtube_transcript) 

            # 要約を UI で確認できるようにする
            with st.expander("🎞️ 自動要約を確認する"):
                st.write(youtube_summary or "要約が取得できませんでした。")

            if youtube_transcript:
                with st.expander("📜 字幕全文を確認する", expanded=False):
                    st.code(youtube_transcript.strip(), language="text")
            else:
                st.info("📜 字幕を取得できませんでした。")
            
        # 4. 発行No.の決定
        issue_number = manual_issue_number if manual_issue_number is not None else DateUtils.get_issue_number(target_date)
        
        # 5. メルマガを生成
        st.info("📧 Step 5: メルマガコンテンツの生成")
        newsletter_content = self._generate_newsletter_content(
            weather_text, schedule_events, event_events, youtube_videos, target_date, issue_number
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
    
    def _generate_newsletter_content(self, weather_text: str, schedule_events: List[str], 
                                   event_events: List[EventInfo], youtube_videos: List[YouTubeVideo], 
                                   target_date: date, issue_number: int) -> str:
        """Jinja2テンプレートを使用してメルマガコンテンツを生成"""
        template = Template(self._get_newsletter_template())
        
        formatted_date = f"{target_date.year}年{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
        weekday = DateUtils.get_japanese_weekday_full(target_date)
        weekday_theme = DateUtils.get_weekday_theme(target_date)
        
        schedule_text = self.formatter.format_schedule_for_newsletter(schedule_events)
        event_text = self.formatter.format_events_for_newsletter(event_events)
        youtube_text = self.formatter.format_youtube_for_newsletter(youtube_videos)
        
        return template.render(
            発行日=formatted_date,
            発行No=issue_number,
            weather=weather_text,
            schedule=schedule_text,
            event=event_text,
            youtube=youtube_text,
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

4. 本日のSNS（YouTube|Instagram）投稿
-----
{{ youtube }}
-----

5. 今日の学校案内（{{ 曜日 }}曜日のテーマ：{{ 曜日テーマ }}）
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