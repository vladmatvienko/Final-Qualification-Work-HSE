"""
View-модели магазина бонусов.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StoreBonusCardViewModel:
    """
    Описание одной карточки бонуса в магазине.
    """
    bonus_id: int
    code: str
    title: str
    description: str
    cost_points: int
    icon: str
    level_label: str
    is_affordable: bool


@dataclass(frozen=True)
class EmployeeStoreDashboardViewModel:
    """
    Полный dashboard магазина для сотрудника.
    """
    points_balance: int
    items: list[StoreBonusCardViewModel] = field(default_factory=list)
    db_available: bool = True
    load_error_message: str | None = None


@dataclass(frozen=True)
class PurchaseBonusResult:
    """
    Результат попытки покупки бонуса.
    """
    success: bool
    message: str
    updated_points_balance: int | None = None
    already_processed: bool = False