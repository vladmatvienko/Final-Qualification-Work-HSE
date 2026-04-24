"""
Service-слой вкладки "Уведомления".
"""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session
from app.models.notification_models import (
    EmployeeNotificationCardViewModel,
    EmployeeNotificationsDashboardViewModel,
    MarkNotificationReadResult,
)
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_generator_service import NotificationGeneratorService


class EmployeeNotificationService:
    def __init__(self) -> None:
        self.generator = NotificationGeneratorService()

    def get_dashboard(self, employee_user_id: int) -> EmployeeNotificationsDashboardViewModel:
        """
        Загружает dashboard уведомлений сотрудника.
        """
        if not employee_user_id:
            return EmployeeNotificationsDashboardViewModel(
                total_count=0,
                unread_count=0,
                items=[],
                db_available=False,
                load_error_message="Сотрудник не определён.",
            )

        try:
            # Генерация идемпотентная.
            self.generator.generate_expiring_qualification_notifications()

            with get_db_session() as session:
                repo = NotificationRepository(session)
                rows = repo.get_employee_notifications(employee_user_id)

                items: list[EmployeeNotificationCardViewModel] = []

                for row in rows:
                    created_at = row["created_at"]
                    status_code = str(row["notification_status"])
                    is_read = status_code == "read"
                    status_label = "Прочитано" if is_read else "Новое"

                    if created_at is not None:
                        date_label = created_at.strftime("%d.%m.%Y %H:%M")
                    else:
                        date_label = "Дата неизвестна"

                    items.append(
                        EmployeeNotificationCardViewModel(
                            notification_id=int(row["id"]),
                            title=str(row["title"]),
                            message=str(row["message"]),
                            date_label=date_label,
                            status_code=status_code,
                            status_label=status_label,
                            is_read=is_read,
                        )
                    )

                unread_count = sum(1 for item in items if not item.is_read)

                return EmployeeNotificationsDashboardViewModel(
                    total_count=len(items),
                    unread_count=unread_count,
                    items=items,
                    db_available=True,
                    load_error_message=None,
                )

        except SQLAlchemyError:
            return EmployeeNotificationsDashboardViewModel(
                total_count=0,
                unread_count=0,
                items=[],
                db_available=False,
                load_error_message="База данных недоступна. Уведомления сейчас не удалось загрузить.",
            )

    def mark_as_read(self, employee_user_id: int, notification_id: int) -> MarkNotificationReadResult:
        """
        Помечает уведомление как прочитанное.
        """
        if not employee_user_id:
            return MarkNotificationReadResult(
                success=False,
                message="Сотрудник не определён.",
            )

        try:
            with get_db_session() as session:
                repo = NotificationRepository(session)

                existing = repo.get_employee_notification(employee_user_id, notification_id)
                if not existing:
                    return MarkNotificationReadResult(
                        success=False,
                        message="Уведомление не найдено.",
                    )

                if str(existing["notification_status"]) == "read":
                    return MarkNotificationReadResult(
                        success=True,
                        message="Уведомление уже было прочитано ранее.",
                    )

                updated_rows = repo.mark_notification_as_read(employee_user_id, notification_id)
                if updated_rows <= 0:
                    return MarkNotificationReadResult(
                        success=False,
                        message="Не удалось обновить статус уведомления.",
                    )

                return MarkNotificationReadResult(
                    success=True,
                    message="Уведомление помечено как прочитанное.",
                )

        except SQLAlchemyError:
            return MarkNotificationReadResult(
                success=False,
                message="База данных недоступна. Не удалось обновить статус уведомления.",
            )