"""
メルマガ「一日一知」生成システム - メインエントリーポイント
日本大学第一中学・高等学校向けメールマガジン自動生成アプリケーション
"""

import os
import streamlit as st

# USER_AGENT環境変数を最初に設定（LangChainの警告を回避）
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "Newsletter-Generator/1.0 (Educational-Purpose)"

# 必要なライブラリのインポートチェック
try:
    from dotenv import load_dotenv
except ImportError:
    st.error("python-dotenvがインストールされていません: pip install python-dotenv")
    st.stop()

try:
    from langchain_community.document_loaders import WebBaseLoader
    from langchain.output_parsers import PydanticOutputParser
    from langchain.schema import OutputParserException
except ImportError:
    st.error("langchainがインストールされていません: pip install langchain langchain-community")
    st.stop()

try:
    from pydantic import BaseModel, Field
except ImportError:
    st.error("pydanticがインストールされていません: pip install pydantic")
    st.stop()

try:
    import openai
except ImportError:
    st.error("openaiがインストールされていません: pip install openai")
    st.stop()

try:
    from jinja2 import Template
except ImportError:
    st.error("jinja2がインストールされていません: pip install jinja2")
    st.stop()

try:
    import pyperclip
except ImportError:
    pyperclip = None
    # pyperclipは必須ではないので警告のみ

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    st.warning("google-api-python-clientがインストールされていません: pip install google-api-python-client")
    # YouTube機能は無効化されますが、他の機能は動作します

# 自作モジュールのインポート
from ui import NewsletterUI


def main():
    """メイン関数"""
    try:
        app = NewsletterUI()
        app.run()
    except Exception as e:
        st.error(f"アプリケーションの起動に失敗しました: {e}")

if __name__ == "__main__":
    main()