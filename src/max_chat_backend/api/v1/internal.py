import csv
import io

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from max_chat_backend.core.config import get_settings
from max_chat_backend.db.session import get_db
from max_chat_backend.models import Conversation, LlmRequest, Message, User
from max_chat_backend.schemas.internal import RecentRequest, SummaryCard, SummaryResponse

router = APIRouter()
settings = get_settings()


def require_internal_api_key(x_internal_api_key: str = Header(default="")) -> None:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal API key.")


def user_to_dict(item: User) -> dict:
    return {
        "id": item.id,
        "max_user_id": item.max_user_id,
        "username": item.username,
        "first_name": item.first_name,
        "last_name": item.last_name,
        "locale": item.locale,
        "is_bot": item.is_bot,
        "total_requests": item.total_requests,
        "first_seen_at": item.first_seen_at.isoformat(),
        "last_seen_at": item.last_seen_at.isoformat(),
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def conversation_to_dict(item: Conversation) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "conversation_type": item.conversation_type,
        "max_chat_id": item.max_chat_id,
        "max_user_id": item.max_user_id,
        "title": item.title,
        "start_payload": item.start_payload,
        "is_active": item.is_active,
        "last_message_at": item.last_message_at.isoformat() if item.last_message_at else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def message_to_dict(item: Message) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "conversation_id": item.conversation_id,
        "source_message_timestamp": item.source_message_timestamp,
        "role": item.role,
        "raw_text": item.raw_text,
        "normalized_text": item.normalized_text,
        "prompt_hash": item.prompt_hash,
        "status": item.status,
        "validation_error": item.validation_error,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def llm_request_to_dict(item: LlmRequest) -> dict:
    return {
        "id": item.id,
        "conversation_id": item.conversation_id,
        "user_message_id": item.user_message_id,
        "assistant_message_id": item.assistant_message_id,
        "provider_name": item.provider_name,
        "provider_model": item.provider_model,
        "status": item.status,
        "error_message": item.error_message,
        "prompt_tokens": item.prompt_tokens,
        "completion_tokens": item.completion_tokens,
        "total_tokens": item.total_tokens,
        "latency_ms": item.latency_ms,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def csv_response(filename: str, rows: list[dict]) -> Response:
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    content = "\ufeff" + buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary", response_model=SummaryResponse, dependencies=[Depends(require_internal_api_key)])
def get_summary(db: Session = Depends(get_db)) -> SummaryResponse:
    users = db.scalar(select(func.count()).select_from(User)) or 0
    conversations = db.scalar(select(func.count()).select_from(Conversation)) or 0
    messages = db.scalar(select(func.count()).select_from(Message)) or 0
    user_messages = db.scalar(select(func.count()).select_from(Message).where(Message.role == "user")) or 0
    assistant_messages = db.scalar(select(func.count()).select_from(Message).where(Message.role == "assistant")) or 0
    llm_requests = db.scalar(select(func.count()).select_from(LlmRequest)) or 0
    failed_llm_requests = (
        db.scalar(select(func.count()).select_from(LlmRequest).where(LlmRequest.status == "failed")) or 0
    )
    active_llm_requests = (
        db.scalar(select(func.count()).select_from(LlmRequest).where(LlmRequest.status.in_(("queued", "processing"))))
        or 0
    )

    items = db.scalars(select(LlmRequest).order_by(LlmRequest.created_at.desc()).limit(10)).all()
    recent = []
    for item in items:
        conversation = db.get(Conversation, item.conversation_id)
        user = db.get(User, conversation.user_id) if conversation else None
        user_message = db.get(Message, item.user_message_id)
        assistant_message = db.get(Message, item.assistant_message_id) if item.assistant_message_id else None
        recent.append(
            RecentRequest(
                llm_request_id=item.id,
                conversation_id=item.conversation_id,
                user_id=user.max_user_id if user else 0,
                username=user.username if user else None,
                status=item.status,
                prompt_preview=(user_message.normalized_text[:120] if user_message else ""),
                answer_preview=(assistant_message.normalized_text[:120] if assistant_message else None),
                created_at=item.created_at.isoformat(),
            )
        )

    return SummaryResponse(
        totals=SummaryCard(
            users=users,
            conversations=conversations,
            messages=messages,
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            llm_requests=llm_requests,
            failed_llm_requests=failed_llm_requests,
            active_llm_requests=active_llm_requests,
        ),
        recent_requests=recent,
    )


@router.get("/users", dependencies=[Depends(require_internal_api_key)])
def list_users(
    limit: int = Query(default=20, ge=1, le=200),
    search: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    query = select(User).order_by(User.last_seen_at.desc()).limit(limit)
    if search:
        pattern = f"%{search}%"
        query = (
            select(User)
            .where(
                (User.username.ilike(pattern))
                | (User.first_name.ilike(pattern))
                | (User.last_name.ilike(pattern))
            )
            .order_by(User.last_seen_at.desc())
            .limit(limit)
        )
    items = db.scalars(query).all()
    return {"items": [user_to_dict(item) for item in items]}


@router.get("/users/{user_id}", dependencies=[Depends(require_internal_api_key)])
def get_user_detail(user_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="User not found.")

    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == item.id).order_by(Conversation.updated_at.desc()).limit(20)
    ).all()
    messages = db.scalars(
        select(Message).where(Message.user_id == item.id).order_by(Message.created_at.desc()).limit(20)
    ).all()
    llm_requests = db.scalars(
        select(LlmRequest)
        .join(Conversation, Conversation.id == LlmRequest.conversation_id)
        .where(Conversation.user_id == item.id)
        .order_by(LlmRequest.created_at.desc())
        .limit(20)
    ).all()
    return {
        "user": user_to_dict(item),
        "recent_conversations": [conversation_to_dict(row) for row in conversations],
        "recent_messages": [message_to_dict(row) for row in messages],
        "recent_llm_requests": [llm_request_to_dict(row) for row in llm_requests],
    }


@router.get("/conversations", dependencies=[Depends(require_internal_api_key)])
def list_conversations(
    limit: int = Query(default=20, ge=1, le=200),
    active: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    query = select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
    if active:
        active_value = active.lower() in {"1", "true", "yes", "active"}
        query = (
            select(Conversation)
            .where(Conversation.is_active == active_value)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
    items = db.scalars(query).all()
    return {"items": [conversation_to_dict(item) for item in items]}


@router.get("/conversations/{conversation_id}", dependencies=[Depends(require_internal_api_key)])
def get_conversation_detail(conversation_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(Conversation, conversation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    user = db.get(User, item.user_id)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == item.id).order_by(Message.created_at.asc())
    ).all()
    llm_requests = db.scalars(
        select(LlmRequest).where(LlmRequest.conversation_id == item.id).order_by(LlmRequest.created_at.desc())
    ).all()
    return {
        "conversation": conversation_to_dict(item),
        "user": user_to_dict(user) if user else None,
        "messages": [message_to_dict(row) for row in messages],
        "llm_requests": [llm_request_to_dict(row) for row in llm_requests],
    }


@router.get("/messages", dependencies=[Depends(require_internal_api_key)])
def list_messages(
    limit: int = Query(default=20, ge=1, le=200),
    role: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    query = select(Message).order_by(Message.created_at.desc()).limit(limit)
    if role:
        query = select(Message).where(Message.role == role).order_by(Message.created_at.desc()).limit(limit)
    items = db.scalars(query).all()
    return {"items": [message_to_dict(item) for item in items]}


@router.get("/messages/{message_id}", dependencies=[Depends(require_internal_api_key)])
def get_message_detail(message_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(Message, message_id)
    if not item:
        raise HTTPException(status_code=404, detail="Message not found.")

    user = db.get(User, item.user_id)
    conversation = db.get(Conversation, item.conversation_id)
    return {
        "message": message_to_dict(item),
        "user": user_to_dict(user) if user else None,
        "conversation": conversation_to_dict(conversation) if conversation else None,
    }


@router.get("/llm-requests", dependencies=[Depends(require_internal_api_key)])
def list_llm_requests(
    limit: int = Query(default=20, ge=1, le=200),
    status: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    query = select(LlmRequest).order_by(LlmRequest.created_at.desc()).limit(limit)
    if status:
        query = (
            select(LlmRequest).where(LlmRequest.status == status).order_by(LlmRequest.created_at.desc()).limit(limit)
        )
    items = db.scalars(query).all()
    return {"items": [llm_request_to_dict(item) for item in items]}


@router.get("/llm-requests/{request_id}", dependencies=[Depends(require_internal_api_key)])
def get_llm_request_detail(request_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(LlmRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="LLM request not found.")

    conversation = db.get(Conversation, item.conversation_id)
    user = db.get(User, conversation.user_id) if conversation else None
    user_message = db.get(Message, item.user_message_id)
    assistant_message = db.get(Message, item.assistant_message_id) if item.assistant_message_id else None
    return {
        "llm_request": llm_request_to_dict(item),
        "conversation": conversation_to_dict(conversation) if conversation else None,
        "user": user_to_dict(user) if user else None,
        "user_message": message_to_dict(user_message) if user_message else None,
        "assistant_message": message_to_dict(assistant_message) if assistant_message else None,
    }


@router.get("/errors", dependencies=[Depends(require_internal_api_key)])
def list_errors(
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    items = db.scalars(
        select(LlmRequest).where(LlmRequest.status == "failed").order_by(LlmRequest.updated_at.desc()).limit(limit)
    ).all()
    return {"items": [llm_request_to_dict(item) for item in items]}


@router.get("/exports/users.csv", dependencies=[Depends(require_internal_api_key)])
def export_users(db: Session = Depends(get_db)) -> Response:
    rows = [user_to_dict(item) for item in db.scalars(select(User).order_by(User.id.asc())).all()]
    return csv_response("users.csv", rows)


@router.get("/exports/conversations.csv", dependencies=[Depends(require_internal_api_key)])
def export_conversations(db: Session = Depends(get_db)) -> Response:
    rows = [
        conversation_to_dict(item)
        for item in db.scalars(select(Conversation).order_by(Conversation.id.asc())).all()
    ]
    return csv_response("conversations.csv", rows)


@router.get("/exports/messages.csv", dependencies=[Depends(require_internal_api_key)])
def export_messages(db: Session = Depends(get_db)) -> Response:
    rows = [message_to_dict(item) for item in db.scalars(select(Message).order_by(Message.id.asc())).all()]
    return csv_response("messages.csv", rows)


@router.get("/exports/llm_requests.csv", dependencies=[Depends(require_internal_api_key)])
def export_llm_requests(db: Session = Depends(get_db)) -> Response:
    rows = [llm_request_to_dict(item) for item in db.scalars(select(LlmRequest).order_by(LlmRequest.id.asc())).all()]
    return csv_response("llm_requests.csv", rows)
