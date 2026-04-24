from __future__ import annotations

"""
Утилиты проверки пароля.
"""


def verify_password(password: str | None, stored_password: str | None) -> bool:
    """
    Проверяет, совпадает ли введённый пароль с тем, что хранится в БД.
    """
    normalized_password = "" if password is None else str(password)
    normalized_stored_password = "" if stored_password is None else str(stored_password)

    return normalized_password == normalized_stored_password