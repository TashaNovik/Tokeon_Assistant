import os
import tempfile
import yaml
import pytest
from tokeon_assistant_rest_api.config import Settings, YaGPTConfig, LoggingConfig

def test_settings_load_from_default():
    settings = Settings.load()
    assert isinstance(settings, Settings)
    assert isinstance(settings.ya_gpt, YaGPTConfig)
    assert isinstance(settings.logging, LoggingConfig)
    assert settings.ya_gpt.api_key
    assert settings.ya_gpt.folder_id
    assert settings.ya_gpt.login
    assert settings.ya_gpt.password

def test_settings_load_from_custom_path():
    config_data = {
        'ya_gpt': {
            'api_key': 'test_key',
            'folder_id': 'test_folder',
            'login': 'test_login',
            'password': 'test_pass',
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(message)s',
        }
    }
    with tempfile.NamedTemporaryFile('w+', delete=False) as tmp:
        yaml.dump(config_data, tmp)
        tmp_path = tmp.name
    try:
        settings = Settings.load(tmp_path)
        assert settings.ya_gpt.api_key == 'test_key'
        assert settings.logging.level == 'DEBUG'
    finally:
        os.unlink(tmp_path)

def test_settings_load_file_not_found():
    with pytest.raises(FileNotFoundError):
        Settings.load('nonexistent.yaml') 