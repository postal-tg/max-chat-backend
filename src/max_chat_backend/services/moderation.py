import re
from dataclasses import dataclass

from max_chat_backend.core.config import Settings


@dataclass
class PromptModerationResult:
    is_allowed: bool
    matched_term: str | None = None
    error_message: str | None = None


def moderate_prompt(text: str, settings: Settings) -> PromptModerationResult:
    normalized = (text or "").casefold()
    terms = [item.strip().casefold() for item in settings.prompt_blocklist.split(",") if item.strip()]
    for term in terms:
        if not term:
            continue
        if _matches_blocked_term(normalized, term):
            return PromptModerationResult(
                is_allowed=False,
                matched_term=term,
                error_message=(
                    "Запрос содержит заблокированную тему. "
                    "Попробуйте переформулировать сообщение безопаснее."
                ),
            )
    return PromptModerationResult(is_allowed=True)


def _matches_blocked_term(normalized_text: str, term: str) -> bool:
    if re.fullmatch(r"[a-z0-9_ -]+", term):
        pattern = rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])"
        return re.search(pattern, normalized_text) is not None
    return term in normalized_text

