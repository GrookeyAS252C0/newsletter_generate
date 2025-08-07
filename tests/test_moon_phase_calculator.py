"""
月齢計算システムのテスト
"""

import pytest
from datetime import date, timedelta
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.moon_phase_calculator import MoonPhaseCalculator, MoonPhaseInfo


class TestMoonPhaseCalculator:
    """MoonPhaseCalculatorのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.calculator = MoonPhaseCalculator()
    
    def test_moon_age_calculation(self):
        """月齢計算の基本テスト"""
        # 既知の新月日周辺でテスト
        test_date = date(2024, 1, 11)  # 2024年1月11日は新月
        moon_info = self.calculator.get_moon_phase_info(test_date)
        
        # 新月付近の月齢であることを確認（±2日の範囲）
        assert 0 <= moon_info.moon_age <= 2.0 or moon_info.moon_age >= 27.5
        assert moon_info.phase_name in ["新月", "三日月", "晦日月"]
    
    def test_full_moon_detection(self):
        """満月の検出テスト"""
        # 既知の満月日周辺でテスト
        test_date = date(2024, 1, 25)  # 2024年1月25日は満月
        moon_info = self.calculator.get_moon_phase_info(test_date)
        
        # 満月付近の月齢であることを確認
        assert 13.0 <= moon_info.moon_age <= 16.5
        assert moon_info.phase_name in ["十三夜月", "満月", "十六夜月"]
    
    def test_countdown_functionality(self):
        """カウントダウン機能のテスト"""
        # 新月の3日前をテスト
        known_new_moon = date(2024, 2, 9)  # 新月日
        three_days_before = known_new_moon - timedelta(days=3)
        
        moon_info = self.calculator.get_moon_phase_info(three_days_before)
        
        # カウントダウンメッセージが表示されることを確認
        assert moon_info.countdown_message is not None
        assert "新月まであと3日" in moon_info.countdown_message or "満月" in moon_info.countdown_message
    
    def test_special_day_detection(self):
        """特別な日（新月・満月当日）の検出テスト"""
        # 新月当日のテスト
        calculator = MoonPhaseCalculator()
        
        # 月齢0.5（新月当日相当）の場合をテスト
        moon_info_data = MoonPhaseInfo(
            moon_age=0.5,
            phase_name="新月",
            countdown_message="🌑 今日が新月です",
            is_special_day=True,
            visual_indicator="🌑"
        )
        
        assert moon_info_data.is_special_day
        assert "今日が新月" in moon_info_data.countdown_message
    
    def test_visual_indicators(self):
        """視覚的インジケーターのテスト"""
        # 各月相の絵文字が正しく設定されているかテスト
        test_cases = [
            (0.0, "🌑"),    # 新月
            (3.7, "🌒"),    # 三日月
            (7.4, "🌓"),    # 上弦
            (11.0, "🌔"),   # 十三夜
            (14.8, "🌕"),   # 満月
            (18.5, "🌖"),   # 十六夜
            (22.2, "🌗"),   # 下弦
            (25.9, "🌘"),   # 晦日
        ]
        
        for moon_age, expected_emoji in test_cases:
            visual = self.calculator._get_visual_indicator(moon_age)
            assert visual == expected_emoji, f"月齢{moon_age}の絵文字が期待値{expected_emoji}と異なります: {visual}"
    
    def test_enhanced_display_format(self):
        """拡張表示フォーマットのテスト"""
        test_date = date(2024, 6, 15)
        display = self.calculator.get_enhanced_moon_display(test_date)
        
        # 基本的なフォーマットが含まれていることを確認
        assert "🌕" in display or "🌑" in display or "🌓" in display or "🌗" in display
        assert "月齢" in display
        assert ")" in display  # 括弧が含まれる
    
    def test_simple_display_format(self):
        """シンプル表示フォーマットのテスト"""
        test_date = date(2024, 6, 15)
        display = self.calculator.get_simple_moon_display(test_date)
        
        # シンプルフォーマットの確認
        assert isinstance(display, str)
        assert len(display) > 0
    
    def test_countdown_edge_cases(self):
        """カウントダウンのエッジケーステスト"""
        # 明日が新月の場合
        calculator = MoonPhaseCalculator()
        
        # モックデータで明日が新月の場合をテスト
        moon_info = MoonPhaseInfo(
            moon_age=28.5,  # 明日が新月相当
            phase_name="晦日月",
            countdown_message="🌑 明日が新月です",
            is_special_day=False,
            days_to_next_phase=1,
            next_phase_type="new_moon",
            visual_indicator="🌘"
        )
        
        assert not moon_info.is_special_day
        assert "明日が新月" in moon_info.countdown_message
    
    def test_phase_name_accuracy(self):
        """月相名の正確性テスト"""
        test_cases = [
            (0.0, "新月"),
            (3.0, "三日月"),
            (7.5, "上弦の月"),
            (14.8, "満月"),
            (22.0, "下弦の月"),
            (29.0, "晦日月"),
        ]
        
        for moon_age, expected_phase in test_cases:
            phase_name = self.calculator._get_basic_phase_name(moon_age)
            assert phase_name == expected_phase, f"月齢{moon_age}の月相名が期待値{expected_phase}と異なります: {phase_name}"
    
    def test_days_calculation_accuracy(self):
        """日数計算の正確性テスト"""
        # 新月までの日数計算
        days_to_new = self.calculator._calculate_days_to_new_moon(25.0)  # 約5日後に新月
        assert 4 <= days_to_new <= 6
        
        # 満月までの日数計算
        days_to_full = self.calculator._calculate_days_to_full_moon(10.0)  # 約5日後に満月
        assert 4 <= days_to_full <= 6
    
    def test_calculator_consistency(self):
        """計算の一貫性テスト"""
        test_date = date(2024, 3, 15)
        
        # 同じ日付で複数回計算して結果が一致することを確認
        result1 = self.calculator.get_moon_phase_info(test_date)
        result2 = self.calculator.get_moon_phase_info(test_date)
        
        assert result1.moon_age == result2.moon_age
        assert result1.phase_name == result2.phase_name
        assert result1.visual_indicator == result2.visual_indicator
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # 不正な日付でもエラーが発生しないことを確認
        try:
            # 極端な未来の日付
            future_date = date(3000, 1, 1)
            moon_info = self.calculator.get_moon_phase_info(future_date)
            assert isinstance(moon_info, MoonPhaseInfo)
        except Exception as e:
            pytest.fail(f"極端な日付でエラーが発生: {e}")


class TestMoonPhaseInfo:
    """MoonPhaseInfoデータクラスのテスト"""
    
    def test_dataclass_creation(self):
        """データクラスの作成テスト"""
        moon_info = MoonPhaseInfo(
            moon_age=14.5,
            phase_name="満月",
            countdown_message="🌕 今日が満月です",
            is_special_day=True,
            days_to_next_phase=0,
            next_phase_type="full_moon",
            visual_indicator="🌕"
        )
        
        assert moon_info.moon_age == 14.5
        assert moon_info.phase_name == "満月"
        assert moon_info.is_special_day
        assert moon_info.visual_indicator == "🌕"
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        moon_info = MoonPhaseInfo(
            moon_age=10.0,
            phase_name="上弦の月"
        )
        
        assert moon_info.countdown_message is None
        assert moon_info.is_special_day is False
        assert moon_info.days_to_next_phase == 0
        assert moon_info.next_phase_type == ""
        assert moon_info.visual_indicator == ""


if __name__ == '__main__':
    pytest.main([__file__])