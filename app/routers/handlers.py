# app/routers/handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes

# ----------------------------
# MODULE: Command Handlers
# DESCRIPTION:
#  - Содержит бизнес-логику для команд бота и сообщений
# ----------------------------
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /start — приветствие пользователя
    logger.info("Команда /start от user_id=%s", update.effective_user.id)
    await update.message.reply_text("🚀 Привет! Я межгалактический уничтожитель Мин.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /help — список доступных команд
    await update.message.reply_text("Команды: /start, /help")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # fallback — эхо любого текстового сообщения
#     await update.message.reply_text(f"🔊 Эхо: {update.message.text}")
    logger.debug("Fallback для user_id=%s: %s", update.effective_user.id, update.message.text)
    await update.message.reply_text(
        "Привет. Я маленький космокораблик, пока ещё учусь отвечать на ваши вопросы. "
        "Скоро вернусь к вам с ответами! Ждите вестей!"
    )
# EXTENSION POINT:
#  - Здесь коллеги могут добавить новые хендлеры (commands, callbacks, inline)
