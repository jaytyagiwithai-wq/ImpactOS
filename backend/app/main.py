from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.model_registry import load_metadata
from app.modules.documents.api import router as documents_router
from app.shared.db.session import engine
from app.modules.health.api import router as health_router
from app.modules.retrieval.api import router as search_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    load_metadata()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.include_router(health_router)
    application.include_router(documents_router)
    application.include_router(search_router)
    return application


app = create_app()
