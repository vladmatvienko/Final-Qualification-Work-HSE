from __future__ import annotations

"""
LangGraph orchestration для candidate search.
"""

from langgraph.graph import END, StateGraph

from app.models.candidate_search_models import CandidateSearchDocument, CandidateSearchGraphState, RankedCandidate
from app.services.hr_candidate_ranking_service import HRCandidateRankingService
from app.services.hr_candidate_retrieval_service import HRCandidateRetrievalService


class HRCandidateSearchGraph:
    """
    Workflow поиска кандидатов через LangGraph.
    """

    def __init__(
        self,
        retrieval_service: HRCandidateRetrievalService,
        ranking_service: HRCandidateRankingService,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._ranking_service = ranking_service
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(CandidateSearchGraphState)

        graph.add_node("prepare_query", self._prepare_query)
        graph.add_node("retrieve_candidates", self._retrieve_candidates)
        graph.add_node("rank_candidates", self._rank_candidates)
        graph.add_node("build_result", self._build_result)

        graph.set_entry_point("prepare_query")
        graph.add_edge("prepare_query", "retrieve_candidates")
        graph.add_edge("retrieve_candidates", "rank_candidates")
        graph.add_edge("rank_candidates", "build_result")
        graph.add_edge("build_result", END)

        return graph.compile()

    def _prepare_query(self, state: CandidateSearchGraphState) -> CandidateSearchGraphState:
        """
        Нормализуем входной текст.
        """
        return {
            "requirements_text": (state.get("requirements_text") or "").strip(),
            "documents": state.get("documents") or [],
        }

    def _retrieve_candidates(self, state: CandidateSearchGraphState) -> CandidateSearchGraphState:
        """
        Retrieval-этап.
        """
        documents: list[CandidateSearchDocument] = state.get("documents") or []
        requirements_text = state.get("requirements_text") or ""

        retrieval_hits = self._retrieval_service.retrieve(
            requirements_text=requirements_text,
            documents=documents,
            top_k=15,
        )

        return {
            **state,
            "retrieval_hits": retrieval_hits,
        }

    def _rank_candidates(self, state: CandidateSearchGraphState) -> CandidateSearchGraphState:
        """
        Ranking-этап.
        """
        ranked_candidates = self._ranking_service.rank(
            requirements_text=state.get("requirements_text") or "",
            retrieval_hits=state.get("retrieval_hits") or [],
        )

        return {
            **state,
            "ranked_candidates": ranked_candidates,
        }

    def _build_result(self, state: CandidateSearchGraphState) -> CandidateSearchGraphState:
        """
        Финальный этап.
        """
        return state

    def run(
        self,
        requirements_text: str,
        documents: list[CandidateSearchDocument],
    ) -> list[RankedCandidate]:
        """
        Запускает полный workflow и возвращает ranked candidates.
        """
        result_state = self._graph.invoke(
            {
                "requirements_text": requirements_text,
                "documents": documents,
            }
        )

        return result_state.get("ranked_candidates") or []