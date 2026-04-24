"""
View-модели для достижений.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AchievementCardViewModel:
    """
    Данные одной карточки достижения для UI.
    """
    achievement_id: int
    code: str
    title: str
    description: str
    points: int
    icon: str
    completed: bool
    completion_count: int
    is_repeatable: bool
    status_label: str
    category_code: str


@dataclass(frozen=True)
class EmployeeAchievementDashboardViewModel:
    """
    Полный payload для вкладки "Достижения".
    """
    points_balance: int
    completed_possible_count: int
    total_possible_count: int
    cards: list[AchievementCardViewModel] = field(default_factory=list)