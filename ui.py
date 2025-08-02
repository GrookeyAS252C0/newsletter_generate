"""
Streamlit UI管理（Google Calendar対応版）
"""

import os
import time
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple

import streamlit as st
import pandas as pd

try:
    import pyperclip
except ImportError:
    pyperclip = None

# デバッグモード
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def debug_print(message):
    """デバッグ用出力"""
    if DEBUG_MODE:
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[UI DEBUG {timestamp}] {message}")

debug_print("ui.pyの読み込み開始")

try:
    from config import AppConfig, YouTubeVideo
    debug_print("config モジュール インポート成功")
except ImportError as e:
    debug_print(f"config モジュール インポート失敗: {e}")
    raise

try:
    from newsletter_generator import NewsletterGenerator
    debug_print("newsletter_generator モジュール インポート成功")
except ImportError as e:
    debug_print(f"newsletter_generator モジュール インポート失敗: {e}")
    raise

try:
    from utils import DateUtils
    debug_print("utils モジュール インポート成功")
except ImportError as e:
    debug_print(f"utils モジュール インポート失敗: {e}")
    raise

debug_print("ui.pyの読み込み完了")


class NewsletterUI:
    """Streamlit UIを管理（Google Calendar対応版）"""
    
    def __init__(self):
        debug_print("NewsletterUI.__init__() 開始")
        try:
            debug_print("AppConfig.from_env() 実行中...")
            self.config = AppConfig.from_env()
            debug_print("AppConfig.from_env() 完了")
            
            if self.config.openai_api_key:
                debug_print("OpenAI APIキーが設定されています")
                # Google Calendar設定は後で初期化
                self.generator = None
                self.calendar_config = None
                
            else:
                debug_print("OpenAI APIキーが未設定")
                self.generator = None
            
            # 学校テーマ追跡機能を初期化
            self._initialize_theme_tracker()
                
        except Exception as e:
            debug_print(f"NewsletterUI.__init__() でエラー: {e}")
            raise
        
        debug_print("NewsletterUI.__init__() 完了")
    
    def _initialize_theme_tracker(self):
        """学校テーマ追跡機能を初期化"""
        # 学校テーマ追跡機能は削除済み
    
    def run(self):
        """メインのUI処理"""
        debug_print("NewsletterUI.run() 開始")
        
        try:
            debug_print("_setup_page() 実行中...")
            self._setup_page()
            debug_print("_setup_page() 完了")
            
            debug_print("_validate_config() 実行中...")
            self._validate_config()
            debug_print("_validate_config() 完了")
            
            if not self.config.openai_api_key:
                debug_print("OpenAI APIキーが未設定のため終了")
                return
            
            debug_print("_setup_sidebar() 実行中...")
            # サイドバー設定（Google Calendar設定を含む）
            publish_date, manual_issue_number, generate_button, self.calendar_config = self._setup_sidebar()
            debug_print("_setup_sidebar() 完了")
            
            # NewsletterGeneratorを初期化（Google Calendar設定を含む）
            if not self.generator or self.calendar_config != getattr(self, '_last_calendar_config', None):
                debug_print("NewsletterGenerator 初期化中...")
                self.generator = NewsletterGenerator(self.config, self.calendar_config)
                self._last_calendar_config = self.calendar_config.copy()
                debug_print("NewsletterGenerator 初期化完了")
            
            debug_print("_display_event_preview() 実行中...")
            # メインコンテンツ
            self._display_event_preview(publish_date)
            debug_print("_display_event_preview() 完了")
            
            # メルマガ生成処理（サイドバーのボタンが押された時のみ）
            if generate_button:
                debug_print("generate_button が押されました")
                self._generate_and_display_newsletter(publish_date, manual_issue_number)
            else:
                debug_print("generate_button は押されていません")
                
        except Exception as e:
            debug_print(f"NewsletterUI.run() でエラー: {e}")
            st.error(f"UI実行中にエラーが発生しました: {e}")
            import traceback
            st.error(f"詳細エラー: {traceback.format_exc()}")
            raise
        
        debug_print("NewsletterUI.run() 完了")
    
    def _setup_page(self):
        """ページ設定"""
        st.set_page_config(
            page_title="メルマガ「一日一知」生成",
            page_icon="📧",
            layout="wide"
        )
        
        st.title("📧 メルマガ「一日一知」生成")
        st.markdown("指定した発行日の天気予報と行事・イベント情報をメールマガジン用の文章として生成します。")
    
    def _validate_config(self):
        """設定の検証"""
        if not self.config.openai_api_key:
            st.error("❌ OpenAI APIキーが設定されていません")
            st.markdown("""
            **設定方法:**
            1. プロジェクトルートに `.env` ファイルを作成
            2. 以下の内容を記載:
            ```
            OPENAI_API_KEY=your_api_key_here
            ```
            """)
            return
        
    
    def _setup_sidebar(self) -> Tuple[date, Optional[int], bool, dict]:
        """サイドバーの設定（Google Calendar設定を含む）"""
        st.sidebar.header("⚙️ メルマガ設定")
        
        # 発行日の選択
        st.sidebar.subheader("📅 発行日設定")
        # 日本時間で今日の日付を取得
        today = DateUtils.get_today_jst()
        publish_date = st.sidebar.date_input(
            "メールマガジン発行日",
            value=today,
            help="天気予報を取得したい日付を選択してください"
        )
        
        formatted_date = f"{publish_date.year}年{publish_date.month}月{publish_date.day}日" + DateUtils.get_japanese_weekday(publish_date)
        st.sidebar.success(f"📆 発行日: {formatted_date}")
        
        # 発行No.設定
        st.sidebar.subheader("📄 発行No.設定")
        auto_issue_number = DateUtils.get_issue_number(publish_date)
        
        # 日曜日の場合の警告表示
        if publish_date.weekday() == 6:  # 日曜日(6)
            st.sidebar.warning(f"⚠️ 日曜日は通常発行しません")
        
        use_manual_issue_number = st.sidebar.checkbox(
            "発行No.を手動設定",
            value=publish_date.weekday() == 6,  # 日曜日の場合はデフォルトで手動設定ON
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
        
        # Google Calendar設定
        calendar_config = self._setup_calendar_settings()
        
        # 天気予報設定
        st.sidebar.subheader("🌐 天気予報設定")
        st.sidebar.info(f"📍 対象地域: 墨田区（東京地方）")
        
        # データ取得優先度
        st.sidebar.markdown("**🎯 データ取得優先度**")
        st.sidebar.info("📅 当日データを最優先で取得")
        st.sidebar.info("⚠️ 当日データが取得不可時は翌日データで代替・明示")
        
        # データソース
        st.sidebar.markdown("**📊 データソース（気象庁互換API）**")
        st.sidebar.code("https://weather.tsukumijima.net/api/forecast?city=130010", language="text")
        
        st.sidebar.success("✅ 気象币互換APIから公式データを取得")
        
        st.sidebar.success("✅ OpenAI APIキーが設定されています")
        
        # 学校テーマ網羅性表示は削除済み
        
        # 生成ボタンをサイドバーの最下部に配置
        st.sidebar.markdown("---")
        st.sidebar.subheader("🚀 メルマガ生成")
        
        generate_button = st.sidebar.button(
            "🔄 メルマガを生成", 
            type="primary",
            use_container_width=True,
            help="設定した内容でメルマガを生成します"
        )
        
        return publish_date, manual_issue_number, generate_button, calendar_config
    
    # [カレンダー設定の関数は先ほど作成したものをここに挿入]
    def _setup_calendar_settings(self) -> dict:
        """Google Calendarの設定画面をサイドバーに追加"""
        st.sidebar.subheader("📅 Google Calendar設定")
        
        # Google Calendar使用の有効/無効
        use_google_calendar = st.sidebar.checkbox(
            "Google Calendarを使用",
            value=True,
            help="Google Calendarからイベント情報を取得します"
        )
        
        calendar_config = {
            'use_google_calendar': use_google_calendar,
            'schedule_calendar_ids': ['nichidai1.haishin@gmail.com'],
            'event_calendar_ids': ['c38f50b10481248d05113108d0ba210e7edd5d60abe152ce319c595f011cb814@group.calendar.google.com'],
            'event_keywords': ['説明会', '見学会', 'オープンキャンパス', '体験会', '相談会', '入試', '文化祭', '学園祭', 'オープンスクール', '櫻墨祭'],
            'credentials_path': 'credentials.json',
            'token_path': 'token.json'
        }
        
        if use_google_calendar:
            st.sidebar.success("✅ Google Calendar機能が有効です")
            st.sidebar.info("📅 学校行事: nichidai1.haishin@gmail.com")
            st.sidebar.info("🎉 広報行事: c38f...cb814@group.calendar.google.com")
        else:
            st.sidebar.info("📄 CSVファイルベースのイベント取得を使用します")
        
        return calendar_config
    
    # 学校テーマ追跡機能は削除済み
    
    # [残りのメソッドは元のui.pyと同じ]
    def _display_event_preview(self, publish_date: date):
        """イベントプレビューの表示"""
        formatted_date = f"{publish_date.year}年{publish_date.month}月{publish_date.day}日" + DateUtils.get_japanese_weekday(publish_date)
        st.info(f"📅 **メールマガジン発行日**: {formatted_date}")
        
        col_schedule, col_event, col_youtube = st.columns([1, 1, 1])
        
        with col_schedule:
            st.subheader("📅 今日の日大一")
            st.caption("行事予定カレンダーから取得 → メルマガの「2. 今日の日大一」セクションに出力")
            
            if self.generator:
                schedule_events = self.generator.event_service.get_events_for_date(publish_date)
                if schedule_events:
                    st.success(f"**{formatted_date}の行事予定** ({len(schedule_events)}件)")
                    for event in schedule_events:
                        st.markdown(f"• {event}")
                else:
                    st.info(f"**{formatted_date}**: 今日はおやすみです。")
            else:
                st.info("ジェネレーターが初期化されていません")
        
        with col_event:
            st.subheader("🎉 今後の学校説明会について")
            st.caption("広報イベントカレンダーから取得 → メルマガの「3. 今後の学校説明会について」セクションに出力")
            
            if self.generator:
                event_events = self.generator.event_service.get_events_within_month(publish_date)
                if event_events:
                    st.success(f"**{formatted_date}から1ヶ月以内のイベント** ({len(event_events)}件)")
                    for event in event_events:
                        st.markdown(f"• **{event.date_str}**: {event.event}")
                else:
                    st.info("今後1ヶ月以内に予定されているイベントはありません。")
            else:
                st.info("ジェネレーターが初期化されていません")
        
        with col_youtube:
            st.subheader("📹 YouTube動画")
            st.caption("YouTube APIから取得（発行日と完全一致） → メルマガの「4. YouTube動画情報」セクションに出力")
            
            st.info("📺 YouTube動画は「メルマガを生成」ボタンを押したときに取得されます")
    
    
    def _generate_and_display_newsletter(self, publish_date: date, manual_issue_number: Optional[int]):
        """メルマガ生成と表示"""
        # 生成処理の開始を明確に表示
        st.success("🚀 メルマガ生成を開始します...")
        
        with st.spinner("🌐 複数の天気予報データソースから情報を取得中..."):
            try:
                result = self.generator.generate_newsletter(publish_date, manual_issue_number)
                
                # 生成完了メッセージ
                st.success("✅ メルマガ生成が完了しました！")
                
                # 学校テーマ履歴機能は削除済み
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    self._display_generation_details(result)
                
                with col2:
                    self._display_newsletter_content(result, publish_date)
                    
            except Exception as e:
                st.error(f"❌ メルマガ生成中にエラーが発生しました: {e}")
                import traceback
                st.error(f"詳細エラー: {traceback.format_exc()}")
    
    
    def _display_generation_details(self, result: Dict[str, Any]):
        """生成詳細の表示"""
        st.subheader("📄 生成詳細情報")
        
        metadata = result['metadata']
        st.info(f"📊 生成統計: {metadata['character_count']:,} 文字")
        
        # 天気情報JSON表示
        if result['weather_info']:
            st.markdown("### 📊 抽出された天気データ（JSON）")
            weather_dict = {
                "気温": result['weather_info'].気温,
                "湿度": result['weather_info'].湿度,
                "風速": result['weather_info'].風速,
                "降水確率": result['weather_info'].降水確率,
                "天気概況": result['weather_info'].天気概況,
                "快適具合": result['weather_info'].快適具合,
                "月齢": result['weather_info'].月齢,
                "気圧状況": result['weather_info'].気圧状況
            }
            st.json(weather_dict)
        
        # 詳細情報のエキスパンダー
        with st.expander("🔍 詳細情報", expanded=False):
            st.markdown("#### 天気情報（文章）")
            st.markdown(result['weather_text'] or "天気情報の取得に失敗しました")
            
            # YouTube動画情報を追加
            if 'youtube_videos' in result and result['youtube_videos']:
                st.markdown("#### YouTube動画情報")
                for video in result['youtube_videos'][:3]:
                    st.markdown(f"- [{video.title}]({video.url})")
            
            st.markdown("#### 発行情報")
            issue_status = "手動設定" if metadata['is_manual_issue_number'] else "自動計算"
            st.markdown(f"""
            - **発行日**: {metadata['formatted_date']}
            - **発行No.**: {metadata['issue_number']} ({issue_status})
            - **曜日**: {metadata['weekday']}曜日
            - **文字数**: {metadata['character_count']:,} 文字
            """)
    
    def _display_newsletter_content(self, result: Dict[str, Any], publish_date: date):
        """メルマガコンテンツの表示"""
        st.subheader("📧 メルマガプレビュー")
        
        # 生成日時を表示（日本時間）
        generated_time = DateUtils.get_now_jst()
        st.caption(f"生成日時: {generated_time.strftime('%Y年%m月%d日 %H:%M:%S')} (JST)")
        
        newsletter_content = result['content']
        st.code(newsletter_content, language="text")
        
        # ダウンロード・コピー機能
        self._display_download_options(newsletter_content, publish_date)
    
    def _display_download_options(self, newsletter_content: str, publish_date: date):
        """ダウンロードオプションの表示"""
        col_copy, col_download_txt, col_download_md = st.columns([1, 1, 1])
        
        with col_copy:
            if st.button("📋 クリップボードにコピー", help="メルマガ全体をクリップボードにコピーします"):
                if pyperclip:
                    try:
                        pyperclip.copy(newsletter_content)
                        st.success("✅ コピーしました！")
                    except Exception as e:
                        st.warning(f"⚠️ コピーに失敗しました: {e}")
                else:
                    st.warning("⚠️ pyperclipがインストールされていません。pip install pyperclip")
        
        with col_download_txt:
            filename_txt = f"newsletter_{publish_date.strftime('%Y%m%d')}.txt"
            st.download_button(
                label="💾 TXTダウンロード",
                data=newsletter_content,
                file_name=filename_txt,
                mime="text/plain"
            )
        
        with col_download_md:
            filename_md = f"newsletter_{publish_date.strftime('%Y%m%d')}.md"
            st.download_button(
                label="📝 MDダウンロード",
                data=newsletter_content,
                file_name=filename_md,
                mime="text/markdown"
            )