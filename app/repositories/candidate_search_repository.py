from __future__ import annotations

import json
from typing import Any

from app.db.mysql_connection import get_connection
from app.models.candidate_search_models import (
    CandidateSearchDocument,
    CandidateSearchIndexSource,
)


class CandidateSearchRepository:
    """
    Repository поискового индекса кандидатов.
    """

    def _fetch_rows(
        self,
        connection,
        query: str,
        params: tuple | None = None,
    ) -> list[dict[str, Any]]:
        """
        Универсальный helper для SELECT-запросов.
        """
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            return rows or []
        finally:
            cursor.close()

    def _table_exists(self, connection, table_name: str) -> bool:
        """
        Проверяет, существует ли таблица в текущей БД.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                """,
                (table_name,),
            )
            count = cursor.fetchone()[0]
            return int(count) > 0
        finally:
            cursor.close()

    def _get_table_columns(self, connection, table_name: str) -> set[str]:
        """
        Возвращает множество имён колонок таблицы.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                """,
                (table_name,),
            )
            rows = cursor.fetchall() or []
            return {str(row[0]) for row in rows}
        finally:
            cursor.close()

    def _resolve_order_by_column(self, connection, table_name: str) -> str | None:
        """
        Пытается подобрать "разумную" колонку для ORDER BY.
        """
        columns = self._get_table_columns(connection, table_name)
        for candidate in (
            "id",
            "employee_user_id",
            "user_id",
            "employee_id",
            "created_at",
            "updated_at",
        ):
            if candidate in columns:
                return candidate
        return None

    def _resolve_owner_id(self, row: dict[str, Any]) -> int | None:
        """
        Пытается извлечь employee/user owner id из строки.
        """
        for key in ("employee_user_id", "user_id", "employee_id"):
            value = row.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _group_rows_by_owner(
        self,
        connection,
        table_name: str,
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Универсально загружает таблицу и группирует строки по владельцу.
        """
        if not self._table_exists(connection, table_name):
            return {}

        order_by_column = self._resolve_order_by_column(connection, table_name)
        query = f"SELECT * FROM {table_name}"
        if order_by_column:
            query += f" ORDER BY {order_by_column}"

        rows = self._fetch_rows(connection, query)

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = self._resolve_owner_id(row)
            if owner_id is None:
                continue
            grouped.setdefault(owner_id, []).append(row)
        return grouped

    def _load_employee_rows(self, connection) -> list[dict[str, Any]]:
        """
        Загружает активных сотрудников, которые участвуют в HR-поиске.
        """
        return self._fetch_rows(
            connection,
            """
            SELECT
                u.id AS id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS full_name
            FROM users u
            INNER JOIN roles r
                ON r.id = u.role_id
            WHERE UPPER(r.code) = 'EMPLOYEE'
              AND u.is_active = TRUE
            ORDER BY full_name ASC, u.id ASC
            """,
        )

    def _load_diploma_group(self, connection) -> dict[int, list[dict[str, Any]]]:
        """
        Загружает дипломы сотрудников с join к education_records.
        """
        if not self._table_exists(connection, "education_records"):
            return {}
        if not self._table_exists(connection, "education_diplomas"):
            return {}

        diploma_columns = self._get_table_columns(connection, "education_diplomas")

        qualification_expr = (
            "ed.qualification_title" if "qualification_title" in diploma_columns else
            "ed.title" if "title" in diploma_columns else
            "NULL"
        )
        series_expr = "ed.diploma_series" if "diploma_series" in diploma_columns else "ed.series" if "series" in diploma_columns else "NULL"
        number_expr = "ed.diploma_number" if "diploma_number" in diploma_columns else "ed.number" if "number" in diploma_columns else "NULL"
        honors_expr = "ed.honors_type" if "honors_type" in diploma_columns else "NULL"
        issued_expr = "ed.issued_at" if "issued_at" in diploma_columns else "ed.issue_date" if "issue_date" in diploma_columns else "NULL"
        filename_expr = "ed.original_filename" if "original_filename" in diploma_columns else "NULL"

        rows = self._fetch_rows(
            connection,
            f"""
            SELECT
                er.employee_user_id AS employee_user_id,
                ed.id AS diploma_id,
                {qualification_expr} AS qualification_title,
                {series_expr} AS diploma_series,
                {number_expr} AS diploma_number,
                {honors_expr} AS honors_type,
                {issued_expr} AS issued_at,
                {filename_expr} AS original_filename
            FROM education_diplomas ed
            INNER JOIN education_records er
                ON er.id = ed.education_id
            ORDER BY ed.id ASC
            """,
        )

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is None:
                continue
            grouped.setdefault(int(owner_id), []).append(row)
        return grouped

    def _load_skill_group(self, connection) -> dict[int, list[dict[str, Any]]]:
        """
        Загружает навыки сотрудников.
        """
        if not self._table_exists(connection, "employee_skills"):
            return {}
        if not self._table_exists(connection, "skills"):
            return self._group_rows_by_owner(connection, "employee_skills")

        skill_columns = self._get_table_columns(connection, "employee_skills")
        prof_expr = "es.proficiency_level" if "proficiency_level" in skill_columns else "NULL"
        years_expr = "es.years_experience" if "years_experience" in skill_columns else "NULL"

        rows = self._fetch_rows(
            connection,
            f"""
            SELECT
                es.employee_user_id AS employee_user_id,
                es.id AS employee_skill_id,
                es.skill_id AS skill_id,
                {prof_expr} AS proficiency_level,
                {years_expr} AS years_experience,
                s.name AS skill_name
            FROM employee_skills es
            INNER JOIN skills s
                ON s.id = es.skill_id
            ORDER BY es.employee_user_id ASC, s.name ASC
            """,
        )

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is None:
                continue
            grouped.setdefault(int(owner_id), []).append(row)
        return grouped

    def _load_additional_courses_group(self, connection) -> dict[int, list[dict[str, Any]]]:
        """
        Загружает дополнительные курсы сотрудников.
        """
        if not self._table_exists(connection, "employee_additional_courses"):
            return {}

        course_columns = self._get_table_columns(connection, "employee_additional_courses")
        has_catalog = self._table_exists(connection, "additional_courses_catalog")

        if has_catalog:
            rows = self._fetch_rows(
                connection,
                f"""
                SELECT
                    eac.employee_user_id AS employee_user_id,
                    COALESCE(acc.name, eac.course_name_override) AS course_name,
                    COALESCE(acc.provider, eac.provider_override) AS provider_name,
                    {('eac.completed_at' if 'completed_at' in course_columns else 'NULL')} AS completed_at,
                    {('eac.status' if 'status' in course_columns else 'NULL')} AS status
                FROM employee_additional_courses eac
                LEFT JOIN additional_courses_catalog acc
                    ON acc.id = eac.course_id
                ORDER BY eac.employee_user_id ASC, COALESCE(eac.completed_at, eac.started_at) DESC, eac.id DESC
                """,
            )
        else:
            rows = self._group_rows_by_owner(connection, "employee_additional_courses")
            return rows

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is None:
                continue
            grouped.setdefault(int(owner_id), []).append(row)
        return grouped

    def _load_qualification_courses_group(self, connection) -> dict[int, list[dict[str, Any]]]:
        """
        Загружает курсы повышения квалификации сотрудников.
        """
        if not self._table_exists(connection, "employee_qualification_courses"):
            return {}

        course_columns = self._get_table_columns(connection, "employee_qualification_courses")
        has_catalog = self._table_exists(connection, "qualification_courses_catalog")

        if has_catalog:
            rows = self._fetch_rows(
                connection,
                f"""
                SELECT
                    eqc.employee_user_id AS employee_user_id,
                    COALESCE(qcc.name, eqc.course_name_override) AS course_name,
                    COALESCE(qcc.provider, eqc.provider_override) AS provider_name,
                    {('eqc.completed_at' if 'completed_at' in course_columns else 'NULL')} AS completed_at,
                    {('eqc.valid_until' if 'valid_until' in course_columns else 'NULL')} AS valid_until,
                    {('eqc.status' if 'status' in course_columns else 'NULL')} AS status
                FROM employee_qualification_courses eqc
                LEFT JOIN qualification_courses_catalog qcc
                    ON qcc.id = eqc.course_id
                ORDER BY eqc.employee_user_id ASC, COALESCE(eqc.completed_at, eqc.started_at) DESC, eqc.id DESC
                """,
            )
        else:
            rows = self._group_rows_by_owner(connection, "employee_qualification_courses")
            return rows

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is None:
                continue
            grouped.setdefault(int(owner_id), []).append(row)
        return grouped

    def fetch_candidate_sources(self) -> list[CandidateSearchIndexSource]:
        """
        Собирает полный список "источников" для построения поискового индекса кандидатов.
        """
        with get_connection() as connection:
            employee_rows = self._load_employee_rows(connection)

            profile_group = self._group_rows_by_owner(connection, "employee_profiles")
            education_group = self._group_rows_by_owner(connection, "education_records")
            diploma_group = self._load_diploma_group(connection)
            work_group = self._group_rows_by_owner(connection, "work_experience_records")
            competition_group = self._group_rows_by_owner(connection, "employee_competition_results")
            skill_group = self._load_skill_group(connection)
            additional_courses_group = self._load_additional_courses_group(connection)
            qualification_courses_group = self._load_qualification_courses_group(connection)

            sources: list[CandidateSearchIndexSource] = []
            for employee_row in employee_rows:
                employee_id = int(employee_row["id"])
                profile_rows = profile_group.get(employee_id, [])

                profile_data = profile_rows[0] if profile_rows else {}

                sources.append(
                    CandidateSearchIndexSource(
                        employee_user_id=employee_id,
                        full_name=str(employee_row.get("full_name") or f"Сотрудник #{employee_id}"),
                        profile_data=profile_data,
                        education_rows=education_group.get(employee_id, []),
                        diploma_rows=diploma_group.get(employee_id, []),
                        work_experience_rows=work_group.get(employee_id, []),
                        competition_rows=competition_group.get(employee_id, []),

                        award_rows=[],

                        skill_rows=skill_group.get(employee_id, []),
                        additional_course_rows=additional_courses_group.get(employee_id, []),
                        qualification_course_rows=qualification_courses_group.get(employee_id, []),
                    )
                )

            return sources

    def fetch_candidate_source_by_employee_id(self, employee_user_id: int) -> CandidateSearchIndexSource | None:
        """
        Возвращает source только для одного сотрудника.
        """
        for source in self.fetch_candidate_sources():
            if source.employee_user_id == int(employee_user_id):
                return source
        return None

    def upsert_candidate_documents(self, documents: list[CandidateSearchDocument]) -> None:
        """
        Сохраняет подготовленные search-документы в candidate_search_documents.
        """
        if not documents:
            return

        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                for document in documents:
                    cursor.execute(
                        """
                        INSERT INTO candidate_search_documents (
                            employee_user_id,
                            anonymous_code,
                            source_hash,
                            profile_text,
                            skills_text,
                            experience_text,
                            education_text,
                            courses_text,
                            aggregated_text,
                            structured_payload,
                            last_indexed_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                        ON DUPLICATE KEY UPDATE
                            anonymous_code = VALUES(anonymous_code),
                            source_hash = VALUES(source_hash),
                            profile_text = VALUES(profile_text),
                            skills_text = VALUES(skills_text),
                            experience_text = VALUES(experience_text),
                            education_text = VALUES(education_text),
                            courses_text = VALUES(courses_text),
                            aggregated_text = VALUES(aggregated_text),
                            structured_payload = VALUES(structured_payload),
                            last_indexed_at = NOW(),
                            updated_at = NOW()
                        """,
                        (
                            document.employee_user_id,
                            document.anonymous_code,
                            document.source_hash,
                            document.profile_text,
                            document.skills_text,
                            document.experience_text,
                            document.education_text,
                            document.courses_text,
                            document.aggregated_text,
                            json.dumps(document.structured_payload, ensure_ascii=False),
                        ),
                    )
                connection.commit()
            finally:
                cursor.close()

    def load_candidate_documents(self) -> list[CandidateSearchDocument]:
        """
        Загружает уже сохранённые search-документы из candidate_search_documents.
        """
        with get_connection() as connection:
            if not self._table_exists(connection, "candidate_search_documents"):
                return []

            rows = self._fetch_rows(
                connection,
                """
                SELECT
                    employee_user_id,
                    anonymous_code,
                    source_hash,
                    profile_text,
                    skills_text,
                    experience_text,
                    education_text,
                    courses_text,
                    aggregated_text,
                    structured_payload
                FROM candidate_search_documents
                ORDER BY updated_at DESC, employee_user_id ASC
                """,
            )

        documents: list[CandidateSearchDocument] = []
        for row in rows:
            raw_payload = row.get("structured_payload") or "{}"

            structured_payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload

            documents.append(
                CandidateSearchDocument(
                    employee_user_id=int(row["employee_user_id"]),
                    anonymous_code=str(row["anonymous_code"]),
                    full_name=str(structured_payload.get("full_name") or ""),
                    source_hash=str(row["source_hash"]),
                    profile_text=str(row.get("profile_text") or ""),
                    skills_text=str(row.get("skills_text") or ""),
                    experience_text=str(row.get("experience_text") or ""),
                    education_text=str(row.get("education_text") or ""),
                    courses_text=str(row.get("courses_text") or ""),
                    aggregated_text=str(row.get("aggregated_text") or ""),
                    structured_payload=structured_payload,
                )
            )
        return documents
