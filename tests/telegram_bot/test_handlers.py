import pytest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, User, Message, Chat
from telegram.ext import ConversationHandler, ContextTypes

from telegram_bot.api.handlers.telegram_handlers import (
    start, help_command, ask_start, ask_receive_question, 
    feedback_button_callback, cancel_conversation, echo,
    ASKING_QUESTION, AWAITING_FEEDBACK_CHOICE, AWAITING_FEEDBACK_COMMENT
)

@pytest.fixture
def mock_update():
    update = AsyncMock(spec=Update)
    
    update.message = AsyncMock()
    update.message.text = "Test message"
    update.message.chat_id = 12345
    update.message.message_id = 1
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.type = "private"
    update.message.chat.id = 12345
    
    update.message.from_user = AsyncMock(spec=User)
    update.message.from_user.id = 12345
    update.message.from_user.username = "testuser"
    update.message.from_user.first_name = "Test"
    update.message.from_user.last_name = "User"
    
    update.callback_query = AsyncMock()
    update.callback_query.data = "feedback:12345:positive"
    update.callback_query.message = AsyncMock(spec=Message)
    update.callback_query.message.message_id = 2
    update.callback_query.message.chat_id = 12345
    
    return update

@pytest.fixture
def mock_context():
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    return context

@pytest.mark.asyncio
async def test_start(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "Привет" in args[0]

@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        await help_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "/ask" in args[0]

@pytest.mark.asyncio
async def test_ask_start(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        result = await ask_start(mock_update, mock_context)
        assert result == ASKING_QUESTION
        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "вопрос" in args[0]

@pytest.mark.asyncio
@patch("telegram_bot.api.handlers.telegram_handlers.ask_assistant_via_api")
async def test_ask_receive_question_success(mock_ask_api, mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        answer_id = "test_answer_id"
        mock_ask_api.return_value = {
            "answer": "Это тестовый ответ ассистента",
            "answer_id": answer_id
        }

        result = await ask_receive_question(mock_update, mock_context)
        assert result == AWAITING_FEEDBACK_COMMENT

        mock_ask_api.assert_called_once_with(mock_update.message.text)
        
        assert mock_update.message.reply_text.call_count >= 2

        assert mock_context.user_data.get('current_answer_id') == answer_id

@pytest.mark.asyncio
@patch("telegram_bot.api.handlers.telegram_handlers.ask_assistant_via_api")
async def test_ask_receive_question_api_error(mock_ask_api, mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        mock_ask_api.side_effect = Exception("API Error")
        
        result = await ask_receive_question(mock_update, mock_context)
        assert result == ConversationHandler.END

        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "ошибка" in args[0].lower()

@pytest.mark.asyncio
async def test_feedback_button_callback(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        mock_update.callback_query.data = "feedback:test_answer_id:positive"
        mock_context.user_data = {
            'current_answer_id': 'test_answer_id',
            'feedback_message_id_to_edit': 123
        }

        result = await feedback_button_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()

        mock_context.bot.edit_message_text.assert_called_once()

        assert result == AWAITING_FEEDBACK_COMMENT
        
        assert mock_context.user_data.get('current_answer_id') == 'test_answer_id'
        assert mock_context.user_data.get('current_reaction_for_feedback') == 'positive'

@pytest.mark.asyncio
async def test_cancel_conversation(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        result = await cancel_conversation(mock_update, mock_context)
        assert result == ConversationHandler.END
        
        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "отменен" in args[0].lower()

@pytest.mark.asyncio
async def test_echo(mock_update, mock_context, mock_settings):
    with patch("telegram_bot.api.handlers.telegram_handlers.settings", mock_settings):
        await echo(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once() 