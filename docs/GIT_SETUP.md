# Git Setup

Проект рассчитан на два отдельных git-репозитория:

- `max_chat_backend`
- `max_chat_frontend`

## Рекомендуемые имена репозиториев

- `max-chat-backend`
- `max-chat-frontend`

## Рекомендуемый порядок

1. Создать два пустых remote-репозитория в GitHub или GitLab.
2. Инициализировать локальный git в каждой папке.
3. Сделать initial commit.
4. Привязать `origin`.
5. Отправить `main`.

## Пример для backend

```bash
cd max_chat_backend
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <BACKEND_REMOTE_URL>
git push -u origin main
```

## Пример для frontend

```bash
cd max_chat_frontend
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <FRONTEND_REMOTE_URL>
git push -u origin main
```

## Как лучше оформлять ревью

- новые изменения вносить через feature-ветки
- создавать PR в `main`
- в backend PR показывать docs и deploy-файлы как source of truth
- во frontend PR держать только frontend-код и ссылку на backend-документацию
