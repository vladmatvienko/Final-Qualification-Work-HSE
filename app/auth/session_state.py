"""
Модель сессии пользователя внутри Gradio.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AuthSession:
    """
    Описание текущей сессии пользователя.
    """
    is_authenticated: bool
    user_id: int | None
    username: str | None
    full_name: str | None
    role: str | None
    role_display_name: str | None

    @classmethod
    def anonymous(cls) -> "AuthSession":
        """
        Возвращает состояние "никто не авторизован".
        """
        return cls(
            is_authenticated=False,
            user_id=None,
            username=None,
            full_name=None,
            role=None,
            role_display_name=None,
        )

    def to_state(self) -> dict:
        """
        Преобразует dataclass в dict для хранения в gr.State.
        """
        return asdict(self)

    @classmethod
    def from_state(cls, state: dict | None) -> "AuthSession":
        """
        Безопасно восстанавливает AuthSession из gr.State.
        """
        if not state:
            return cls.anonymous()

        return cls(
            is_authenticated=bool(state.get("is_authenticated")),
            user_id=state.get("user_id"),
            username=state.get("username"),
            full_name=state.get("full_name"),
            role=state.get("role"),
            role_display_name=state.get("role_display_name"),
        )