from fastapi import APIRouter

from max_chat_backend.api.v1.health import router as health_router
from max_chat_backend.api.v1.internal import router as internal_router
from max_chat_backend.api.v1.max_webhook import router as max_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(max_router, prefix="/max", tags=["max"])
router.include_router(internal_router, prefix="/internal", tags=["internal"])

