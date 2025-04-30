from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ConversationHandler, ContextTypes, MessageHandler, filters
from app.clients.ya_gpt import answer_from_knowledge_base
from app.config import settings
import logging

ASKING = 1

def create_bot() -> Application:
    """
    Create and configure the Telegram Application with command handlers.
    """
    app = Application.builder() \
        .token(settings.telegram.token) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))

    conv = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.bot.set_my_commands([
        BotCommand("start", "Welcome message"),
        BotCommand("help", "List available commands"),
        BotCommand("ask", "Begin asking a question"),
        BotCommand("cancel", "Cancel the current operation"),
    ])

    return app



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет!\n"
        "Используй `/ask`, чтобы задать вопрос."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /help — list all commands.
    """
    await update.message.reply_text(
        "/start — Welcome message\n"
        "/help  — List available commands\n"
        "/ask   — Begin the question flow\n"
        "/cancel— Cancel the current operation"
    )


async def ask_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /ask — prompt the user for their question.
    """
    await update.message.reply_text("📝 Please send me your question:")
    return ASKING


async def ask_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive the actual question and respond with GPT answer.
    """
    question = update.message.text
    try:
        answer = await answer_from_knowledge_base(question)
    except Exception as e:
        logging.error("GPT service failed", exc_info=e)
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again later."
        )
    else:
        await update.message.reply_text(answer)
    # End conversation
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /cancel — cancel the current conversation.
    """
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Fallback handler: when no command matches, just mirror the user.
    """
    await update.message.reply_text(
        "🤖 I didn’t recognize that command. "
        "Use /help to see available commands."
    )

# from data.knowledge_base import search_docs
# from app.clients.openai_client import chat_completion

