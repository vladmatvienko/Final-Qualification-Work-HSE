from types import SimpleNamespace

import pytest

from app.services.employee_personal_data_service import EmployeePersonalDataService


def _service_with_tmp_uploads(tmp_path):
    service = EmployeePersonalDataService()
    service.settings = SimpleNamespace(
        base_dir=tmp_path,
        uploads_root_dir=tmp_path / "uploads",
    )
    return service


def test_upload_rejects_executable_extension(tmp_path):
    service = _service_with_tmp_uploads(tmp_path)

    source_file = tmp_path / "payload.exe"
    source_file.write_bytes(b"MZ fake executable")

    with pytest.raises(ValueError):
        service._store_uploaded_file(
            employee_user_id=1,
            source_file_path=str(source_file),
        )


def test_upload_accepts_small_pdf(tmp_path):
    service = _service_with_tmp_uploads(tmp_path)

    source_file = tmp_path / "resume.pdf"
    source_file.write_bytes(b"%PDF-1.4\n% test pdf")

    meta = service._store_uploaded_file(
        employee_user_id=1,
        source_file_path=str(source_file),
    )

    assert meta.file_path_relative.endswith(".pdf")
    assert meta.mime_type == "application/pdf"
    assert meta.file_size_bytes > 0