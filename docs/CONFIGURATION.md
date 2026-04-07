# Configuration

Источником правды для конфигурации остается `.env`, а Python-runtime собирается из него через типизированные settings.

## Backend

Главные параметры backend лежат в:

- [config.py](../src/max_chat_backend/core/config.py)
- [bot_config.py](../src/max_chat_backend/core/bot_config.py)
- [.env.example](../.env.example)
- [migrate.py](../src/max_chat_backend/scripts/migrate.py)

Для локальной разработки без публичного webhook можно использовать:

- [poll_updates.py](../src/max_chat_backend/scripts/poll_updates.py)

## Что нужно заполнить

Перед реальным запуском потребуются:

- `MAX_BOT_TOKEN`
- `MAX_BOT_SECRET`
- `MAX_BOT_NAME`
- `MAX_BOT_PUBLIC_LINK`
- `BASE_WEBHOOK_URL`
- `INTERNAL_API_KEY`
- `DEEPSEEK_API_KEY`

Для frontend еще нужны:

- `FRONTEND_SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

## Откуда брать значения

### Из вашей инфраструктуры MAX

- `MAX_BOT_TOKEN` - токен уже созданного бота
- `MAX_BOT_NAME` - имя бота, например `@max_chat_bot`
- `MAX_BOT_PUBLIC_LINK` - публичная ссылка на бота
- данные webhook - домен, путь и доступ к подпискам

Если прямого доступа к организационному контуру `MAX` у тебя нет, эти значения должен дать наставник или коллега, который ведет бота.

### Из DeepSeek

- `DEEPSEEK_API_KEY`

Обычно это секретный токен для запросов к `DeepSeek API`. Его нужно положить только в backend `.env` и никогда не коммитить в git.

### Сгенерировать самостоятельно

- `MAX_BOT_SECRET`
- `INTERNAL_API_KEY`
- `FRONTEND_SECRET_KEY`
- `ADMIN_PASSWORD`

Пример команды:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Что можно заполнить уже сейчас

Даже без доступов к `MAX` можно заранее заполнить:

- `MAX_BOT_SECRET`
- `INTERNAL_API_KEY`
- `DEEPSEEK_API_KEY`
- `FRONTEND_SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

А позже добавить:

- `MAX_BOT_TOKEN`
- `MAX_BOT_NAME`
- `MAX_BOT_PUBLIC_LINK`
- `BASE_WEBHOOK_URL`

## Пример минимального backend `.env`

```env
MAX_BOT_TOKEN=replace-me-from-max
MAX_BOT_SECRET=generated-random-secret
MAX_BOT_NAME=@max_chat_bot
MAX_BOT_PUBLIC_LINK=https://max.ru/max_chat_bot
BASE_WEBHOOK_URL=https://bot.example.com
INTERNAL_API_KEY=generated-internal-api-key
DEEPSEEK_API_KEY=replace-me
```

## Пример минимального frontend `.env`

```env
INTERNAL_API_KEY=generated-internal-api-key
FRONTEND_SECRET_KEY=generated-frontend-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong-password
```

## Требование по plain text

- входящий текст берем из `message.body.text`
- длину считаем по нормальному plain text
- raw webhook payload сохраняем только в `webhook_events`
- основная логика обработки не должна зависеть от raw-представления сообщения

Это сделано специально, чтобы не повторять проблему с некорректным подсчетом длины при работе с raw-текстом.

## Полезные ссылки

Внутренние ссылки:

- [backend `.env.example`](../.env.example)
- [backend config](../src/max_chat_backend/core/config.py)
- [backend bot config](../src/max_chat_backend/core/bot_config.py)
- [backend migrate script](../src/max_chat_backend/scripts/migrate.py)
- [poll updates script](../src/max_chat_backend/scripts/poll_updates.py)

Официальные внешние ссылки:

- MAX docs: https://dev.max.ru/docs
- MAX API overview: https://dev.max.ru/docs-api
- DeepSeek docs: https://api-docs.deepseek.com/
- DeepSeek chat completions: https://api-docs.deepseek.com/api/create-chat-completion/
- DeepSeek models: https://api-docs.deepseek.com/api/list-models

## Какой у нас подход

- чувствительные данные храним в `.env`
- runtime-конфиг собираем в Python
- лимиты не размазываем по коду
- под `MAX` сразу держим ограничение `MAX_MESSAGE_TEXT_LIMIT=4000`
- для пользовательского текста держим отдельный лимит `PROMPT_TEXT_LIMIT`
- длинные ответы режем по `MAX_RESPONSE_CHUNK_SIZE`
- миграции БД прогоняются через `Alembic`
