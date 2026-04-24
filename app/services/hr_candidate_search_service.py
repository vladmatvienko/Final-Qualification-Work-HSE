from __future__ import annotations

"""
Facade-service для HR candidate search.
"""

from app.models.candidate_search_models import (
    CandidateSearchDocument,
    CandidateSearchUIResult,
    RankedCandidate,
)
from app.repositories.candidate_search_repository import CandidateSearchRepository
from app.services.hr_candidate_ranking_service import HRCandidateRankingService
from app.services.hr_candidate_retrieval_service import HRCandidateRetrievalService
from app.services.hr_candidate_search_graph import HRCandidateSearchGraph
from app.services.hr_resume_document_builder import HRResumeDocumentBuilder


class HRCandidateSearchService:
    """
    Высокоуровневый сервис поиска кандидатов.
    """

    def __init__(self) -> None:
        self._repository = CandidateSearchRepository()
        self._builder = HRResumeDocumentBuilder()
        self._retrieval_service = HRCandidateRetrievalService()
        self._ranking_service = HRCandidateRankingService()
        self._graph = HRCandidateSearchGraph(
            retrieval_service=self._retrieval_service,
            ranking_service=self._ranking_service,
        )

        self._documents_cache: list[CandidateSearchDocument] = []
        self._documents_by_anonymous_code: dict[str, CandidateSearchDocument] = {}

        self._ranked_candidates_cache: list[RankedCandidate] = []
        self._ranked_candidates_by_anonymous_code: dict[str, RankedCandidate] = {}

    # =========================================================
    # Внутренние cache-хелперы
    # =========================================================
    def _set_documents_cache(self, documents: list[CandidateSearchDocument]) -> None:
        self._documents_cache = documents or []
        self._documents_by_anonymous_code = {
            document.anonymous_code: document
            for document in self._documents_cache
            if getattr(document, "anonymous_code", None)
        }

    def _set_ranked_candidates_cache(self, ranked_candidates: list[RankedCandidate]) -> None:
        self._ranked_candidates_cache = ranked_candidates or []
        self._ranked_candidates_by_anonymous_code = {
            candidate.anonymous_code: candidate
            for candidate in self._ranked_candidates_cache
            if getattr(candidate, "anonymous_code", None)
        }

    # =========================================================
    # Индекс
    # =========================================================
    def refresh_index(self) -> None:
        """
        Пересобирает индекс из текущих данных сотрудников и сразу обновляет runtime-cache.
        """
        sources = self._repository.fetch_candidate_sources()
        documents = self._builder.build_documents(sources)
        self._repository.upsert_candidate_documents(documents)
        self._set_documents_cache(documents)

    def _ensure_documents(self) -> list[CandidateSearchDocument]:
        """
        Гарантирует, что search-документы есть в БД и в runtime-cache.
        """
        if self._documents_cache:
            return self._documents_cache

        documents = self._repository.load_candidate_documents()
        if documents:
            self._set_documents_cache(documents)
            return self._documents_cache

        self.refresh_index()
        return self._documents_cache

    # =========================================================
    # Поиск
    # =========================================================
    def search(self, requirements_text: str) -> CandidateSearchUIResult:
        """
        Полный поиск кандидатов по требованиям.
        """
        normalized_text = (requirements_text or "").strip()
        if not normalized_text:
            self._set_ranked_candidates_cache([])
            return CandidateSearchUIResult(
                message_text="Введите требования к должности, чтобы запустить подбор.",
                is_error=True,
            )

        self.refresh_index()
        documents = self._ensure_documents()

        ranked_candidates = self._graph.run(
            requirements_text=normalized_text,
            documents=documents,
        )

        self._set_ranked_candidates_cache(ranked_candidates)

        if not ranked_candidates:
            return CandidateSearchUIResult(
                message_text="Подходящие кандидаты не найдены. Попробуйте уточнить требования или сделать их шире.",
                is_error=False,
                ranked_candidates=[],
            )

        table_rows: list[list[str]] = []
        dropdown_choices: list[tuple[str, str]] = []

        for candidate in ranked_candidates:
            table_rows.append(
                [
                    candidate.anonymous_code,
                    f"{candidate.final_score}%",
                    candidate.key_skills_text,
                    candidate.relevant_experience_text,
                    candidate.courses_education_text,
                ]
            )

            dropdown_choices.append(
                (
                    f"{candidate.anonymous_code} · {candidate.final_score}% совпадения",
                    candidate.anonymous_code,
                )
            )

        return CandidateSearchUIResult(
            table_rows=table_rows,
            dropdown_choices=dropdown_choices,
            default_candidate_code=ranked_candidates[0].anonymous_code,
            ranked_candidates=ranked_candidates,
            message_text=f"Найдено кандидатов: {len(ranked_candidates)}. Таблица отсортирована по убыванию score.",
            is_error=False,
        )

    # =========================================================
    # Разрешение выбранного кандидата
    # =========================================================
    def resolve_ranked_candidate(self, anonymous_code: str) -> RankedCandidate | None:
        """
        Возвращает ranked-кандидата по анонимному коду.
        """
        normalized_code = (anonymous_code or "").strip()
        if not normalized_code:
            return None

        cached_candidate = self._ranked_candidates_by_anonymous_code.get(normalized_code)
        if cached_candidate is not None:
            return cached_candidate

        return None

    def resolve_employee_user_id(self, anonymous_code: str) -> int | None:
        """
        По анонимному коду находит employee_user_id.
        """
        normalized_code = (anonymous_code or "").strip()
        if not normalized_code:
            return None

        documents = self._ensure_documents()
        if not documents:
            return None

        document = self._documents_by_anonymous_code.get(normalized_code)
        if document is None:
            return None

        return int(document.employee_user_id)

    # =========================================================
    # HTML полного анонимного профиля
    # =========================================================
    def get_full_resume_html(self, anonymous_code: str) -> str:
        """
        Возвращает HTML полного профиля кандидата по анонимному коду.
        """
        normalized_code = (anonymous_code or "").strip()
        if not normalized_code:
            return """
            <div class="page-card">
                <div class="page-title">Профиль кандидата</div>
                <div class="empty-state-text">Не выбран кандидат для просмотра.</div>
            </div>
            """

        self._ensure_documents()

        document = self._documents_by_anonymous_code.get(normalized_code)

        # На случай, если индекс был пуст или устарел
        if document is None:
            self.refresh_index()
            document = self._documents_by_anonymous_code.get(normalized_code)

        if document is None:
            return f"""
            <div class="page-card">
                <div class="page-title">Профиль кандидата</div>
                <div class="empty-state-text">
                    Кандидат с кодом {normalized_code} не найден в индексе.
                </div>
            </div>
            """

        builder = self._builder

        if hasattr(builder, "build_full_resume_html"):
            try:
                return builder.build_full_resume_html(document=document, anonymous_code=normalized_code)
            except TypeError:
                return builder.build_full_resume_html(document)

        if hasattr(builder, "render_full_resume_html"):
            try:
                return builder.render_full_resume_html(document=document, anonymous_code=normalized_code)
            except TypeError:
                return builder.render_full_resume_html(document)

        return f"""
        <div class="page-card">
            <div class="page-title">Профиль кандидата</div>
            <div class="empty-state-text">
                У билдера резюме не найден метод построения HTML.
            </div>
        </div>
        """

    # =========================================================
    # Утилита для приглашения
    # =========================================================
    def derive_position_title(self, requirements_text: str) -> str:
        """
        Выделяет короткое название роли из текста требований.
        """
        normalized = (requirements_text or "").strip()
        if not normalized:
            return "Новая роль"

        first_line = normalized.splitlines()[0].strip()
        first_sentence = first_line.split(".")[0].strip()

        if len(first_sentence) > 80:
            first_sentence = first_sentence[:80].rstrip(" ,;:-") + "…"

        return first_sentence or "Новая роль"