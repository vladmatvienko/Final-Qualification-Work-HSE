"""
Repository для авторизации.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_for_auth(self, username: str):
        query = text(
            """
            SELECT
                u.id AS user_id,
                u.username AS username,
                u.password_hash AS password_hash,
                u.is_active AS is_active,
                u.is_locked AS is_locked,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS full_name,
                r.code AS role_code
            FROM users u
            INNER JOIN roles r
                ON r.id = u.role_id
            WHERE u.username = :username
            LIMIT 1
            """
        )

        return self.session.execute(
            query,
            {"username": username},
        ).mappings().first()

    def update_last_login(self, user_id: int) -> None:
        query = text(
            """
            UPDATE users
            SET last_login_at = NOW(),
                updated_at = NOW()
            WHERE id = :user_id
            """
        )

        self.session.execute(query, {"user_id": user_id})

    def create_login_event(self, user_id: int) -> None:
        """
        Пишет факт успешного входа.
        """
        query = text(
            """
            INSERT INTO user_login_events (
                user_id,
                logged_in_at,
                success
            ) VALUES (
                :user_id,
                NOW(),
                TRUE
            )
            """
        )

        self.session.execute(query, {"user_id": user_id})