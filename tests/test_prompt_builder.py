from max_chat_backend.core.config import Settings
from max_chat_backend.services.prompt_builder import normalize_user_prompt


def test_prompt_is_normalized() -> None:
    settings = Settings()
    result = normalize_user_prompt("  Привет,   расскажи про   Python  ", settings)

    assert result.is_valid is True
    assert result.normalized_text == "Привет, расскажи про Python"
    assert result.prompt_hash is not None
    assert len(result.prompt_hash) == 64


def test_prompt_limit_is_enforced() -> None:
    settings = Settings(prompt_text_limit=10)
    result = normalize_user_prompt("x" * 11, settings)

    assert result.is_valid is False
    assert "10" in (result.error_message or "")
