import numpy as np

from app.models.candidate_search_models import CandidateSearchDocument
from app.services.hr_candidate_retrieval_service import HRCandidateRetrievalService


def _doc(employee_user_id: int, text: str) -> CandidateSearchDocument:
    return CandidateSearchDocument(
        employee_user_id=employee_user_id,
        anonymous_code=f"CAND-{employee_user_id}",
        full_name=f"CAND-{employee_user_id}",
        source_hash="hash",
        profile_text=text,
        skills_text=text,
        experience_text="",
        education_text="",
        courses_text="",
        aggregated_text=text,
        structured_payload={"skills_text": text},
    )


def test_retrieval_uses_env_top_k_without_calling_old_get_hf_top_k(monkeypatch):
    monkeypatch.setenv("HF_TOP_K", "1")

    service = HRCandidateRetrievalService()

    def fake_encode_texts(texts: list[str]) -> np.ndarray:
        if len(texts) == 1:
            return np.array([[1.0, 0.0]])

        return np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ]
        )

    monkeypatch.setattr(service, "_encode_texts", fake_encode_texts)

    hits = service.retrieve(
        requirements_text="python",
        documents=[
            _doc(1, "python backend"),
            _doc(2, "excel analytics"),
        ],
    )

    assert len(hits) == 1
    assert hits[0].employee_user_id == 1