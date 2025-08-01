"""
設定とデータクラス
"""

import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

# USER_AGENT環境変数を早期に設定
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "Newsletter-Generator/1.0 (Educational-Purpose)"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("pydanticがインストールされていません: pip install pydantic")


@dataclass
class AppConfig:
    """アプリケーション設定"""
    openai_api_key: str
    youtube_api_key: Optional[str]
    user_agent: str = "Newsletter-Generator/1.0 (Educational-Purpose)"
    youtube_channel_handle: str = "nichidaiichi"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """環境変数から設定を読み込み"""
        user_agent = os.getenv("USER_AGENT", "Newsletter-Generator/1.0 (Educational-Purpose)")
        
        # Streamlit Cloudの場合はst.secretsから取得
        try:
            import streamlit as st
            openai_api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            youtube_api_key = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
        except:
            openai_api_key = os.getenv("OPENAI_API_KEY", "")
            youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        return cls(
            openai_api_key=openai_api_key,
            youtube_api_key=youtube_api_key,
            user_agent=user_agent,
        )


class WeatherInfo(BaseModel):
    """天気情報のデータ構造"""
    気温: str = Field(description="最高気温と最低気温（例：最高25度、最低18度）")
    湿度: str = Field(description="湿度の情報（例：65%）")
    風速: str = Field(description="風の情報（例：南西の風3m/s）")
    降水確率: str = Field(description="降水確率の情報（例：午前10%、午後20%）")
    天気概況: str = Field(description="天気の概況（例：晴れ時々曇り）")
    快適具合: str = Field(description="過ごしやすさの評価（例：過ごしやすい、蒸し暑い、肌寒い）")
    月齢: str = Field(description="月の満ち欠けの状態（例：新月、上弦の月、満月、下弦の月）", default="")
    気圧状況: str = Field(description="気圧の状況（例：高気圧、低気圧、気圧の谷、気圧変化なし）", default="")


@dataclass
class YouTubeVideo:
    """YouTube動画情報"""
    title: str
    url: str
    published_at: str
    thumbnail: str
    channel_title: str
    matched_query: str


@dataclass
class EventInfo:
    """イベント情報"""
    date: date
    event: str
    date_str: str