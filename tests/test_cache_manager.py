"""
キャッシュ管理のテスト
"""

import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.cache_manager import CacheManager, cache_api_response


class TestCacheManager:
    """CacheManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_set_and_get(self):
        """キャッシュの保存と取得のテスト"""
        test_data = {'key': 'value', 'number': 123}
        cache_key = 'test_key'
        
        # データを保存
        self.cache_manager.set(cache_key, test_data)
        
        # データを取得
        result = self.cache_manager.get(cache_key)
        
        assert result == test_data
    
    def test_cache_get_nonexistent(self):
        """存在しないキャッシュの取得テスト"""
        result = self.cache_manager.get('nonexistent_key')
        assert result is None
    
    def test_cache_expiry(self):
        """キャッシュの有効期限テスト"""
        test_data = {'test': 'data'}
        cache_key = 'expiry_test'
        
        # データを保存
        self.cache_manager.set(cache_key, test_data)
        
        # キャッシュファイルの時刻を古い時刻に変更
        cache_file = self.cache_manager._get_cache_file_path(cache_key)
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # 2時間前の時刻に変更
        old_time = datetime.now() - timedelta(hours=2)
        cache_data['timestamp'] = old_time.isoformat()
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # 1時間以内のキャッシュを要求（期限切れのため None が返される）
        result = self.cache_manager.get(cache_key, max_age_hours=1)
        assert result is None
        
        # ファイルが削除されていることを確認
        assert not os.path.exists(cache_file)
    
    def test_cache_key_generation(self):
        """キャッシュキー生成のテスト"""
        key1 = self.cache_manager._get_cache_key('test', 'arg1', 'arg2', param1='value1')
        key2 = self.cache_manager._get_cache_key('test', 'arg1', 'arg2', param1='value1')
        key3 = self.cache_manager._get_cache_key('test', 'arg1', 'arg3', param1='value1')
        
        # 同じ引数なら同じキー
        assert key1 == key2
        # 異なる引数なら異なるキー
        assert key1 != key3
    
    def test_clear_old_cache(self):
        """古いキャッシュのクリーンアップテスト"""
        # 新しいキャッシュを作成
        new_data = {'type': 'new'}
        self.cache_manager.set('new_cache', new_data)
        
        # 古いキャッシュを作成（手動で古い時刻に設定）
        old_data = {'type': 'old'}
        self.cache_manager.set('old_cache', old_data)
        
        cache_file = self.cache_manager._get_cache_file_path('old_cache')
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # 8日前の時刻に変更
        old_time = datetime.now() - timedelta(days=8)
        cache_data['timestamp'] = old_time.isoformat()
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # 古いキャッシュをクリーンアップ（7日=168時間）
        self.cache_manager.clear_old_cache(max_age_hours=168)
        
        # 新しいキャッシュは残っている
        assert self.cache_manager.get('new_cache') == new_data
        
        # 古いキャッシュは削除されている
        assert self.cache_manager.get('old_cache') is None
    
    def test_cache_error_handling(self):
        """キャッシュエラーハンドリングのテスト"""
        # 無効なJSONファイルを作成
        invalid_cache_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_cache_file, 'w') as f:
            f.write('invalid json content')
        
        # エラーが発生してもNoneが返される
        result = self.cache_manager.get('invalid')
        assert result is None


class TestCacheDecorator:
    """キャッシュデコレータのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_manager = None
        
        # グローバルのcache_managerを一時的に置き換え
        import src.utils.cache_manager as cache_module
        self.original_cache_manager = cache_module.cache_manager
        cache_module.cache_manager = CacheManager(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        shutil.rmtree(self.temp_dir)
        
        # グローバルのcache_managerを元に戻す
        if self.original_cache_manager:
            import src.utils.cache_manager as cache_module
            cache_module.cache_manager = self.original_cache_manager
    
    def test_cache_api_response_decorator(self):
        """APIレスポンスキャッシュデコレータのテスト"""
        call_count = 0
        
        @cache_api_response('test_api', max_age_hours=1)
        def mock_api_call(param1, param2):
            nonlocal call_count
            call_count += 1
            return {'result': f'{param1}_{param2}', 'call_count': call_count}
        
        # 最初の呼び出し
        result1 = mock_api_call('a', 'b')
        assert result1['result'] == 'a_b'
        assert result1['call_count'] == 1
        assert call_count == 1
        
        # 2回目の呼び出し（キャッシュから取得）
        result2 = mock_api_call('a', 'b')
        assert result2['result'] == 'a_b'
        assert result2['call_count'] == 1  # キャッシュから取得なので同じ
        assert call_count == 1  # 実際の関数は呼ばれない
        
        # 異なる引数での呼び出し
        result3 = mock_api_call('c', 'd')
        assert result3['result'] == 'c_d'
        assert result3['call_count'] == 2
        assert call_count == 2
    
    def test_cache_api_response_none_result(self):
        """API呼び出しでNoneが返された場合のテスト"""
        call_count = 0
        
        @cache_api_response('test_api_none', max_age_hours=1)
        def mock_api_call_none():
            nonlocal call_count
            call_count += 1
            return None
        
        # Noneが返される場合は毎回API呼び出しが実行される
        result1 = mock_api_call_none()
        assert result1 is None
        assert call_count == 1
        
        result2 = mock_api_call_none()
        assert result2 is None
        assert call_count == 2  # キャッシュされない


if __name__ == '__main__':
    pytest.main([__file__])