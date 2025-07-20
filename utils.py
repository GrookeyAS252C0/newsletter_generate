"""
ユーティリティ関数
"""

from datetime import date, datetime, timedelta, timezone
from typing import List


class DateUtils:
    """日付関連のユーティリティ"""
    
    @staticmethod
    def get_japanese_weekday_full(date_obj: date) -> str:
        """日付から日本語の曜日（フル）を取得"""
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        return weekdays[date_obj.weekday()]
    
    @staticmethod
    def get_japanese_weekday(date_obj: date) -> str:
        """日付から日本語の曜日（括弧付き）を取得"""
        weekdays = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
        return weekdays[date_obj.weekday()]
    
    @staticmethod
    def get_issue_number(target_date: date) -> int:
        """発行No.を計算（2025年4月3日を基準とし、日曜日は発行しない）"""
        base_date = date(2025, 4, 3)  # 基準日（木曜日）
        
        if target_date < base_date:
            return 1  # 基準日より前の場合は1号とする
        
        # 対象日が日曜日の場合、直前の土曜日の号数を返す
        if target_date.weekday() == 6:  # 日曜日(6)
            # 直前の土曜日を探す
            last_saturday = target_date - timedelta(days=1)
            target_date = last_saturday
        
        # 基準日から対象日までの日曜日以外をカウント
        current_date = base_date
        issue_count = 1  # 基準日を1号とする
        
        while current_date < target_date:
            current_date += timedelta(days=1)
            # 日曜日(6)以外をカウント
            if current_date.weekday() != 6:  # 0-6 (月-日)
                issue_count += 1
        
        return issue_count
    
    @staticmethod
    def get_today_jst() -> date:
        """日本時間（JST）で今日の日付を取得"""
        jst = timezone(timedelta(hours=9))
        return datetime.now(jst).date()
    
    @staticmethod
    def get_now_jst() -> datetime:
        """日本時間（JST）で現在の日時を取得"""
        jst = timezone(timedelta(hours=9))
        return datetime.now(jst)
    
    @staticmethod
    def get_weekday_theme(date_obj: date) -> str:
        """曜日に応じたテーマを取得"""
        themes = {
            0: "日大一の地理情報",    # 月曜日
            1: "日大一の6年間",       # 火曜日
            2: "日大一の進路",        # 水曜日
            3: "日大一の学校行事",    # 木曜日
            4: "日大一の入試",        # 金曜日
            5: "日大一ストーリー",    # 土曜日
            6: ""                     # 日曜日（発行しない）
        }
        return themes.get(date_obj.weekday(), "")
    
    @staticmethod
    def get_date_formats(target_date: date) -> List[str]:
        """複数の日付形式を生成"""
        # Pythonの%-dは一部の環境で動作しないため、手動で変換
        year = target_date.year
        month = target_date.month
        day = target_date.day
        
        return [
            target_date.strftime("%Y年%m月%d日"),   # 2025年05月25日
            target_date.strftime("%Y/%m/%d"),        # 2025/05/25
            target_date.strftime("%Y-%m-%d"),        # 2025-05-25
            target_date.strftime("%Y\\%m/%d"),       # 2025\05/25
            f"{year}年{month}月{day}日",             # 2025年5月25日
            f"{year}\\{month:02d}/{day:02d}",       # 2025\05/25 (with zero padding)
            f"{year}\\{month}/{day}",                # 2025\5/25 (without zero padding)
            target_date.strftime("%m月%d日"),        # 05月25日
            f"{month}月{day}日",                     # 5月25日
            target_date.strftime("%m/%d"),           # 05/25
            f"{month}/{day}",                        # 5/25
            target_date.strftime("%m-%d"),           # 05-25
        ]