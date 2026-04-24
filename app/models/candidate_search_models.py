from __future__ import annotations

"""
Модели рейтинговой таблицы:
"""

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass
class CandidateSearchIndexSource:
    """
    Сырые данные одного сотрудника для построения поискового документа.
    """

    employee_user_id: int
    full_name: str

    profile_data: dict[str, Any] = field(default_factory=dict)

    education_rows: list[dict[str, Any]] = field(default_factory=list)
    diploma_rows: list[dict[str, Any]] = field(default_factory=list)
    work_experience_rows: list[dict[str, Any]] = field(default_factory=list)
    competition_rows: list[dict[str, Any]] = field(default_factory=list)
    award_rows: list[dict[str, Any]] = field(default_factory=list)
    skill_rows: list[dict[str, Any]] = field(default_factory=list)
    additional_course_rows: list[dict[str, Any]] = field(default_factory=list)
    qualification_course_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CandidateSearchDocument:
    """
    Уже нормализованный документ сотрудника для retrieval/ranking.
    """

    employee_user_id: int
    anonymous_code: str
    full_name: str
    source_hash: str

    profile_text: str
    skills_text: str
    experience_text: str
    education_text: str
    courses_text: str
    aggregated_text: str

    structured_payload: dict[str, Any]


@dataclass
class CandidateRetrievalHit:
    """
    Результат retrieval-слоя.
    """

    employee_user_id: int
    anonymous_code: str
    full_name: str
    retrieval_score: float

    matched_skills: list[str] = field(default_factory=list)
    matched_experience: list[str] = field(default_factory=list)
    matched_courses_or_education: list[str] = field(default_factory=list)

    document: CandidateSearchDocument | None = None


@dataclass
class RankedCandidate:
    """
    Финальная модель кандидата для HR-таблицы.
    """

    employee_user_id: int
    anonymous_code: str
    full_name: str
    final_score: int

    key_skills_text: str
    relevant_experience_text: str
    courses_education_text: str
    explanation_text: str


@dataclass
class CandidateSearchUIResult:
    """
    То, что отдаём в UI после поиска.
    """

    table_rows: list[list[str]] = field(default_factory=list)
    dropdown_choices: list[tuple[str, str]] = field(default_factory=list)
    default_candidate_code: str | None = None
    ranked_candidates: list[RankedCandidate] = field(default_factory=list)
    message_text: str = ""
    is_error: bool = False


@dataclass
class JobInvitationCommand:
    """
    Команда на создание приглашения сотруднику.
    """

    hr_user_id: int
    employee_user_id: int
    anonymous_code: str
    position_title: str
    requirements_text: str
    comment_text: str = ""


@dataclass
class ServiceResult:
    """
    Универсальный результат service-слоя.
    """

    success: bool
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


class CandidateSearchGraphState(TypedDict, total=False):
    """
    State для LangGraph workflow.
    """

    requirements_text: str
    documents: list[CandidateSearchDocument]
    retrieval_hits: list[CandidateRetrievalHit]
    ranked_candidates: list[RankedCandidate]