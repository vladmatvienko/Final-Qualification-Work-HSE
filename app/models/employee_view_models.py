"""
View-модели сотрудника для интерфейса.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# -------------------------------
# Константы кодов вкладок.
# -------------------------------
TAB_PERSONAL = "personal_data"
TAB_ACHIEVEMENTS = "achievements"
TAB_STORE = "store"
TAB_NOTIFICATIONS = "notifications"


@dataclass(frozen=True)
class SidebarTab:
    """
    Описание одной вкладки в левом вертикальном меню.
    """
    code: str
    label: str


# Список вкладок сотрудника.
EMPLOYEE_TABS: list[SidebarTab] = [
    SidebarTab(code=TAB_PERSONAL, label="Личные данные"),
    SidebarTab(code=TAB_ACHIEVEMENTS, label="Достижения"),
    SidebarTab(code=TAB_STORE, label="Магазин"),
    SidebarTab(code=TAB_NOTIFICATIONS, label="Уведомления"),
]


@dataclass(frozen=True)
class ResumeSection:
    """
    Один логический блок на странице "Личные данные".
    """
    title: str
    lines: list[str]


@dataclass(frozen=True)
class AchievementCard:
    """
    Данные одной карточки достижения.
    """
    icon: str
    title: str
    description: str
    points: int
    completed: bool


@dataclass(frozen=True)
class StoreItemCard:
    """
    Данные одной карточки магазина бонусов.
    """
    icon: str
    title: str
    description: str
    price_points: int


@dataclass(frozen=True)
class NotificationCard:
    """
    Данные одного уведомления сотрудника.
    """
    title: str
    description: str
    priority_label: str
    status_label: str


@dataclass(frozen=True)
class EmployeeDashboardViewModel:
    """
    Корневая view-модель сотрудника.
    """
    full_name: str
    achievements_done: int
    achievements_total: int
    points: int
    resume_sections: list[ResumeSection] = field(default_factory=list)
    achievements: list[AchievementCard] = field(default_factory=list)
    store_items: list[StoreItemCard] = field(default_factory=list)
    notifications: list[NotificationCard] = field(default_factory=list)