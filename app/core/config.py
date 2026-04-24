"""
Централизованный конфиг приложения.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    """
    Преобразует строку из .env в bool.
    """
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    """
    Безопасно преобразует строку в int.
    """
    if value is None:
        return default

    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return default


def _normalize_demo_role(value: str | None) -> str:
    """
    Нормализует роль из .env.
    """
    if not value:
        return "employee"

    normalized = value.strip().lower()
    if normalized not in {"employee", "hr"}:
        return "employee"

    return normalized


def _resolve_path(value: str | None, default_relative: str) -> Path:
    """
    Преобразует путь из .env в абсолютный Path.
    """
    raw_value = value.strip() if value else default_relative
    path = Path(raw_value)

    if path.is_absolute():
        return path

    return BASE_DIR / path


@dataclass(frozen=True)
class Settings:
    """
    Единый неизменяемый объект настроек приложения.
    """
    base_dir: Path

    app_title: str
    gradio_server_name: str
    gradio_server_port: int
    gradio_debug: bool

    demo_role: str
    demo_employee_name: str
    demo_hr_name: str
    demo_employee_user_id: int

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    uploads_root_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Возвращает кэшированный экземпляр настроек.
    """
    return Settings(
        base_dir=BASE_DIR,

        app_title=os.getenv("APP_TITLE", "Эльбрус"),
        gradio_server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        gradio_server_port=_to_int(os.getenv("GRADIO_SERVER_PORT"), 7860),
        gradio_debug=_to_bool(os.getenv("GRADIO_DEBUG"), default=True),

        demo_role=_normalize_demo_role(os.getenv("DEMO_ROLE")),
        demo_employee_name=os.getenv("DEMO_EMPLOYEE_NAME", "Матвиенко Матвей Матвеевич"),
        demo_hr_name=os.getenv("DEMO_HR_NAME", "Соколова Марина Игоревна"),
        demo_employee_user_id=_to_int(os.getenv("DEMO_EMPLOYEE_USER_ID"), 2001),

        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=_to_int(os.getenv("DB_PORT"), 3306),
        db_name=os.getenv("DB_NAME", "elbrus"),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),

        uploads_root_dir=_resolve_path(
            os.getenv("UPLOADS_ROOT_DIR"),
            default_relative="uploads",
        ),
    )