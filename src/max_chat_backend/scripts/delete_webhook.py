import json

from max_chat_backend.core.bot_config import build_backend_runtime_config
from max_chat_backend.core.config import get_settings
from max_chat_backend.services.max_client import MaxBotClient


def main() -> None:
    runtime = build_backend_runtime_config()
    payload = MaxBotClient(get_settings()).delete_subscription(runtime.max_bot.webhook_url)
    print(json.dumps({"url": runtime.max_bot.webhook_url, "response": payload}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

