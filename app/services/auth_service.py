from __future__ import annotations

"""
Бизнес-логика авторизации.
"""

from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from app.auth.passwords import verify_password
from app.auth.session_state import AuthSession
from app.db.session import get_db_session
from app.repositories.auth_repository import AuthRepository


@dataclass(frozen=True)
class LoginResult:
    success: bool
    message: str
    session: AuthSession


class AuthService:
    def authenticate(self, username: str | None, password: str | None) -> LoginResult:
        """
        Проверяет логин и пароль пользователя.
        """
        normalized_username = (username or "").strip()
        normalized_password = (password or "").strip()

        if not normalized_username:
            return LoginResult(
                success=False,
                message="Введите логин.",
                session=AuthSession.anonymous(),
            )

        if not normalized_password:
            return LoginResult(
                success=False,
                message="Введите пароль.",
                session=AuthSession.anonymous(),
            )

        try:
            with get_db_session() as session:
                repo = AuthRepository(session)
                user_row = repo.get_user_for_auth(normalized_username)

                if not user_row:
                    return LoginResult(
                        success=False,
                        message="Пользователь с таким логином не найден.",
                        session=AuthSession.anonymous(),
                    )

                if not bool(user_row["is_active"]):
                    return LoginResult(
                        success=False,
                        message="Пользователь неактивен. Обратитесь к HR или администратору.",
                        session=AuthSession.anonymous(),
                    )

                if bool(user_row["is_locked"]):
                    return LoginResult(
                        success=False,
                        message="Пользователь заблокирован. Обратитесь к администратору.",
                        session=AuthSession.anonymous(),
                    )

                stored_password_value = str(user_row["password_hash"] or "")

                if not verify_password(normalized_password, stored_password_value):
                    return LoginResult(
                        success=False,
                        message="Неверный пароль.",
                        session=AuthSession.anonymous(),
                    )

                role_code = str(user_row["role_code"] or "").upper()

                if role_code == "EMPLOYEE":
                    app_role = "employee"
                    app_role_display_name = "Сотрудник"
                elif role_code == "HR_MANAGER":
                    app_role = "hr"
                    app_role_display_name = "HR-менеджер"
                else:
                    return LoginResult(
                        success=False,
                        message="Для пользователя назначена неподдерживаемая роль.",
                        session=AuthSession.anonymous(),
                    )

                repo.update_last_login(int(user_row["user_id"]))
                repo.create_login_event(int(user_row["user_id"]))

                auth_session = AuthSession(
                    is_authenticated=True,
                    user_id=int(user_row["user_id"]),
                    username=str(user_row["username"]),
                    full_name=str(user_row["full_name"] or normalized_username),
                    role=app_role,
                    role_display_name=app_role_display_name,
                )

                return LoginResult(
                    success=True,
                    message="Вход выполнен успешно.",
                    session=auth_session,
                )

        except SQLAlchemyError:
            return LoginResult(
                success=False,
                message="База данных недоступна. Проверьте подключение к MySQL.",
                session=AuthSession.anonymous(),
            )

    def logout(self) -> AuthSession:
        """
        Сбрасывает авторизацию.
        """
        return AuthSession.anonymous()