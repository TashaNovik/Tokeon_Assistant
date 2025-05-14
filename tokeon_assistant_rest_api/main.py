import logging
from fastapi import FastAPI

from tokeon_assistant_rest_api.api.router.assistant_router import assistant_router
import logging

logger = logging.getLogger(__name__)

def configure_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI app."""
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
