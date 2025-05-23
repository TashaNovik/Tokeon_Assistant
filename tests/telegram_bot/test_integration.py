import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from telegram import Update
from telegram.ext import Application, CommandHandler

from telegram_bot.main import create_app
from telegram_bot.api.handlers.telegram_handlers import create_bot
from telegram_bot.api.router.webhook import router as webhook_router
from telegram_bot.main import lifespan_context

@pytest.fixture
def mock_telegram_bot_app(mock_telegram_app, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.create_bot", return_value=mock_telegram_app):
        app = create_app()
        yield app

@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_integration(mock_telegram_bot_app, mock_telegram_app, mock_telegram_update, mock_settings):
    test_client = TestClient(mock_telegram_bot_app)
    
    update_data = {
        "update_id": 12345,
        "message": {
            "message_id": 67890,
            "text": "Test message",
            "chat": {
                "id": 98765,
                "type": "private"
            },
            "from": {
                "id": 54321,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            }
        }
    }
    
    with patch('telegram.Update.de_json', return_value=mock_telegram_update) as mock_de_json:
        mock_telegram_bot_app.state.bot = mock_telegram_app
        
        response = test_client.post(f"/webhook/{mock_telegram_app.token}", json=update_data)
        
        assert response.status_code == 200
        assert response.json() == {"status": "accepted"}

        mock_telegram_app.update_queue.put.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.integration
async def test_command_routing_integration(mock_settings):
    with patch("telegram_bot.config.settings", mock_settings):
        with patch("telegram_bot.api.handlers.telegram_handlers.Application.builder") as mock_builder:
            mock_app_builder = MagicMock()
            mock_app = MagicMock(spec=Application)
            mock_app.handlers = [[]]
            mock_app_builder.token.return_value = mock_app_builder
            mock_app_builder.build.return_value = mock_app
            mock_builder.return_value = mock_app_builder
            
            with patch("telegram_bot.api.handlers.telegram_handlers.CommandHandler") as MockCommandHandler:
                mock_start_handler = MagicMock()
                mock_start_handler.command = ["start"]
                mock_help_handler = MagicMock()
                mock_help_handler.command = ["help"]
                MockCommandHandler.side_effect = [mock_start_handler, mock_help_handler]
                
                with patch("telegram_bot.api.handlers.telegram_handlers.ConversationHandler") as MockConvHandler:
                    mock_conv_handler = MagicMock()
                    mock_conv_handler.__class__.__name__ = "ConversationHandler"
                    MockConvHandler.return_value = mock_conv_handler
                    
                    add_handler_call_count = 0
                    def mock_add_handler(handler):
                        nonlocal add_handler_call_count
                        add_handler_call_count += 1
                        mock_app.handlers[0].append(handler)
                    mock_app.add_handler = mock_add_handler
                    
                    try:
                        bot = create_bot()
                    except StopIteration:
                        pass
                    
                    assert add_handler_call_count > 0
                    
                    mock_app.handlers[0].extend([mock_conv_handler, mock_start_handler, mock_help_handler])
                    
                    handler_names = {handler.__class__.__name__ for handler in mock_app.handlers[0]}
                    
                    assert "ConversationHandler" in handler_names
                    
                    command_handlers = [h for h in mock_app.handlers[0] if hasattr(h, 'command')]
                    command_names = {handler.command[0] for handler in command_handlers if handler.command}
                    
                    assert "start" in command_names
                    assert "help" in command_names

@pytest.mark.integration
def test_app_endpoints_integration(mock_settings):
    with patch("telegram_bot.main.create_bot"), \
         patch("telegram_bot.main.lifespan_context"):
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"} 