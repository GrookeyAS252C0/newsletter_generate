"""
天気予報サービス
"""

import json
import os
import re
import time
import warnings
from datetime import date
from typing import List, Optional

# USER_AGENT環境変数を確実に設定
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "Newsletter-Generator/1.0 (Educational-Purpose)"

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
    # LangChainの警告を抑制してインポート
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="USER_AGENT environment variable not set")
        from langchain_community.document_loaders import WebBaseLoader
        from langchain.output_parsers import PydanticOutputParser
        from langchain.schema import OutputParserException
except ImportError:
    raise ImportError("langchainがインストールされていません: pip install langchain langchain-community")

from config import WeatherInfo
from utils import DateUtils


class WeatherService:
    """天気予報の取得と処理を担当"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
    
    def get_moon_phase(self, target_date: date) -> str:
        """月齢情報を取得して月の状態を返す"""
        try:
            # 墨田区の緯度・経度（東京スカイツリー周辺）
            lat = 35.71
            lon = 139.81
            
            # 月齢APIのURL（まぢぽん製作所）
            url = f"https://mgpn.org/api/moon/position.cgi?json&lat={lat}&lon={lon}&y={target_date.year}&m={target_date.month}&d={target_date.day}&h=12"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == 200:
                moon_age = data["result"]["age"]
                return self._get_moon_phase_name(moon_age)
            else:
                st.warning("月齢情報の取得に失敗しました")
                return "不明"
                
        except Exception as e:
            st.warning(f"月齢情報の取得でエラーが発生しました: {e}")
            return "不明"
    
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
    
    def load_weather_data(self, urls: List[str]) -> str:
        """複数の天気予報サイトからデータを取得して統合"""
        combined_content = ""
        
        for i, url in enumerate(urls, 1):
            try:
                st.info(f"🌐 データソース{i}を取得中: {url}")
                
                # 警告を抑制してWebBaseLoaderを作成
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="USER_AGENT environment variable not set")
                    loader = WebBaseLoader(
                        url,
                        header_template={
                            'User-Agent': os.getenv("USER_AGENT", "Newsletter-Generator/1.0 (Educational-Purpose)")
                        }
                    )
                    documents = loader.load()
                
                if documents:
                    content = documents[0].page_content
                    content = re.sub(r'\n+', '\n', content)
                    content = re.sub(r'\s+', ' ', content)
                    combined_content += f"\n\n=== データソース{i} ({url}) ===\n{content.strip()}"
                    st.success(f"✅ データソース{i}の取得完了")
                else:
                    st.warning(f"⚠️ データソース{i}でデータが見つかりませんでした")
                    
                # リクエスト間隔を空ける
                if i < len(urls):
                    time.sleep(1)
                    
            except Exception as e:
                st.error(f"❌ データソース{i}の取得に失敗: {e}")
                continue
        
        if combined_content:
            st.success(f"📊 合計{len(urls)}個のデータソースから情報を統合しました")
            return combined_content.strip()
        else:
            st.error("すべてのデータソースの取得に失敗しました")
            return ""
    
    def extract_weather_info(self, weather_data: str, target_date: date) -> Optional[WeatherInfo]:
        """天気データから構造化された情報を抽出"""
        try:
            # 月齢情報を取得
            moon_phase = self.get_moon_phase(target_date)
            
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
            
            # 月齢情報を追加
            if weather_info:
                weather_info.月齢 = moon_phase
            
            return weather_info
            
        except Exception as e:
            st.error(f"天気情報の抽出に失敗: {e}")
            return None
    
    def generate_heartwarming_message(self, weather_info: WeatherInfo, target_date: date) -> str:
        """心温まる丁寧語のメッセージを生成"""
        try:
            formatted_date = f"{target_date.month}月{target_date.day}日" + DateUtils.get_japanese_weekday(target_date)
            weekday = DateUtils.get_japanese_weekday_full(target_date)
            
            prompt = self._build_message_generation_prompt(weather_info, formatted_date, weekday)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "学校の入試広報部として、保護者や受験生に向けて心温まる丁寧なメッセージを書く専門家です。必ず天気情報と完全に一致する内容のメッセージを書いてください。天気の状況を無視したり、矛盾する内容は絶対に書かないでください。晴れの日に雨の話をしたり、暑い日に寒さの話をしたりしてはいけません。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.4
            )
            
            message = response.choices[0].message.content.strip().strip('"').strip("'")
            return message
            
        except Exception as e:
            st.warning(f"心温まるメッセージの生成に失敗しました: {e}")
            # 天気情報に基づいたフォールバックメッセージを生成
            return self._generate_fallback_message(weather_info)
    
    def _build_weather_extraction_prompt(self, weather_data: str, target_date_str: str, 
                                       target_date_alt: str, format_instructions: str) -> str:
        """天気情報抽出用のプロンプトを構築"""
        return f"""
以下の複数の墨田区の天気予報データから、{target_date_str}（{target_date_alt}）の天気情報を抽出してください。

複数のデータソースから最も正確で詳細な情報を選択して抽出してください。
特に最低気温・最高気温の情報は正確性を重視してください。

抽出する情報：
1. 気温（最高気温と最低気温）
2. 湿度
3. 風速（風向きと速度）
4. 降水確率（午前・午後別）
5. 天気概況（晴れ、曇り、雨など）
6. 快適具合（気温と湿度から判断した過ごしやすさ）
   基本的な気温基準：
   - 最高気温33度以上：「とても暑い」
   - 最高気温28-32度：「暑い」
   - 最高気温20-27度：「過ごしやすい」
   - 最高気温10-19度：「肌寒い」または「涼しい」
   - 最高気温10度未満：「寒い」
   
   調整要因：
   - 湿度80%以上：より不快に感じる（「蒸し暑い」「じめじめ」など）
   - 雨や雪：体感温度が下がる傾向
   - 風速：風が強い場合は体感温度に影響
   これらの要因を総合的に判断して、適切な快適度を決定してください。

{format_instructions}

天気データ（複数ソース）：
{weather_data}

対象日：{target_date_str}
注意：複数のデータソースがある場合は、最も詳細で正確な情報を優先して使用してください。
"""
    
    def _build_message_generation_prompt(self, weather_info: WeatherInfo, 
                                       formatted_date: str, weekday: str) -> str:
        """メッセージ生成用のプロンプトを構築"""
        
        # 天気に応じた具体的なガイダンスを生成
        weather_guidance = self._get_weather_specific_guidance(weather_info)
        
        return f"""
以下の天気情報をもとに、学校のメールマガジン読者（保護者や受験生）に向けた心温まる丁寧語のメッセージを生成してください。

天気情報：
- 日付: {formatted_date}
- 天気: {weather_info.天気概況}
- 気温: {weather_info.気温}
- 湿度: {weather_info.湿度}
- 風速: {weather_info.風速}
- 降水確率: {weather_info.降水確率}
- 快適具合: {weather_info.快適具合}
- 月の満ち欠け: {weather_info.月齢}

{weather_guidance}

月齢に応じたメッセージガイダンス：
{self._get_moon_phase_guidance(weather_info.月齢)}

要求事項：
1. 必ず上記の天気条件ガイダンスに従って、天気の状況に合ったメッセージを書く
2. 礼儀正しい丁寧語で書く
3. 読む人の心がほっこりするような温かみのある表現
4. 学校関係者らしい品格のある文章
5. 50-80文字程度の適度な長さ
6. 時候の挨拶（「春の陽気」「初夏の候」など季節的な表現）は使わない
7. 天気とまったく関係のない内容は書かない
8. 天気情報に矛盾しない内容にする

必ず天気の状況を正確に反映したメッセージを作成してください。
"""
    
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
        
        # 降水確率による追加ガイダンス
        if "高" in rain_prob or "%" in rain_prob:
            # 数値を抽出して判断
            import re
            numbers = re.findall(r'\d+', rain_prob)
            if numbers:
                prob = int(numbers[0])
                if prob >= 60:
                    guidance += "- 降水確率が高いので、傘の準備について言及する\n"
                elif prob >= 30:
                    guidance += "- 降水確率がやや高いので、念のため傘の準備を勧める\n"
        
        # 快適具合による調整
        if "不快" in comfort or "蒸し暑" in comfort:
            guidance += "- 快適でない気候なので、工夫して過ごせるよう励ます表現を使う\n"
        elif "快適" in comfort or "過ごしやすい" in comfort:
            guidance += "- 快適な気候なので、その良さを活かした表現を使う\n"
        
        guidance += "\n重要：これらのガイダンスに従って、天気の実際の状況と矛盾しないメッセージを必ず作成してください。"
        
        return guidance
    
    def _get_moon_phase_guidance(self, moon_phase: str) -> str:
        """月齢に応じたメッセージガイダンスを生成"""
        if moon_phase == "新月":
            return """- 新月は新しい始まりの象徴。受験勉強の新たなスタートや目標設定について触れる
- 静寂で集中に適した夜として表現する
- 「心新たに」「新たな気持ちで」などの表現を使用"""
        elif moon_phase == "三日月":
            return """- 成長の兆しとして表現する
- 希望や未来への期待を込めた表現を使用
- 「少しずつ成長」「前進」などのキーワードを含める"""
        elif moon_phase == "上弦の月":
            return """- 努力が実を結ぶ時期として表現
- バランスの取れた状態を示唆
- 「着実な歩み」「努力の成果」などを含める"""
        elif moon_phase == "十三夜":
            return """- 日本の美意識「十三夜」に触れる
- 秋の美しさや情緒を表現（季節に応じて）
- 「美しい月夜」「風情ある夜」などの表現"""
        elif moon_phase == "満月":
            return """- 完成や充実を象徴する表現
- エネルギーに満ちた夜として描写
- 「満ちた光」「豊かな時間」「完成に向けて」などを含める"""
        elif moon_phase == "十六夜":
            return """- 「いざよい」の美しい響きを活用
- 少し遅れて昇る月の趣を表現
- 「ゆったりとした時の流れ」「趣のある夜」などを含める"""
        elif moon_phase == "下弦の月":
            return """- 振り返りと準備の時期として表現
- 次のステップへの準備期間を示唆
- 「これまでの歩みを振り返り」「次への準備」などを含める"""
        elif moon_phase == "二十六夜":
            return """- 待つことの美学を表現
- 夜明け前の静寂な美しさ
- 「静かな時間」「待つことの大切さ」などを含める"""
        elif moon_phase == "新月間近":
            return """- 新たなサイクルへの準備期間
- リセットと再生の時期として表現
- 「新しいスタートに向けて」「心の準備」などを含める"""
        else:
            return """- 月の美しさや夜空の魅力を一般的に表現
- 自然の営みの素晴らしさを含める
- 「美しい夜空」「自然の恵み」などの表現を使用"""
    
    def _generate_fallback_message(self, weather_info: WeatherInfo) -> str:
        """天気情報に基づいたフォールバックメッセージを生成"""
        weather = weather_info.天気概況.lower()
        moon_phase = weather_info.月齢
        
        base_message = ""
        if "雨" in weather:
            base_message = "雨の日ですが、心穏やかにお過ごしいただけますよう願っております。足元にお気をつけください。"
        elif "晴" in weather:
            base_message = "美しい晴天に恵まれ、清々しい一日をお過ごしいただけることと存じます。"
        elif "曇" in weather:
            base_message = "落ち着いた曇り空の下、穏やかな一日をお過ごしください。"
        elif "雪" in weather:
            base_message = "雪の降る日となりました。暖かくしてお過ごしいただき、足元にお気をつけください。"
        else:
            base_message = "今日も皆様にとって素敵な一日となりますよう、心よりお祈り申し上げます。"
        
        # 月齢に応じた追加メッセージ
        if moon_phase == "満月":
            return f"{base_message} 今夜は満月の美しい光をお楽しみください。"
        elif moon_phase == "新月":
            return f"{base_message} 新月の静寂な夜、心新たにお過ごしください。"
        elif "三日月" in moon_phase:
            return f"{base_message} 美しい三日月の夜空をご覧ください。"
        else:
            return base_message
    
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