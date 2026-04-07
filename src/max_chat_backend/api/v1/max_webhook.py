from hashlib import sha256

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from max_chat_backend.core.config import get_settings
from max_chat_backend.db.session import new_session
from max_chat_backend.models import WebhookEvent
from max_chat_backend.tasks.workflows import process_webhook_event

router = APIRouter()
settings = get_settings()


def build_external_event_id(payload: dict) -> str:
    base = repr(
        (
            payload.get("update_type"),
            payload.get("timestamp"),
            payload.get("message", {}).get("timestamp"),
            payload.get("message", {}).get("sender", {}).get("user_id"),
            payload.get("callback", {}).get("callback_id"),
            payload.get("chat_id"),
            payload.get("user", {}).get("user_id"),
            payload.get("payload"),
        )
    )
    return sha256(base.encode("utf-8")).hexdigest()


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_max_bot_api_secret: str | None = Header(default=None),
) -> dict[str, str]:
    if settings.max_bot_secret and x_max_bot_api_secret != settings.max_bot_secret:
        raise HTTPException(status_code=401, detail="Invalid MAX webhook secret.")

    payload = await request.json()
    external_id = build_external_event_id(payload)

    with new_session() as db:
        existing = db.scalar(select(WebhookEvent).where(WebhookEvent.external_id == external_id))
        if existing:
            return {"status": "duplicate"}

        event = WebhookEvent(
            external_id=external_id,
            update_type=payload.get("update_type", "unknown"),
            payload=payload,
            status="accepted",
        )
        db.add(event)
        db.commit()
        db.refresh(event)

    process_webhook_event.delay(event.id)
    return {"status": "accepted"}

