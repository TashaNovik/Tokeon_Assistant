import pytest
import os
import yaml
from unittest.mock import patch, mock_open

from knowledge_base_api.config import Settings, YaGPTConfig, LoggingConfig


def test_ya_gpt_config():
    config = YaGPTConfig(
        api_key="test_api_key",
        folder_id="test_folder_id",
        login="test_login",
        password="test_password"
    )
    assert config.api_key == "test_api_key"
    assert config.folder_id == "test_folder_id"
    assert config.login == "test_login"
    assert config.password == "test_password"


def test_logging_config():
    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.format == "%(asctime)s %(levelname)s %(name)s: %(message)s"
    
    config = LoggingConfig(level="DEBUG", format="%(message)s")
    assert config.level == "DEBUG"
    assert config.format == "%(message)s"


def test_settings_creation():
    ya_gpt = YaGPTConfig(
        api_key="test_api_key",
        folder_id="test_folder_id",
        login="test_login",
        password="test_password"
    )
    logging = LoggingConfig(level="DEBUG")
    
    settings = Settings(ya_gpt=ya_gpt, logging=logging)
    
    assert settings.ya_gpt.api_key == "test_api_key"
    assert settings.ya_gpt.folder_id == "test_folder_id"
    assert settings.ya_gpt.login == "test_login"
    assert settings.ya_gpt.password == "test_password"
    assert settings.logging.level == "DEBUG"
    assert settings.logging.format == "%(asctime)s %(levelname)s %(name)s: %(message)s"

def test_settings_load():
    config_data = {
        "ya_gpt": {
            "api_key": "test_api_key_from_file",
            "folder_id": "test_folder_id_from_file",
            "login": "test_login_from_file",
            "password": "test_password_from_file"
        },
        "logging": {
            "level": "DEBUG",
            "format": "custom_format"
        }
    }
    
    mock_file_content = yaml.dump(config_data)
    
    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        settings = Settings.load("dummy_path.yaml")
        
        mock_file.assert_called_once_with("dummy_path.yaml", "r")
        
        assert settings.ya_gpt.api_key == "test_api_key_from_file"
        assert settings.ya_gpt.folder_id == "test_folder_id_from_file"
        assert settings.ya_gpt.login == "test_login_from_file"
        assert settings.ya_gpt.password == "test_password_from_file"
        assert settings.logging.level == "DEBUG"
        assert settings.logging.format == "custom_format"


def test_settings_load_error():
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            Settings.load("non_existent_file.yaml") 