"""
telegram_handlers.py — version using messages + ratings.message_id.

Handles Telegram bot interaction:
- /start, /help, /ask, /cancel
- inline feedback (👍😐👎)
- comment collection
- assistant API call (stub or real)
"""

from __future__ import annotations

import os
import sys
import re
import logging

sys.path.insert(0, os.path.abspath(os.getcwd()))

import httpx  # noqa: E402
from sqlalchemy import select  # noqa: E402
from telegram import (  # noqa: E402
    Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.helpers import escape_markdown  # noqa: E402
from telegram.ext import (  # noqa: E402
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters,
)

from telegram_bot.config import settings  # noqa: E402
from db.db import AsyncSessionLocal  # noqa: E402
from db.models.message import Message  # noqa: E402
from db.repository.log_repository import LogRepository  # noqa: E402
from telegram_bot.api.handlers.rating import (  # noqa: E402
    handle_rating, handle_comment, skip_comment,
)

# ───── Logging setup ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ───── Text cleaning ──────────────────────────────────────────────────────
_MAX_LEN = 1_000
_CTRL_RE = re.compile(r"[\u0000-\u001F\u007F-\u009F\u202A-\u202F]")


def clean(text: str | None) -> str:
    """Removes control characters and trims to max length."""
    return _CTRL_RE.sub("", text or "").strip()[:_MAX_LEN]


def md(text: str) -> str:
    """Escapes text for Markdown V2."""
    return escape_markdown(text, version=2)


# ───── Conversation handler state ─────────────────────────────────────────
ASKING_QUESTION = 1

# ───── Basic command handlers ─────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /start command."""
    await update.message.reply_text("👋 Привет!\nИспользуй /ask, чтобы задать вопрос.")


async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command."""
    await update.message.reply_text(
        "/start — приветствие\n"
        "/help  — справка\n"
        "/ask   — задать вопрос ассистенту\n"
        "/cancel — отменить операцию"
    )


async def cancel_conversation(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /cancel command to end current conversation."""
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END


# ───── /ask flow ──────────────────────────────────────────────────────────
async def ask_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user to enter a question."""
    await update.message.reply_text("📝 Пожалуйста, отправьте ваш вопрос:")
    return ASKING_QUESTION


async def ask_receive_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes user's question, sends it to the assistant, and asks for feedback."""
    question = clean(update.message.text)
    user = update.effective_user

    try:
        assistant_response = await ask_assistant_via_api(question)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Assistant API error: %s", exc)
        await update.message.reply_text("⚠️ Ошибка при получении ответа. Попробуйте позже.")
        return ConversationHandler.END

    if not assistant_response or not assistant_response.get("answer"):
        await update.message.reply_text("⚠️ Ассистент не смог дать ответ.")
        return ConversationHandler.END

    answer_text = assistant_response["answer"]
    await update.message.reply_text(md(answer_text), parse_mode="MarkdownV2")

    async with AsyncSessionLocal() as session:
        sess = await LogRepository.add_log_async(
            session, user.id, question, answer_text,
            username=user.username, first_name=user.first_name, last_name=user.last_name
        )
        assistant_msg_id: int | None = await session.scalar(
            select(Message.id).where(
                Message.session_id == sess.id, Message.role == "assistant"
            ).limit(1)
        )

    if assistant_msg_id is None:
        return ConversationHandler.END

    kb = [[
        InlineKeyboardButton("👍", callback_data=f"rate:{assistant_msg_id}:positive"),
        InlineKeyboardButton("😐", callback_data=f"rate:{assistant_msg_id}:neutral"),
        InlineKeyboardButton("👎", callback_data=f"rate:{assistant_msg_id}:negative"),
    ]]
    await update.message.reply_text("Оцените ответ:", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


# ───── Assistant stub for development ─────────────────────────────────────
async def ask_assistant_via_api(question: str) -> dict | None:
    """Stub for assistant API."""
    return {"answer": f"Заглушка: ответ на '{question}'.", "answer_id": "dummy"}


# ───── ORIGINAL API IMPLEMENTATION (DO NOT DELETE) ────────────────────────
# async def ask_assistant_via_api(question: str) -> dict | None:
#     base_url = os.getenv("TOKEON_ASSISTANT_REST_API_URL",
#                          "http://tokeon_assistant_rest_api:8001")
#     url = f"{base_url}/answers"
#     data = {"query": question}
#     logger.info(f"Sending question to assistant API: {url} with data: {data}")
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 url, json=data,
#                 timeout=httpx.Timeout(60, connect=10)
#             )
#         response.raise_for_status()
#         answer_data = response.json()
#         if 'answer' in answer_data and 'answer_id' in answer_data:
#             logger.info(f"Received from assistant API: {answer_data}")
#             return answer_data
#         else:
#             logger.error("Assistant API response missing keys. Got: %s", answer_data)
#             return {"answer": None, "answer_id": answer_data.get("answer_id")}
#     except httpx.HTTPStatusError as e:
#         logger.error("HTTP error from assistant API: %s - %s",
#                      e.response.status_code, e.response.text)
#         try:
#             err = e.response.json()
#             return {"answer": None, "answer_id": err.get("answer_id")}
#         except Exception:
#             pass
#         raise
#     except Exception as e:
#         logger.error("Error calling assistant API: %s", e)
#         raise


# ───── Fallback for unknown text ──────────────────────────────────────────
async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback handler when no known command matches."""
    await update.message.reply_text("🤖 Я не распознал команду. /help")


# ───── Bot application setup ──────────────────────────────────────────────
def create_bot() -> Application:
    """Initializes the bot application and all handlers."""
    token = settings.telegram_token if hasattr(settings, "telegram_token") else settings.telegram.token
    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_start)],
        states={ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_receive_question)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    app.add_handler(conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_rating, pattern=r"^rate:"))
    app.add_handler(CommandHandler("skip", skip_comment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo), group=1)

    async def _post_init(a: Application) -> None:
        await a.bot.set_my_commands([
            BotCommand("start", "Приветствие"),
            BotCommand("help", "Помощь"),
            BotCommand("ask", "Вопрос"),
            BotCommand("cancel", "Отмена"),
        ])

    app.post_init = _post_init
    return app
