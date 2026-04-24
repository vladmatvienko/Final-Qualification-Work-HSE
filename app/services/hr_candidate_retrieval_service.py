from __future__ import annotations

"""
Retrieval-слой stage 9 на Hugging Face embeddings.
"""

import re
from typing import Iterable

import numpy as np

from app.models.candidate_search_models import CandidateRetrievalHit, CandidateSearchDocument
from app.services.hf_local_models import (
    get_embedding_model,
    get_hf_batch_size,
    get_hf_top_k,
    should_normalize_embeddings,
)


class HRCandidateRetrievalService:
    """
    Retrieval по embeddings на Hugging Face.
    """

    TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё0-9_+#./-]{2,}")

    def _tokenize(self, text: str) -> set[str]:
        """
        Простая токенизация для UI-совпадений по секциям.
        """
        if not text:
            return set()

        return {
            token.lower().strip()
            for token in self.TOKEN_PATTERN.findall(text)
            if token and len(token.strip()) >= 2
        }

    def _match_items(self, query_tokens: set[str], items: Iterable[str]) -> list[str]:
        """
        Возвращает top совпавших элементов из конкретной секции резюме.
        """
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

        skills = payload.get("skills", []) or []
        experiences = payload.get("work_experiences", []) or []
        educations = payload.get("educations", []) or []
        diplomas = payload.get("diplomas", []) or []
        additional_courses = payload.get("additional_courses", []) or []
        qualification_courses = payload.get("qualification_courses", []) or []

        matched_skills = self._match_items(query_tokens, skills)
        matched_experience = self._match_items(query_tokens, experiences)
        matched_learning = self._match_items(
            query_tokens,
            educations + diplomas + additional_courses + qualification_courses,
        )

        return matched_skills, matched_experience, matched_learning

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """
        Строит embeddings для списка текстов.
        """
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

        return embeddings

    def retrieve(
        self,
        requirements_text: str,
        documents: list[CandidateSearchDocument],
        top_k: int | None = None,
    ) -> list[CandidateRetrievalHit]:
        """
        Главная retrieval-функция.
        """
        normalized_text = (requirements_text or "").strip()
        if not normalized_text:
            return []

        if not documents:
            return []

        effective_top_k = top_k or get_hf_top_k()

        query_embedding = self._encode_texts([normalized_text])[0]
        document_texts = [document.aggregated_text for document in documents]
        document_embeddings = self._encode_texts(document_texts)

        similarities = np.dot(document_embeddings, query_embedding)

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