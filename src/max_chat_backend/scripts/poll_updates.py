import time
from hashlib import sha256

from sqlalchemy import select

from max_chat_backend.core.config import get_settings
from max_chat_backend.db.session import new_session
from max_chat_backend.models import WebhookEvent
from max_chat_backend.services.max_client import MaxBotClient
from max_chat_backend.tasks.workflows import process_webhook_event


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


def main() -> None:
    settings = get_settings()
    client = MaxBotClient(settings)
    marker: int | None = None

    while True:
        response = client.get_updates(marker=marker, timeout=25, limit=100)
        updates = response.get("updates", [])
        marker = response.get("marker", marker)

        if not updates:
            time.sleep(1)
            continue

        for payload in updates:
            external_id = build_external_event_id(payload)
            with new_session() as db:
                existing = db.scalar(select(WebhookEvent).where(WebhookEvent.external_id == external_id))
                if existing:
                    continue
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


if __name__ == "__main__":
    main()

