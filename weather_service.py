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
            return self._parse_weather_response(response_text, parser)
            
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
                    {"role": "system", "content": "学校の入試広報部として、保護者や受験生に向けて心温まる丁寧なメッセージを書く専門家です。時候の挨拶は使わず、天気に関連した具体的で温かいアドバイスを中心に書いてください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            message = response.choices[0].message.content.strip().strip('"').strip("'")
            return message
            
        except Exception as e:
            return "今日も皆様にとって素敵な一日となりますよう、心よりお祈り申し上げます。"
    
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

{format_instructions}

天気データ（複数ソース）：
{weather_data}

対象日：{target_date_str}
注意：複数のデータソースがある場合は、最も詳細で正確な情報を優先して使用してください。
"""
    
    def _build_message_generation_prompt(self, weather_info: WeatherInfo, 
                                       formatted_date: str, weekday: str) -> str:
        """メッセージ生成用のプロンプトを構築"""
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

要求事項：
1. 礼儀正しい丁寧語で書く
2. 読む人の心がほっこりするような温かみのある表現
3. 気温や降水確率に応じた具体的で優しいアドバイス
4. 学校関係者らしい品格のある文章
5. 50-80文字程度の適度な長さ
6. 毎回異なる表現や視点を使用
7. 時候の挨拶（「春の陽気」「初夏の候」など季節的な表現）は使わない
8. 天気や気温に関連した具体的なアドバイスに重点を置く

天気に合わせて、読者の方々への思いやりを込めたメッセージをお願いします。
"""
    
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