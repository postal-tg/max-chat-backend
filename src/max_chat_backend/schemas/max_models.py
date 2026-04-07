from typing import Any

from pydantic import BaseModel, model_validator


class MaxUserSchema(BaseModel):
    user_id: int
    first_name: str | None = None
    name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_bot: bool | None = None

    @model_validator(mode="after")
    def fill_first_name_from_legacy_name(self) -> "MaxUserSchema":
        if not self.first_name and self.name:
            self.first_name = self.name
        return self


class MaxRecipientSchema(BaseModel):
    chat_id: int | None = None
    user_id: int | None = None


class MaxMessageBodySchema(BaseModel):
    text: str | None = None
    attachments: list[dict[str, Any]] | None = None


class MaxMessageSchema(BaseModel):
    sender: MaxUserSchema | None = None
    recipient: MaxRecipientSchema
    timestamp: int
    body: MaxMessageBodySchema | None = None


class MaxCallbackSchema(BaseModel):
    callback_id: str
    payload: str | None = None


class MaxUpdateSchema(BaseModel):
    update_type: str
    timestamp: int
    message: MaxMessageSchema | None = None
    callback: MaxCallbackSchema | None = None
    chat_id: int | None = None
    user: MaxUserSchema | None = None
    payload: str | None = None
    user_locale: str | None = None

