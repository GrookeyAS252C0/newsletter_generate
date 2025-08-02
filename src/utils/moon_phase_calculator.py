"""
改善された月齢計算システム
満月・新月の3日前からカウントダウン表示機能付き
"""

import math
from datetime import date, datetime, timedelta
from typing import Tuple, Dict, Optional
from dataclasses import dataclass

from .logging_config import logger


@dataclass
class MoonPhaseInfo:
    """月齢情報データクラス"""
    moon_age: float
    phase_name: str
    countdown_message: Optional[str] = None
    is_special_day: bool = False  # 満月・新月当日
    days_to_next_phase: int = 0
    next_phase_type: str = ""  # "new_moon" or "full_moon"
    visual_indicator: str = ""  # 🌑🌒🌓🌔🌕🌖🌗🌘


class MoonPhaseCalculator:
    """改善された月齢計算クラス"""
    
    # 月齢の基準値
    LUNAR_CYCLE = 29.530588853  # より正確な朔望月
    NEW_MOON_AGE = 0.0
    FULL_MOON_AGE = 14.765294426  # LUNAR_CYCLE / 2
    
    # カウントダウン設定
    COUNTDOWN_DAYS = 3  # 3日前からカウントダウン
    PHASE_THRESHOLD = 1.0  # 当日判定の閾値
    
    def __init__(self):
        logger.debug("MoonPhaseCalculator を初期化")
    
    def get_moon_phase_info(self, target_date: date) -> MoonPhaseInfo:
        """指定日の詳細な月齢情報を取得"""
        try:
            # 月齢を計算
            moon_age = self._calculate_moon_age(target_date)
            
            # 基本的な月相名を取得
            phase_name = self._get_basic_phase_name(moon_age)
            
            # カウントダウン情報を計算
            countdown_info = self._calculate_countdown_info(moon_age)
            
            # 視覚的インジケーターを取得
            visual_indicator = self._get_visual_indicator(moon_age)
            
            moon_info = MoonPhaseInfo(
                moon_age=moon_age,
                phase_name=phase_name,
                countdown_message=countdown_info['message'],
                is_special_day=countdown_info['is_special_day'],
                days_to_next_phase=countdown_info['days_to_next'],
                next_phase_type=countdown_info['next_type'],
                visual_indicator=visual_indicator
            )
            
            logger.debug(f"月齢情報計算完了: {target_date} -> {moon_info}")
            return moon_info
            
        except Exception as e:
            logger.error(f"月齢情報の計算でエラー: {e}", e)
            return MoonPhaseInfo(
                moon_age=0.0,
                phase_name="不明",
                countdown_message=None,
                visual_indicator="🌑"
            )
    
    def _calculate_moon_age(self, target_date: date) -> float:
        """月齢を計算"""
        # 既知の新月日（2000年1月6日 18:14 UTC）を基準
        known_new_moon = datetime(2000, 1, 6, 18, 14)
        target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))  # 正午で計算
        
        # 経過日数を計算
        days_since_known = (target_datetime - known_new_moon).total_seconds() / (24 * 3600)
        
        # 月齢を計算（0-29.53の範囲）
        moon_age = days_since_known % self.LUNAR_CYCLE
        
        return moon_age
    
    def _get_basic_phase_name(self, moon_age: float) -> str:
        """基本的な月相名を取得"""
        # 8分割の月相
        if moon_age < 1.84566:
            return "新月"
        elif moon_age < 5.53699:
            return "三日月"
        elif moon_age < 9.22831:
            return "上弦の月"
        elif moon_age < 12.91963:
            return "十三夜月"
        elif moon_age < 16.61096:
            return "満月"
        elif moon_age < 20.30228:
            return "十六夜月"
        elif moon_age < 23.99361:
            return "下弦の月"
        elif moon_age < 27.68493:
            return "二十六夜月"
        else:
            return "晦日月"
    
    def _calculate_countdown_info(self, moon_age: float) -> Dict:
        """カウントダウン情報を計算"""
        # 新月・満月との距離を計算
        new_moon_distance = min(moon_age, self.LUNAR_CYCLE - moon_age)
        full_moon_distance = abs(moon_age - self.FULL_MOON_AGE)
        
        # 新月・満月当日の判定
        is_new_moon_today = new_moon_distance <= self.PHASE_THRESHOLD
        is_full_moon_today = full_moon_distance <= self.PHASE_THRESHOLD
        
        # 当日の場合
        if is_new_moon_today:
            return {
                'message': "🌑 今日が新月です",
                'is_special_day': True,
                'days_to_next': 0,
                'next_type': 'new_moon'
            }
        
        if is_full_moon_today:
            return {
                'message': "🌕 今日が満月です", 
                'is_special_day': True,
                'days_to_next': 0,
                'next_type': 'full_moon'
            }
        
        # 次の新月・満月までの日数を計算
        days_to_new_moon = self._calculate_days_to_new_moon(moon_age)
        days_to_full_moon = self._calculate_days_to_full_moon(moon_age)
        
        # より近い方を選択
        if days_to_new_moon <= days_to_full_moon:
            next_type = 'new_moon'
            days_to_next = days_to_new_moon
            phase_emoji = "🌑"
            phase_name = "新月"
        else:
            next_type = 'full_moon'
            days_to_next = days_to_full_moon
            phase_emoji = "🌕"
            phase_name = "満月"
        
        # カウントダウンメッセージの生成
        countdown_message = None
        if days_to_next <= self.COUNTDOWN_DAYS:
            if days_to_next == 1:
                countdown_message = f"{phase_emoji} 明日が{phase_name}です"
            elif days_to_next == 2:
                countdown_message = f"{phase_emoji} あさってが{phase_name}です"
            elif days_to_next == 3:
                countdown_message = f"{phase_emoji} {phase_name}まであと{days_to_next}日です"
        
        return {
            'message': countdown_message,
            'is_special_day': False,
            'days_to_next': days_to_next,
            'next_type': next_type
        }
    
    def _calculate_days_to_new_moon(self, moon_age: float) -> int:
        """新月までの日数を計算"""
        if moon_age == 0:
            return 0
        days = self.LUNAR_CYCLE - moon_age
        return max(0, int(round(days)))
    
    def _calculate_days_to_full_moon(self, moon_age: float) -> int:
        """満月までの日数を計算"""
        if moon_age < self.FULL_MOON_AGE:
            days = self.FULL_MOON_AGE - moon_age
        else:
            days = self.FULL_MOON_AGE + (self.LUNAR_CYCLE - moon_age)
        return max(0, int(round(days)))
    
    def _get_visual_indicator(self, moon_age: float) -> str:
        """月相の視覚的インジケーターを取得"""
        # 8段階の月相絵文字
        phase_ratio = moon_age / self.LUNAR_CYCLE
        
        if phase_ratio < 0.0625:  # 新月
            return "🌑"
        elif phase_ratio < 0.1875:  # 三日月
            return "🌒"
        elif phase_ratio < 0.3125:  # 上弦
            return "🌓"
        elif phase_ratio < 0.4375:  # 十三夜
            return "🌔"
        elif phase_ratio < 0.5625:  # 満月
            return "🌕"
        elif phase_ratio < 0.6875:  # 十六夜
            return "🌖"
        elif phase_ratio < 0.8125:  # 下弦
            return "🌗"
        else:  # 晦日
            return "🌘"
    
    def get_enhanced_moon_display(self, target_date: date) -> str:
        """拡張された月齢表示文字列を生成"""
        moon_info = self.get_moon_phase_info(target_date)
        
        # 基本表示
        base_display = f"{moon_info.visual_indicator} {moon_info.phase_name}（月齢{moon_info.moon_age:.1f}）"
        
        # カウントダウンメッセージがある場合は追加
        if moon_info.countdown_message:
            return f"{base_display} - {moon_info.countdown_message}"
        
        return base_display
    
    def get_simple_moon_display(self, target_date: date) -> str:
        """シンプルな月齢表示（既存システム互換）"""
        moon_info = self.get_moon_phase_info(target_date)
        
        if moon_info.countdown_message:
            return moon_info.countdown_message
        else:
            return f"{moon_info.phase_name}（月齢{moon_info.moon_age:.1f}）"


# グローバルインスタンス
moon_calculator = MoonPhaseCalculator()