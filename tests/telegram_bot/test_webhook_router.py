import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from fastapi import HTTPException
from telegram import Update

from telegram_bot.api.router.webhook import router, telegram_webhook

@pytest.mark.asyncio
async def test_telegram_webhook_success(mock_settings):
    request = AsyncMock()
    request.app = AsyncMock()
    request.app.state = MagicMock()
    
    bot = AsyncMock()
    bot.token = "test_token"
    bot.update_queue = AsyncMock()
    request.app.state.bot = bot
    
    update_data = {"update_id": 12345, "message": {"text": "Test"}}
    request.json = AsyncMock(return_value=update_data)
    
    update_obj = MagicMock(spec=Update)
    
    with patch('telegram.Update.de_json', return_value=update_obj) as mock_de_json:
        result = await telegram_webhook("test_token", request)
        
        request.json.assert_called_once()
        
        mock_de_json.assert_called_once_with(update_data, bot.bot)
        
        bot.update_queue.put.assert_called_once_with(update_obj)
        
        assert result == {"status": "accepted"}

@pytest.mark.asyncio
async def test_telegram_webhook_invalid_token(mock_settings):
    request = AsyncMock()
    request.app = AsyncMock()
    request.app.state = MagicMock()
    
    bot = AsyncMock()
    bot.token = "correct_token"
    request.app.state.bot = bot
    
    with pytest.raises(HTTPException) as exc_info:
        await telegram_webhook("wrong_token", request)
    
    assert exc_info.value.status_code == 401
    assert "Invalid Telegram webhook token" in exc_info.value.detail 