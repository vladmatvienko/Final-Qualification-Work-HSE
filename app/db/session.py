"""
Подключение к MySQL через SQLAlchemy.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    """
    Создаёт и кэширует engine SQLAlchemy.
    """
    settings = get_settings()

    encoded_user = quote_plus(settings.db_user)
    encoded_password = quote_plus(settings.db_password)

    database_url = (
        f"mysql+mysqlconnector://{encoded_user}:{encoded_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        f"?charset=utf8mb4"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache(maxsize=1)
def get_session_factory():
    """
    Возвращает фабрику SQLAlchemy-сессий.
    """
    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


@contextmanager
def get_db_session():
    """
    Контекстный менеджер для безопасной работы с БД.
    """
    session = get_session_factory()()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()