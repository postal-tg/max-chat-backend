from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from max_chat_backend.core.config import get_settings
from max_chat_backend.models.base import Base

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from max_chat_backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def new_session() -> Session:
    return SessionLocal()

