import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram.ext import Application

from telegram_bot.api.router.webhook import router as telegram_router
from telegram_bot.api.handlers.telegram_handlers import create_bot

logger = logging.getLogger(__name__)

def configure_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle:
      - Start the Telegram bot in polling mode on startup
      - Stop the Telegram bot cleanly on shutdown
    """
    logger.info("Starting Telegram bot in polling mode...")
    bot: Application = create_bot()
    await bot.initialize()
    await bot.start()
    await bot.bot.delete_webhook()
    # Commands are set in create_bot() via post_init
    asyncio.create_task(bot.updater.start_polling(poll_interval=3))
    app.state.bot = bot
    logger.info("Telegram bot started")

    yield  # Application is now ready to serve requests

    logger.info("Stopping Telegram bot polling...")
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    logger.info("Telegram bot stopped")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI app."""
    configure_logging()

    app = FastAPI(
        title="Telegram Bot",
        description="Telegram bot for answering user questions from a knowledge base using GPT",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    app.include_router(telegram_router)

    return app


app = create_app()
