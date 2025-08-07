"""
カスタムWebLoader - USER_AGENT警告を回避
"""

import os
import warnings
from typing import List

# USER_AGENT環境変数を確実に設定
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "Newsletter-Generator/1.0 (Educational-Purpose)"

try:
    # LangChainの警告を一時的に抑制
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="USER_AGENT environment variable not set")
        from langchain_community.document_loaders import WebBaseLoader
except ImportError:
    raise ImportError("langchainがインストールされていません: pip install langchain langchain-community")


class SafeWebLoader:
    """USER_AGENT警告を回避するWebBaseLoaderのラッパー"""
    
    @staticmethod
    def load_documents(urls: List[str]) -> List:
        """URLからドキュメントを読み込む"""
        all_documents = []
        
        for url in urls:
            try:
                # 各URLごとにWebBaseLoaderを作成
                loader = WebBaseLoader(
                    url,
                    header_template={
                        'User-Agent': os.getenv("USER_AGENT", "Newsletter-Generator/1.0 (Educational-Purpose)")
                    }
                )
                documents = loader.load()
                all_documents.extend(documents)
            except Exception as e:
                print(f"Failed to load {url}: {e}")
                continue
        
        return all_documents
    
    @staticmethod
    def load_single_document(url: str):
        """単一URLからドキュメントを読み込む"""
        try:
            loader = WebBaseLoader(
                url,
                header_template={
                    'User-Agent': os.getenv("USER_AGENT", "Newsletter-Generator/1.0 (Educational-Purpose)")
                }
            )
            return loader.load()
        except Exception as e:
            print(f"Failed to load {url}: {e}")
            return []