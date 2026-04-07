from dataclasses import dataclass

from max_chat_backend.core.config import Settings, get_settings


@dataclass(frozen=True)
class MaxBotRuntimeConfig:
    bot_token: str
    bot_secret: str
    bot_name: str
    bot_public_link: str
    api_base_url: str
    server_url: str
    webhook_path: str
    base_webhook_url: str
    webhook_update_types: tuple[str, ...]
    web_server_host: str
    web_server_port: int
    rate_limiter_capacity: int
    rate_limiter_period: int
    max_message_text_length: int
    prompt_text_limit: int
    max_response_chunk_size: int

    @property
    def webhook_url(self) -> str:
        return f"{self.base_webhook_url.rstrip('/')}{self.webhook_path}"


@dataclass(frozen=True)
class LlmRuntimeConfig:
    provider: str
    deepseek_api_base_url: str
    deepseek_model: str
    deepseek_temperature: float
    deepseek_max_tokens: int
    deepseek_context_messages: int
    request_retry_attempts: int
    request_retry_backoff_seconds: int
    assistant_system_prompt: str


@dataclass(frozen=True)
class BackendRuntimeConfig:
    max_bot: MaxBotRuntimeConfig
    llm: LlmRuntimeConfig
    internal_api_key: str
    database_url: str
    redis_url: str


def build_backend_runtime_config(settings: Settings | None = None) -> BackendRuntimeConfig:
    cfg = settings or get_settings()
    return BackendRuntimeConfig(
        max_bot=MaxBotRuntimeConfig(
            bot_token=cfg.max_bot_token,
            bot_secret=cfg.max_bot_secret,
            bot_name=cfg.max_bot_name,
            bot_public_link=cfg.max_bot_public_link,
            api_base_url=cfg.max_api_base_url,
            server_url=cfg.server_url,
            webhook_path=cfg.webhook_path,
            base_webhook_url=cfg.base_webhook_url,
            webhook_update_types=tuple(
                item.strip() for item in cfg.max_webhook_update_types.split(",") if item.strip()
            ),
            web_server_host=cfg.web_server_host,
            web_server_port=cfg.web_server_port,
            rate_limiter_capacity=cfg.rate_limiter_capacity,
            rate_limiter_period=cfg.rate_limiter_period,
            max_message_text_length=cfg.max_message_text_limit,
            prompt_text_limit=cfg.prompt_text_limit,
            max_response_chunk_size=cfg.max_response_chunk_size,
        ),
        llm=LlmRuntimeConfig(
            provider=cfg.llm_provider,
            deepseek_api_base_url=cfg.deepseek_api_base_url,
            deepseek_model=cfg.deepseek_model,
            deepseek_temperature=cfg.deepseek_temperature,
            deepseek_max_tokens=cfg.deepseek_max_tokens,
            deepseek_context_messages=cfg.deepseek_context_messages,
            request_retry_attempts=cfg.request_retry_attempts,
            request_retry_backoff_seconds=cfg.request_retry_backoff_seconds,
            assistant_system_prompt=cfg.assistant_system_prompt,
        ),
        internal_api_key=cfg.internal_api_key,
        database_url=cfg.database_url,
        redis_url=cfg.redis_url,
    )
