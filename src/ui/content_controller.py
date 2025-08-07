"""
メインコンテンツ表示コントローラー
"""

import streamlit as st
from datetime import date
from typing import Any, Dict, Optional

from .base_controller import BaseUIController
from ..utils.logging_config import logger
from utils import DateUtils


class ContentController(BaseUIController):
    """メインコンテンツ表示管理"""
    
    def __init__(self):
        super().__init__()

    
    def render(self):
        """抽象メソッドの実装（ダミー）"""
        pass
    
    def render_event_preview(self, publish_date: date, generator: Any):
        """イベントプレビューの表示"""
        formatted_date = f"{publish_date.year}年{publish_date.month}月{publish_date.day}日" + DateUtils.get_japanese_weekday(publish_date)
        st.info(f"📅 **メールマガジン発行日**: {formatted_date}")
        
        col_schedule, col_event, col_youtube, col_moon = st.columns([1, 1, 1, 1])
        
        with col_schedule:
            self._render_schedule_events(formatted_date, publish_date, generator)
        
        with col_event:
            self._render_promotion_events(formatted_date, publish_date, generator)
        
        with col_youtube:
            self._render_youtube_preview()
        
        with col_moon:
            self._render_moon_phase_preview(publish_date)
    
    def _render_schedule_events(self, formatted_date: str, publish_date: date, generator: Any):
        """学校行事の表示"""
        st.subheader("📅 今日の日大一")
        st.caption("行事予定カレンダーから取得 → メルマガの「2. 今日の日大一」セクションに出力")
        
        if generator:
            try:
                schedule_events = generator.event_service.get_events_for_date(publish_date)
                if schedule_events:
                    st.success(f"**{formatted_date}の行事予定** ({len(schedule_events)}件)")
                    for event in schedule_events:
                        st.markdown(f"• {event}")
                else:
                    st.info(f"**{formatted_date}**: 今日はおやすみです。")
            except Exception as e:
                self.show_error("学校行事の取得に失敗", e)
        else:
            st.info("ジェネレーターが初期化されていません")
    
    def _render_promotion_events(self, formatted_date: str, publish_date: date, generator: Any):
        """広報イベントの表示"""
        st.subheader("🎉 今後の学校説明会について")
        st.caption("広報イベントカレンダーから取得 → メルマガの「3. 今後の学校説明会について」セクションに出力")
        
        if generator:
            try:
                event_events = generator.event_service.get_events_within_month(publish_date)
                if event_events:
                    st.success(f"**{formatted_date}から1ヶ月以内のイベント** ({len(event_events)}件)")
                    for event in event_events:
                        st.markdown(f"• **{event.date_str}**: {event.event}")
                else:
                    st.info("今後1ヶ月以内に予定されているイベントはありません。")
            except Exception as e:
                self.show_error("広報イベントの取得に失敗", e)
        else:
            st.info("ジェネレーターが初期化されていません")
    
    def _render_youtube_preview(self):
        """YouTube動画プレビュー"""
        st.subheader("📹 YouTube動画")
        st.caption("YouTube APIから取得（発行日と完全一致） → メルマガの「4. YouTube動画情報」セクションに出力")
        st.info("📺 YouTube動画は「メルマガを生成」ボタンを押したときに取得されます")

    def _render_moon_phase_preview(self, publish_date: date):
        """月齢プレビューの表示"""
        st.subheader("🌙 月齢・カウントダウン情報")
        st.caption("改善された月齢計算システム → メルマガの天気セクションに統合")
        
        try:
            from ..utils.moon_phase_calculator import moon_calculator
            moon_info = moon_calculator.get_moon_phase_info(publish_date)
            
            # 基本月齢情報
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.info(f"🌙 **基本情報**\n- 月相: {moon_info.visual_indicator} {moon_info.phase_name}\n- 月齢: {moon_info.moon_age:.1f}日")
            
            with col2:
                if moon_info.is_special_day:
                    if "新月" in moon_info.countdown_message:
                        st.success(f"🌑 **{moon_info.countdown_message}**")
                    else:
                        st.success(f"🌕 **{moon_info.countdown_message}**")
                elif moon_info.countdown_message:
                    st.warning(f"⏰ **{moon_info.countdown_message}**")
                else:
                    st.info(f"📅 次の特別な日まで{moon_info.days_to_next_phase}日")
            
            # 詳細情報（エキスパンダー）
            with st.expander("🔍 月齢計算詳細", expanded=False):
                st.markdown(f"""
                **計算詳細:**
                - 朔望月周期: {moon_calculator.LUNAR_CYCLE:.6f}日
                - 新月基準: {moon_calculator.NEW_MOON_AGE}日
                - 満月基準: {moon_calculator.FULL_MOON_AGE:.6f}日
                - カウントダウン開始: {moon_calculator.COUNTDOWN_DAYS}日前
                
                **次の主要月相:**
                - 次の{moon_info.next_phase_type.replace('_', ' ')}: {moon_info.days_to_next_phase}日後
                - 視覚インジケーター: {moon_info.visual_indicator}
                """)
                
        except ImportError:
            st.warning("⚠️ 新しい月齢システムが利用できません（フォールバック使用）")
        except Exception as e:
            self.show_error("月齢プレビューの表示に失敗", e)
    
    def render_newsletter_generation(self, publish_date: date, manual_issue_number: Optional[int], generator: Any):
        """メルマガ生成と表示"""
        st.success("🚀 メルマガ生成を開始します...")
        
        with st.spinner("🌐 複数の天気予報データソースから情報を取得中..."):
            try:
                result = generator.generate_newsletter(publish_date, manual_issue_number)
                self.show_success("メルマガ生成が完了しました！")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    self._render_generation_details(result)
                
                with col2:
                    self._render_newsletter_content(result, publish_date)
                    
            except Exception as e:
                self.show_error("メルマガ生成中にエラーが発生", e)
    
    def _render_generation_details(self, result: Dict[str, Any]):
        """生成詳細情報の表示"""
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
    
    def _render_newsletter_content(self, result: Dict[str, Any], publish_date: date):
        """メルマガコンテンツの表示"""
        st.subheader("📧 メルマガプレビュー")
        
        # 生成日時を表示（日本時間）
        generated_time = DateUtils.get_now_jst()
        st.caption(f"生成日時: {generated_time.strftime('%Y年%m月%d日 %H:%M:%S')} (JST)")
        
        newsletter_content = result['content']
        st.code(newsletter_content, language="text")
        
        # ダウンロード・コピー機能
        self._render_download_options(newsletter_content, publish_date)
    
    def _render_download_options(self, newsletter_content: str, publish_date: date):
        """ダウンロードオプションの表示"""
        col_copy, col_download_txt, col_download_md = st.columns([1, 1, 1])
        
        with col_copy:
            if st.button("📋 クリップボードにコピー", help="メルマガ全体をクリップボードにコピーします"):
                try:
                    import pyperclip
                    pyperclip.copy(newsletter_content)
                    self.show_success("コピーしました！")
                except ImportError:
                    self.show_warning("pyperclipがインストールされていません。pip install pyperclip")
                except Exception as e:
                    self.show_warning(f"コピーに失敗しました: {e}")
        
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