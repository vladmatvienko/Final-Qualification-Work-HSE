"""
Rule engine достижений.
"""

from __future__ import annotations

from datetime import date, datetime

from app.db.session import get_db_session
from app.repositories.achievement_repository import AchievementRepository


THRESHOLD_CODES = {
    "FIRST_FIVE",
    "FIFTEEN_REASONS",
    "THIRTY_JOYS",
    "FIFTY_WINS",
}


class AchievementEngineService:
    """
    Сервис оценки достижений.
    """

    def evaluate_for_employee(self, employee_user_id: int) -> None:
        """
        Главная точка входа.
        """
        with get_db_session() as session:
            repo = AchievementRepository(session)
            catalog_rows = repo.get_active_achievement_catalog()
            catalog_by_code = {str(row["code"]): row for row in catalog_rows}

            self._evaluate_profile_activated(repo, catalog_by_code, employee_user_id)
            self._evaluate_completed_qualification_courses(repo, catalog_by_code, employee_user_id)
            self._evaluate_external_expert(repo, catalog_by_code, employee_user_id)
            self._evaluate_competition_participation(repo, catalog_by_code, employee_user_id)
            self._evaluate_competition_winner(repo, catalog_by_code, employee_user_id)
            self._evaluate_resume_update_quarter(repo, catalog_by_code, employee_user_id)
            self._evaluate_service_anniversary(repo, catalog_by_code, employee_user_id)

            self._evaluate_threshold_achievements(repo, catalog_by_code, employee_user_id)

            repo.sync_employee_profile_achievement_metrics(employee_user_id)

    # =========================================================
    # Вспомогательные методы
    # =========================================================
    def _award_if_missing(
        self,
        repo: AchievementRepository,
        catalog_by_code: dict,
        employee_user_id: int,
        achievement_code: str,
        award_key: str,
        source_entity_type: str | None = None,
        source_entity_id: int | None = None,
        rule_snapshot: dict | None = None,
    ) -> bool:
        achievement = catalog_by_code.get(achievement_code)
        if not achievement:
            return False

        achievement_id = int(achievement["id"])
        points = int(achievement["points"])

        if repo.award_exists(employee_user_id, achievement_id, award_key):
            return False

        repo.create_achievement_award(
            employee_user_id=employee_user_id,
            achievement_id=achievement_id,
            award_key=award_key,
            points_awarded=points,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            rule_snapshot=rule_snapshot,
        )

        repo.create_point_transaction(
            employee_user_id=employee_user_id,
            points_delta=points,
            source_entity_type="achievement_award",
            source_entity_id=achievement_id,
            comment=f"Начисление за достижение: {achievement['name']}",
        )

        return True

    def _current_quarter_start(self) -> date:
        today = date.today()
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, quarter_start_month, 1)

    def _current_quarter_key(self) -> str:
        today = date.today()
        quarter_number = ((today.month - 1) // 3) + 1
        return f"{today.year}Q{quarter_number}"

    # =========================================================
    # Реализация правил
    # =========================================================
    def _evaluate_profile_activated(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Профиль активирован" — как только у пользователя есть хотя бы один успешный вход.
        """
        login_count = repo.get_login_event_count(employee_user_id)
        if login_count > 0:
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="PROFILE_ACTIVATED",
                award_key="ONCE",
                source_entity_type="user_login_events",
                source_entity_id=None,
                rule_snapshot={"login_count": login_count},
            )

    def _evaluate_completed_qualification_courses(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Курс завершён" — один раз за каждый завершённый курс повышения квалификации.
        """
        rows = repo.get_completed_qualification_courses(employee_user_id)

        for row in rows:
            course_id = int(row["id"])
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="COURSE_COMPLETED",
                award_key=f"qualification_course:{course_id}",
                source_entity_type="employee_qualification_courses",
                source_entity_id=course_id,
                rule_snapshot={"qualification_course_id": course_id},
            )

    def _evaluate_external_expert(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Внешний эксперт" — один раз за:
        - завершённый дополнительный курс
        - диплом / новое образование
        """
        additional_courses = repo.get_completed_additional_courses(employee_user_id)
        diplomas = repo.get_diploma_ids(employee_user_id)

        for row in additional_courses:
            course_id = int(row["id"])
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="EXTERNAL_EXPERT",
                award_key=f"additional_course:{course_id}",
                source_entity_type="employee_additional_courses",
                source_entity_id=course_id,
                rule_snapshot={"additional_course_id": course_id},
            )

        for row in diplomas:
            diploma_id = int(row["diploma_id"])
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="EXTERNAL_EXPERT",
                award_key=f"diploma:{diploma_id}",
                source_entity_type="education_diplomas",
                source_entity_id=diploma_id,
                rule_snapshot={"diploma_id": diploma_id},
            )

    def _evaluate_competition_participation(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Участник соревнований" — один раз за каждую запись участия.
        """
        rows = repo.get_competition_results(employee_user_id)

        for row in rows:
            result_id = int(row["id"])
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="COMPETITION_PARTICIPANT",
                award_key=f"competition_result:{result_id}",
                source_entity_type="employee_competition_results",
                source_entity_id=result_id,
                rule_snapshot={"competition_result_id": result_id},
            )

    def _evaluate_competition_winner(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Призёр чемпионата" — один раз за каждую запись участия с призовым местом.
        """
        rows = repo.get_competition_results(employee_user_id)

        for row in rows:
            result_id = int(row["id"])
            placement_id = row["placement_id"]

            if placement_id is None:
                continue

            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="CHAMPIONSHIP_WINNER",
                award_key=f"competition_prize:{result_id}",
                source_entity_type="employee_competition_results",
                source_entity_id=result_id,
                rule_snapshot={
                    "competition_result_id": result_id,
                    "placement_id": int(placement_id),
                },
            )

    def _evaluate_resume_update_quarter(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правила квартальной активности по обновлению резюме.
        """
        quarter_start = self._current_quarter_start()
        quarter_key = self._current_quarter_key()

        update_count = repo.get_current_quarter_resume_update_count(
            employee_user_id=employee_user_id,
            period_start=quarter_start,
        )

        if update_count <= 0:
            return

        quarter_award_key = f"quarter:{quarter_key}"
        rule_snapshot_base = {
            "quarter": quarter_key,
            "resume_updates_count": update_count,
        }

        cumulative_rules = [
            ("SKILLS_UP_TO_DATE", 1),
            ("ACTIVE_PARTICIPANT", 3),
            ("HOW_DID_YOU_MANAGE_IT", 6),
        ]

        for achievement_code, threshold_value in cumulative_rules:
            if update_count < threshold_value:
                continue

            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code=achievement_code,
                award_key=quarter_award_key,
                source_entity_type="resume_change_requests",
                source_entity_id=None,
                rule_snapshot={
                    **rule_snapshot_base,
                    "threshold": threshold_value,
                    "evaluation_mode": "cumulative_quarter_threshold",
                },
            )

    def _evaluate_service_anniversary(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        """
        Правило:
        "Выслуга 3 года" — разовое достижение после 3 лет в компании.
        """
        hire_reference_date = repo.get_hire_reference_date(employee_user_id)
        if not hire_reference_date:
            return

        today = date.today()
        full_years = today.year - hire_reference_date.year - (
            (today.month, today.day) < (hire_reference_date.month, hire_reference_date.day)
        )

        if full_years >= 3:
            self._award_if_missing(
                repo=repo,
                catalog_by_code=catalog_by_code,
                employee_user_id=employee_user_id,
                achievement_code="SERVICE_3_YEARS",
                award_key="ONCE",
                source_entity_type="employee_profiles",
                source_entity_id=employee_user_id,
                rule_snapshot={
                    "hire_reference_date": str(hire_reference_date),
                    "full_years": full_years,
                },
            )

    def _evaluate_threshold_achievements(self, repo: AchievementRepository, catalog_by_code: dict, employee_user_id: int) -> None:
        award_rows = repo.get_employee_award_rows(employee_user_id)

        base_award_count = sum(
            1
            for row in award_rows
            if str(row["achievement_code"]) not in THRESHOLD_CODES
        )

        threshold_rules = [
            ("FIRST_FIVE", 5),
            ("FIFTEEN_REASONS", 15),
            ("THIRTY_JOYS", 30),
            ("FIFTY_WINS", 50),
        ]

        for achievement_code, threshold_value in threshold_rules:
            if base_award_count >= threshold_value:
                self._award_if_missing(
                    repo=repo,
                    catalog_by_code=catalog_by_code,
                    employee_user_id=employee_user_id,
                    achievement_code=achievement_code,
                    award_key="ONCE",
                    source_entity_type="employee_achievement_awards",
                    source_entity_id=None,
                    rule_snapshot={"base_award_count": base_award_count, "threshold": threshold_value},
                )