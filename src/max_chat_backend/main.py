from fastapi import FastAPI

from max_chat_backend.api.router import router
from max_chat_backend.core.config import get_settings
from max_chat_backend.core.logging import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_v1_prefix)
