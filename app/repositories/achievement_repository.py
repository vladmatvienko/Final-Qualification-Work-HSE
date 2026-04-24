"""
Repository-слой достижений.
"""

from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


class AchievementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # =========================================================
    # КАТАЛОГ ДОСТИЖЕНИЙ
    # =========================================================
    def get_active_achievement_catalog(self):
        query = text(
            """
            SELECT
                id,
                code,
                name,
                description,
                points,
                icon,
                category_code,
                verification_type,
                rule_type,
                rule_config_json,
                is_repeatable,
                repeat_period,
                sort_order,
                is_active
            FROM achievements
            WHERE is_active = TRUE
            ORDER BY sort_order ASC, id ASC
            """
        )
        return self.session.execute(query).mappings().all()

    def get_achievement_by_code(self, code: str):
        query = text(
            """
            SELECT
                id,
                code,
                name,
                description,
                points,
                icon,
                category_code,
                verification_type,
                rule_type,
                rule_config_json,
                is_repeatable,
                repeat_period,
                sort_order,
                is_active
            FROM achievements
            WHERE code = :code
              AND is_active = TRUE
            LIMIT 1
            """
        )
        return self.session.execute(query, {"code": code}).mappings().first()

    # =========================================================
    # ЖУРНАЛ ВХОДОВ
    # =========================================================
    def get_login_event_count(self, employee_user_id: int) -> int:
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM user_login_events
            WHERE user_id = :employee_user_id
              AND success = TRUE
            """
        )
        row = self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().first()
        return int(row["total_count"]) if row else 0

    # =========================================================
    # ДАННЫЕ ДЛЯ ПРАВИЛ
    # =========================================================
    def get_completed_qualification_courses(self, employee_user_id: int):
        query = text(
            """
            SELECT id
            FROM employee_qualification_courses
            WHERE employee_user_id = :employee_user_id
              AND status = 'completed'
            ORDER BY id ASC
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()

    def get_completed_additional_courses(self, employee_user_id: int):
        query = text(
            """
            SELECT id
            FROM employee_additional_courses
            WHERE employee_user_id = :employee_user_id
              AND status = 'completed'
            ORDER BY id ASC
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()

    def get_diploma_ids(self, employee_user_id: int):
        query = text(
            """
            SELECT ed.id AS diploma_id
            FROM education_diplomas ed
            INNER JOIN education_records er
                ON er.id = ed.education_id
            WHERE er.employee_user_id = :employee_user_id
            ORDER BY ed.id ASC
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()

    def get_competition_results(self, employee_user_id: int):
        query = text(
            """
            SELECT
                id,
                placement_id
            FROM employee_competition_results
            WHERE employee_user_id = :employee_user_id
            ORDER BY id ASC
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()

    def get_current_quarter_resume_update_count(self, employee_user_id: int, period_start: date) -> int:
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM resume_change_requests
            WHERE employee_user_id = :employee_user_id
              AND submitted_at >= :period_start
            """
        )
        row = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "period_start": period_start,
            },
        ).mappings().first()

        return int(row["total_count"]) if row else 0

    def get_hire_reference_date(self, employee_user_id: int):
        """
        Возвращает дату найма, а если её нет — дату создания пользователя.
        """
        query = text(
            """
            SELECT
                COALESCE(ep.hire_date, DATE(u.created_at)) AS hire_reference_date
            FROM users u
            INNER JOIN employee_profiles ep
                ON ep.user_id = u.id
            WHERE u.id = :employee_user_id
            LIMIT 1
            """
        )
        row = self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().first()
        return row["hire_reference_date"] if row else None

    # =========================================================
    # ВЫДАННЫЕ ДОСТИЖЕНИЯ
    # =========================================================
    def get_employee_award_rows(self, employee_user_id: int):
        """
        Возвращает все выданные достижения сотрудника с кодами достижений.
        """
        query = text(
            """
            SELECT
                eaa.id,
                eaa.achievement_id,
                eaa.award_key,
                eaa.points_awarded,
                a.code AS achievement_code
            FROM employee_achievement_awards eaa
            INNER JOIN achievements a
                ON a.id = eaa.achievement_id
            WHERE eaa.employee_user_id = :employee_user_id
              AND eaa.status = 'awarded'
            ORDER BY eaa.id ASC
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()

    def get_employee_award_summary_map(self, employee_user_id: int) -> dict[int, int]:
        """
        Возвращает словарь achievement_id -> количество получений.
        """
        query = text(
            """
            SELECT
                achievement_id,
                COUNT(*) AS total_count
            FROM employee_achievement_awards
            WHERE employee_user_id = :employee_user_id
              AND status = 'awarded'
            GROUP BY achievement_id
            """
        )

        rows = self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().all()
        return {int(row["achievement_id"]): int(row["total_count"]) for row in rows}

    def award_exists(self, employee_user_id: int, achievement_id: int, award_key: str) -> bool:
        query = text(
            """
            SELECT id
            FROM employee_achievement_awards
            WHERE employee_user_id = :employee_user_id
              AND achievement_id = :achievement_id
              AND award_key = :award_key
              AND status = 'awarded'
            LIMIT 1
            """
        )
        row = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "achievement_id": achievement_id,
                "award_key": award_key,
            },
        ).mappings().first()

        return row is not None

    def get_next_achievement_counter(self, employee_user_id: int, achievement_id: int) -> int:
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM employee_achievement_awards
            WHERE employee_user_id = :employee_user_id
              AND achievement_id = :achievement_id
              AND status = 'awarded'
            """
        )
        row = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "achievement_id": achievement_id,
            },
        ).mappings().first()

        current_count = int(row["total_count"]) if row else 0
        return current_count + 1

    def create_achievement_award(
        self,
        employee_user_id: int,
        achievement_id: int,
        award_key: str,
        points_awarded: int,
        source_entity_type: str | None = None,
        source_entity_id: int | None = None,
        awarded_by_user_id: int | None = None,
        rule_snapshot: dict | None = None,
    ) -> None:
        next_counter = self.get_next_achievement_counter(employee_user_id, achievement_id)

        query = text(
            """
            INSERT INTO employee_achievement_awards (
                employee_user_id,
                achievement_id,
                award_key,
                achievement_counter,
                points_awarded,
                awarded_at,
                source_entity_type,
                source_entity_id,
                awarded_by_user_id,
                status,
                rule_snapshot_json
            ) VALUES (
                :employee_user_id,
                :achievement_id,
                :award_key,
                :achievement_counter,
                :points_awarded,
                NOW(),
                :source_entity_type,
                :source_entity_id,
                :awarded_by_user_id,
                'awarded',
                :rule_snapshot_json
            )
            """
        )

        self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "achievement_id": achievement_id,
                "award_key": award_key,
                "achievement_counter": next_counter,
                "points_awarded": points_awarded,
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "awarded_by_user_id": awarded_by_user_id,
                "rule_snapshot_json": json.dumps(rule_snapshot, ensure_ascii=False) if rule_snapshot else None,
            },
        )

    def create_point_transaction(
        self,
        employee_user_id: int,
        points_delta: int,
        source_entity_type: str,
        source_entity_id: int | None,
        comment: str,
    ) -> None:
        query = text(
            """
            INSERT INTO employee_point_transactions (
                employee_user_id,
                transaction_type,
                points_delta,
                source_entity_type,
                source_entity_id,
                comment
            ) VALUES (
                :employee_user_id,
                'achievement_award',
                :points_delta,
                :source_entity_type,
                :source_entity_id,
                :comment
            )
            """
        )

        self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "points_delta": points_delta,
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "comment": comment,
            },
        )

    # =========================================================
    # СИНХРОНИЗАЦИЯ С employee_profiles
    # =========================================================
    def sync_employee_profile_achievement_metrics(self, employee_user_id: int) -> None:
        """
        Обновляет агрегаты в employee_profiles:
        - points_balance
        - completed_achievements_count
        """
        query = text(
            """
            UPDATE employee_profiles ep
            SET
                ep.completed_achievements_count = (
                    SELECT COUNT(DISTINCT eaa.achievement_id)
                    FROM employee_achievement_awards eaa
                    WHERE eaa.employee_user_id = :employee_user_id
                      AND eaa.status = 'awarded'
                ),
                ep.points_balance = COALESCE((
                    SELECT SUM(ept.points_delta)
                    FROM employee_point_transactions ept
                    WHERE ept.employee_user_id = :employee_user_id
                ), 0)
            WHERE ep.user_id = :employee_user_id
            """
        )

        self.session.execute(query, {"employee_user_id": employee_user_id})

    def get_profile_achievement_metrics(self, employee_user_id: int):
        query = text(
            """
            SELECT
                points_balance,
                completed_achievements_count
            FROM employee_profiles
            WHERE user_id = :employee_user_id
            LIMIT 1
            """
        )
        return self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().first()