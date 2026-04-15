import logging
from datetime import UTC, datetime

from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from max_chat_backend.core.config import get_settings
from max_chat_backend.db.session import new_session
from max_chat_backend.models import Conversation, LlmRequest, Message, User, WebhookEvent
from max_chat_backend.schemas.max_models import MaxUpdateSchema
from max_chat_backend.services.llm_provider import get_chat_provider
from max_chat_backend.services.max_client import MaxBotClient
from max_chat_backend.services.message_templates import (
    active_request_message,
    blocked_prompt_message,
    callback_new_dialog_message,
    callback_unknown_message,
    help_message,
    invalid_prompt_message,
    new_dialog_message,
    rate_limit_message,
    response_failed_message,
    thinking_message,
    welcome_message,
)
from max_chat_backend.services.moderation import moderate_prompt
from max_chat_backend.services.prompt_builder import normalize_user_prompt
from max_chat_backend.services.rate_limiter import RedisRateLimiter
from max_chat_backend.services.text_chunks import split_text_for_max
from max_chat_backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(name="max_chat_backend.process_webhook_event")
def process_webhook_event(event_id: int) -> None:
    with new_session() as db:
        event = db.get(WebhookEvent, event_id)
        if not event:
            return

        try:
            event.status = "processing"
            db.commit()
            update_payload = MaxUpdateSchema.model_validate(event.payload)

            if update_payload.update_type == "message_created":
                _handle_message_created(db, update_payload)
            elif update_payload.update_type == "message_callback":
                _handle_callback(db, update_payload)
            elif update_payload.update_type == "bot_started":
                _handle_bot_started(db, update_payload)
            else:
                event.status = "ignored"

            event.processed_at = datetime.now(UTC)
            if event.status == "processing":
                event.status = "processed"
            db.commit()
        except Exception as exc:
            logger.exception("Webhook event failed", extra={"event_id": event_id})
            db.rollback()
            event = db.get(WebhookEvent, event_id)
            if not event:
                return
            event.status = "failed"
            event.error_message = str(exc)
            event.processed_at = datetime.now(UTC)
            db.commit()


def _handle_message_created(db: Session, update_payload: MaxUpdateSchema) -> None:
    message = update_payload.message
    if not message or not message.sender:
        return

    raw_text = message.body.text if message.body and message.body.text else ""
    user = _upsert_user(db, update_payload)
    conversation = _get_or_create_active_conversation(
        db,
        user=user,
        chat_id=message.recipient.chat_id,
        title=user.first_name,
    )
    max_client = MaxBotClient(settings)

    command = raw_text.strip().lower()
    if command == "/start":
        max_client.send_text_message(user_id=user.max_user_id, text=welcome_message(settings.max_bot_name))
        return
    if command == "/help":
        max_client.send_text_message(user_id=user.max_user_id, text=help_message(settings.max_bot_name))
        return
    if command == "/new":
        _start_new_conversation(db, user=user, chat_id=message.recipient.chat_id, title=user.first_name)
        max_client.send_text_message(user_id=user.max_user_id, text=new_dialog_message())
        return

    rate_limit = RedisRateLimiter(settings).check(
        RedisRateLimiter.user_key(user.max_user_id, action="incoming_message")
    )
    if not rate_limit.is_allowed:
        max_client.send_text_message(user_id=user.max_user_id, text=rate_limit_message(rate_limit.retry_after_seconds))
        return

    validation = normalize_user_prompt(raw_text, settings)
    if not validation.is_valid:
        max_client.send_text_message(
            user_id=user.max_user_id,
            text=validation.error_message or invalid_prompt_message(),
        )
        return

    moderation = moderate_prompt(validation.normalized_text, settings)
    if not moderation.is_allowed:
        blocked_message = Message(
            user_id=user.id,
            conversation_id=conversation.id,
            source_message_timestamp=message.timestamp,
            role="user",
            raw_text=validation.raw_text,
            normalized_text=validation.normalized_text,
            prompt_hash=validation.prompt_hash,
            status="blocked",
            validation_error=moderation.error_message,
        )
        db.add(blocked_message)
        conversation.last_message_at = datetime.now(UTC)
        db.commit()
        max_client.send_text_message(user_id=user.max_user_id, text=blocked_prompt_message())
        return

    active_requests = _count_active_requests(db, user.id)
    if active_requests >= settings.max_active_requests_per_user:
        max_client.send_text_message(user_id=user.max_user_id, text=active_request_message())
        return

    user_message = Message(
        user_id=user.id,
        conversation_id=conversation.id,
        source_message_timestamp=message.timestamp,
        role="user",
        raw_text=validation.raw_text,
        normalized_text=validation.normalized_text,
        prompt_hash=validation.prompt_hash,
        status="accepted",
    )
    db.add(user_message)
    user.total_requests += 1
    conversation.last_message_at = datetime.now(UTC)
    db.commit()
    db.refresh(user_message)

    llm_request = LlmRequest(
        conversation_id=conversation.id,
        user_message_id=user_message.id,
        provider_name=settings.llm_provider,
        provider_model=settings.deepseek_model if settings.llm_provider == "deepseek" else "local-preview",
        status="queued",
    )
    db.add(llm_request)
    db.commit()
    db.refresh(llm_request)

    max_client.send_text_message(user_id=user.max_user_id, text=thinking_message())
    generate_reply.delay(llm_request.id)


def _handle_callback(db: Session, update_payload: MaxUpdateSchema) -> None:
    callback = update_payload.callback
    if not callback:
        return

    max_client = MaxBotClient(settings)
    payload = callback.payload or ""

    if payload.startswith("new_dialog:"):
        try:
            conversation_id = int(payload.split(":", maxsplit=1)[1])
        except (IndexError, ValueError):
            max_client.answer_callback(callback.callback_id, notification=callback_unknown_message())
            return

        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            max_client.answer_callback(callback.callback_id, notification=callback_unknown_message())
            return

        user = db.get(User, conversation.user_id)
        if not user:
            max_client.answer_callback(callback.callback_id, notification=callback_unknown_message())
            return

        _start_new_conversation(
            db,
            user=user,
            chat_id=conversation.max_chat_id,
            title=user.first_name,
        )
        max_client.answer_callback(callback.callback_id, notification=callback_new_dialog_message())
        max_client.send_text_message(user_id=user.max_user_id, text=new_dialog_message())
        return

    max_client.answer_callback(callback.callback_id, notification=callback_unknown_message())


def _handle_bot_started(db: Session, update_payload: MaxUpdateSchema) -> None:
    if not update_payload.user or not update_payload.chat_id:
        return

    user = _upsert_user_from_started_payload(db, update_payload)
    _start_new_conversation(
        db,
        user=user,
        chat_id=update_payload.chat_id,
        title=user.first_name,
        start_payload=update_payload.payload,
    )
    MaxBotClient(settings).send_text_message(user_id=user.max_user_id, text=welcome_message(settings.max_bot_name))


@celery_app.task(name="max_chat_backend.generate_reply")
def generate_reply(llm_request_id: int) -> None:
    with new_session() as db:
        llm_request = db.get(LlmRequest, llm_request_id)
        if not llm_request:
            return

        conversation = db.get(Conversation, llm_request.conversation_id)
        user = db.get(User, conversation.user_id) if conversation else None
        if not conversation or not user:
            return

        llm_request.status = "processing"
        llm_request.started_at = datetime.now(UTC)
        db.commit()

        try:
            provider = get_chat_provider(settings)
            provider_messages = _build_provider_messages(db, conversation.id)
            result = provider.generate_reply(provider_messages)

            assistant_message = Message(
                user_id=user.id,
                conversation_id=conversation.id,
                role="assistant",
                raw_text=result.answer_text,
                normalized_text=result.answer_text,
                status="accepted",
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)

            llm_request.provider_name = result.provider_name
            llm_request.provider_model = result.model
            llm_request.assistant_message_id = assistant_message.id
            llm_request.prompt_tokens = result.prompt_tokens
            llm_request.completion_tokens = result.completion_tokens
            llm_request.total_tokens = result.total_tokens
            llm_request.request_payload = result.request_payload
            llm_request.response_payload = result.response_payload
            llm_request.status = "completed"
            llm_request.finished_at = datetime.now(UTC)
            if llm_request.started_at:
                delta = llm_request.finished_at - llm_request.started_at
                llm_request.latency_ms = int(delta.total_seconds() * 1000)
            conversation.last_message_at = llm_request.finished_at
            db.commit()

            chunks = split_text_for_max(result.answer_text, settings.max_response_chunk_size)
            max_client = MaxBotClient(settings)
            for index, chunk in enumerate(chunks):
                attachments = None
                if index == len(chunks) - 1:
                    attachments = [max_client.build_new_dialog_keyboard(conversation.id)]
                max_client.send_text_message(
                    user_id=user.max_user_id,
                    text=chunk,
                    attachments=attachments,
                )
        except Exception as exc:
            logger.exception("Reply generation failed", extra={"llm_request_id": llm_request_id})
            llm_request.status = "failed"
            llm_request.error_message = str(exc)
            llm_request.finished_at = datetime.now(UTC)
            db.commit()

            try:
                MaxBotClient(settings).send_text_message(
                    user_id=user.max_user_id,
                    text=response_failed_message(),
                )
            except Exception:
                logger.exception(
                    "Unable to notify user about LLM failure",
                    extra={"llm_request_id": llm_request_id},
                )


def _build_provider_messages(db: Session, conversation_id: int) -> list[dict[str, str]]:
    history = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(settings.deepseek_context_messages)
    ).all()
    history = list(reversed(history))

    messages = [{"role": "system", "content": settings.assistant_system_prompt}]
    for item in history:
        if not item.normalized_text:
            continue
        role = item.role if item.role in {"user", "assistant", "system"} else "user"
        messages.append({"role": role, "content": item.normalized_text})
    return messages


def _count_active_requests(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(LlmRequest)
        .join(Conversation, Conversation.id == LlmRequest.conversation_id)
        .where(
            and_(
                Conversation.user_id == user_id,
                LlmRequest.status.in_(("queued", "processing")),
            )
        )
    ) or 0


def _upsert_user(db: Session, update_payload: MaxUpdateSchema) -> User:
    message = update_payload.message
    if not message or not message.sender:
        raise ValueError("Message sender is required to upsert a user.")

    sender = message.sender
    return _persist_user(
        db,
        max_user_id=sender.user_id,
        username=sender.username,
        first_name=sender.first_name,
        last_name=sender.last_name,
        is_bot=bool(sender.is_bot),
        locale=update_payload.user_locale,
    )


def _upsert_user_from_started_payload(db: Session, update_payload: MaxUpdateSchema) -> User:
    if not update_payload.user:
        raise ValueError("Started payload user is required to upsert a user.")
    sender = update_payload.user
    return _persist_user(
        db,
        max_user_id=sender.user_id,
        username=sender.username,
        first_name=sender.first_name,
        last_name=sender.last_name,
        is_bot=bool(sender.is_bot),
        locale=update_payload.user_locale,
    )


def _persist_user(
    db: Session,
    *,
    max_user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    is_bot: bool,
    locale: str | None,
) -> User:
    user = db.scalar(select(User).where(User.max_user_id == max_user_id))
    now = datetime.now(UTC)
    if user is None:
        user = User(
            max_user_id=max_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_bot=is_bot,
            locale=locale,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(user)
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.locale = locale
        user.last_seen_at = now
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.scalar(select(User).where(User.max_user_id == max_user_id))
        if user is None:
            raise
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.locale = locale
        user.last_seen_at = now
        db.commit()
    db.refresh(user)
    return user


def _get_or_create_active_conversation(
    db: Session,
    *,
    user: User,
    chat_id: int | None,
    title: str | None,
) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .where(and_(Conversation.user_id == user.id, Conversation.is_active.is_(True)))
        .order_by(Conversation.updated_at.desc())
    )
    if conversation:
        conversation.max_chat_id = chat_id or conversation.max_chat_id
        conversation.title = title or conversation.title
        db.commit()
        db.refresh(conversation)
        return conversation
    return _start_new_conversation(db, user=user, chat_id=chat_id, title=title)


def _start_new_conversation(
    db: Session,
    *,
    user: User,
    chat_id: int | None,
    title: str | None,
    start_payload: str | None = None,
) -> Conversation:
    db.execute(
        update(Conversation)
        .where(and_(Conversation.user_id == user.id, Conversation.is_active.is_(True)))
        .values(is_active=False)
    )
    conversation = Conversation(
        user_id=user.id,
        conversation_type="direct",
        max_chat_id=chat_id,
        max_user_id=user.max_user_id,
        title=title,
        start_payload=start_payload,
        is_active=True,
        last_message_at=datetime.now(UTC),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation
