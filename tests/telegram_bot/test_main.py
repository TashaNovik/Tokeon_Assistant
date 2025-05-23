import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from telegram.ext import Application

from telegram_bot.main import create_app, lifespan_context

def test_create_app(mock_settings):
    with patch('telegram_bot.main.configure_logging') as mock_configure_logging:
        app = create_app()
        
        mock_configure_logging.assert_called_once()
        
        assert isinstance(app, FastAPI)
        
        assert app.title == "Telegram Bot"
        assert app.description == "Telegram bot for answering user questions from a knowledge base using GPT"
        assert app.version == "1.0.0"
        
        assert callable(app.router.lifespan_context)
        
        routes = [route for route in app.routes]
        assert any(route.path == "/healthz" for route in routes)

def test_healthz_endpoint(mock_settings):
    with patch('telegram_bot.main.create_bot'):
        app = create_app()
        
        client = TestClient(app)
        response = client.get("/healthz")
        
        assert response.status_code == 200
        
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_lifespan(mock_settings):
    app = AsyncMock(spec=FastAPI)
    app.state = MagicMock()
    
    bot = AsyncMock(spec=Application)
    bot.bot = AsyncMock()
    bot.updater = AsyncMock()
    
    with patch('telegram_bot.main.create_bot', return_value=bot):
        lifespan_gen = lifespan_context(app)
        
        await lifespan_gen.__aenter__()
        
        bot.initialize.assert_awaited_once()
        bot.start.assert_awaited_once()
        bot.bot.delete_webhook.assert_awaited_once()

        assert bot.updater.start_polling.called
        
        assert app.state.bot == bot
        
        await lifespan_gen.__aexit__(None, None, None)
        
        bot.updater.stop.assert_awaited_once()
        bot.stop.assert_awaited_once()
        bot.shutdown.assert_awaited_once() 