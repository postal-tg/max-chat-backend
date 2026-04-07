from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from max_chat_backend.core.config import Settings


@dataclass
class ChatCompletionResult:
    answer_text: str
    provider_name: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]


class ChatProvider(ABC):
    @abstractmethod
    def generate_reply(self, messages: list[dict[str, str]]) -> ChatCompletionResult:
        raise NotImplementedError


class DummyChatProvider(ChatProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_reply(self, messages: list[dict[str, str]]) -> ChatCompletionResult:
        latest_user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        answer = (
            "Тестовый режим без ключа DeepSeek. "
            f"Я получил запрос: {latest_user_message[:250]}"
        )
        return ChatCompletionResult(
            answer_text=answer,
            provider_name="dummy",
            model="local-preview",
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            request_payload={"messages": messages},
            response_payload={"answer_text": answer},
        )


class DeepSeekChatProvider(ChatProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.deepseek_api_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate_reply(self, messages: list[dict[str, str]]) -> ChatCompletionResult:
        payload = {
            "model": self.settings.deepseek_model,
            "messages": messages,
            "temperature": self.settings.deepseek_temperature,
            "max_tokens": self.settings.deepseek_max_tokens,
            "stream": False,
        }
        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})
        answer_text = choice.get("content") or ""

        return ChatCompletionResult(
            answer_text=answer_text,
            provider_name="deepseek",
            model=data.get("model", self.settings.deepseek_model),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            request_payload=payload,
            response_payload=data,
        )


def get_chat_provider(settings: Settings) -> ChatProvider:
    if settings.llm_provider == "deepseek" and settings.deepseek_api_key:
        return DeepSeekChatProvider(settings)
    return DummyChatProvider(settings)
