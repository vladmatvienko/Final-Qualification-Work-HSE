"""
Service-слой вкладки "Достижения".
"""

from __future__ import annotations

from app.db.session import get_db_session
from app.models.achievement_models import (
    AchievementCardViewModel,
    EmployeeAchievementDashboardViewModel,
)
from app.repositories.achievement_repository import AchievementRepository
from app.services.achievement_engine_service import AchievementEngineService


class EmployeeAchievementService:
    def __init__(self) -> None:
        self.engine = AchievementEngineService()

    def get_dashboard(self, employee_user_id: int) -> EmployeeAchievementDashboardViewModel:
        """
        Главная точка входа для UI вкладки "Достижения".
        """
        self.engine.evaluate_for_employee(employee_user_id)

        with get_db_session() as session:
            repo = AchievementRepository(session)

            catalog_rows = repo.get_active_achievement_catalog()
            award_summary = repo.get_employee_award_summary_map(employee_user_id)
            profile_metrics = repo.get_profile_achievement_metrics(employee_user_id)

            cards: list[AchievementCardViewModel] = []

            for row in catalog_rows:
                achievement_id = int(row["id"])
                completion_count = int(award_summary.get(achievement_id, 0))
                completed = completion_count > 0
                is_repeatable = bool(row["is_repeatable"])

                if completed and is_repeatable and completion_count > 1:
                    status_label = f"Выполнено ×{completion_count}"
                elif completed:
                    status_label = "Выполнено"
                else:
                    status_label = "Не выполнено"

                cards.append(
                    AchievementCardViewModel(
                        achievement_id=achievement_id,
                        code=str(row["code"]),
                        title=str(row["name"]),
                        description=str(row["description"]),
                        points=int(row["points"]),
                        icon=str(row["icon"] or "🏆"),
                        completed=completed,
                        completion_count=completion_count,
                        is_repeatable=is_repeatable,
                        status_label=status_label,
                        category_code=str(row["category_code"]),
                    )
                )

            completed_possible_count = sum(1 for card in cards if card.completed)
            total_possible_count = len(cards)

            points_balance = int(profile_metrics["points_balance"]) if profile_metrics else 0

            return EmployeeAchievementDashboardViewModel(
                points_balance=points_balance,
                completed_possible_count=completed_possible_count,
                total_possible_count=total_possible_count,
                cards=cards,
            )