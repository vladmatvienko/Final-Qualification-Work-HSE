import json

from app.models.candidate_search_models import CandidateSearchIndexSource
from app.services.hr_resume_document_builder import HRResumeDocumentBuilder


def test_candidate_document_does_not_expose_diploma_number_series_or_file(monkeypatch):
    monkeypatch.setenv("ANONYMIZATION_SALT", "test-salt")

    builder = HRResumeDocumentBuilder()

    source = CandidateSearchIndexSource(
        employee_user_id=2001,
        full_name="Иванов Иван Иванович",
        diploma_rows=[
            {
                "qualification_title": "Бакалавр бизнес-информатики",
                "diploma_series": "AA",
                "diploma_number": "123456",
                "original_filename": "ivanov_diploma.pdf",
                "issued_at": "2024-06-01",
            }
        ],
    )

    document = builder.build_document(source)
    payload_json = json.dumps(document.structured_payload, ensure_ascii=False)

    assert "Иванов Иван Иванович" not in document.aggregated_text
    assert "Иванов Иван Иванович" not in payload_json
    assert "123456" not in document.aggregated_text
    assert "123456" not in payload_json
    assert "ivanov_diploma.pdf" not in document.aggregated_text
    assert "ivanov_diploma.pdf" not in payload_json
    assert document.full_name.startswith("CAND-")