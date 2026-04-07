from pydantic import BaseModel


class SummaryCard(BaseModel):
    users: int
    conversations: int
    messages: int
    user_messages: int
    assistant_messages: int
    llm_requests: int
    failed_llm_requests: int
    active_llm_requests: int


class RecentRequest(BaseModel):
    llm_request_id: int
    conversation_id: int
    user_id: int
    username: str | None = None
    status: str
    prompt_preview: str
    answer_preview: str | None = None
    created_at: str


class SummaryResponse(BaseModel):
    totals: SummaryCard
    recent_requests: list[RecentRequest]
