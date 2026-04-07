# MAX Chat Backend

Основной backend для чат-бота в `MAX`, который отвечает через `DeepSeek`.

В этом репозитории лежат:

- `FastAPI` webhook и внутренний API для админки
- `Celery + Redis` для фоновой обработки сообщений
- `PostgreSQL` и `Alembic` для хранения пользователей, диалогов, промптов и ответов
- интеграция с `MAX API`
- adapter для `DeepSeek API`
- документация и deploy-файлы для всего проекта

Этот репозиторий считается главной точкой входа по проекту. Frontend-репозиторий содержит только код внутренней админки.

## Что умеет проект

- принимает сообщение пользователя из `MAX`
- работает с plain text из `message.body.text`
- не строит бизнес-логику на raw-представлении сообщения
- сохраняет пользователей, диалоги, сообщения и вызовы LLM
- отправляет ответ модели обратно в `MAX`
- разбивает длинные ответы на несколько сообщений под лимит `MAX`
- отдает внутренний API для web-админки

## Быстрый локальный запуск

1. Скопируйте `.env.example` в `.env` и заполните значения.
2. Рядом должен лежать frontend-репозиторий `max_chat_frontend`.
3. Из корня backend-репозитория выполните:

```bash
docker compose -f docker-compose.workspace.yml up --build
```

4. Backend будет доступен на `http://localhost:8000`.
5. Frontend-админка будет доступна на `http://localhost:8001`.

## Health endpoints

- `GET /api/v1/health`
- `GET /api/v1/health/ready`

## Internal API

- `GET /api/v1/internal/summary`
- `GET /api/v1/internal/users`
- `GET /api/v1/internal/users/{id}`
- `GET /api/v1/internal/conversations`
- `GET /api/v1/internal/conversations/{id}`
- `GET /api/v1/internal/messages`
- `GET /api/v1/internal/messages/{id}`
- `GET /api/v1/internal/llm-requests`
- `GET /api/v1/internal/llm-requests/{id}`
- `GET /api/v1/internal/errors`
- `GET /api/v1/internal/exports/users.csv`
- `GET /api/v1/internal/exports/conversations.csv`
- `GET /api/v1/internal/exports/messages.csv`
- `GET /api/v1/internal/exports/llm_requests.csv`

## Регистрация webhook в MAX

После заполнения `MAX_BOT_TOKEN`, `MAX_BOT_SECRET` и `BASE_WEBHOOK_URL`:

```bash
python -m max_chat_backend.scripts.register_webhook
```

## Полезные скрипты

```bash
python -m max_chat_backend.scripts.migrate
python -m max_chat_backend.scripts.get_me
python -m max_chat_backend.scripts.list_subscriptions
python -m max_chat_backend.scripts.delete_webhook
python -m max_chat_backend.scripts.poll_updates
```

`poll_updates` полезен для локальной разработки, когда публичный webhook еще не выведен наружу.

## Проверки в CI

```bash
pip install ".[dev]"
ruff check src tests
pytest
```

## Документация

- [Техническое задание](docs/TZ.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [Конфигурация](docs/CONFIGURATION.md)
- [Деплой](docs/DEPLOY.md)
- [Git Setup](docs/GIT_SETUP.md)
- [Deploy folder](deploy/README.md)
- [Workspace compose](docker-compose.workspace.yml)

Если смотреть проект на GitHub, для понимания всей системы достаточно открыть этот backend-репозиторий.
