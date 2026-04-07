import json

from max_chat_backend.core.bot_config import build_backend_runtime_config
from max_chat_backend.core.config import get_settings
from max_chat_backend.services.max_client import MaxBotClient


def main() -> None:
    runtime = build_backend_runtime_config()
    payload = {
        "url": runtime.max_bot.webhook_url,
        "update_types": list(runtime.max_bot.webhook_update_types),
        "secret": runtime.max_bot.bot_secret,
    }

    response = MaxBotClient(get_settings()).register_subscription(
        url=payload["url"],
        update_types=payload["update_types"],
        secret=payload["secret"],
    )
    print(json.dumps({"request": payload, "response": response}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

