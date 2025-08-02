"""
APIキャッシュ機能とStreamlitキャッシュの統合管理
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import streamlit as st
import hashlib

from .logging_config import logger


class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """キャッシュディレクトリの作成"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """キャッシュキーの生成"""
        key_data = f"{prefix}_{str(args)}_{str(kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """キャッシュファイルパスの取得"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, cache_key: str, max_age_hours: int = 24) -> Optional[Any]:
        """キャッシュからデータを取得"""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 有効期限チェック
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=max_age_hours):
                os.remove(cache_file)
                return None
            
            logger.debug(f"キャッシュヒット: {cache_key}")
            return cache_data['data']
            
        except Exception as e:
            logger.warning(f"キャッシュ読み込みエラー: {e}")
            return None
    
    def set(self, cache_key: str, data: Any):
        """データをキャッシュに保存"""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"キャッシュ保存: {cache_key}")
            
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")
    
    def clear_old_cache(self, max_age_hours: int = 168):  # 1週間
        """古いキャッシュを削除"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        cached_time = datetime.fromisoformat(cache_data['timestamp'])
                        if cached_time < cutoff_time:
                            os.remove(filepath)
                            logger.debug(f"古いキャッシュを削除: {filename}")
                    
                    except Exception:
                        # 破損したキャッシュファイルは削除
                        os.remove(filepath)
            
        except Exception as e:
            logger.warning(f"キャッシュクリーンアップエラー: {e}")


# グローバルキャッシュマネージャー
cache_manager = CacheManager()


# Streamlitキャッシュデコレータ
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def cached_json_load(file_path: str) -> Dict[str, Any]:
    """JSONファイル読み込みのキャッシュ"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"JSONファイル読み込みエラー: {file_path}", e)
        return {}


@st.cache_data(ttl=1800)  # 30分キャッシュ
def cached_weather_api_call(api_url: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """天気APIコールのキャッシュ"""
    import requests
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"天気API呼び出しエラー: {api_url}", e)
        return None


def cache_api_response(cache_key_prefix: str, max_age_hours: int = 1):
    """API応答キャッシュデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = cache_manager._get_cache_key(cache_key_prefix, *args, **kwargs)
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get(cache_key, max_age_hours)
            if cached_result is not None:
                return cached_result
            
            # API呼び出し実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            if result is not None:
                cache_manager.set(cache_key, result)
            
            return result
        return wrapper
    return decorator