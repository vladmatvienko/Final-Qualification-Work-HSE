"""
View-модели уведомлений сотрудника.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmployeeNotificationCardViewModel:
    """
    Одна карточка уведомления для UI.
    """
    notification_id: int
    title: str
    message: str
    date_label: str
    status_code: str
    status_label: str
    is_read: bool


@dataclass(frozen=True)
class EmployeeNotificationsDashboardViewModel:
    """
    Полный dashboard вкладки "Уведомления".
    """
    total_count: int
    unread_count: int
    items: list[EmployeeNotificationCardViewModel] = field(default_factory=list)
    db_available: bool = True
    load_error_message: str | None = None


@dataclass(frozen=True)
class MarkNotificationReadResult:
    """
    Результат попытки пометить уведомление как прочитанное.
    """
    success: bool
    message: str