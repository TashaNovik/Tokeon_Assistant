import logging
from fastapi import FastAPI

from tokeon_assistant_rest_api.api.router.assistant_router import assistant_router
import logging

logger = logging.getLogger(__name__)

def configure_logging() -> None:
    """
    Configure logging settings for the application.

    Sets the logging level to INFO and defines the log message format.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    Configures logging, initializes the FastAPI app with metadata,
    adds a health check endpoint, and includes the assistant router.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    configure_logging()

    app = FastAPI(
        title="Tokeon Assistant REST API",
        description="REST API for answering user questions from a knowledge base using GPT",
        version="1.0.0"
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(assistant_router)

    return app


app = create_app()
