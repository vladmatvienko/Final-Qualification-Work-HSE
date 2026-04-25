from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.candidate_search_models import (
    CandidateSearchDocument,
    CandidateSearchIndexSource,
)


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CandidateSearchRepository:
    """
    Repository поискового индекса кандидатов.
    """

    def _quote_identifier(self, name: str) -> str:
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"Некорректный SQL identifier: {name}")
        return f"`{name}`"

    def _fetch_rows(
        self,
        session: Session,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = session.execute(text(query), params or {}).mappings().all()
        return [dict(row) for row in rows]

    def _table_exists(self, session: Session, table_name: str) -> bool:
        """
        Проверяет, существует ли таблица в текущей БД.
        """
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            """
        )

        row = session.execute(
            query,
            {"table_name": table_name},
        ).mappings().first()

        if not row:
            return False

        row_dict = dict(row)

        value = (
            row_dict.get("total_count")
            or row_dict.get("TOTAL_COUNT")
            or row_dict.get("COUNT(*)")
        )

        if value is None and row_dict:
            value = next(iter(row_dict.values()))

        return int(value or 0) > 0

    def _get_table_columns(self, session: Session, table_name: str) -> set[str]:
        """
        Возвращает множество имён колонок таблицы.
        """
        query = text(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            """
        )

        rows = session.execute(
            query,
            {"table_name": table_name},
        ).mappings().all()

        columns: set[str] = set()

        for row in rows:
            row_dict = dict(row)

            value = (
                row_dict.get("column_name")
                or row_dict.get("COLUMN_NAME")
                or row_dict.get("Column_name")
            )

            if value is None and row_dict:
                value = next(iter(row_dict.values()))

            if value is not None:
                columns.add(str(value))

        return columns

    def _resolve_order_by_column(self, session: Session, table_name: str) -> str | None:
        columns = self._get_table_columns(session, table_name)

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
        session: Session,
        table_name: str,
    ) -> dict[int, list[dict[str, Any]]]:
        if not self._table_exists(session, table_name):
            return {}

        quoted_table = self._quote_identifier(table_name)
        order_by_column = self._resolve_order_by_column(session, table_name)

        query = f"SELECT * FROM {quoted_table}"
        if order_by_column:
            query += f" ORDER BY {self._quote_identifier(order_by_column)}"

        rows = self._fetch_rows(session, query)

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = self._resolve_owner_id(row)
            if owner_id is None:
                continue
            grouped.setdefault(owner_id, []).append(row)

        return grouped

    def _load_employee_rows(self, session: Session) -> list[dict[str, Any]]:
        return self._fetch_rows(
            session,
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

    def _load_diploma_group(self, session: Session) -> dict[int, list[dict[str, Any]]]:
        if not self._table_exists(session, "education_records"):
            return {}
        if not self._table_exists(session, "education_diplomas"):
            return {}

        diploma_columns = self._get_table_columns(session, "education_diplomas")

        qualification_expr = (
            "ed.qualification_title" if "qualification_title" in diploma_columns else
            "ed.title" if "title" in diploma_columns else
            "NULL"
        )
        honors_expr = "ed.honors_type" if "honors_type" in diploma_columns else "NULL"
        issued_expr = "ed.issued_at" if "issued_at" in diploma_columns else "ed.issue_date" if "issue_date" in diploma_columns else "NULL"

        rows = self._fetch_rows(
            session,
            f"""
            SELECT
                er.employee_user_id AS employee_user_id,
                ed.id AS diploma_id,
                {qualification_expr} AS qualification_title,
                {honors_expr} AS honors_type,
                {issued_expr} AS issued_at
            FROM education_diplomas ed
            INNER JOIN education_records er
                ON er.id = ed.education_id
            ORDER BY ed.id ASC
            """,
        )

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is not None:
                grouped.setdefault(int(owner_id), []).append(row)

        return grouped

    def _load_skill_group(self, session: Session) -> dict[int, list[dict[str, Any]]]:
        if not self._table_exists(session, "employee_skills"):
            return {}
        if not self._table_exists(session, "skills"):
            return self._group_rows_by_owner(session, "employee_skills")

        skill_columns = self._get_table_columns(session, "employee_skills")
        prof_expr = "es.proficiency_level" if "proficiency_level" in skill_columns else "NULL"
        years_expr = "es.years_experience" if "years_experience" in skill_columns else "NULL"

        rows = self._fetch_rows(
            session,
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
            if owner_id is not None:
                grouped.setdefault(int(owner_id), []).append(row)

        return grouped

    def _load_additional_courses_group(self, session: Session) -> dict[int, list[dict[str, Any]]]:
        if not self._table_exists(session, "employee_additional_courses"):
            return {}

        course_columns = self._get_table_columns(session, "employee_additional_courses")
        has_catalog = self._table_exists(session, "additional_courses_catalog")

        if not has_catalog:
            return self._group_rows_by_owner(session, "employee_additional_courses")

        rows = self._fetch_rows(
            session,
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

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is not None:
                grouped.setdefault(int(owner_id), []).append(row)

        return grouped

    def _load_qualification_courses_group(self, session: Session) -> dict[int, list[dict[str, Any]]]:
        if not self._table_exists(session, "employee_qualification_courses"):
            return {}

        course_columns = self._get_table_columns(session, "employee_qualification_courses")
        has_catalog = self._table_exists(session, "qualification_courses_catalog")

        if not has_catalog:
            return self._group_rows_by_owner(session, "employee_qualification_courses")

        rows = self._fetch_rows(
            session,
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

        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            owner_id = row.get("employee_user_id")
            if owner_id is not None:
                grouped.setdefault(int(owner_id), []).append(row)

        return grouped

    def fetch_candidate_sources(self) -> list[CandidateSearchIndexSource]:
        with get_db_session() as session:
            employee_rows = self._load_employee_rows(session)

            profile_group = self._group_rows_by_owner(session, "employee_profiles")
            education_group = self._group_rows_by_owner(session, "education_records")
            diploma_group = self._load_diploma_group(session)
            work_group = self._group_rows_by_owner(session, "work_experience_records")
            competition_group = self._group_rows_by_owner(session, "employee_competition_results")
            skill_group = self._load_skill_group(session)
            additional_courses_group = self._load_additional_courses_group(session)
            qualification_courses_group = self._load_qualification_courses_group(session)

            sources: list[CandidateSearchIndexSource] = []

            for employee_row in employee_rows:
                employee_id = int(employee_row["id"])
                profile_rows = profile_group.get(employee_id, [])

                sources.append(
                    CandidateSearchIndexSource(
                        employee_user_id=employee_id,
                        full_name=str(employee_row.get("full_name") or f"Сотрудник #{employee_id}"),
                        profile_data=profile_rows[0] if profile_rows else {},
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
        for source in self.fetch_candidate_sources():
            if source.employee_user_id == int(employee_user_id):
                return source
        return None

    def upsert_candidate_documents(self, documents: list[CandidateSearchDocument]) -> None:
        if not documents:
            return

        query = text(
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
                :employee_user_id,
                :anonymous_code,
                :source_hash,
                :profile_text,
                :skills_text,
                :experience_text,
                :education_text,
                :courses_text,
                :aggregated_text,
                :structured_payload,
                NOW()
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
            """
        )

        with get_db_session() as session:
            for document in documents:
                session.execute(
                    query,
                    {
                        "employee_user_id": document.employee_user_id,
                        "anonymous_code": document.anonymous_code,
                        "source_hash": document.source_hash,
                        "profile_text": document.profile_text,
                        "skills_text": document.skills_text,
                        "experience_text": document.experience_text,
                        "education_text": document.education_text,
                        "courses_text": document.courses_text,
                        "aggregated_text": document.aggregated_text,
                        "structured_payload": json.dumps(document.structured_payload, ensure_ascii=False),
                    },
                )

    def load_candidate_documents(self) -> list[CandidateSearchDocument]:
        with get_db_session() as session:
            if not self._table_exists(session, "candidate_search_documents"):
                return []

            rows = self._fetch_rows(
                session,
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
                    full_name=str(structured_payload.get("full_name") or row["anonymous_code"]),
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