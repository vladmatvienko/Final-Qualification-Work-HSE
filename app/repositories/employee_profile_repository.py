"""
Repository для чтения данных профиля сотрудника из MySQL.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class EmployeeProfileRepository:
    """
    Репозиторий для чтения резюме сотрудника.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_employee_base_profile(self, employee_user_id: int):
        """
        Возвращает базовый профиль сотрудника
        """
        query = text(
            """
            SELECT
                u.id AS user_id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS full_name,
                ep.gender AS gender,
                ep.birth_date AS birth_date,
                ep.marital_status AS marital_status,
                ep.citizenship AS citizenship,
                ep.driver_license_categories AS driver_license_categories,
                ep.has_criminal_record AS has_criminal_record,
                ep.criminal_record_details AS criminal_record_details,
                ep.points_balance AS points_balance,
                ep.completed_achievements_count AS completed_achievements_count
            FROM users u
            INNER JOIN employee_profiles ep
                ON ep.user_id = u.id
            WHERE u.id = :employee_user_id
            LIMIT 1
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().first()

    def get_total_active_achievements_count(self) -> int:
        """
        Считает общее количество активных достижений в системе.
        """
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM achievements
            WHERE is_active = TRUE
            """
        )

        result = self.session.execute(query).mappings().first()
        return int(result["total_count"]) if result else 0

    def get_request_section_options(self):
        """
        Возвращает список разделов резюме для формы "Добавить информацию"
        """
        query = text(
            """
            SELECT id, name
            FROM resume_sections
            ORDER BY id
            """
        )

        return self.session.execute(query).mappings().all()

    def get_education_records(self, employee_user_id: int):
        """
        Возвращает записи об образовании сотрудника.
        """
        query = text(
            """
            SELECT
                education_level,
                institution_name,
                faculty,
                specialization,
                start_date,
                end_date,
                graduation_year,
                is_current
            FROM education_records
            WHERE employee_user_id = :employee_user_id
            ORDER BY COALESCE(end_date, CURDATE()) DESC, start_date DESC, id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_diplomas(self, employee_user_id: int):
        """
        Возвращает дипломы сотрудника.
        """
        query = text(
            """
            SELECT
                ed.qualification_title,
                ed.diploma_series,
                ed.diploma_number,
                ed.honors_type,
                ed.issued_at,
                ed.original_filename
            FROM education_diplomas ed
            INNER JOIN education_records er
                ON er.id = ed.education_id
            WHERE er.employee_user_id = :employee_user_id
            ORDER BY COALESCE(ed.issued_at, er.end_date) DESC, ed.id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_work_experience_records(self, employee_user_id: int):
        """
        Возвращает опыт работы сотрудника.
        """
        query = text(
            """
            SELECT
                company_name,
                position_title,
                start_date,
                end_date,
                is_current,
                responsibilities,
                achievements
            FROM work_experience_records
            WHERE employee_user_id = :employee_user_id
            ORDER BY is_current DESC, COALESCE(end_date, CURDATE()) DESC, start_date DESC, id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_competition_participation(self, employee_user_id: int):
        """
        Возвращает участие сотрудника в соревнованиях.
        """
        query = text(
            """
            SELECT
                c.name AS competition_name,
                c.competition_level AS competition_level,
                ecr.event_date AS event_date
            FROM employee_competition_results ecr
            INNER JOIN competitions c
                ON c.id = ecr.competition_id
            WHERE ecr.employee_user_id = :employee_user_id
            ORDER BY COALESCE(ecr.event_date, CURDATE()) DESC, ecr.id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_competition_awards(self, employee_user_id: int):
        """
        Возвращает призовые места / награды сотрудника в соревнованиях.
        """
        query = text(
            """
            SELECT
                c.name AS competition_name,
                cp.name AS placement_name,
                cp.rank_value AS rank_value,
                ecr.award_title AS award_title,
                ecr.event_date AS event_date
            FROM employee_competition_results ecr
            INNER JOIN competitions c
                ON c.id = ecr.competition_id
            LEFT JOIN competition_placements cp
                ON cp.id = ecr.placement_id
            WHERE ecr.employee_user_id = :employee_user_id
              AND (ecr.placement_id IS NOT NULL OR ecr.award_title IS NOT NULL)
            ORDER BY COALESCE(ecr.event_date, CURDATE()) DESC, COALESCE(cp.rank_value, 999) ASC, ecr.id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_employee_skills(self, employee_user_id: int):
        """
        Возвращает личные навыки сотрудника.
        """
        query = text(
            """
            SELECT
                s.name AS skill_name,
                es.proficiency_level AS proficiency_level,
                es.years_experience AS years_experience
            FROM employee_skills es
            INNER JOIN skills s
                ON s.id = es.skill_id
            WHERE es.employee_user_id = :employee_user_id
            ORDER BY s.name ASC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_additional_courses(self, employee_user_id: int):
        """
        Возвращает дополнительные курсы сотрудника.
        """
        query = text(
            """
            SELECT
                COALESCE(acc.name, eac.course_name_override) AS course_name,
                COALESCE(acc.provider, eac.provider_override) AS provider_name,
                eac.completed_at AS completed_at,
                eac.status AS status
            FROM employee_additional_courses eac
            LEFT JOIN additional_courses_catalog acc
                ON acc.id = eac.course_id
            WHERE eac.employee_user_id = :employee_user_id
            ORDER BY COALESCE(eac.completed_at, eac.started_at) DESC, eac.id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()

    def get_qualification_courses(self, employee_user_id: int):
        """
        Возвращает курсы повышения квалификации сотрудника.
        """
        query = text(
            """
            SELECT
                COALESCE(qcc.name, eqc.course_name_override) AS course_name,
                COALESCE(qcc.provider, eqc.provider_override) AS provider_name,
                eqc.completed_at AS completed_at,
                eqc.valid_until AS valid_until,
                eqc.status AS status
            FROM employee_qualification_courses eqc
            LEFT JOIN qualification_courses_catalog qcc
                ON qcc.id = eqc.course_id
            WHERE eqc.employee_user_id = :employee_user_id
            ORDER BY COALESCE(eqc.completed_at, eqc.started_at) DESC, eqc.id DESC
            """
        )

        return self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().all()