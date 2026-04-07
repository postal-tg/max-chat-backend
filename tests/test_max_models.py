from max_chat_backend.schemas.max_models import MaxUpdateSchema, MaxUserSchema


def test_user_name_fallback_populates_first_name() -> None:
    user = MaxUserSchema.model_validate({"user_id": 1, "name": "Иван"})
    assert user.first_name == "Иван"


def test_bot_started_update_is_parsed() -> None:
    payload = {
        "update_type": "bot_started",
        "timestamp": 1712345678,
        "chat_id": 12345,
        "payload": "campaign=spring",
        "user": {
            "user_id": 777,
            "name": "Иван",
            "username": "ivan_user",
        },
    }

    update = MaxUpdateSchema.model_validate(payload)

    assert update.update_type == "bot_started"
    assert update.chat_id == 12345
    assert update.payload == "campaign=spring"
    assert update.user is not None
    assert update.user.first_name == "Иван"

