def welcome_message(bot_name: str) -> str:
    return (
        f"Привет! Я {bot_name}. Пришли вопрос или задачу одним сообщением, "
        "и я отвечу через DeepSeek."
    )


def help_message(bot_name: str) -> str:
    return (
        f"{bot_name} отвечает на сообщения пользователей через DeepSeek.\n"
        "1. Отправь вопрос или инструкцию одним сообщением.\n"
        "2. Дождись ответа.\n"
        "3. Нажми «Новый диалог» или отправь /new,\n"
        "чтобы начать разговор заново."
    )


def rate_limit_message(retry_after_seconds: int | None) -> str:
    if retry_after_seconds:
        return (
            "Слишком много сообщений за короткое время. "
            f"Подожди примерно {retry_after_seconds} сек.\n"
            "И попробуй снова."
        )
    return (
        "Слишком много запросов за короткое время. "
        "Немного подожди и попробуй снова."
    )


def active_request_message() -> str:
    return (
        "У тебя уже есть активный запрос. Дождись ответа "
        "и потом отправь следующий."
    )


def thinking_message() -> str:
    return "Думаю над ответом..."


def response_failed_message() -> str:
    return (
        "Не получилось получить ответ от модели. "
        "Попробуй переформулировать запрос\n"
        "и отправить его еще раз."
    )


def blocked_prompt_message() -> str:
    return (
        "Этот запрос заблокирован правилами безопасности. "
        "Попробуй другую формулировку."
    )


def invalid_prompt_message() -> str:
    return "Пришли текстовый запрос одним сообщением."


def new_dialog_message() -> str:
    return "Начал новый диалог. Можешь отправлять следующий запрос."


def callback_unknown_message() -> str:
    return "Неизвестное действие."


def callback_new_dialog_message() -> str:
    return "Новый диалог создан."
