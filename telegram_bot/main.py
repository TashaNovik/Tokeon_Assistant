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
    """Manage application lifecycle: start and stop Telegram bot.

    On startup, initializes and starts the Telegram bot in polling mode.
    On shutdown, stops and cleans up the Telegram bot.

    Args:
        app: FastAPI application instance.
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

    yield

    logger.info("Stopping Telegram bot polling...")
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    logger.info("Telegram bot stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance.

    Configures logging, sets up application metadata, lifespan handler,
    health check endpoint, and includes the Telegram router.

    Returns:
        Configured FastAPI application.
    """
    configure_logging()

    app = FastAPI(
        title="Telegram Bot",
        description="Telegram bot for answering user questions from a knowledge base using GPT",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        """Health check endpoint.

                Returns:
                    Dictionary with status key indicating app health.
        """
        return {"status": "ok"}

    app.include_router(telegram_router)

    return app


app = create_app()
