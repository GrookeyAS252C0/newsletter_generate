"""
ユーティリティ関数
"""

from datetime import date, timedelta
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
        """発行No.を計算（2025年4月3日を基準とし、土日は発行しない）"""
        base_date = date(2025, 4, 3)  # 基準日（木曜日）
        
        if target_date < base_date:
            return 1  # 基準日より前の場合は1号とする
        
        # 基準日から対象日までの平日（月-金）をカウント
        current_date = base_date
        issue_count = 1  # 基準日を1号とする
        
        while current_date < target_date:
            current_date += timedelta(days=1)
            # 月曜日(0)から金曜日(4)のみカウント
            if current_date.weekday() < 5:  # 0-6 (月-日)
                issue_count += 1
        
        return issue_count
    
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