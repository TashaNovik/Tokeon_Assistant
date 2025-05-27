import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram.ext import Application

from telegram_bot.api.router.webhook import router as telegram_router
from telegram_bot.api.handlers.telegram_handlers import create_bot

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

def configure_logging() -> None:
    """Sets up global logging configuration and suppresses verbose telegram logs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan: bot startup/shutdown with FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts the Telegram bot in polling mode on FastAPI startup.

    Args:
        app (FastAPI): The FastAPI app instance.

    Yields:
        None
    """
    logger.info("Starting Telegram bot in polling mode…")

    bot: Application = create_bot()
    await bot.initialize()
    await bot.start()
    await bot.bot.delete_webhook(drop_pending_updates=True)

    # Note: `Application.run_polling()` is not yet available in PTB v20+
    # This uses updater as a temporary workaround
    polling_task = asyncio.create_task(bot.updater.start_polling(poll_interval=3))

    app.state.bot = bot  # can be accessed in webhook routes if needed
    logger.info("Telegram bot started")

    try:
        yield
    finally:
        logger.info("Stopping Telegram bot polling…")
        polling_task.cancel()
        await bot.updater.stop()
        await bot.stop()
        await bot.shutdown()
        logger.info("Telegram bot stopped")


# ---------------------------------------------------------------------------
# FastAPI app factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Creates and configures a FastAPI application instance.

    Returns:
        FastAPI: Configured app with routes and Telegram bot integration.
    """
    configure_logging()

    app = FastAPI(
        title="Telegram Bot",
        description="Telegram bot for answering user questions from a knowledge base using GPT",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    app.include_router(telegram_router)

    return app


app = create_app()
