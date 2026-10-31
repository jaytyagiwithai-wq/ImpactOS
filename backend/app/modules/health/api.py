import logging
from time import perf_counter

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.shared.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger("impactos.api")
logger.setLevel(logging.INFO)


@router.get("")
def health() -> dict[str, str]:
    settings = get_settings()
    logger.info("health.checked", extra={"app_env": settings.app_env})
    return {
        "status": "ok",
        "service": "impactos",
        "environment": settings.app_env,
    }


@router.get("/ready")
def readiness() -> dict[str, str]:
    started = perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as error:
        logger.error(
            "readiness.checked",
            extra={
                "app.outcome": "database_unavailable",
                "app.duration_ms": (perf_counter() - started) * 1000,
                "error.type": type(error).__name__,
            },
        )
        raise HTTPException(503, "Database unavailable") from None

    logger.info(
        "readiness.checked",
        extra={
            "app.outcome": "success",
            "app.duration_ms": (perf_counter() - started) * 1000,
        },
    )
    return {"status": "ready", "database": "ok"}
