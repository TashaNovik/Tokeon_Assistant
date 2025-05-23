import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open

from telegram_bot.config import TelegramConfig, LoggingConfig, Settings

def test_telegram_config():
    config = TelegramConfig(token="test_token", webhook_path="/webhook")
    assert config.token == "test_token"
    assert config.webhook_path == "/webhook"

def test_logging_config():
    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.format == "%(asctime)s %(levelname)s %(name)s: %(message)s"
    
    config = LoggingConfig(level="DEBUG", format="%(message)s")
    assert config.level == "DEBUG"
    assert config.format == "%(message)s"

def test_settings_creation():
    telegram = TelegramConfig(token="test_token", webhook_path="/webhook")
    logging = LoggingConfig(level="DEBUG")
    
    settings = Settings(telegram=telegram, logging=logging)
    
    assert settings.telegram.token == "test_token"
    assert settings.telegram.webhook_path == "/webhook"
    assert settings.logging.level == "DEBUG"
    assert settings.logging.format == "%(asctime)s %(levelname)s %(name)s: %(message)s"


def test_settings_load():
    config_data = {
        "telegram": {
            "token": "test_token_from_file",
            "webhook_path": "/webhook_from_file"
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
        
        assert settings.telegram.token == "test_token_from_file"
        assert settings.telegram.webhook_path == "/webhook_from_file"
        assert settings.logging.level == "DEBUG"
        assert settings.logging.format == "custom_format"

def test_settings_load_error():
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            Settings.load("non_existent_file.yaml") 