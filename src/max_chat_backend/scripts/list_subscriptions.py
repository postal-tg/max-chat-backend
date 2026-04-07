import json

from max_chat_backend.core.config import get_settings
from max_chat_backend.services.max_client import MaxBotClient


def main() -> None:
    client = MaxBotClient(get_settings())
    payload = client.list_subscriptions()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

