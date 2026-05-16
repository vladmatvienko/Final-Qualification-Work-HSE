"""
Semantic routing для автоматического выбора раздела резюме.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.services.hf_local_models import (
    get_hf_embeddings,
    get_hf_pair_scores,
    get_hf_single_embedding,
    get_hf_top_k,
)


@dataclass(frozen=True)
class ResumeSectionDocument:
    section_id: int
    code: str
    name: str
    description: str
    document_text: str


@dataclass(frozen=True)
class ResumeSectionCandidate:
    section_id: int
    section_name: str
    section_code: str
    embedding_score: float
    rerank_score: float | None
    confidence: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResumeSectionClassificationResult:
    success: bool
    section_id: int | None
    section_name: str | None
    confidence: float
    reason: str
    candidates: list[ResumeSectionCandidate]
    needs_manual_selection: bool = False

    def candidates_as_dicts(self) -> list[dict[str, Any]]:
        return [candidate.to_dict() for candidate in self.candidates]


class ResumeSectionClassifierService:
    """
    Классификатор раздела резюме через embedding retrieval + reranker.
    """

    MAX_QUERY_CHARS = 12_000

    def __init__(self) -> None:
        self.settings = get_settings()

    def classify_section(
        self,
        change_description: str,
        attachment_text: str | None = None,
    ) -> ResumeSectionClassificationResult:
        """
        Возвращает лучший раздел резюме или fallback на ручной выбор.
        """
        query_text = self._build_query_text(change_description, attachment_text)

        if not query_text:
            return ResumeSectionClassificationResult(
                success=False,
                section_id=None,
                section_name=None,
                confidence=0.0,
                reason="Недостаточно текста для определения раздела.",
                candidates=[],
                needs_manual_selection=True,
            )

        sections = self._load_section_documents()

        if not sections:
            return ResumeSectionClassificationResult(
                success=False,
                section_id=None,
                section_name=None,
                confidence=0.0,
                reason="Не удалось загрузить справочник разделов резюме.",
                candidates=[],
                needs_manual_selection=True,
            )

        try:
            query_embedding = get_hf_single_embedding(query_text)
            section_embeddings = get_hf_embeddings([section.document_text for section in sections])

            top_k = max(1, int(self.settings.resume_section_top_k))
            top_k_hits = get_hf_top_k(
                query_embedding=query_embedding,
                candidate_embeddings=section_embeddings,
                top_k=min(top_k, len(sections)),
            )

            if not top_k_hits:
                return ResumeSectionClassificationResult(
                    success=False,
                    section_id=None,
                    section_name=None,
                    confidence=0.0,
                    reason="Embedding-поиск не вернул кандидатов.",
                    candidates=[],
                    needs_manual_selection=True,
                )

            top_sections = [sections[index] for index, _score in top_k_hits]
            top_embedding_scores = {
                sections[index].section_id: float(score)
                for index, score in top_k_hits
            }

            rerank_scores = get_hf_pair_scores(
                query_text=query_text,
                documents=[section.document_text for section in top_sections],
            )

        except Exception as exc:
            return ResumeSectionClassificationResult(
                success=False,
                section_id=None,
                section_name=None,
                confidence=0.0,
                reason=(
                    "AI-модели для определения раздела сейчас недоступны. "
                    f"Детали: {exc}"
                ),
                candidates=[],
                needs_manual_selection=True,
            )

        candidates: list[ResumeSectionCandidate] = []

        for index, section in enumerate(top_sections):
            rerank_score = rerank_scores[index] if index < len(rerank_scores) else None
            embedding_score = top_embedding_scores.get(section.section_id, 0.0)
            confidence = self._calculate_confidence(
                embedding_score=embedding_score,
                rerank_score=rerank_score,
            )

            candidates.append(
                ResumeSectionCandidate(
                    section_id=section.section_id,
                    section_name=section.name,
                    section_code=section.code,
                    embedding_score=round(float(embedding_score), 6),
                    rerank_score=round(float(rerank_score), 6) if rerank_score is not None else None,
                    confidence=round(float(confidence), 6),
                )
            )

        candidates.sort(
            key=lambda item: (
                item.confidence if item.confidence is not None else 0.0,
                item.rerank_score if item.rerank_score is not None else -9999.0,
                item.embedding_score,
            ),
            reverse=True,
        )

        best = candidates[0]
        confidence = float(best.confidence or 0.0)
        threshold = float(self.settings.resume_section_confidence_threshold)

        reason = (
            f"Embedding top-{len(candidates)} + reranker. "
            f"Лучший раздел: «{best.section_name}», confidence={confidence:.3f}, "
            f"порог={threshold:.3f}."
        )

        if confidence < threshold:
            return ResumeSectionClassificationResult(
                success=False,
                section_id=best.section_id,
                section_name=best.section_name,
                confidence=confidence,
                reason=reason,
                candidates=candidates,
                needs_manual_selection=True,
            )

        return ResumeSectionClassificationResult(
            success=True,
            section_id=best.section_id,
            section_name=best.section_name,
            confidence=confidence,
            reason=reason,
            candidates=candidates,
            needs_manual_selection=False,
        )

    def _build_query_text(self, change_description: str, attachment_text: str | None) -> str:
        parts = [
            "Описание заявки:",
            (change_description or "").strip(),
        ]

        normalized_attachment_text = (attachment_text or "").strip()
        if normalized_attachment_text:
            parts.extend(
                [
                    "",
                    "Текст вложения:",
                    normalized_attachment_text,
                ]
            )

        query_text = "\n".join(part for part in parts if part is not None).strip()
        return " ".join(query_text.split())[: self.MAX_QUERY_CHARS]

    def _load_section_documents(self) -> list[ResumeSectionDocument]:
        try:
            with get_db_session() as session:
                rows = self._fetch_section_rows(session)
        except SQLAlchemyError:
            rows = self._fallback_section_rows()
        except Exception:
            rows = self._fallback_section_rows()

        documents: list[ResumeSectionDocument] = []

        for row in rows:
            try:
                section_id = int(row["id"])
            except (TypeError, ValueError, KeyError):
                continue

            name = str(row.get("name") or f"Раздел #{section_id}")
            code = str(row.get("code") or f"section_{section_id}")
            description = str(row.get("description") or "")

            document_text = self._build_section_document_text(row)

            documents.append(
                ResumeSectionDocument(
                    section_id=section_id,
                    code=code,
                    name=name,
                    description=description,
                    document_text=document_text,
                )
            )

        return documents

    def _fetch_section_rows(self, session: Session) -> list[dict[str, Any]]:
        columns = self._get_table_columns(session, "resume_sections")

        if not {"id", "name"}.issubset(columns):
            return self._fallback_section_rows()

        optional_columns = [
            "code",
            "description",
            "keywords",
            "keywords_json",
            "examples",
            "examples_json",
            "sample_text",
            "sort_order",
            "is_active",
        ]

        select_fragments = ["id", "name"]
        for column_name in optional_columns:
            if column_name in columns:
                select_fragments.append(column_name)

        where_clause = "WHERE is_active = TRUE" if "is_active" in columns else ""
        order_clause = "ORDER BY sort_order ASC, id ASC" if "sort_order" in columns else "ORDER BY id ASC"

        query = text(
            f"""
            SELECT {", ".join(select_fragments)}
            FROM resume_sections
            {where_clause}
            {order_clause}
            """
        )

        rows = session.execute(query).mappings().all()
        return [dict(row) for row in rows]

    def _get_table_columns(self, session: Session, table_name: str) -> set[str]:
        query = text(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """
        )

        rows = session.execute(query, {"table_name": table_name}).mappings().all()
        return {str(row["column_name"]) for row in rows if row.get("column_name")}

    def _build_section_document_text(self, row: dict[str, Any]) -> str:
        parts = [
            f"Название раздела: {row.get('name') or ''}",
            f"Код раздела: {row.get('code') or ''}",
            f"Описание раздела: {row.get('description') or ''}",
        ]

        for field_name in (
            "keywords",
            "keywords_json",
            "examples",
            "examples_json",
            "sample_text",
        ):
            value = row.get(field_name)
            if value is None:
                continue

            normalized_value = self._stringify_metadata_value(value)
            if normalized_value:
                parts.append(f"{field_name}: {normalized_value}")

        return " ".join(" ".join(parts).split())

    def _stringify_metadata_value(self, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False)

        raw_value = str(value).strip()
        if not raw_value:
            return ""

        try:
            parsed_value = json.loads(raw_value)
            if isinstance(parsed_value, (dict, list)):
                return json.dumps(parsed_value, ensure_ascii=False)
        except Exception:
            pass

        return raw_value

    def _calculate_confidence(
        self,
        embedding_score: float,
        rerank_score: float | None,
    ) -> float:
        """
        Переводит raw-score reranker в [0, 1] и мягко учитывает embedding score.
        """
        embedding_component = max(0.0, min(1.0, (float(embedding_score) + 1.0) / 2.0))

        if rerank_score is None:
            return embedding_component

        rerank_component = self._sigmoid(float(rerank_score))
        return max(0.0, min(1.0, 0.75 * rerank_component + 0.25 * embedding_component))

    def _sigmoid(self, value: float) -> float:
        if value >= 30:
            return 1.0
        if value <= -30:
            return 0.0
        return 1.0 / (1.0 + math.exp(-value))

    def _fallback_section_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 1,
                "code": "personal_data",
                "name": "Личные данные",
                "description": "Пол, дата рождения, семейное положение, гражданство, водительское удостоверение, судимость.",
                "keywords": "паспорт, гражданство, дата рождения, пол, семья, водительские права, судимость",
                "examples": "Изменить гражданство; добавить категорию водительского удостоверения.",
            },
            {
                "id": 2,
                "code": "education",
                "name": "Образование",
                "description": "Учебные заведения, факультет, специальность, уровень образования, годы обучения.",
                "keywords": "вуз, университет, институт, колледж, факультет, специальность, образование",
                "examples": "Добавить магистратуру; обновить специальность.",
            },
            {
                "id": 3,
                "code": "diplomas",
                "name": "Дипломы",
                "description": "Дипломы, квалификация, серия, номер, дата выдачи, подтверждающие документы.",
                "keywords": "диплом, квалификация, серия диплома, номер диплома, красный диплом",
                "examples": "Приложить диплом; добавить сведения о квалификации.",
            },
            {
                "id": 4,
                "code": "work_experience",
                "name": "Опыт работы",
                "description": "Компании, должности, периоды работы, обязанности, достижения и проекты.",
                "keywords": "опыт работы, компания, должность, обязанности, проект, стаж",
                "examples": "Добавить новую должность; обновить обязанности на прошлом месте работы.",
            },
            {
                "id": 5,
                "code": "competitions",
                "name": "Участие в соревнованиях",
                "description": "Участие в конкурсах, чемпионатах, хакатонах и профессиональных соревнованиях.",
                "keywords": "соревнование, конкурс, чемпионат, хакатон, участие",
                "examples": "Добавить участие в чемпионате; приложить сертификат участника.",
            },
            {
                "id": 6,
                "code": "competition_awards",
                "name": "Призёр/Победитель соревнований",
                "description": "Призовые места, победы, награды, дипломы победителя.",
                "keywords": "победитель, призер, призовое место, награда, диплом победителя",
                "examples": "Добавить первое место; приложить диплом победителя конкурса.",
            },
            {
                "id": 7,
                "code": "skills",
                "name": "Личные навыки",
                "description": "Профессиональные и личные навыки, уровень владения, годы опыта.",
                "keywords": "навык, компетенция, Python, SQL, управление, опыт, уровень",
                "examples": "Добавить навык SQL; повысить уровень Python до senior.",
            },
            {
                "id": 8,
                "code": "additional_courses",
                "name": "Пройденные дополнительные курсы",
                "description": "Дополнительное обучение, сертификаты и курсы без обязательного срока действия.",
                "keywords": "курс, сертификат, дополнительное обучение, обучение",
                "examples": "Добавить курс по аналитике; приложить сертификат онлайн-курса.",
            },
            {
                "id": 9,
                "code": "qualification_courses",
                "name": "Пройденные курсы повышения квалификации",
                "description": "Курсы повышения квалификации, период действия, обязательное обучение.",
                "keywords": "повышение квалификации, удостоверение, срок действия, аттестация",
                "examples": "Добавить удостоверение о повышении квалификации; обновить срок действия курса.",
            },
        ]