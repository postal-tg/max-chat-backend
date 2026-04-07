# Deploy Folder

Содержимое:

- `docker-compose.staging.yml` - staging/prod-like стек
- `Caddyfile.staging.example` - шаблон reverse proxy
- `.env.staging.example` - переменные для compose

Этот каталог лежит в backend-репозитории и считается основной точкой входа для деплоя всего продукта.

Ожидается, что рядом с backend-репозиторием будет лежать frontend-репозиторий:

```text
parent-folder/
  max_chat_backend/
  max_chat_frontend/
```

Быстрый порядок:

1. Скопировать `.env.staging.example` в `.env`.
2. Скопировать `Caddyfile.staging.example` в `Caddyfile`.
3. Заполнить домены и пароли.
4. Подготовить `../.env` для backend и `../../max_chat_frontend/.env` для frontend.
5. Выполнить `docker compose -f docker-compose.staging.yml --env-file .env up -d --build`.
