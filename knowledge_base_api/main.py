import logging
from fastapi import FastAPI

from knowledge_base_api.api.router.knowledge_base_router import knowledge_base_router
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
        title="Knowledge Base API",
        description="API for managing knowledge bases",
        version="1.0.0"
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(knowledge_base_router, tags=["knowledge_base"])

    return app


app = create_app()
