from __future__ import annotations

import math
import os
import re
from typing import Any

from app.models.candidate_search_models import CandidateRetrievalHit, RankedCandidate
from app.services.hf_local_models import get_hf_pair_scores


class HRCandidateRankingService:
    """
    Ранжирование кандидатов.
    """

    _STOPWORDS = {
        "и", "в", "во", "на", "по", "для", "с", "со", "к", "из", "от", "до",
        "под", "над", "или", "а", "но", "не", "это", "как", "что", "нужен",
        "нужна", "нужно", "требуется", "опыт", "знание", "умение", "навык",
        "навыки", "работа", "позиция", "должность", "кандидат", "релевантный",
        "желательно", "будет", "плюсом", "проект", "разработка", "система",
        "сервисы", "внутренние",
        "and", "or", "the", "a", "an", "to", "for", "with", "of", "in", "on",
        "at", "by", "from", "is", "are", "be", "as", "role", "position",
        "candidate", "experience", "knowledge", "skills", "skill", "required",
        "plus", "nice", "have",
    }

    _TECH_KEYWORDS = [
        "python", "mysql", "sql", "postgresql", "oracle", "api", "rest", "graphql",
        "fastapi", "flask", "django", "pandas", "numpy", "scikit-learn", "sklearn",
        "pytorch", "tensorflow", "rag", "langgraph", "langchain", "gradio",
        "docker", "kubernetes", "git", "linux", "qa", "pytest", "selenium",
        "javascript", "typescript", "react", "vue", "java", "c#", "c++", "go",
        "product", "backend", "frontend", "analytics", "power bi", "tableau",
    ]

    def _get_rerank_top_n(self) -> int:
        raw_value = os.getenv("HR_RERANK_TOP_N", "10")
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 10

    @staticmethod
    def _safe_text(value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).strip().split())

    @staticmethod
    def _sigmoid(value: float) -> float:
        try:
            return 1.0 / (1.0 + math.exp(-value))
        except OverflowError:
            return 0.0 if value < 0 else 1.0

    def _tokenize_query(self, text: str) -> list[str]:
        normalized = self._safe_text(text).lower()
        raw_tokens = re.findall(r"[a-zA-Zа-яА-Я0-9\+\#\.\-_]+", normalized)

        tokens: list[str] = []
        for token in raw_tokens:
            token = token.strip(".,;:()[]{}<>\"'")
            if not token or len(token) <= 1:
                continue
            if token in self._STOPWORDS:
                continue
            tokens.append(token)

        seen: set[str] = set()
        unique_tokens: list[str] = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)

        return unique_tokens

    def _normalize_rerank_scores(self, raw_scores: list[float]) -> list[float]:
        if not raw_scores:
            return []

        float_scores = [float(score) for score in raw_scores]
        min_score = min(float_scores)
        max_score = max(float_scores)

        if abs(max_score - min_score) < 1e-9:
            return [self._sigmoid(score) for score in float_scores]

        return [(score - min_score) / (max_score - min_score) for score in float_scores]

    def _split_loose_text(self, text: str) -> list[str]:
        cleaned = self._safe_text(text)
        if not cleaned:
            return []

        parts = re.split(r"[,\|\;\•/]+", cleaned)
        result = [self._safe_text(part) for part in parts if self._safe_text(part)]
        return result

    def _dedupe_keep_order(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower()
            if not item or key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _walk_payload_for_skill_values(self, node: Any, collector: list[str]) -> None:
        """
        Рекурсивно ищем skill/competency-поля в payload.
        """
        if isinstance(node, dict):
            for key, value in node.items():
                key_lower = str(key).lower()

                if key_lower in {
                    "skill_name", "skill", "skills", "competency_name",
                    "competency", "competencies", "hard_skill", "soft_skill",
                    "technology", "stack", "tool", "tool_name",
                }:
                    if isinstance(value, list):
                        for item in value:
                            text = self._safe_text(item)
                            if text:
                                collector.append(text)
                    else:
                        text = self._safe_text(value)
                        if text:
                            collector.append(text)

                self._walk_payload_for_skill_values(value, collector)

        elif isinstance(node, list):
            for item in node:
                self._walk_payload_for_skill_values(item, collector)

    def _extract_skill_names_from_text(self, text: str) -> list[str]:
        lowered = self._safe_text(text).lower()
        if not lowered:
            return []

        found: list[str] = []
        for keyword in self._TECH_KEYWORDS:
            if keyword in lowered:
                found.append(keyword.upper() if keyword == "sql" else keyword)

        return self._dedupe_keep_order(found)

    def _extract_skill_names(self, payload: dict, hit: CandidateRetrievalHit) -> list[str]:
        result: list[str] = []

        candidate_keys = [
            "skill_rows",
            "skills_rows",
            "skills",
            "skill_list",
            "competency_rows",
            "competencies",
            "hard_skill_rows",
            "soft_skill_rows",
        ]

        for key in candidate_keys:
            rows = payload.get(key, []) or []
            if isinstance(rows, list):
                for row in rows[:20]:
                    if isinstance(row, dict):
                        skill_name = self._safe_text(
                            row.get("skill_name")
                            or row.get("name")
                            or row.get("title")
                            or row.get("competency_name")
                            or row.get("skill")
                            or row.get("competency")
                            or row.get("technology")
                            or row.get("stack")
                            or row.get("tool_name")
                        )
                        if skill_name:
                            result.append(skill_name)
                    else:
                        text = self._safe_text(row)
                        if text:
                            result.append(text)

        self._walk_payload_for_skill_values(payload, result)

        if hit.document is not None:
            document_skills_text = self._safe_text(getattr(hit.document, "skills_text", ""))
            result.extend(self._split_loose_text(document_skills_text))

        if hit.document is not None:
            aggregated_text = self._safe_text(getattr(hit.document, "aggregated_text", ""))
            result.extend(self._extract_skill_names_from_text(aggregated_text))

        return self._dedupe_keep_order(result)

    def _extract_experience_lines(self, payload: dict, hit: CandidateRetrievalHit) -> list[str]:
        result: list[str] = []

        work_rows = payload.get("work_experience_rows", []) or []
        for row in work_rows[:6]:
            if not isinstance(row, dict):
                continue

            company = self._safe_text(
                row.get("company_name")
                or row.get("employer_name")
                or row.get("organization_name")
                or row.get("workplace")
            )
            position = self._safe_text(
                row.get("position")
                or row.get("job_title")
                or row.get("role_name")
                or row.get("position_title")
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

            parts: list[str] = []
            if company:
                parts.append(company)
            if position:
                parts.append(position)
            if date_from or date_to:
                parts.append(f"{date_from or '?'} — {date_to or 'настоящее время'}")

            line = " • ".join(part for part in parts if part)
            if line:
                result.append(line)

        if not result and hit.document is not None:
            exp_text = self._safe_text(getattr(hit.document, "experience_text", ""))
            if exp_text:
                result = [self._safe_text(part) for part in exp_text.split("|") if self._safe_text(part)]

        return result

    def _extract_learning_lines(self, payload: dict, hit: CandidateRetrievalHit) -> list[str]:
        result: list[str] = []

        education_rows = payload.get("education_rows", []) or []
        additional_course_rows = payload.get("additional_course_rows", []) or []
        qualification_course_rows = payload.get("qualification_course_rows", []) or []

        for row in education_rows[:3]:
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

            parts = [part for part in [institution, degree, specialty] if part]
            if parts:
                result.append(" • ".join(parts))

        for row in additional_course_rows[:2]:
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

            parts = [part for part in [course_name, provider] if part]
            if parts:
                result.append(" • ".join(parts))

        for row in qualification_course_rows[:2]:
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
            valid_until = self._safe_text(
                row.get("valid_until")
                or row.get("end_date")
                or row.get("date_to")
            )

            parts = [part for part in [course_name, provider, valid_until] if part]
            if parts:
                result.append(" • ".join(parts))

        if not result and hit.document is not None:
            edu_text = self._safe_text(getattr(hit.document, "education_text", ""))
            courses_text = self._safe_text(getattr(hit.document, "courses_text", ""))

            if edu_text:
                result.extend([self._safe_text(part) for part in edu_text.split("|") if self._safe_text(part)])
            if courses_text:
                result.extend([self._safe_text(part) for part in courses_text.split("|") if self._safe_text(part)])

        return result

    def _match_items(self, items: list[str], query_tokens: list[str], limit: int = 4) -> list[str]:
        if not items or not query_tokens:
            return []

        scored_items: list[tuple[int, str]] = []

        for item in items:
            item_lower = item.lower()
            score = 0
            for token in query_tokens:
                if token in item_lower:
                    score += 1
            if score > 0:
                scored_items.append((score, item))

        scored_items.sort(key=lambda pair: (-pair[0], len(pair[1])))

        result: list[str] = []
        seen: set[str] = set()
        for _, item in scored_items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
            if len(result) >= limit:
                break

        return result

    def _coverage_score(self, items: list[str], query_tokens: list[str]) -> float:
        if not items or not query_tokens:
            return 0.0

        matched_tokens: set[str] = set()
        lowered_items = [item.lower() for item in items]

        for token in query_tokens:
            for item in lowered_items:
                if token in item:
                    matched_tokens.add(token)
                    break

        return len(matched_tokens) / max(1, len(query_tokens))

    def _build_ranked_candidate(
        self,
        hit: CandidateRetrievalHit,
        query_tokens: list[str],
        final_score: int,
        explanation_text: str,
    ) -> RankedCandidate:
        payload = hit.document.structured_payload if hit.document else {}

        skill_items = self._extract_skill_names(payload, hit)
        experience_items = self._extract_experience_lines(payload, hit)
        learning_items = self._extract_learning_lines(payload, hit)

        matched_skills = hit.matched_skills or self._match_items(skill_items, query_tokens, limit=4)
        matched_experience = hit.matched_experience or self._match_items(experience_items, query_tokens, limit=2)
        matched_learning = hit.matched_courses_or_education or self._match_items(learning_items, query_tokens, limit=2)

        display_skills = matched_skills or skill_items[:4] or ["Навыки не заполнены"]
        display_experience = matched_experience or experience_items[:2] or ["Опыт не заполнен"]
        display_learning = matched_learning or learning_items[:2] or ["Обучение не заполнено"]

        return RankedCandidate(
            employee_user_id=hit.employee_user_id,
            anonymous_code=hit.anonymous_code,
            full_name=hit.full_name,
            final_score=final_score,
            key_skills_text=", ".join(display_skills),
            relevant_experience_text=" | ".join(display_experience),
            courses_education_text=" | ".join(display_learning),
            explanation_text=explanation_text,
        )

    def rank(
        self,
        requirements_text: str,
        retrieval_hits: list[CandidateRetrievalHit],
    ) -> list[RankedCandidate]:
        normalized_text = self._safe_text(requirements_text)
        if not normalized_text or not retrieval_hits:
            return []

        query_tokens = self._tokenize_query(normalized_text)

        rerank_top_n = min(self._get_rerank_top_n(), len(retrieval_hits))
        reranked_candidates = retrieval_hits[:rerank_top_n]
        untouched_tail = retrieval_hits[rerank_top_n:]

        rerank_documents: list[str] = []
        for hit in reranked_candidates:
            document_text = ""
            if hit.document is not None:
                document_text = self._safe_text(getattr(hit.document, "aggregated_text", ""))
            rerank_documents.append(document_text)

        raw_scores = get_hf_pair_scores(
            query_text=normalized_text,
            documents=rerank_documents,
        )
        normalized_rerank_scores = self._normalize_rerank_scores(raw_scores)

        ranked: list[RankedCandidate] = []

        for index, hit in enumerate(reranked_candidates):
            payload = hit.document.structured_payload if hit.document else {}

            skill_items = self._extract_skill_names(payload, hit)
            experience_items = self._extract_experience_lines(payload, hit)
            learning_items = self._extract_learning_lines(payload, hit)

            retrieval_component = float(hit.retrieval_score)
            rerank_component = normalized_rerank_scores[index] if index < len(normalized_rerank_scores) else 0.0

            skill_component = self._coverage_score(skill_items, query_tokens)
            experience_component = self._coverage_score(experience_items, query_tokens)
            learning_component = self._coverage_score(learning_items, query_tokens)

            final_score_float = (
                retrieval_component * 0.38
                + rerank_component * 0.32
                + skill_component * 0.18
                + experience_component * 0.08
                + learning_component * 0.04
            )
            final_score = max(1, min(99, round(final_score_float * 100)))

            explanation_parts = [
                f"retrieval={round(retrieval_component, 3)}",
                f"rerank={round(rerank_component, 3)}",
                f"skills={round(skill_component, 3)}",
                f"experience={round(experience_component, 3)}",
                f"learning={round(learning_component, 3)}",
            ]

            ranked.append(
                self._build_ranked_candidate(
                    hit=hit,
                    query_tokens=query_tokens,
                    final_score=final_score,
                    explanation_text=" | ".join(explanation_parts),
                )
            )

        for hit in untouched_tail:
            payload = hit.document.structured_payload if hit.document else {}

            skill_items = self._extract_skill_names(payload, hit)
            experience_items = self._extract_experience_lines(payload, hit)
            learning_items = self._extract_learning_lines(payload, hit)

            retrieval_component = float(hit.retrieval_score)
            skill_component = self._coverage_score(skill_items, query_tokens)
            experience_component = self._coverage_score(experience_items, query_tokens)
            learning_component = self._coverage_score(learning_items, query_tokens)

            final_score_float = (
                retrieval_component * 0.55
                + skill_component * 0.20
                + experience_component * 0.17
                + learning_component * 0.08
            )
            final_score = max(1, min(99, round(final_score_float * 100)))

            ranked.append(
                self._build_ranked_candidate(
                    hit=hit,
                    query_tokens=query_tokens,
                    final_score=final_score,
                    explanation_text=(
                        f"retrieval={round(retrieval_component, 3)}"
                        f" | skills={round(skill_component, 3)}"
                        f" | experience={round(experience_component, 3)}"
                        f" | learning={round(learning_component, 3)}"
                    ),
                )
            )

        ranked.sort(key=lambda item: item.final_score, reverse=True)
        return ranked