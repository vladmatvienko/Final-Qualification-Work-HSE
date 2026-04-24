"""
View-модели для интерфейса HR-менеджера.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Коды вкладок HR-экрана.
TAB_RATING = "rating_table"
TAB_NOTIFICATIONS = "notifications"


@dataclass(frozen=True)
class SidebarTab:
    """
    Описание одной кнопки/вкладки в левом меню HR.
    """
    code: str
    label: str


HR_TABS: list[SidebarTab] = [
    SidebarTab(code=TAB_RATING, label="Рейтинговая таблица"),
    SidebarTab(code=TAB_NOTIFICATIONS, label="Уведомления"),
]


@dataclass(frozen=True)
class CandidateTableRow:
    """
    Одна строка рейтинговой таблицы кандидатов.
    """
    anonymous_code: str
    target_position: str
    fit_score: str
    key_strengths: str
    readiness_status: str


@dataclass(frozen=True)
class HRNotificationCard:
    """
    Описание одного уведомления для HR.
    """
    title: str
    description: str
    priority_label: str
    status_label: str


@dataclass(frozen=True)
class HRDashboardViewModel:
    """
    Корневая view-модель для экрана HR.
    """
    full_name: str
    role_label: str
    unread_notifications_count: int
    default_requirements_text: str
    candidates: list[CandidateTableRow] = field(default_factory=list)
    notifications: list[HRNotificationCard] = field(default_factory=list)