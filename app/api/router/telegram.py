from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from app.config import settings

def create_bot() -> Application:
    """
    Create and configure the Telegram Application with command handlers.
    """
    app = Application.builder() \
        .token(settings.telegram.token) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask_gpt))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.bot.set_my_commands([
        BotCommand("start", "Welcome message"),
        BotCommand("help", "List available commands"),
        BotCommand("ask", "Ask a question to the GPT-powered KB")
    ])

    return app



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет!\n"
        "Используй `/ask`, чтобы задать вопрос."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /help — list all available commands.
    """
    help_text = (
        "/start — Welcome message\n"
        "/help  — This help text\n"
        "/ask   — Ask a question to the knowledge base"
    )
    await update.message.reply_text(help_text)


async def ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /ask <your question> — take the trailing text as a query,
    search the KB, call GPT and return the answer.
    """
    user_question = " ".join(context.args)
    if not user_question:
        return await update.message.reply_text("❗️ Please provide a question after /ask.")
    # 1) Search your knowledge base
    # docs = search_docs(user_question)
    # # 2) Build and call GPT
    # prompt = f"Context:\n{docs}\n\nQuestion: {user_question}"
    # answer = await chat_completion(prompt)
    # 3) Send the answer back
    await update.message.reply_text("answer")


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

