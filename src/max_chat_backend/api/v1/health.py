import redis
from fastapi import APIRouter
from sqlalchemy import text

from max_chat_backend.core.config import get_settings
from max_chat_backend.db.session import engine

router = APIRouter()
settings = get_settings()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness() -> dict:
    checks = {"database": False, "redis": False}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    try:
        redis.Redis.from_url(settings.redis_url, decode_responses=True).ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    return {"status": "ok" if all(checks.values()) else "degraded", "checks": checks}

