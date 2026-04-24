"""
Сервис служебной генерации уведомлений.
"""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session
from app.repositories.notification_repository import NotificationRepository


class NotificationGeneratorService:
    """
    Генератор уведомлений по бизнес-правилам.
    """

    DEFAULT_DAYS_BEFORE_EXPIRY = 30

    def generate_expiring_qualification_notifications(self, days_before_expiry: int | None = None) -> int:
        """
        Генерирует уведомления для курсов, срок действия которых скоро истекает.
        """
        threshold_days = days_before_expiry or self.DEFAULT_DAYS_BEFORE_EXPIRY
        created_count = 0

        try:
            with get_db_session() as session:
                repo = NotificationRepository(session)
                expiring_courses = repo.get_expiring_qualification_courses(threshold_days)

                for row in expiring_courses:
                    course_id = int(row["id"])
                    employee_user_id = int(row["employee_user_id"])
                    course_name = str(row["course_name"])
                    valid_until = row["valid_until"]
                    days_left = int(row["days_left"])

                    if days_left == 0:
                        days_part = "сегодня"
                    elif days_left == 1:
                        days_part = "через 1 день"
                    else:
                        days_part = f"через {days_left} дней"

                    notification_key = f"qualification_expiring:{course_id}:{valid_until}"

                    title = "Скоро истекает срок действия курса"
                    message = (
                        f"Срок действия курса повышения квалификации «{course_name}» "
                        f"истекает {days_part} ({valid_until:%d.%m.%Y}). "
                        f"Необходимо пройти новый курс."
                    )

                    created = repo.create_notification_if_missing(
                        employee_user_id=employee_user_id,
                        notification_type="qualification_expiring",
                        notification_key=notification_key,
                        title=title,
                        message=message,
                        related_entity_type="employee_qualification_courses",
                        related_entity_id=course_id,
                        expires_at=valid_until,
                    )

                    if created:
                        created_count += 1

            return created_count

        except SQLAlchemyError:
            return 0