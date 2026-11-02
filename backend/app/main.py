from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.model_registry import load_metadata
from app.modules.documents.api import router as documents_router
from app.shared.db.session import engine
from app.modules.health.api import router as health_router
from app.modules.retrieval.api import router as search_router
from app.modules.retrieval.reranking import get_reranker

from app.modules.answering.api import router as answers_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_reranker()
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
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:4178"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],

    )
    application.include_router(health_router)
    application.include_router(documents_router)
    application.include_router(search_router)
    application.include_router(answers_router)
    return application


app = create_app()
