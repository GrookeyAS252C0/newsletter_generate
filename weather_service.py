"""
天気予報サービス
"""

import json
import os
import re
import requests
import time
from datetime import date
from typing import List, Optional

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
    import openai
except ImportError:
    raise ImportError("openaiがインストールされていません: pip install openai")

try:
    import requests
except ImportError:
    raise ImportError("requestsがインストールされていません: pip install requests")

try:
    from langchain.output_parsers import PydanticOutputParser
    from langchain.schema import OutputParserException
except ImportError:
    raise ImportError("langchainがインストールされていません: pip install langchain")

from config import WeatherInfo
from utils import DateUtils

# ログシステム（改善版システムが利用可能な場合）
try:
    from src.utils.logging_config import logger
except ImportError:
    # フォールバック: 基本的なログ
    import logging
    logger = logging.getLogger(__name__)


class WeatherService:
    """天気予報の取得と処理を担当"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.latest_moon_age = None  # 最新の月齢数値を保存
    
    def get_moon_phase(self, target_date: date) -> str:
        """改善された月齢情報を取得（カウントダウン機能付き）"""
        try:
            # 新しい月齢計算システムを使用
            try:
                from src.utils.moon_phase_calculator import moon_calculator
                moon_info = moon_calculator.get_moon_phase_info(target_date)
                
                # 月齢数値を保存（既存システム互換）
                self.latest_moon_age = moon_info.moon_age
                
                # 拡張された表示を返す
                return moon_calculator.get_enhanced_moon_display(target_date)
                
            except ImportError:
                # フォールバック: 既存システムを使用
                logger.warning("新しい月齢システムのインポートに失敗、既存システムを使用")
                return self._get_moon_phase_fallback(target_date)
                
        except Exception as e:
            logger.error(f"月齢情報の取得でエラー: {e}", e)
            return "不明"
    
    def _get_moon_phase_fallback(self, target_date: date) -> str:
        """既存の月齢取得システム（フォールバック用）"""
        try:
            # 墨田区の緯度・経度（東京スカイツリー周辺）
            lat = 35.71
            lon = 139.81
            
            # 月齢API のURL（まぢぽん製作所）
            url = f"https://mgpn.org/api/moon/position.cgi?json&lat={lat}&lon={lon}&y={target_date.year}&m={target_date.month}&d={target_date.day}&h=12"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == 200:
                moon_age = data["result"]["age"]
                days_info = self._calculate_days_to_next_phase(moon_age)
                # 月齢数値も保存して後で使用できるようにする
                self.latest_moon_age = moon_age
                return days_info
            else:
                st.warning("月齢情報の取得に失敗しました")
                return "不明"
                
        except Exception as e:
            st.warning(f"月齢情報の取得でエラーが発生しました: {e}")
            return "不明"
    
    def get_pressure_info(self, target_date: date) -> str:
        """気象庁互換APIから気圧情報を取得"""
        try:
            # 東京のcityID（墨田区も含む東京地方）
            city_id = "130010"
            url = f"https://weather.tsukumijima.net/api/forecast?city={city_id}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # description.textから気圧情報を抽出
            description_text = data.get("description", {}).get("text", "")
            return self._extract_pressure_from_text(description_text)
            
        except Exception as e:
            st.warning(f"気圧情報の取得でエラーが発生しました: {e}")
            return "不明"
    
    def _extract_pressure_from_text(self, text: str) -> str:
        """テキストから気圧状況を抽出"""
        if not text:
            return "不明"
        
        # 気圧に関するキーワードを検索
        if "高気圧に覆われ" in text:
            if "気圧の谷" in text:
                return "高気圧圏内だが気圧の谷の影響"
            else:
                return "高気圧に覆われる"
        elif "低気圧" in text:
            return "低気圧の影響"
        elif "気圧の谷" in text:
            return "気圧の谷の影響"
        elif "気圧配置" in text:
            return "気圧配置の変化"
        elif "前線" in text:
            if "高気圧" in text:
                return "前線と高気圧の影響"
            else:
                return "前線の影響"
        else:
            return "安定した気圧"
    
    def get_moon_phase_name(self, moon_age: float) -> str:
        """月齢から月の満ち欠けの名前を取得（public method）"""
        return self._get_moon_phase_name(moon_age)
    
    def _get_moon_phase_name(self, moon_age: float) -> str:
        """月齢から月の満ち欠けの名前を取得"""
        # 月齢は0-29.5日の周期
        age = moon_age % 29.5
        
        if age < 1.85:
            return "新月"
        elif age < 7.4:
            return "三日月"
        elif age < 9.25:
            return "上弦の月"
        elif age < 13.75:
            return "十三夜"
        elif age < 16.6:
            return "満月"
        elif age < 20.05:
            return "十六夜"
        elif age < 22.1:
            return "下弦の月"
        elif age < 25.95:
            return "二十六夜"
        else:
            return "新月間近"
    
    def _calculate_days_to_next_phase(self, moon_age: float) -> str:
        """次の満月または新月までの日数を計算"""
        # 月齢は0-29.5日の周期
        age = moon_age % 29.5
        
        # 満月は約14.75日（29.5/2）
        # 新月は0日または29.5日
        
        # 新月・満月当日の判定（より厳密に）
        new_moon_threshold = 1.0  # 新月前後1日以内
        full_moon_threshold = 1.0  # 満月前後1日以内
        
        # 新月・満月との距離を計算
        new_moon_distance = min(age, 29.5 - age)
        full_moon_distance = abs(age - 14.75)
        
        # 新月当日の判定（月齢0付近または29.5付近）
        if new_moon_distance <= new_moon_threshold:
            return "今日が新月"
        
        # 満月当日の判定（月齢14.75付近）
        if full_moon_distance <= full_moon_threshold:
            return "今日が満月"
        
        # 次の新月・満月までの日数を計算
        # 新月までの日数を正確に計算
        if age <= 14.75:
            # 新月→満月の期間：次の新月は29.5日後
            days_to_new_moon = 29.5 - age
        else:
            # 満月→新月の期間：次の新月は29.5-ageで計算
            days_to_new_moon = 29.5 - age
        
        # 満月までの日数
        if age < 14.75:
            days_to_full_moon = 14.75 - age
        else:
            days_to_full_moon = 14.75 + (29.5 - age)
        
        # より近い方を選択
        if days_to_new_moon <= days_to_full_moon:
            days = int(round(days_to_new_moon))
            if days <= 0:
                return "今日が新月"
            elif days == 1:
                return "明日が新月"
            else:
                return f"新月まであと{days}日"
        else:
            days = int(round(days_to_full_moon))
            if days <= 0:
                return "今日が満月"
            elif days == 1:
                return "明日が満月"
            else:
                return f"満月まであと{days}日"
    
    def load_weather_data(self, target_date: date) -> str:
        """気象庁互換APIから天気予報データを取得"""
        try:
            st.info("🌐 気象庁互換APIから天気データを取得中...")
            
            # 東京のcityID（墨田区も含む東京地方）
            city_id = "130010"
            url = f"https://weather.tsukumijima.net/api/forecast?city={city_id}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 天気データを文章形式に変換
            weather_text = self._format_weather_api_data(data, target_date)
            
            st.success("✅ 気象庁互換APIからのデータ取得完了")
            return weather_text
            
        except Exception as e:
            st.error(f"❌ 気象庁互換APIの取得に失敗: {e}")
            return ""
    
    def get_humidity_data(self, target_date: date) -> dict:
        """Open-Meteo APIから湿度データを取得"""
        try:
            st.info("🌊 Open-Meteo APIから湿度データを取得中...")
            
            # 墨田区横網1丁目の座標（日本大学第一中学高等学校周辺）
            lat = 35.70
            lon = 139.798
            
            # 日別湿度データを取得
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=relative_humidity_2m_max,relative_humidity_2m_min&timezone=Asia%2FTokyo&forecast_days=3"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 対象日のデータを検索
            target_date_str = target_date.strftime("%Y-%m-%d")
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            hum_max = daily.get("relative_humidity_2m_max", [])
            hum_min = daily.get("relative_humidity_2m_min", [])
            
            for i, date_str in enumerate(dates):
                if date_str == target_date_str:
                    humidity_data = {
                        "date": target_date_str,
                        "humidity_max": hum_max[i] if i < len(hum_max) else None,
                        "humidity_min": hum_min[i] if i < len(hum_min) else None,
                        "source": "Open-Meteo API"
                    }
                    
                    # 平均湿度を計算
                    if humidity_data["humidity_max"] is not None and humidity_data["humidity_min"] is not None:
                        humidity_data["humidity_avg"] = (humidity_data["humidity_max"] + humidity_data["humidity_min"]) / 2
                    
                    st.success(f"✅ 湿度データ取得成功: {humidity_data['humidity_min']}% - {humidity_data['humidity_max']}%")
                    return humidity_data
            
            st.warning(f"⚠️ {target_date_str}の湿度データが見つかりません")
            return {}
            
        except Exception as e:
            st.error(f"❌ Open-Meteo API湿度データ取得失敗: {e}")
            return {}

    def get_wind_data(self, target_date: date) -> dict:
        """Open-Meteo APIから風速データを取得"""
        try:
            st.info("🌪️ Open-Meteo APIから風速データを取得中...")
            
            # 墨田区横網1丁目の座標（日本大学第一中学高等学校周辺）
            lat = 35.70
            lon = 139.798
            
            # 日別風速データを取得
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=wind_speed_10m_max,wind_direction_10m_dominant&timezone=Asia%2FTokyo&forecast_days=3"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 対象日のデータを検索
            target_date_str = target_date.strftime("%Y-%m-%d")
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            wind_speed = daily.get("wind_speed_10m_max", [])
            wind_direction = daily.get("wind_direction_10m_dominant", [])
            
            for i, date_str in enumerate(dates):
                if date_str == target_date_str:
                    wind_data = {
                        "date": target_date_str,
                        "wind_speed_max": wind_speed[i] if i < len(wind_speed) else None,
                        "wind_direction": wind_direction[i] if i < len(wind_direction) else None,
                        "source": "Open-Meteo API"
                    }
                    
                    # 風向きを方位に変換
                    if wind_data["wind_direction"] is not None:
                        wind_data["wind_direction_text"] = self._convert_degrees_to_direction(wind_data["wind_direction"])
                    
                    st.success(f"✅ 風速データ取得成功: {wind_data['wind_direction_text']}の風{wind_data['wind_speed_max']:.1f}m/s")
                    return wind_data
            
            st.warning(f"⚠️ {target_date_str}の風速データが見つかりません")
            return {}
            
        except Exception as e:
            st.error(f"❌ Open-Meteo API風速データ取得失敗: {e}")
            return {}

    def _convert_degrees_to_direction(self, degrees: float) -> str:
        """風向き（度数）を方位に変換"""
        if degrees is None:
            return "不明"
        
        directions = [
            "北", "北北東", "北東", "東北東",
            "東", "東南東", "南東", "南南東", 
            "南", "南南西", "南西", "西南西",
            "西", "西北西", "北西", "北北西"
        ]
        
        # 360度を16方位に分割（22.5度ずつ）
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]

    def get_temperature_data(self, target_date: date) -> dict:
        """Open-Meteo APIから気温データを取得"""
        try:
            st.info("🌡️ Open-Meteo APIから気温データを取得中...")
            
            # 墨田区横網1丁目の座標（日本大学第一中学高等学校周辺）
            lat = 35.70
            lon = 139.798
            
            # 日別気温データを取得
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_min,temperature_2m_max&timezone=Asia%2FTokyo&forecast_days=3"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 対象日のデータを検索
            target_date_str = target_date.strftime("%Y-%m-%d")
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            temp_min = daily.get("temperature_2m_min", [])
            temp_max = daily.get("temperature_2m_max", [])
            
            for i, date_str in enumerate(dates):
                if date_str == target_date_str:
                    temperature_data = {
                        "date": target_date_str,
                        "temperature_min": temp_min[i] if i < len(temp_min) else None,
                        "temperature_max": temp_max[i] if i < len(temp_max) else None,
                        "source": "Open-Meteo API"
                    }
                    
                    st.success(f"✅ 気温データ取得成功: 最低{temperature_data['temperature_min']}℃ 最高{temperature_data['temperature_max']}℃")
                    return temperature_data
            
            st.warning(f"⚠️ {target_date_str}の気温データが見つかりません")
            return {}
            
        except Exception as e:
            st.error(f"❌ Open-Meteo API気温データ取得失敗: {e}")
            return {}
    
    def merge_weather_data(self, weather_data: str, humidity_data: dict, wind_data: dict = None) -> str:
        """気象庁互換APIデータとOpen-Meteo湿度・風速データを統合"""
        merged_data = weather_data
        
        try:
            # 湿度情報を統合
            if humidity_data:
                humidity_section = self._format_humidity_section(humidity_data)
                
                # 【降水確率】セクションの前に【湿度】セクションを挿入
                if "【降水確率】" in merged_data:
                    parts = merged_data.split("【降水確率】")
                    merged_data = parts[0] + humidity_section + "\n\n【降水確率】" + parts[1]
                else:
                    # 【降水確率】が見つからない場合は末尾に追加
                    merged_data = merged_data + "\n\n" + humidity_section
            
            # 風速情報を統合
            if wind_data:
                wind_section = self._format_wind_section(wind_data)
                
                # 【詳細予報】セクション内の風情報を更新
                if "【詳細予報】" in merged_data and "風: 情報なし" in merged_data:
                    # 既存の「風: 情報なし」を新しい風情報に置き換え
                    wind_replacement = f"風: {wind_data.get('wind_direction_text', '不明')}の風{wind_data.get('wind_speed_max', 0):.1f}m/s (Open-Meteo)"
                    merged_data = merged_data.replace("風: 情報なし", wind_replacement)
                    st.info("✅ 風情報を Open-Meteo データで更新")
                elif "【詳細予報】" in merged_data:
                    # 詳細予報セクションに追加の風情報を挿入
                    detail_section_start = merged_data.find("【詳細予報】")
                    detail_section_end = merged_data.find("\n\n【", detail_section_start + 1)
                    if detail_section_end == -1:
                        detail_section_end = len(merged_data)
                    
                    before_detail = merged_data[:detail_section_end]
                    after_detail = merged_data[detail_section_end:]
                    merged_data = before_detail + f"\n補足風情報 (Open-Meteo): {wind_data.get('wind_direction_text', '不明')}の風{wind_data.get('wind_speed_max', 0):.1f}m/s" + after_detail
            
            if humidity_data or wind_data:
                st.info("✅ 気象データと補足データの統合完了")
            
            return merged_data
            
        except Exception as e:
            st.warning(f"データ統合中にエラー: {e}")
            return weather_data
    
    def _format_humidity_section(self, humidity_data: dict) -> str:
        """湿度データをフォーマット"""
        if not humidity_data:
            return "【湿度】\nデータなし"
        
        hum_min = humidity_data.get("humidity_min")
        hum_max = humidity_data.get("humidity_max")
        hum_avg = humidity_data.get("humidity_avg")
        source = humidity_data.get("source", "Open-Meteo API")
        
        if hum_min is not None and hum_max is not None:
            return f"【湿度】\n最小{hum_min:.0f}% - 最大{hum_max:.0f}% (平均{hum_avg:.0f}%) ※{source}"
        else:
            return "【湿度】\nデータなし"

    def _format_wind_section(self, wind_data: dict) -> str:
        """風速データをフォーマット"""
        if not wind_data or not wind_data.get('wind_speed_max'):
            return "【風速情報】\nデータなし (Open-Meteo)"
        
        wind_speed = wind_data.get('wind_speed_max', 0)
        wind_direction = wind_data.get('wind_direction_text', '不明')
        
        return f"""【風速情報 (Open-Meteo)】
最大風速: {wind_speed:.1f}m/s
主風向: {wind_direction}"""
    
    def _format_weather_api_data(self, data: dict, target_date: date) -> str:
        """気象庁互換APIのJSONデータを文章形式に変換"""
        try:
            target_date_str = target_date.strftime("%Y-%m-%d")
            
            # 対象日の予報データを検索
            target_forecast = None
            next_forecast = None
            forecasts = data.get("forecasts", [])
            
            for i, forecast in enumerate(forecasts):
                if forecast.get("date") == target_date_str:
                    target_forecast = forecast
                    # 翌日のデータも取得（気温がnullの場合の参考用）
                    if i + 1 < len(forecasts):
                        next_forecast = forecasts[i + 1]
                    break
            
            if not target_forecast:
                # 対象日が見つからない場合は最初の予報を使用
                target_forecast = forecasts[0] if forecasts else {}
                next_forecast = forecasts[1] if len(forecasts) > 1 else None
            
            # 基本情報を抽出
            publishing_office = data.get("publishingOffice", "気象庁")
            title = data.get("title", "東京都 東京 の天気")
            description_text = data.get("description", {}).get("text", "")
            
            # 予報詳細を抽出
            telop = target_forecast.get("telop", "情報なし")
            detail_weather = target_forecast.get("detail", {}).get("weather", "")
            detail_wind = target_forecast.get("detail", {}).get("wind", "")
            
            # 気温情報の処理
            temp_data = target_forecast.get("temperature", {})
            min_temp = temp_data.get("min", {}).get("celsius")
            max_temp = temp_data.get("max", {}).get("celsius")
            
            # Open-Meteoから気温データを取得（最低気温がnullの場合に備えて）
            open_meteo_temp = self.get_temperature_data(target_date)
            
            # 最高気温と最低気温を決定
            if max_temp is not None:
                final_max_temp = max_temp
                max_temp_source = "気象庁"
            elif open_meteo_temp.get("temperature_max") is not None:
                final_max_temp = round(open_meteo_temp["temperature_max"])
                max_temp_source = "Open-Meteo"
            else:
                final_max_temp = None
                max_temp_source = None
            
            if min_temp is not None:
                final_min_temp = min_temp
                min_temp_source = "気象庁"
            elif open_meteo_temp.get("temperature_min") is not None:
                final_min_temp = round(open_meteo_temp["temperature_min"])
                min_temp_source = "Open-Meteo"
            else:
                final_min_temp = None
                min_temp_source = None
            
            # 気温表示を作成
            if final_max_temp is not None and final_min_temp is not None:
                if max_temp_source == min_temp_source:
                    temp_info = f"最高気温: {final_max_temp}℃ (最低気温: {final_min_temp}℃)"
                else:
                    temp_info = f"最高気温: {final_max_temp}℃ ({max_temp_source}) (最低気温: {final_min_temp}℃ ({min_temp_source}))"
            elif final_max_temp is not None:
                temp_info = f"最高気温: {final_max_temp}℃ ({max_temp_source}) (最低気温: データなし)"
            elif final_min_temp is not None:
                temp_info = f"最高気温: データなし (最低気温: {final_min_temp}℃ ({min_temp_source}))"
            else:
                # 最後の手段として翌日データを使用
                if next_forecast:
                    next_temp = next_forecast.get("temperature", {})
                    next_min = next_temp.get("min", {}).get("celsius")
                    next_max = next_temp.get("max", {}).get("celsius")
                    if next_min is not None and next_max is not None:
                        temp_info = f"最高気温: {next_max}℃ (最低気温: {next_min}℃) ※当日データなし、翌日予報データを使用"
                    else:
                        temp_info = "気温データなし"
                else:
                    temp_info = "気温データなし"
            
            # 降水確率
            rain_chances = target_forecast.get("chanceOfRain", {})
            
            # 文章形式で結合
            formatted_text = f"""
=== {publishing_office} - {title} ===
発表日時: {data.get('publicTimeFormatted', '不明')}
対象日: {target_date.strftime('%Y年%m月%d日')} ({target_forecast.get('dateLabel', '不明')})

【天気概況】
{telop}

【詳細予報】
天気: {detail_weather if detail_weather else telop}
風: {detail_wind if detail_wind else '情報なし'}

【気温】
{temp_info}

【降水確率】
00-06時: {rain_chances.get('T00_06', '--')}
06-12時: {rain_chances.get('T06_12', '--')}
12-18時: {rain_chances.get('T12_18', '--')}
18-24時: {rain_chances.get('T18_24', '--')}

【気象解説】
{description_text}
            """.strip()
            
            return formatted_text
            
        except Exception as e:
            st.warning(f"天気データの変換中にエラー: {e}")
            return f"気象庁互換API データ (変換エラー): {str(data)[:500]}..."
    
    def extract_weather_info(self, weather_data: str, target_date: date) -> Optional[WeatherInfo]:
        """天気データから構造化された情報を抽出"""
        try:
            # 月齢情報を取得
            moon_phase = self.get_moon_phase(target_date)
            
            # 気圧情報を取得
            pressure_info = self.get_pressure_info(target_date)
            
            parser = PydanticOutputParser(pydantic_object=WeatherInfo)
            format_instructions = parser.get_format_instructions()
            
            target_date_str = f"{target_date.year}年{target_date.month}月{target_date.day}日"
            target_date_alt = f"{target_date.month}月{target_date.day}日"
            
            prompt = self._build_weather_extraction_prompt(
                weather_data, target_date_str, target_date_alt, format_instructions
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "天気予報データから必要な情報を正確に抽出し、指定されたJSON形式で出力する専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            response_text = response.choices[0].message.content.strip()
            weather_info = self._parse_weather_response(response_text, parser)
            
            # 月齢・気圧情報を追加
            if weather_info:
                weather_info.月齢 = moon_phase
                weather_info.気圧状況 = pressure_info
            
            return weather_info
            
        except Exception as e:
            st.error(f"天気情報の抽出に失敗: {e}")
            return None
    
    def generate_heartwarming_message(self, weather_info: WeatherInfo, target_date: date) -> str:
        """RAGシステムを使用して科学的根拠に基づくメッセージを生成"""
        try:
            # RAGシステムを使用してメッセージを生成
            from health_knowledge_rag import HealthKnowledgeRAG
            
            rag_system = HealthKnowledgeRAG(openai_client=self.client)
            
            # メイン: 受験生向けの健康アドバイス生成
            try:
                moon_age = getattr(self, 'latest_moon_age', None)
                student_message = rag_system.generate_student_focused_message(weather_info, moon_age)
                if student_message and len(student_message.strip()) > 10:
                    st.info("✅ 受験生向け健康アドバイス生成完了")
                    return student_message
            except Exception as e:
                st.warning(f"受験生向けメッセージ生成失敗: {e}")
            
            # フォールバック：従来のRAGメッセージ
            rag_message = rag_system.generate_evidence_based_message(weather_info, target_date)
            if rag_message and len(rag_message.strip()) > 10:
                st.info("✅ 従来RAGシステムによるメッセージ生成完了")
                return rag_message
            else:
                st.warning("RAGシステムが利用できないため、従来方式を使用")
                return self._generate_legacy_message(weather_info, target_date)
            
        except ImportError:
            st.warning("RAGシステムが利用できないため、従来方式を使用")
            return self._generate_legacy_message(weather_info, target_date)
        except Exception as e:
            st.warning(f"RAGメッセージ生成に失敗、従来方式にフォールバック: {e}")
            return self._generate_legacy_message(weather_info, target_date)
    
    def _generate_legacy_message(self, weather_info: WeatherInfo, target_date: date) -> str:
        """従来のWeb検索ベース方式でメッセージを生成（フォールバック用）"""
        try:
            formatted_date = f"{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
            weekday = DateUtils.get_japanese_weekday_full(target_date)
            
            # Web検索で得た専門知識を活用してより詳細なプロンプトを構築
            prompt = self._build_enhanced_message_generation_prompt(weather_info, formatted_date, weekday)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "学校の入試広報部として、保護者や受験生に向けて体調を気遣う温かいメッセージを書く専門家です。最新の医学的知見に基づいて、気圧・月の満ち欠けが体調に与える影響を踏まえた、科学的根拠のある体調管理アドバイスを含むメッセージを作成してください。毎回異なる視点から体調を気遣い、バリエーション豊かなメッセージを生成してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7  # 温度を上げてバリエーションを増加
            )
            
            message = response.choices[0].message.content.strip().strip('"').strip("'")
            return message
            
        except Exception as e:
            st.warning(f"従来方式のメッセージ生成に失敗しました: {e}")
            # 天気情報に基づいたフォールバックメッセージを生成
            return self._generate_fallback_message(weather_info)
    
    def _build_weather_extraction_prompt(self, weather_data: str, target_date_str: str, 
                                       target_date_alt: str, format_instructions: str) -> str:
        """天気情報抽出用のプロンプトを構築（当日優先・代替明示）"""
        return f"""
以下の気象庁互換APIの天気予報データから、{target_date_str}（{target_date_alt}）の天気情報を抽出してください。

重要な抽出ルール：
1. 当日データを最優先で使用してください
2. 当日データが取得できない場合のみ代替データを使用し、必ずその旨を明記してください
3. 推定・予想は行わず、APIから実際に取得できるデータのみを使用してください
4. データが取得できない項目は「データなし」と記載してください

抽出する情報：
1. 気温（最高気温と最低気温を「最高○℃、最低○℃」形式で）
   - 当日データ優先：実際の気温がある場合はそのまま使用
   - 当日データがnullの場合：「当日データなし（発表時刻により未発表）」と明記
   - 代替データ使用時：「当日データ取得不可のため○○日データで代替」と明記
   - 完全にデータがない場合：「データなし」

2. 湿度
   - Open-Meteo APIからの実測値がある場合：「最小○% - 最大○% (平均○%)」形式で記載
   - データがない場合：「データなし」

3. 風速（風向きと速度を「○の風○m/s」形式で）
   - 気象庁API詳細情報から実際の表記をそのまま抽出
   - 気象庁APIで「情報なし」の場合、Open-Meteoデータがあればそちらを使用し「○の風○m/s (Open-Meteo補完)」と明記
   - どちらもデータがない場合は「データなし」
   - 風速の数値が含まれない場合は表記をそのまま使用

4. 降水確率（時間帯別から午前・午後を統合）
   - 06-18時の最大値を「午前・日中」、18-06時（翌日）の最大値を「夜間」として記載
   - データがない時間帯は「--」のまま

5. 天気概況（telopフィールドから抽出）
   - APIの天気概況をそのまま使用

6. 快適具合（気温と天気から判断）
   - 実際の気温データがある場合のみ：
     - 最高気温35度以上：「厳しい暑さ」
     - 最高気温30-34度：「とても暑い」
     - 最高気温25-29度：「暑い」
     - 最高気温20-24度：「過ごしやすい」
     - 最高気温15-19度：「涼しい」
     - 最高気温15度未満：「肌寒い」
   - 気温データがない場合：天気概況から「雨で肌寒い」「曇りで涼しい」程度の表現のみ

{format_instructions}

気象庁互換API天気データ：
{weather_data}

対象日：{target_date_str}
注意：
- 当日データを最優先で使用し、取得できない場合は明確に理由を記載してください
- 推定は一切行わず、APIから取得できる実データのみを使用してください
- 代替データ使用時は必ずその旨を明記してください
- Open-Meteoから補完された風速データは「(Open-Meteo補完)」を併記してください
"""
    
    def _build_enhanced_message_generation_prompt(self, weather_info: WeatherInfo, 
                                                formatted_date: str, weekday: str) -> str:
        """Web検索で得た専門知識を活用した拡張メッセージ生成プロンプト"""
        
        # Web検索から得た専門知識を統合
        medical_knowledge = self._get_medical_knowledge_guidance(weather_info)
        variation_prompts = self._get_variation_prompts()
        
        return f"""
以下の情報をもとに、メールマガジンを読んでくれている受験生・保護者の体調を気遣う温かい丁寧語のメッセージを生成してください。

天気情報：
- 日付: {formatted_date}
- 天気: {weather_info.天気概況}
- 気温: {weather_info.気温}
- 湿度: {weather_info.湿度}
- 風速: {weather_info.風速}
- 降水確率: {weather_info.降水確率}
- 快適具合: {weather_info.快適具合}
- 月の満ち欠け: {weather_info.月齢}
- 気圧状況: {weather_info.気圧状況}

{medical_knowledge}

**メッセージ構成の必須要件：**

1. **冒頭で気圧配置と月齢を明示**
   例：「今日は高気圧に覆われ、新月の静寂な夜空となります。」
   例：「低気圧の影響で、満月まであと3日の夜空です。」
   
2. **体調への影響を説明**
   - 気圧による体調変化（頭痛、関節痛、自律神経への影響など）
   - 月齢による体調変化（水分バランス、感情の変化、体内リズムなど）
   
3. **具体的なアドバイスと労い**
   - 実践的な対処法を提案（耳マッサージ、水分補給、ストレッチなど）
   - 受験生・保護者への温かい労いの言葉

**バリエーション豊かなメッセージ作成のためのガイダンス**:
{variation_prompts}

**医学的根拠に基づく体調管理アドバイス**:
1. **気圧による影響**（2025年最新研究より）:
   - 低気圧時：自律神経の乱れ、交感神経の活発化により頭痛・関節痛が悪化
   - 気圧変化を感じる内耳の血流促進（耳マッサージ）を提案
   - 台風・前線通過時は特に注意が必要

2. **月の満ち欠けによる影響**（東洋医学・現代医学の知見）:
   - 新月時：体内浄化・解毒に適した時期、水分摂取を促進
   - 満月時：栄養・水分吸収力が最大、感情の高ぶりやすい時期
   - 月の引力による体内水分（60-70%）への自然な影響

3. **季節的要因**:
   - 春・秋：低気圧の定期的通過で症状悪化しやすい
   - 梅雨・台風時期：湿気と気圧変化のダブル影響

**重要な構成順序：**
1. 気圧配置と月齢の明示（冒頭）
2. 体調への影響の説明
3. 具体的なアドバイス
4. 温かい労いの言葉

文字数：70-100文字程度、学校らしい品格のある丁寧語でお願いします。
"""
    
    def _get_medical_knowledge_guidance(self, weather_info: WeatherInfo) -> str:
        """Web検索で得た医学的知見を統合したガイダンス"""
        knowledge = "**最新医学的知見に基づく体調影響分析**:\n"
        
        # 気圧による影響
        if "低気圧" in weather_info.気圧状況:
            knowledge += "- 低気圧により内耳の気圧センサーが反応し、自律神経が乱れやすい状態\n"
            knowledge += "- 交感神経優位により頭痛・めまい・関節痛が悪化する可能性\n"
            knowledge += "- 体内水分バランスの乱れによる不調が起きやすい\n"
        elif "高気圧" in weather_info.気圧状況:
            knowledge += "- 高気圧により大気が安定し、自律神経も比較的安定\n"
            knowledge += "- 血行が良好になり、体調も安定しやすい環境\n"
        
        # 月齢による影響
        if "新月" in weather_info.月齢:
            knowledge += "- 新月時期：体内の解毒・浄化機能が活発化\n"
            knowledge += "- デトックス効果が高まるため、水分補給が重要\n"
            knowledge += "- 新しいスタートに向けて精神的にも整いやすい時期\n"
        elif "満月" in weather_info.月齢:
            knowledge += "- 満月時期：栄養・水分の吸収力が最大になる\n"
            knowledge += "- 感情が高ぶりやすく、自律神経のバランスに注意が必要\n"
            knowledge += "- 月の引力により体内水分（60-70%）への影響が最大\n"
        else:
            knowledge += "- 月の満ち欠け周期により、体内リズムが自然と調整される時期\n"
            knowledge += "- 月齢29.5日の自然なサイクルによる体調変化\n"
        
        return knowledge
    
    def _get_variation_prompts(self) -> str:
        """バリエーション豊かなメッセージ作成のためのプロンプト"""
        import random
        
        perspectives = [
            "**今日の視点：予防的ケア**\n- 体調不良を未然に防ぐための積極的アドバイスを中心に\n- 「〜に気をつけて」「〜を心がけて」などの予防表現を使用",
            "**今日の視点：体のケア**\n- 身体的な不調への対処法を中心に\n- マッサージ、ストレッチ、水分補給などの具体的ケア方法を提案",
            "**今日の視点：心のケア**\n- 精神的な安定や リラックスを中心に\n- 気持ちの安定、ストレス解消、心の平穏などを重視した表現",
            "**今日の視点：東洋医学的アプローチ**\n- 気の流れ、自然との調和を重視\n- 月の満ち欠けとの調和、自然のリズムに合わせた生活を提案",
            "**今日の視点：現代医学的アプローチ**\n- 科学的根拠に基づいた体調管理\n- 自律神経、内耳、血流などの医学用語を適度に使用",
            "**今日の視点：季節感重視**\n- 季節の変わり目、気候変動への対応を中心に\n- その時期特有の体調変化への配慮を表現"
        ]
        
        return random.choice(perspectives)
    
    def _get_weather_specific_guidance(self, weather_info: WeatherInfo) -> str:
        """天気条件に応じた具体的なガイダンスを生成"""
        weather = weather_info.天気概況.lower()
        temp_info = weather_info.気温.lower()
        rain_prob = weather_info.降水確率.lower()
        comfort = weather_info.快適具合.lower()
        
        guidance = "天気条件に応じたメッセージガイダンス：\n"
        
        # 天気による分岐
        if "雨" in weather:
            guidance += "- 雨の日なので、傘や濡れ対策について優しく言及する\n"
            guidance += "- 室内での過ごし方や足元への気遣いを含める\n"
            guidance += "- 雨の音や雨上がりの清々しさなど、雨の良い面も触れる\n"
        elif "晴" in weather:
            guidance += "- 晴天なので、明るく爽やかな表現を使う\n"
            guidance += "- 日差しや紫外線対策について言及することもできる\n"
            guidance += "- 外での活動やお散歩に適している旨を伝える\n"
        elif "曇" in weather:
            guidance += "- 曇りなので、穏やかで落ち着いた表現を使う\n"
            guidance += "- 過ごしやすい天気であることを強調する\n"
            guidance += "- 急な天候変化への軽い注意喚起もよい\n"
        elif "雪" in weather:
            guidance += "- 雪の日なので、防寒や足元の安全について言及する\n"
            guidance += "- 雪景色の美しさや季節感を表現に含める\n"
            guidance += "- 暖かい格好での外出を促す\n"
        
        # 気温による追加ガイダンス
        if "低" in temp_info or "寒" in temp_info or "冷" in temp_info:
            guidance += "- 気温が低いので、防寒対策や温かい服装について触れる\n"
            guidance += "- 体調管理への気遣いを含める\n"
        elif "高" in temp_info or "暖" in temp_info or "暑" in temp_info:
            guidance += "- 気温が高いので、涼しく過ごす工夫や水分補給について触れる\n"
            guidance += "- 熱中症対策への軽い注意喚起もよい\n"
        
        # 降水確率による雨具への心配を追加
        if "%" in rain_prob:
            # 数値を抽出して判断
            import re
            numbers = re.findall(r'\d+', rain_prob)
            if numbers:
                prob = int(numbers[0])
                if prob >= 50:
                    guidance += "- 降水確率が高いので、雨具の準備や傘を忘れないよう心配して言及する\n"
                    guidance += "- 受験生や保護者の方が濡れないよう、雨具の心配を温かく表現する\n"
                elif prob >= 30:
                    guidance += "- 降水確率がやや高いので、念のため雨具の準備を優しく勧める\n"
        
        # 快適具合による調整
        if "不快" in comfort or "蒸し暑" in comfort:
            guidance += "- 快適でない気候なので、工夫して過ごせるよう励ます表現を使う\n"
        elif "快適" in comfort or "過ごしやすい" in comfort:
            guidance += "- 快適な気候なので、その良さを活かした表現を使う\n"
        
        guidance += "\n重要：これらのガイダンスに従って、天気の実際の状況と矛盾しないメッセージを必ず作成してください。"
        
        return guidance
    
    def _get_moon_phase_guidance(self, moon_phase: str) -> str:
        """月齢に応じたメッセージガイダンスを生成"""
        if "新月まであと" in moon_phase:
            return """- 新月に向かう時期として表現
- カウントダウンの期待感を表現
- 「新月に向けて心の準備を」「新月まで○日」などを含める
- 新しいスタートへの準備期間として表現"""
        elif "満月まであと" in moon_phase:
            return """- 満月に向かう高まりを表現
- エネルギーが蓄積される時期として表現
- 「満月に向けて充実した日々」「満月まで○日」などを含める
- 完成に向かう過程として表現"""
        elif "今日が新月" in moon_phase:
            return """- 新月の特別さを強調
- 新しい始まりの象徴として表現
- 「今日は新月」「心新たに」「新たな気持ちで」などの表現を使用"""
        elif "明日が新月" in moon_phase:
            return """- 明日の新月への準備を表現
- 新しい始まりへの心構えを示唆
- 「明日は新月」「心の準備を」などの表現を使用"""
        elif "今日が満月" in moon_phase:
            return """- 満月の特別さを強調
- 完成や充実を象徴する表現
- 「今日は満月」「満ちた光」「エネルギーに満ちた夜」などを含める"""
        elif "明日が満月" in moon_phase:
            return """- 明日の満月への期待を表現
- 完成への最終段階として表現
- 「明日は満月」「完成に向けて」などを含める"""
        else:
            return """- 月の満ち欠けのサイクルを表現
- 自然の営みの素晴らしさを含める
- 「月の美しさ」「時の流れ」などの表現を使用"""
    
    def _get_pressure_guidance(self, pressure_status: str) -> str:
        """気圧状況に応じたメッセージガイダンスを生成"""
        if "高気圧" in pressure_status:
            if "気圧の谷" in pressure_status:
                return """- 高気圧圏内だが気圧の谷の影響で不安定
- 体調の変化に注意を促す表現
- 「気圧の変化にお気をつけください」「体調管理にご注意を」などを含める"""
            else:
                return """- 高気圧で安定した気候
- 爽やかで心地よい気候として表現
- 「安定した気候」「心地よい日」「体調も安定」などの表現を使用"""
        elif "低気圧" in pressure_status:
            return """- 低気圧の影響で体調不良になりやすい
- 頭痛や関節痛への配慮を示す
- 「体調の変化にお気をつけください」「無理をなさらず」などを含める"""
        elif "気圧の谷" in pressure_status:
            return """- 気圧の変化で体調に影響が出やすい
- 敏感な方への配慮メッセージ
- 「気圧の変化を感じる方はお気をつけください」「ゆっくりお過ごしを」などを含める"""
        elif "前線" in pressure_status:
            return """- 前線の影響で天候・気圧が不安定
- 体調管理への注意喚起
- 「天候の変化に合わせて体調管理を」「お体をお大事に」などを含める"""
        else:
            return """- 安定した気圧状況
- 過ごしやすい日として表現
- 「穏やかな気候」「快適にお過ごしください」などの表現を使用"""
    
    def _generate_fallback_message(self, weather_info: WeatherInfo) -> str:
        """天気・月齢・気圧を統合したフォールバックメッセージを生成"""
        weather = weather_info.天気概況.lower()
        moon_phase = weather_info.月齢
        pressure = weather_info.気圧状況
        
        # 天気ベース
        if "雨" in weather:
            weather_part = "雨の日ですが"
        elif "晴" in weather:
            weather_part = "美しい晴天に恵まれ"
        elif "曇" in weather:
            weather_part = "落ち着いた曇り空の下"
        elif "雪" in weather:
            weather_part = "雪景色の美しい日"
        else:
            weather_part = "穏やかな一日"
        
        # 月齢部分
        if "今日が満月" in moon_phase:
            moon_part = "今夜は満月の美しい光に包まれ"
        elif "明日が満月" in moon_phase:
            moon_part = "明日の満月を楽しみに"
        elif "満月まであと" in moon_phase:
            moon_part = f"{moon_phase}の美しい夜空を見上げながら"
        elif "今日が新月" in moon_phase:
            moon_part = "新月の静寂な夜空に心を落ち着かせ"
        elif "明日が新月" in moon_phase:
            moon_part = "明日の新月に向けて心を整え"
        elif "新月まであと" in moon_phase:
            moon_part = f"{moon_phase}の夜空に思いを馳せ"
        else:
            moon_part = "美しい夜空を見上げながら"
        
        # 気圧部分
        if "低気圧" in pressure or "気圧の谷" in pressure:
            pressure_part = "気圧の変化で体調を崩しやすい時期ですが、お体をお大事にお過ごしください。"
        elif "高気圧" in pressure and "谷" not in pressure:
            pressure_part = "安定した気圧で心身ともに快適にお過ごしいただけることと存じます。"
        else:
            pressure_part = "気圧の変化にお気をつけて、ゆっくりとお過ごしください。"
        
        return f"{weather_part}、{moon_part}、{pressure_part}"
    
    def _parse_weather_response(self, response_text: str, parser: PydanticOutputParser) -> Optional[WeatherInfo]:
        """天気情報のレスポンスをパース"""
        try:
            return parser.parse(response_text)
        except OutputParserException:
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                    return WeatherInfo(**data)
                else:
                    st.error("JSON形式の応答が見つかりませんでした")
                    return None
            except json.JSONDecodeError:
                st.error("JSON解析に失敗しました")
                return None