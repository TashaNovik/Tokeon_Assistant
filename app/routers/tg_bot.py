# app/routers/tg_bot.py

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.config import TELEGRAM_TOKEN
from app.routers.handlers import start, help_command, echo

# ----------------------------
# MODULE: Telegram Application Factory
# DESCRIPTION:
#  - Конфигурирует и создаёт объект Application
#  - Регистрирует хендлеры команд и сообщений
# ----------------------------
def create_bot():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .concurrent_updates(True)  # параллельная обработка апдейтов
        .build()
    )

    # CORE COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # FALLBACK: обработка любых текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # EXTENSION POINTS:
    #  - здесь можно добавить CallbackQueryHandler, InlineQueryHandler и др.
    return app
