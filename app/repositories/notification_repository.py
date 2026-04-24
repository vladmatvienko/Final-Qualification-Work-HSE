"""
Repository-слой уведомлений сотрудника.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # =========================================================
    # Уведомления сотрудника
    # =========================================================
    def get_employee_notifications(self, employee_user_id: int):
        """
        Возвращает уведомления сотрудника
        """
        query = text(
            """
            SELECT
                id,
                title,
                message,
                notification_status,
                created_at,
                read_at
            FROM employee_notifications
            WHERE employee_user_id = :employee_user_id
            ORDER BY
                CASE
                    WHEN notification_status = 'new' THEN 0
                    ELSE 1
                END ASC,
                created_at DESC,
                id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_employee_notification(self, employee_user_id: int, notification_id: int):
        """
        Возвращает конкретное уведомление сотрудника.
        """
        query = text(
            """
            SELECT
                id,
                title,
                message,
                notification_status,
                created_at,
                read_at
            FROM employee_notifications
            WHERE employee_user_id = :employee_user_id
              AND id = :notification_id
            LIMIT 1
            """
        )

        return self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "notification_id": notification_id,
            },
        ).mappings().first()

    def mark_notification_as_read(self, employee_user_id: int, notification_id: int) -> int:
        """
        Помечает уведомление как прочитанное.
        """
        query = text(
            """
            UPDATE employee_notifications
            SET
                notification_status = 'read',
                read_at = NOW()
            WHERE employee_user_id = :employee_user_id
              AND id = :notification_id
              AND notification_status = 'new'
            """
        )

        result = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "notification_id": notification_id,
            },
        )

        return int(result.rowcount or 0)

    # =========================================================
    # Генерация уведомлений по курсам
    # =========================================================
    def get_expiring_qualification_courses(self, days_before_expiry: int):
        """
        Ищем курсы повышения квалификации
        """
        query = text(
            """
            SELECT
                eqc.id,
                eqc.employee_user_id,
                COALESCE(
                    eqc.course_name_override,
                    CONCAT('Курс повышения квалификации #', eqc.id)
                ) AS course_name,
                eqc.valid_until,
                DATEDIFF(eqc.valid_until, CURDATE()) AS days_left
            FROM employee_qualification_courses eqc
            WHERE eqc.status = 'completed'
              AND eqc.valid_until IS NOT NULL
              AND DATEDIFF(eqc.valid_until, CURDATE()) BETWEEN 0 AND :days_before_expiry
            ORDER BY eqc.valid_until ASC, eqc.id ASC
            """
        )

        return self.session.execute(
            query,
            {"days_before_expiry": days_before_expiry},
        ).mappings().all()

    def create_notification_if_missing(
        self,
        employee_user_id: int,
        notification_type: str,
        notification_key: str,
        title: str,
        message: str,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
        expires_at=None,
    ) -> bool:
        """
        Создаёт уведомление, только если уведомление с таким ключом
        ещё не существует у этого сотрудника.
        """
        exists_query = text(
            """
            SELECT id
            FROM employee_notifications
            WHERE employee_user_id = :employee_user_id
              AND notification_key = :notification_key
            LIMIT 1
            """
        )

        exists_row = self.session.execute(
            exists_query,
            {
                "employee_user_id": employee_user_id,
                "notification_key": notification_key,
            },
        ).mappings().first()

        if exists_row:
            return False

        insert_query = text(
            """
            INSERT INTO employee_notifications (
                employee_user_id,
                notification_type,
                notification_key,
                title,
                message,
                notification_status,
                related_entity_type,
                related_entity_id,
                expires_at,
                created_at
            ) VALUES (
                :employee_user_id,
                :notification_type,
                :notification_key,
                :title,
                :message,
                'new',
                :related_entity_type,
                :related_entity_id,
                :expires_at,
                NOW()
            )
            """
        )

        self.session.execute(
            insert_query,
            {
                "employee_user_id": employee_user_id,
                "notification_type": notification_type,
                "notification_key": notification_key,
                "title": title,
                "message": message,
                "related_entity_type": related_entity_type,
                "related_entity_id": related_entity_id,
                "expires_at": expires_at,
            },
        )

        return True