"""
設定管理のテスト
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.config_manager import EnhancedAppConfig, ConfigManager


class TestEnhancedAppConfig:
    """EnhancedAppConfigのテスト"""
    
    def test_from_env_basic(self):
        """基本的な環境変数読み込みテスト"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key',
            'YOUTUBE_API_KEY': 'test_youtube_key',
            'USER_AGENT': 'Test-Agent',
            'DEBUG_MODE': 'true',
            'CACHE_ENABLED': 'false',
            'CACHE_TTL_HOURS': '2'
        }):
            config = EnhancedAppConfig.from_env()
            
            assert config.openai_api_key == 'test_openai_key'
            assert config.youtube_api_key == 'test_youtube_key'
            assert config.user_agent == 'Test-Agent'
            assert config.debug_mode is True
            assert config.cache_enabled is False
            assert config.cache_ttl_hours == 2
    
    def test_from_env_defaults(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key'
        }, clear=True):
            config = EnhancedAppConfig.from_env()
            
            assert config.openai_api_key == 'test_key'
            assert config.youtube_api_key is None
            assert config.user_agent == "Newsletter-Generator/1.0 (Educational-Purpose)"
            assert config.debug_mode is False
            assert config.cache_enabled is True
            assert config.cache_ttl_hours == 1
    
    def test_from_env_invalid_cache_ttl(self):
        """無効なCACHE_TTL_HOURSのテスト"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'CACHE_TTL_HOURS': 'invalid'
        }):
            config = EnhancedAppConfig.from_env()
            assert config.cache_ttl_hours == 1  # デフォルト値
    
    @patch('streamlit.secrets')
    def test_from_env_streamlit_secrets(self, mock_secrets):
        """Streamlit secretsからの読み込みテスト"""
        mock_secrets.get.side_effect = lambda key, default: {
            'OPENAI_API_KEY': 'streamlit_openai_key',
            'YOUTUBE_API_KEY': 'streamlit_youtube_key'
        }.get(key, default)
        
        with patch.dict(os.environ, {}, clear=True):
            config = EnhancedAppConfig.from_env()
            
            assert config.openai_api_key == 'streamlit_openai_key'
            assert config.youtube_api_key == 'streamlit_youtube_key'
    
    def test_validate_success(self):
        """設定検証成功のテスト"""
        config = EnhancedAppConfig(
            openai_api_key='valid_api_key_123456789',
            youtube_api_key=None
        )
        assert config.validate() is True
    
    def test_validate_empty_key(self):
        """空のAPIキーのテスト"""
        config = EnhancedAppConfig(
            openai_api_key='',
            youtube_api_key=None
        )
        assert config.validate() is False
    
    def test_validate_short_key(self):
        """短すぎるAPIキーのテスト"""
        config = EnhancedAppConfig(
            openai_api_key='short',
            youtube_api_key=None
        )
        assert config.validate() is False
    
    def test_to_dict_hides_secrets(self):
        """機密情報が隠されることのテスト"""
        config = EnhancedAppConfig(
            openai_api_key='secret_key',
            youtube_api_key='secret_youtube_key'
        )
        result = config.to_dict()
        
        assert result['openai_api_key'] == '***HIDDEN***'
        assert result['youtube_api_key'] == '***HIDDEN***'
        assert result['user_agent'] == config.user_agent


class TestConfigManager:
    """ConfigManagerのテスト"""
    
    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2
    
    def test_config_caching(self):
        """設定のキャッシュテスト"""
        manager = ConfigManager()
        
        with patch.object(EnhancedAppConfig, 'from_env') as mock_from_env:
            mock_config = EnhancedAppConfig(
                openai_api_key='test_key',
                youtube_api_key=None
            )
            mock_from_env.return_value = mock_config
            
            # 最初の呼び出し
            config1 = manager.get_config()
            # 2回目の呼び出し
            config2 = manager.get_config()
            
            # 同じインスタンスが返される
            assert config1 is config2
            # from_envは一度だけ呼ばれる
            mock_from_env.assert_called_once()
    
    def test_reload_config(self):
        """設定の再読み込みテスト"""
        manager = ConfigManager()
        
        with patch.object(EnhancedAppConfig, 'from_env') as mock_from_env:
            mock_config1 = EnhancedAppConfig(
                openai_api_key='test_key1',
                youtube_api_key=None
            )
            mock_config2 = EnhancedAppConfig(
                openai_api_key='test_key2',
                youtube_api_key=None
            )
            mock_from_env.side_effect = [mock_config1, mock_config2]
            
            # 最初の読み込み
            config1 = manager.get_config()
            # 再読み込み
            config2 = manager.reload_config()
            
            # 異なるインスタンスが返される
            assert config1 is not config2
            assert config1.openai_api_key != config2.openai_api_key
            # from_envは2回呼ばれる
            assert mock_from_env.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__])