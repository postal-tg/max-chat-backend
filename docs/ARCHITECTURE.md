# Architecture

## Backend

- `FastAPI` принимает webhook от `MAX`
- входящий update сохраняется в `webhook_events`
- `Celery` обрабатывает событие в фоне
- rate limiter режет флуд до тяжелой обработки
- текст пользователя берется из `message.body.text`
- raw payload хранится отдельно только для аудита
- промпт нормализуется и проходит blocklist-модерацию
- создаются записи в `messages` и `llm_requests`
- backend формирует контекст диалога и вызывает `DeepSeek`
- ответ модели сохраняется в БД и отправляется обратно в `MAX`
- длинный ответ режется на несколько сообщений под лимит `MAX`
- схема БД фиксируется через `Alembic`

## Frontend

- отдельный Python frontend на `FastAPI + Jinja2`
- логин через cookie session
- данные читаются из backend internal API
- своих доменных данных frontend не хранит

## Data flow

1. Пользователь отправляет текст в `MAX`.
2. `MAX` дергает webhook backend.
3. Backend быстро отвечает `200 OK` и кладет событие в очередь.
4. Worker валидирует plain text, сохраняет сообщение и собирает контекст диалога.
5. Worker вызывает `DeepSeek`.
6. Ответ сохраняется как assistant message и отправляется пользователю.
7. Frontend показывает пользователей, диалоги, сообщения, LLM-вызовы и ошибки через internal API.
