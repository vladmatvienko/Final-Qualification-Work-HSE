from __future__ import annotations

"""
Retrieval-слой stage 9 на Hugging Face embeddings.
"""

import re
from typing import Any, Iterable

import numpy as np

from app.models.candidate_search_models import CandidateRetrievalHit, CandidateSearchDocument
from app.services.hf_local_models import (
    get_embedding_model,
    get_hf_batch_size,
    get_hf_retrieval_top_k,
    should_normalize_embeddings,
)


class HRCandidateRetrievalService:
    """
    Retrieval по embeddings на Hugging Face.
    """

    TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё0-9_+#./-]{2,}")

    def _tokenize(self, text: str) -> set[str]:
        if not text:
            return set()

        return {
            token.lower().strip()
            for token in self.TOKEN_PATTERN.findall(text)
            if token and len(token.strip()) >= 2
        }

    def _as_text_items(self, value: Any) -> list[str]:
        """
        Приводит list[str] / list[dict] / str к списку человекочитаемых строк.
        """
        if value is None:
            return []

        if isinstance(value, str):
            return [value] if value.strip() else []

        if not isinstance(value, list):
            return [str(value)] if str(value).strip() else []

        result: list[str] = []
        for item in value:
            if item is None:
                continue

            if isinstance(item, str):
                text_value = item.strip()
                if text_value:
                    result.append(text_value)
                continue

            if isinstance(item, dict):
                parts = [
                    str(raw).strip()
                    for raw in item.values()
                    if raw is not None and str(raw).strip()
                ]
                if parts:
                    result.append(" • ".join(parts))
                continue

            text_value = str(item).strip()
            if text_value:
                result.append(text_value)

        return result

    def _match_items(self, query_tokens: set[str], items: Iterable[str]) -> list[str]:
        scored_items: list[tuple[float, str]] = []

        for item in items:
            item_text = str(item or "").strip()
            if not item_text:
                continue

            item_tokens = self._tokenize(item_text)
            common = query_tokens.intersection(item_tokens)

            if not common:
                continue

            score = len(common) / max(1, len(query_tokens))
            scored_items.append((score, item_text))

        scored_items.sort(key=lambda pair: pair[0], reverse=True)
        return [text for _, text in scored_items[:5]]

    def _extract_matches(
        self,
        requirements_text: str,
        document: CandidateSearchDocument,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Достаёт красивые совпадения по секциям резюме.
        """
        query_tokens = self._tokenize(requirements_text)
        payload = document.structured_payload or {}

        skills = (
            self._as_text_items(payload.get("skills"))
            + self._as_text_items(payload.get("skill_rows"))
            + self._as_text_items(payload.get("skills_text"))
        )

        experiences = (
            self._as_text_items(payload.get("work_experiences"))
            + self._as_text_items(payload.get("work_experience_rows"))
            + self._as_text_items(payload.get("experience_text"))
        )

        learning = (
            self._as_text_items(payload.get("educations"))
            + self._as_text_items(payload.get("education_rows"))
            + self._as_text_items(payload.get("diplomas"))
            + self._as_text_items(payload.get("diploma_rows"))
            + self._as_text_items(payload.get("additional_course_rows"))
            + self._as_text_items(payload.get("qualification_course_rows"))
            + self._as_text_items(payload.get("education_text"))
            + self._as_text_items(payload.get("courses_text"))
        )

        return (
            self._match_items(query_tokens, skills),
            self._match_items(query_tokens, experiences),
            self._match_items(query_tokens, learning),
        )

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        model = get_embedding_model()

        embeddings = model.encode(
            texts,
            batch_size=get_hf_batch_size(),
            convert_to_numpy=True,
            normalize_embeddings=should_normalize_embeddings(),
            show_progress_bar=False,
        )

        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)

        return embeddings.astype(float)

    def _calculate_similarities(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        if should_normalize_embeddings():
            return np.dot(document_embeddings, query_embedding)

        query_norm = np.linalg.norm(query_embedding)
        document_norms = np.linalg.norm(document_embeddings, axis=1)

        denominator = document_norms * query_norm
        denominator = np.where(denominator == 0, 1.0, denominator)

        return np.dot(document_embeddings, query_embedding) / denominator

    def retrieve(
        self,
        requirements_text: str,
        documents: list[CandidateSearchDocument],
        top_k: int | None = None,
    ) -> list[CandidateRetrievalHit]:
        normalized_text = (requirements_text or "").strip()
        if not normalized_text or not documents:
            return []

        effective_top_k = int(top_k) if top_k is not None else get_hf_retrieval_top_k()
        effective_top_k = max(1, effective_top_k)

        query_embedding = self._encode_texts([normalized_text])[0]
        document_texts = [document.aggregated_text or "" for document in documents]
        document_embeddings = self._encode_texts(document_texts)

        similarities = self._calculate_similarities(
            query_embedding=query_embedding,
            document_embeddings=document_embeddings,
        )

        hits: list[CandidateRetrievalHit] = []

        for document, raw_similarity in zip(documents, similarities):
            retrieval_score = max(0.0, min(1.0, float((raw_similarity + 1.0) / 2.0)))

            matched_skills, matched_experience, matched_learning = self._extract_matches(
                requirements_text=normalized_text,
                document=document,
            )

            hits.append(
                CandidateRetrievalHit(
                    employee_user_id=document.employee_user_id,
                    anonymous_code=document.anonymous_code,
                    full_name=document.full_name,
                    retrieval_score=retrieval_score,
                    matched_skills=matched_skills,
                    matched_experience=matched_experience,
                    matched_courses_or_education=matched_learning,
                    document=document,
                )
            )

        hits.sort(key=lambda item: item.retrieval_score, reverse=True)
        return hits[:effective_top_k]