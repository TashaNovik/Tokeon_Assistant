import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

import yaml
from fastapi import FastAPI
from telegram import Update, User, Message, Chat, CallbackQuery
from telegram.ext import ContextTypes, Application


@pytest.fixture
def mock_settings():
    settings_data = {
        "telegram": {
            "token": "test_bot_token",
            "webhook_path": "/test_webhook_path"
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(message)s"
        }
    }
    
    with patch("telegram_bot.config.Settings.load") as mock_load:
        from telegram_bot.config import Settings, TelegramConfig, LoggingConfig
        
        telegram_config = TelegramConfig(**settings_data["telegram"])
        logging_config = LoggingConfig(**settings_data["logging"])
        settings = Settings(telegram=telegram_config, logging=logging_config)
        
        mock_load.return_value = settings
        yield settings

@pytest.fixture
def mock_telegram_update():
    update = MagicMock(spec=Update)
    
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.message_id = 12345
    
    chat = MagicMock(spec=Chat)
    chat.id = 67890
    chat.type = "private"
    message.chat = chat
    
    user = MagicMock(spec=User)
    user.id = 54321
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    message.from_user = user
    
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "feedback:answer_id:positive"
    callback_query.message = MagicMock(spec=Message)
    callback_query.message.chat = chat
    callback_query.message.message_id = 98765
    
    update.message = message
    update.callback_query = callback_query
    
    return update

@pytest.fixture
def mock_telegram_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.edit_message_reply_markup = AsyncMock()
    
    return context

@pytest.fixture
def mock_fastapi_app():
    app = MagicMock(spec=FastAPI)
    app.state = MagicMock()
    return app

@pytest.fixture
def mock_telegram_app():
    app = MagicMock(spec=Application)
    app.token = "test_bot_token"
    app.bot = MagicMock()
    app.update_queue = AsyncMock()
    app.updater = AsyncMock()
    
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()
    
    return app 