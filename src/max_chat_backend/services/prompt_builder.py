import hashlib
import re
from dataclasses import dataclass

from max_chat_backend.core.config import Settings


@dataclass
class PromptValidationResult:
    is_valid: bool
    raw_text: str
    normalized_text: str
    prompt_hash: str | None = None
    error_message: str | None = None


def normalize_user_prompt(raw_text: str, settings: Settings) -> PromptValidationResult:
    plain_text = (raw_text or "").strip()
    plain_text = re.sub(r"\s+", " ", plain_text)

    if not plain_text:
        return PromptValidationResult(
            is_valid=False,
            raw_text=raw_text,
            normalized_text="",
            error_message="Пришлите текстовый запрос.",
        )

    if len(plain_text) > settings.prompt_text_limit:
        return PromptValidationResult(
            is_valid=False,
            raw_text=raw_text,
            normalized_text=plain_text[: settings.prompt_text_limit],
            error_message=(
                "Запрос слишком длинный. "
                "В первой версии принимаем сообщения "
                f"до {settings.prompt_text_limit} символов."
            ),
        )

    prompt_hash = hashlib.sha256(plain_text.encode("utf-8")).hexdigest()
    return PromptValidationResult(
        is_valid=True,
        raw_text=raw_text,
        normalized_text=plain_text,
        prompt_hash=prompt_hash,
    )
