from __future__ import annotations

"""
Небольшой отдельный helper для рейтинговой таблицы.
"""

from contextlib import contextmanager
import os

import mysql.connector

from app.core.config import get_settings


def _pick_value(*values, default: str = "") -> str:
    """
    Берёт первое непустое значение.=
    """
    for value in values:
        if value is None:
            continue
        if str(value).strip() == "":
            continue
        return str(value)
    return default


def create_connection():
    """
    Создаёт новое соединение с MySQL.
    """
    settings = get_settings()

    host = _pick_value(
        getattr(settings, "mysql_host", None),
        getattr(settings, "db_host", None),
        os.getenv("MYSQL_HOST"),
        os.getenv("DB_HOST"),
        default="127.0.0.1",
    )

    port_raw = _pick_value(
        getattr(settings, "mysql_port", None),
        getattr(settings, "db_port", None),
        os.getenv("MYSQL_PORT"),
        os.getenv("DB_PORT"),
        default="3306",
    )

    user = _pick_value(
        getattr(settings, "mysql_user", None),
        getattr(settings, "db_user", None),
        os.getenv("MYSQL_USER"),
        os.getenv("DB_USER"),
        default="root",
    )

    password = _pick_value(
        getattr(settings, "mysql_password", None),
        getattr(settings, "db_password", None),
        os.getenv("MYSQL_PASSWORD"),
        os.getenv("DB_PASSWORD"),
        default="",
    )

    database = _pick_value(
        getattr(settings, "mysql_database", None),
        getattr(settings, "db_name", None),
        os.getenv("MYSQL_DATABASE"),
        os.getenv("DB_NAME"),
        default="elbrus",
    )

    return mysql.connector.connect(
        host=host,
        port=int(port_raw),
        user=user,
        password=password,
        database=database,
    )


@contextmanager
def get_connection():
    """
    Контекстный менеджер для безопасной работы с соединением.
    """
    connection = create_connection()
    try:
        yield connection
    finally:
        connection.close()