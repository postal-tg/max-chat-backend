FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

CMD ["sh", "-c", "python -m max_chat_backend.scripts.migrate && uvicorn max_chat_backend.main:app --host 0.0.0.0 --port 8000"]

