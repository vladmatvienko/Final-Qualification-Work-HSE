from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time
from decimal import Decimal
from html import escape
from typing import Any

from app.models.candidate_search_models import (
    CandidateSearchDocument,
    CandidateSearchIndexSource,
)


class HRResumeDocumentBuilder:
    """
    Builder для анонимных личных данных
    """

    # =========================================================
    # Базовые безопасные хелперы
    # =========================================================
    def _safe_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _non_empty(self, value: Any) -> bool:
        return bool(self._safe_text(value))

    def _to_list(self, value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _as_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _normalize_text(self, text: str) -> str:
        """
        Нормализует текст перед хешированием и сборкой индекса.
        """
        return " ".join(self._safe_text(text).split())

    def _join_parts(self, parts: list[str], separator: str = " | ") -> str:
        cleaned = [self._normalize_text(part) for part in parts if self._non_empty(part)]
        return separator.join(part for part in cleaned if part)

    def _render_empty(self, text: str = "Нет данных") -> str:
        return f'<div style="color:#6C7FA5; line-height:1.5;">{escape(text)}</div>'

    # =========================================================
    # JSON-safe сериализация
    # =========================================================
    def _to_json_safe(self, value: Any) -> Any:
        """
        Рекурсивно приводит объект к JSON-совместимому виду.
        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, (date, datetime, time)):
            return value.isoformat()

        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return repr(value)

        if isinstance(value, dict):
            return {
                str(key): self._to_json_safe(val)
                for key, val in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [self._to_json_safe(item) for item in value]

        return str(value)

    # =========================================================
    # Анонимизация
    # =========================================================
    def _build_anonymous_code(self, source: CandidateSearchIndexSource) -> str:
        """
        Строит анонимный код кандидата.
        """
        salt = os.getenv("ANONYMIZATION_SALT", "elbrus-local-anonymization-salt").strip()
        raw = f"{salt}:employee:{source.employee_user_id}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
        return f"CAND-{digest}"

    # =========================================================
    # Извлечение профессионального профиля
    # =========================================================
    def _extract_profile_text(self, source: CandidateSearchIndexSource) -> str:
        """
        Собирает краткий профессиональный профиль из profile_data.
        """
        profile = self._as_dict(source.profile_data)

        parts: list[str] = []

        current_position = self._safe_text(
            profile.get("current_position")
            or profile.get("position")
            or profile.get("job_title")
            or profile.get("specialization")
            or profile.get("target_position")
        )
        if current_position:
            parts.append(f"Текущее направление: {current_position}")

        department = self._safe_text(
            profile.get("department")
            or profile.get("division")
            or profile.get("team_name")
        )
        if department:
            parts.append(f"Подразделение: {department}")

        summary = self._safe_text(
            profile.get("summary")
            or profile.get("about_work")
            or profile.get("professional_summary")
            or profile.get("about")
        )
        if summary:
            parts.append(summary)

        city = self._safe_text(profile.get("city"))
        if city:
            parts.append(f"Локация: {city}")

        return self._join_parts(parts)

    # =========================================================
    # Навыки
    # =========================================================
    def _extract_skill_items(self, source: CandidateSearchIndexSource) -> list[str]:
        skill_items: list[str] = []

        for row in self._to_list(source.skill_rows):
            if not isinstance(row, dict):
                continue

            skill_name = self._safe_text(
                row.get("skill_name")
                or row.get("name")
                or row.get("title")
                or row.get("competency_name")
            )
            if skill_name:
                skill_items.append(skill_name)

        profile = self._as_dict(source.profile_data)
        fallback_skills = self._safe_text(
            profile.get("skills")
            or profile.get("key_skills")
            or profile.get("stack")
        )

        if not skill_items and fallback_skills:
            raw_parts = (
                fallback_skills.replace(";", ",")
                .replace("|", ",")
                .split(",")
            )
            skill_items = [self._safe_text(part) for part in raw_parts if self._non_empty(part)]

        seen: set[str] = set()
        deduplicated: list[str] = []
        for item in skill_items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                deduplicated.append(item)

        return deduplicated

    def _extract_skills_text(self, source: CandidateSearchIndexSource) -> str:
        skill_items = self._extract_skill_items(source)
        if not skill_items:
            return "Нет явных совпадений по навыкам"
        return self._join_parts(skill_items)

    # =========================================================
    # Опыт работы
    # =========================================================
    def _extract_experience_items(self, source: CandidateSearchIndexSource) -> list[str]:
        items: list[str] = []

        for row in self._to_list(source.work_experience_rows):
            if not isinstance(row, dict):
                continue

            employer = self._safe_text(
                row.get("company_name")
                or row.get("employer_name")
                or row.get("organization_name")
                or row.get("workplace")
            )
            position = self._safe_text(
                row.get("position")
                or row.get("job_title")
                or row.get("role_name")
            )
            date_from = self._safe_text(
                row.get("start_date")
                or row.get("date_from")
                or row.get("worked_from")
            )
            date_to = self._safe_text(
                row.get("end_date")
                or row.get("date_to")
                or row.get("worked_to")
            )
            responsibilities = self._safe_text(
                row.get("responsibilities")
                or row.get("description")
                or row.get("result_text")
            )

            line_parts: list[str] = []
            if employer:
                line_parts.append(employer)
            if date_from or date_to:
                line_parts.append(f"{date_from or '?'} — {date_to or 'настоящее время'}")
            if position:
                line_parts.append(position)
            if responsibilities:
                line_parts.append(responsibilities)

            line = " • ".join(part for part in line_parts if part)
            if line:
                items.append(line)

        return items

    def _extract_experience_text(self, source: CandidateSearchIndexSource) -> str:
        items = self._extract_experience_items(source)
        return self._join_parts(items)

    # =========================================================
    # Образование
    # =========================================================
    def _extract_education_items(self, source: CandidateSearchIndexSource) -> list[str]:
        items: list[str] = []

        for row in self._to_list(source.education_rows):
            if not isinstance(row, dict):
                continue

            institution = self._safe_text(
                row.get("institution_name")
                or row.get("university_name")
                or row.get("organization_name")
                or row.get("education_place")
            )
            degree = self._safe_text(
                row.get("degree")
                or row.get("education_level")
                or row.get("qualification")
            )
            specialty = self._safe_text(
                row.get("specialty")
                or row.get("specialization")
                or row.get("faculty")
            )
            graduation = self._safe_text(
                row.get("graduation_year")
                or row.get("end_date")
                or row.get("date_to")
            )

            line_parts: list[str] = []
            if institution:
                line_parts.append(institution)
            if degree:
                line_parts.append(degree)
            if specialty:
                line_parts.append(specialty)
            if graduation:
                line_parts.append(graduation)

            line = " • ".join(part for part in line_parts if part)
            if line:
                items.append(line)

        return items

    def _extract_education_text(self, source: CandidateSearchIndexSource) -> str:
        return self._join_parts(self._extract_education_items(source))

    # =========================================================
    # Дипломы
    # =========================================================
    def _extract_diploma_items(self, source: CandidateSearchIndexSource) -> list[str]:
        """
        Дипломы для HR-профиля без серии, номера, имени файла и иных deanonymizing-атрибутов.
        """
        items: list[str] = []

        for row in self._to_list(source.diploma_rows):
            if not isinstance(row, dict):
                continue

            qualification_title = self._safe_text(
                row.get("qualification_title")
                or row.get("diploma_name")
                or row.get("title")
            )
            honors_type = self._safe_text(row.get("honors_type"))
            issued_year = self._safe_year(
                row.get("issued_at")
                or row.get("issue_date")
            )

            line_parts: list[str] = []
            if qualification_title:
                line_parts.append(qualification_title)
            if honors_type:
                line_parts.append(f"Отличие: {honors_type}")
            if issued_year:
                line_parts.append(f"Год выдачи: {issued_year}")

            line = " • ".join(part for part in line_parts if part)
            if line:
                items.append(line)

        return items

    # =========================================================
    # Курсы и квалификация
    # =========================================================
    def _extract_course_items(self, source: CandidateSearchIndexSource) -> list[str]:
        items: list[str] = []

        all_rows = self._to_list(source.additional_course_rows) + self._to_list(source.qualification_course_rows)

        for row in all_rows:
            if not isinstance(row, dict):
                continue

            course_name = self._safe_text(
                row.get("course_name")
                or row.get("program_name")
                or row.get("title")
            )
            provider = self._safe_text(
                row.get("provider_name")
                or row.get("organization_name")
            )
            completed_at = self._safe_text(row.get("completed_at"))
            valid_until = self._safe_text(
                row.get("valid_until")
                or row.get("end_date")
                or row.get("date_to")
            )
            status = self._safe_text(row.get("status"))

            line_parts: list[str] = []
            if course_name:
                line_parts.append(course_name)
            if provider:
                line_parts.append(provider)
            if completed_at:
                line_parts.append(f"Завершён: {completed_at}")
            if valid_until:
                line_parts.append(f"Действует до: {valid_until}")
            if status:
                line_parts.append(f"Статус: {status}")

            line = " • ".join(part for part in line_parts if part)
            if line:
                items.append(line)

        return items

    def _extract_courses_text(self, source: CandidateSearchIndexSource) -> str:
        return self._join_parts(self._extract_course_items(source))

    # =========================================================
    # Structured payload
    # =========================================================
    def _build_structured_payload(
        self,
        source: CandidateSearchIndexSource,
        anonymous_code: str,
        profile_text: str,
        skills_text: str,
        experience_text: str,
        education_text: str,
        courses_text: str,
    ) -> dict[str, Any]:
        profile = self._as_dict(source.profile_data)

        sanitized_profile = self._sanitize_profile_data(profile)

        payload = {
            "employee_user_id": source.employee_user_id,
            "anonymous_code": anonymous_code,
            "full_name": anonymous_code,

            "current_position": self._safe_text(
                sanitized_profile.get("current_position")
                or sanitized_profile.get("position")
                or sanitized_profile.get("job_title")
                or sanitized_profile.get("specialization")
            ),
            "summary": self._safe_text(
                sanitized_profile.get("summary")
                or sanitized_profile.get("about_work")
                or sanitized_profile.get("professional_summary")
            ),

            "profile_text": profile_text,
            "skills_text": skills_text,
            "experience_text": experience_text,
            "education_text": education_text,
            "courses_text": courses_text,

            "profile_data": sanitized_profile,

            "skill_rows": self._sanitize_rows(
                self._to_list(source.skill_rows),
                {
                    "skill_name",
                    "name",
                    "title",
                    "competency_name",
                    "proficiency_level",
                    "years_experience",
                },
            ),
            "work_experience_rows": self._sanitize_rows(
                self._to_list(source.work_experience_rows),
                {
                    "position",
                    "position_title",
                    "job_title",
                    "role_name",
                    "start_date",
                    "end_date",
                    "date_from",
                    "date_to",
                    "responsibilities",
                    "description",
                    "result_text",
                },
            ),
            "education_rows": self._sanitize_rows(
                self._to_list(source.education_rows),
                {
                    "education_level",
                    "degree",
                    "qualification",
                    "specialty",
                    "specialization",
                    "faculty",
                    "graduation_year",
                    "end_date",
                    "date_to",
                },
            ),
            "diploma_rows": self._sanitize_rows(
                self._to_list(source.diploma_rows),
                {
                    "qualification_title",
                    "diploma_name",
                    "title",
                    "honors_type",
                    "issued_at",
                    "issue_date",
                },
            ),
            "additional_course_rows": self._sanitize_rows(
                self._to_list(source.additional_course_rows),
                {
                    "course_name",
                    "program_name",
                    "title",
                    "provider_name",
                    "organization_name",
                    "completed_at",
                    "status",
                },
            ),
            "qualification_course_rows": self._sanitize_rows(
                self._to_list(source.qualification_course_rows),
                {
                    "course_name",
                    "program_name",
                    "title",
                    "provider_name",
                    "organization_name",
                    "completed_at",
                    "valid_until",
                    "end_date",
                    "date_to",
                    "status",
                },
            ),
        }

        return self._to_json_safe(payload)

    # =========================================================
    # Индексные документы
    # =========================================================
    def build_document(self, source: CandidateSearchIndexSource) -> CandidateSearchDocument:
        """
        Строит один CandidateSearchDocument из одного source.
        """
        anonymous_code = self._build_anonymous_code(source)

        profile_text = self._extract_profile_text(source)
        skills_text = self._extract_skills_text(source)
        experience_text = self._extract_experience_text(source)
        education_text = self._extract_education_text(source)
        courses_text = self._extract_courses_text(source)

        structured_payload = self._build_structured_payload(
            source=source,
            anonymous_code=anonymous_code,
            profile_text=profile_text,
            skills_text=skills_text,
            experience_text=experience_text,
            education_text=education_text,
            courses_text=courses_text,
        )

        aggregated_text = "\n".join(
            part for part in [
                f"Анонимный код: {anonymous_code}",
                f"Профиль: {profile_text}" if profile_text else "",
                f"Навыки: {skills_text}" if skills_text else "",
                f"Опыт: {experience_text}" if experience_text else "",
                f"Образование: {education_text}" if education_text else "",
                f"Курсы: {courses_text}" if courses_text else "",
            ]
            if self._non_empty(part)
        )

        source_hash_payload = self._to_json_safe(
            {
                "employee_user_id": source.employee_user_id,
                "profile_text": profile_text,
                "skills_text": skills_text,
                "experience_text": experience_text,
                "education_text": education_text,
                "courses_text": courses_text,
                "profile_data": source.profile_data,
                "skill_rows": self._to_list(source.skill_rows),
                "work_experience_rows": self._to_list(source.work_experience_rows),
                "education_rows": self._to_list(source.education_rows),
                "diploma_rows": self._to_list(source.diploma_rows),
                "additional_course_rows": self._to_list(source.additional_course_rows),
                "qualification_course_rows": self._to_list(source.qualification_course_rows),
            }
        )

        source_hash = hashlib.sha256(
            json.dumps(source_hash_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return CandidateSearchDocument(
            employee_user_id=source.employee_user_id,
            anonymous_code=anonymous_code,
            full_name=anonymous_code,
            source_hash=source_hash,
            profile_text=profile_text,
            skills_text=skills_text,
            experience_text=experience_text,
            education_text=education_text,
            courses_text=courses_text,
            aggregated_text=aggregated_text,
            structured_payload=structured_payload,
        )

    def build_documents(self, sources: list[CandidateSearchIndexSource]) -> list[CandidateSearchDocument]:
        """
        Строит список индексных документов.
        """
        return [self.build_document(source) for source in sources]

    # =========================================================
    # HTML-представление анонимного профиля
    # =========================================================
    def _render_section(self, title: str, inner_html: str) -> str:
        return f"""
        <div style="margin-top: 28px;">
            <div style="
                font-size: 24px;
                font-weight: 700;
                color: #2D63D1;
                margin-bottom: 12px;
            ">
                {escape(title)}
            </div>
            {inner_html}
        </div>
        """

    def _render_bullets(self, items: list[str]) -> str:
        filtered = [self._safe_text(item) for item in items if self._non_empty(item)]
        if not filtered:
            return self._render_empty()

        rows = "".join(
            f'<li style="margin-bottom:10px; color:#24324D; line-height:1.55;">{escape(item)}</li>'
            for item in filtered
        )
        return f'<ul style="margin:0; padding-left:22px;">{rows}</ul>'

    def _extract_document(self, *args, **kwargs):
        if args and args[0] is not None:
            return args[0]

        for key in ("document", "candidate_document", "resume_document", "resume_doc"):
            value = kwargs.get(key)
            if value is not None:
                return value

        return None

    def _build_html(self, document: Any) -> str:
        """
        Строит HTML анонимизированного профиля кандидата.
        """
        if document is None:
            return """
            <div class="page-card">
                <div class="page-title">Профиль кандидата</div>
                <div style="color:#A94442;">Не удалось загрузить данные кандидата.</div>
            </div>
            """

        anonymous_code = self._safe_text(getattr(document, "anonymous_code", "")) or "Кандидат"
        structured_payload = getattr(document, "structured_payload", {}) or {}

        profile_text = self._safe_text(getattr(document, "profile_text", ""))
        skills_text = self._safe_text(getattr(document, "skills_text", ""))
        experience_text = self._safe_text(getattr(document, "experience_text", ""))
        education_text = self._safe_text(getattr(document, "education_text", ""))
        courses_text = self._safe_text(getattr(document, "courses_text", ""))

        professional_profile_parts: list[str] = []

        current_position = self._safe_text(
            structured_payload.get("current_position")
            or structured_payload.get("target_position")
        )
        if current_position:
            professional_profile_parts.append(f"Направление: {current_position}")

        summary = self._safe_text(structured_payload.get("summary"))
        if summary:
            professional_profile_parts.append(summary)

        if profile_text and profile_text not in professional_profile_parts:
            professional_profile_parts.append(profile_text)

        skill_items: list[str] = []
        for row in self._to_list(structured_payload.get("skill_rows")):
            if not isinstance(row, dict):
                continue
            skill_name = self._safe_text(
                row.get("skill_name")
                or row.get("name")
                or row.get("title")
                or row.get("competency_name")
            )
            if skill_name:
                skill_items.append(skill_name)

        if not skill_items and skills_text:
            raw_parts = (
                skills_text.replace("|", ",")
                .replace("•", ",")
                .replace(";", ",")
                .split(",")
            )
            skill_items = [self._safe_text(part) for part in raw_parts if self._non_empty(part)]

        experience_items: list[str] = []
        for row in self._to_list(structured_payload.get("work_experience_rows")):
            if not isinstance(row, dict):
                continue

            employer = self._safe_text(
                row.get("company_name")
                or row.get("employer_name")
                or row.get("organization_name")
                or row.get("workplace")
            )
            position = self._safe_text(
                row.get("position")
                or row.get("job_title")
                or row.get("role_name")
            )
            date_from = self._safe_text(
                row.get("start_date")
                or row.get("date_from")
                or row.get("worked_from")
            )
            date_to = self._safe_text(
                row.get("end_date")
                or row.get("date_to")
                or row.get("worked_to")
            )
            responsibilities = self._safe_text(
                row.get("responsibilities")
                or row.get("description")
                or row.get("result_text")
            )

            line_parts: list[str] = []
            if employer:
                line_parts.append(employer)
            if date_from or date_to:
                line_parts.append(f"{date_from or '?'} — {date_to or 'настоящее время'}")
            if position:
                line_parts.append(position)
            if responsibilities:
                line_parts.append(responsibilities)

            line = " • ".join(part for part in line_parts if part)
            if line:
                experience_items.append(line)

        if not experience_items and experience_text:
            experience_items = [part.strip() for part in experience_text.split("|") if part.strip()]

        education_items: list[str] = []
        for row in self._to_list(structured_payload.get("education_rows")):
            if not isinstance(row, dict):
                continue

            institution = self._safe_text(
                row.get("institution_name")
                or row.get("university_name")
                or row.get("organization_name")
                or row.get("education_place")
            )
            degree = self._safe_text(
                row.get("degree")
                or row.get("education_level")
                or row.get("qualification")
            )
            specialty = self._safe_text(
                row.get("specialty")
                or row.get("specialization")
                or row.get("faculty")
            )
            graduation = self._safe_text(
                row.get("graduation_year")
                or row.get("end_date")
                or row.get("date_to")
            )

            line_parts: list[str] = []
            if institution:
                line_parts.append(institution)
            if degree:
                line_parts.append(degree)
            if specialty:
                line_parts.append(specialty)
            if graduation:
                line_parts.append(graduation)

            line = " • ".join(part for part in line_parts if part)
            if line:
                education_items.append(line)

        if not education_items and education_text:
            education_items = [part.strip() for part in education_text.split("|") if part.strip()]

        diploma_items: list[str] = []
        for row in self._to_list(structured_payload.get("diploma_rows")):
            if not isinstance(row, dict):
                continue

            qualification_title = self._safe_text(
                row.get("qualification_title")
                or row.get("diploma_name")
                or row.get("title")
            )
            series = self._safe_text(row.get("diploma_series") or row.get("series"))
            number = self._safe_text(row.get("diploma_number") or row.get("number"))
            honors_type = self._safe_text(row.get("honors_type"))
            issued_at = self._safe_text(
                row.get("issued_at")
                or row.get("issue_date")
            )
            original_filename = self._safe_text(row.get("original_filename"))

            line_parts: list[str] = []
            if qualification_title:
                line_parts.append(qualification_title)
            if series:
                line_parts.append(f"Серия: {series}")
            if number:
                line_parts.append(f"Номер: {number}")
            if honors_type:
                line_parts.append(f"Отличие: {honors_type}")
            if issued_at:
                line_parts.append(f"Дата выдачи: {issued_at}")
            if original_filename:
                line_parts.append(f"Файл: {original_filename}")

            line = " • ".join(part for part in line_parts if part)
            if line:
                diploma_items.append(line)

        course_items: list[str] = []
        all_course_rows = self._to_list(structured_payload.get("additional_course_rows")) + self._to_list(
            structured_payload.get("qualification_course_rows")
        )

        for row in all_course_rows:
            if not isinstance(row, dict):
                continue

            course_name = self._safe_text(
                row.get("course_name")
                or row.get("program_name")
                or row.get("title")
            )
            provider = self._safe_text(
                row.get("provider_name")
                or row.get("organization_name")
            )
            completed_at = self._safe_text(row.get("completed_at"))
            valid_until = self._safe_text(
                row.get("valid_until")
                or row.get("end_date")
                or row.get("date_to")
            )
            status = self._safe_text(row.get("status"))

            line_parts: list[str] = []
            if course_name:
                line_parts.append(course_name)
            if provider:
                line_parts.append(provider)
            if completed_at:
                line_parts.append(f"Завершён: {completed_at}")
            if valid_until:
                line_parts.append(f"Действует до: {valid_until}")
            if status:
                line_parts.append(f"Статус: {status}")

            line = " • ".join(part for part in line_parts if part)
            if line:
                course_items.append(line)

        if not course_items and courses_text:
            course_items = [part.strip() for part in courses_text.split("|") if part.strip()]

        return f"""
        <div class="page-card" style="margin-top: 18px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
                <div>
                    <div style="
                        font-size: 32px;
                        font-weight: 800;
                        color: #2D63D1;
                        line-height: 1.2;
                        margin-bottom: 8px;
                    ">
                        Профиль кандидата
                    </div>
                    <div style="
                        color:#5B7096;
                        font-size:18px;
                        line-height:1.45;
                    ">
                        Анонимизированное резюме для HR-отбора. Личные данные скрыты.
                    </div>
                </div>
                <div style="
                    font-size: 18px;
                    color: #6C7FA5;
                    white-space: nowrap;
                    font-weight: 600;
                ">
                    {escape(anonymous_code)}
                </div>
            </div>

            {self._render_section("Профессиональный профиль", self._render_bullets(professional_profile_parts))}
            {self._render_section("Ключевые навыки", self._render_bullets(skill_items))}
            {self._render_section("Опыт работы", self._render_bullets(experience_items))}
            {self._render_section("Образование", self._render_bullets(education_items))}
            {self._render_section("Дипломы", self._render_bullets(diploma_items))}
            {self._render_section("Курсы и квалификация", self._render_bullets(course_items))}
        </div>
        """

    def build_resume_html(self, *args, **kwargs) -> str:
        document = self._extract_document(*args, **kwargs)
        return self._build_html(document)

    def build_full_resume_html(self, *args, **kwargs) -> str:
        document = self._extract_document(*args, **kwargs)
        return self._build_html(document)

    def build_html(self, *args, **kwargs) -> str:
        document = self._extract_document(*args, **kwargs)
        return self._build_html(document)

    def render_resume(self, *args, **kwargs) -> str:
        document = self._extract_document(*args, **kwargs)
        return self._build_html(document)

    def _safe_year(self, value: Any) -> str:
        raw = self._safe_text(value)
        if not raw:
            return ""

        if len(raw) >= 4 and raw[:4].isdigit():
            return raw[:4]

        return raw


    def _sanitize_rows(
        self,
        rows: list[dict[str, Any]],
        allowed_keys: set[str],
    ) -> list[dict[str, Any]]:
        """
        Оставляет только whitelisted-поля для HR payload.
        """
        sanitized_rows: list[dict[str, Any]] = []

        for row in self._to_list(rows):
            if not isinstance(row, dict):
                continue

            sanitized_row = {
                key: value
                for key, value in row.items()
                if key in allowed_keys and value is not None and self._safe_text(value)
            }

            if sanitized_row:
                sanitized_rows.append(sanitized_row)

        return sanitized_rows


    def _sanitize_profile_data(self, profile: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = {
            "current_position",
            "position",
            "job_title",
            "specialization",
            "target_position",
            "department",
            "division",
            "team_name",
            "summary",
            "about_work",
            "professional_summary",
            "skills",
            "key_skills",
            "stack",
        }

        return {
            key: value
            for key, value in profile.items()
            if key in allowed_keys and value is not None and self._safe_text(value)
        }