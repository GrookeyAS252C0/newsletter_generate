"""
メルマガ「一日一知」生成システム - 改善版メインエントリーポイント
日本大学第一中学・高等学校向けメールマガジン自動生成アプリケーション

改善点:
- UIコントローラーの分割
- 統一ログシステム
- APIキャッシュ機能
- エラーハンドリングの改善
"""

import os
import sys

# USER_AGENT環境変数を最初に設定（LangChainの警告を回避）
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "Newsletter-Generator/1.0 (Educational-Purpose)"

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 必要なライブラリのインポートチェック
def check_dependencies():
    """依存関係の確認"""
    missing_packages = []
    
    try:
        from dotenv import load_dotenv
        load_dotenv()  # .envファイルを読み込み
    except ImportError:
        missing_packages.append("python-dotenv")
    
    try:
        import streamlit as st
    except ImportError:
        missing_packages.append("streamlit")
    
    # オプション機能：LangChain
    try:
        from langchain_community.document_loaders import WebBaseLoader
        from langchain.output_parsers import PydanticOutputParser
        from langchain.schema import OutputParserException
    except ImportError:
        pass  # LangChainは高度な機能用なのでオプション
    
    # オプション機能：Pydantic
    try:
        from pydantic import BaseModel, Field
    except ImportError:
        pass  # Pydanticは高度な機能用なのでオプション
    
    try:
        import openai
    except ImportError:
        missing_packages.append("openai")
    
    try:
        from jinja2 import Template
    except ImportError:
        missing_packages.append("jinja2")
    
    if missing_packages:
        import streamlit as st
        st.error("以下のパッケージがインストールされていません:")
        for pkg in missing_packages:
            st.error(f"pip install {pkg}")
        st.stop()
    
    # オプションパッケージの確認
    try:
        import pyperclip
    except ImportError:
        # pyperclipは必須ではないので警告のみ
        pass
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        import streamlit as st
        st.warning("google-api-python-clientがインストールされていません: pip install google-api-python-client")
        # YouTube機能は無効化されますが、他の機能は動作します


def main():
    """メイン関数"""
    # 依存関係チェック
    check_dependencies()
    
    try:
        # 改善されたUIコントローラーをインポート
        from src.ui.main_controller import MainUIController
        from src.utils.logging_config import logger
        
        logger.info("=== メルマガ生成システム（改善版）開始 ===")
        
        # メインコントローラー実行
        controller = MainUIController()
        controller.run()
        
        logger.info("=== メルマガ生成システム（改善版）正常終了 ===")
        
    except Exception as e:
        import streamlit as st
        st.error(f"❌ アプリケーションの起動に失敗しました: {e}")
        
        # デバッグモードの場合は詳細エラーを表示
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            import traceback
            st.error(f"詳細エラー: {traceback.format_exc()}")


if __name__ == "__main__":
    main()