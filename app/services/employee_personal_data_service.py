"""
Service-слой для вкладки "Личные данные".
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.employee_resume_models import (
    EmployeePersonalDataViewModel,
    ResumeChangeRequestResult,
    ResumeDisplaySection,
    ResumeRequestSectionOption,
)
from app.repositories.employee_profile_repository import EmployeeProfileRepository
from app.repositories.resume_request_repository import ResumeRequestRepository


@dataclass(frozen=True)
class _StoredFileMeta:
    """
    Внутренняя служебная структура для уже сохранённого файла.
    """
    file_path_relative: str
    original_filename: str
    mime_type: str | None
    file_size_bytes: int
    file_checksum: str
    file_path_absolute: Path


class EmployeePersonalDataService:
    """
    Главный service для:
    - загрузки резюме сотрудника;
    - отправки заявок на изменение резюме.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    # =========================================================
    # Публичный метод загрузки вкладки "Личные данные"
    # =========================================================
    def _get_fallback_request_section_options(self) -> list[ResumeRequestSectionOption]:
        """
        Резервный список разделов формы.
        """
        labels = [
            "Личные данные",
            "Образование",
            "Дипломы",
            "Опыт работы",
            "Участие в соревнованиях",
            "Призёр/Победитель соревнований",
            "Личные навыки",
            "Пройденные дополнительные курсы",
            "Пройденные курсы повышения квалификации",
        ]
        return [
            ResumeRequestSectionOption(section_id=index + 1, label=label)
            for index, label in enumerate(labels)
        ]

    def _safe_section(self, title: str, loader, formatter) -> ResumeDisplaySection:
        """
        Загружает один раздел резюме без падения всего payload.
        """
        try:
            rows = loader()
            lines = formatter(rows)
            return ResumeDisplaySection(title=title, lines=lines)
        except Exception:
            return ResumeDisplaySection(
                title=title,
                lines=["Не удалось загрузить данные раздела."],
            )

    # =========================================================
    # Публичный метод загрузки вкладки "Личные данные"
    # =========================================================
    def get_personal_data(self, employee_user_id: int) -> EmployeePersonalDataViewModel:
        """
        Загружает и собирает данные сотрудника для вкладки "Личные данные".
        """
        try:
            with get_db_session() as session:
                profile_repo = EmployeeProfileRepository(session)

                base_profile = profile_repo.get_employee_base_profile(employee_user_id)
                if not base_profile:
                    return EmployeePersonalDataViewModel(
                        employee_user_id=employee_user_id,
                        full_name="Неизвестный сотрудник",
                        points_balance=0,
                        completed_achievements_count=0,
                        total_achievements_count=0,
                        sections=[],
                        request_section_options=self._get_fallback_request_section_options(),
                        db_available=True,
                        load_error_message=(
                            "Не удалось загрузить профиль сотрудника: "
                            "в БД не найдена запись для указанного пользователя."
                        ),
                    )

                try:
                    section_options_rows = profile_repo.get_request_section_options()
                except Exception:
                    section_options_rows = []

                request_section_options = [
                    ResumeRequestSectionOption(
                        section_id=int(row["id"]),
                        label=str(row["name"]),
                    )
                    for row in section_options_rows
                ]
                if not request_section_options:
                    request_section_options = self._get_fallback_request_section_options()

                try:
                    total_achievements_count = profile_repo.get_total_active_achievements_count()
                except Exception:
                    total_achievements_count = 0

                sections = [
                    ResumeDisplaySection(
                        title="Пол",
                        lines=[self._format_gender(base_profile.get("gender"))],
                    ),
                    ResumeDisplaySection(
                        title="Дата рождения",
                        lines=[self._format_date_or_placeholder(base_profile.get("birth_date"))],
                    ),
                    ResumeDisplaySection(
                        title="Семейное положение",
                        lines=[self._format_optional_text(base_profile.get("marital_status"))],
                    ),
                    ResumeDisplaySection(
                        title="Гражданство",
                        lines=[self._format_optional_text(base_profile.get("citizenship"))],
                    ),
                    ResumeDisplaySection(
                        title="Водительское удостоверение",
                        lines=[self._format_driver_license(base_profile.get("driver_license_categories"))],
                    ),
                    ResumeDisplaySection(
                        title="Судимость",
                        lines=[
                            self._format_criminal_record(
                                has_criminal_record=base_profile.get("has_criminal_record"),
                                details=base_profile.get("criminal_record_details"),
                            )
                        ],
                    ),
                    self._safe_section(
                        "Образование",
                        lambda: profile_repo.get_education_records(employee_user_id),
                        self._format_education_lines,
                    ),
                    self._safe_section(
                        "Дипломы",
                        lambda: profile_repo.get_diplomas(employee_user_id),
                        self._format_diploma_lines,
                    ),
                    self._safe_section(
                        "Опыт работы",
                        lambda: profile_repo.get_work_experience_records(employee_user_id),
                        self._format_work_experience_lines,
                    ),
                    self._safe_section(
                        "Участие в соревнованиях",
                        lambda: profile_repo.get_competition_participation(employee_user_id),
                        self._format_competition_participation_lines,
                    ),
                    self._safe_section(
                        "Призёр/Победитель соревнований",
                        lambda: profile_repo.get_competition_awards(employee_user_id),
                        self._format_competition_awards_lines,
                    ),
                    self._safe_section(
                        "Личные навыки",
                        lambda: profile_repo.get_employee_skills(employee_user_id),
                        self._format_skill_lines,
                    ),
                    self._safe_section(
                        "Пройденные дополнительные курсы",
                        lambda: profile_repo.get_additional_courses(employee_user_id),
                        self._format_additional_course_lines,
                    ),
                    self._safe_section(
                        "Пройденные курсы повышения квалификации",
                        lambda: profile_repo.get_qualification_courses(employee_user_id),
                        self._format_qualification_course_lines,
                    ),
                ]

                return EmployeePersonalDataViewModel(
                    employee_user_id=employee_user_id,
                    full_name=str(base_profile.get("full_name") or "Неизвестный сотрудник"),
                    points_balance=int(base_profile.get("points_balance") or 0),
                    completed_achievements_count=int(base_profile.get("completed_achievements_count") or 0),
                    total_achievements_count=total_achievements_count,
                    sections=sections,
                    request_section_options=request_section_options,
                    db_available=True,
                    load_error_message=None,
                )

        except SQLAlchemyError:
            return EmployeePersonalDataViewModel(
                employee_user_id=employee_user_id,
                full_name=self.settings.demo_employee_name,
                points_balance=0,
                completed_achievements_count=0,
                total_achievements_count=0,
                sections=[],
                request_section_options=self._get_fallback_request_section_options(),
                db_available=False,
                load_error_message=(
                    "Не удалось загрузить данные из MySQL. "
                    "Проверьте, что сервер БД запущен, параметры в .env указаны верно, "
                    "а схема elbrus создана и доступна."
                ),
            )
        except Exception as exc:
            return EmployeePersonalDataViewModel(
                employee_user_id=employee_user_id,
                full_name=self.settings.demo_employee_name,
                points_balance=0,
                completed_achievements_count=0,
                total_achievements_count=0,
                sections=[],
                request_section_options=self._get_fallback_request_section_options(),
                db_available=False,
                load_error_message=(
                    "Произошла непредвиденная ошибка при загрузке резюме: "
                    f"{exc}"
                ),
            )

    def submit_resume_change_request(
        self,
        employee_user_id: int,
        section_id_raw: str | int | None,
        change_description: str | None,
        uploaded_file_path: str | None,
    ) -> ResumeChangeRequestResult:
        """
        Обрабатывает форму сотрудника и сохраняет заявку в БД.
        """
        # -----------------------------
        # Валидация выбранного раздела
        # -----------------------------
        if section_id_raw in (None, "", "None"):
            return ResumeChangeRequestResult(
                success=False,
                message="Выберите раздел, который хотите дополнить или изменить.",
            )

        try:
            section_id = int(section_id_raw)
        except (TypeError, ValueError):
            return ResumeChangeRequestResult(
                success=False,
                message="Выбран некорректный раздел. Повторите выбор из списка.",
            )

        # -----------------------------
        # Валидация описания
        # -----------------------------
        normalized_description = (change_description or "").strip()
        if not normalized_description:
            return ResumeChangeRequestResult(
                success=False,
                message="Введите описание изменений, которые нужно отправить HR.",
            )

        stored_file: _StoredFileMeta | None = None

        try:
            if uploaded_file_path:
                stored_file = self._store_uploaded_file(
                    employee_user_id=employee_user_id,
                    source_file_path=uploaded_file_path,
                )

            with get_db_session() as session:
                request_repo = ResumeRequestRepository(session)

                section_row = request_repo.get_section_by_id(section_id)
                if not section_row:
                    raise ValueError(
                        "Выбранный раздел не найден в справочнике resume_sections."
                    )

                employee_full_name = request_repo.get_employee_full_name(employee_user_id)
                if not employee_full_name:
                    raise ValueError(
                        "Не удалось определить сотрудника, который отправляет заявку."
                    )

                proposed_payload_json = json.dumps(
                    {
                        "submitted_via": "employee_personal_data_form",
                        "has_attachment": bool(stored_file),
                    },
                    ensure_ascii=False,
                )

                request_id = request_repo.create_resume_change_request(
                    employee_user_id=employee_user_id,
                    section_id=section_id,
                    change_description=normalized_description,
                    proposed_payload_json=proposed_payload_json,
                )

                if stored_file:
                    request_repo.create_employee_document_for_request(
                        owner_user_id=employee_user_id,
                        request_id=request_id,
                        file_path=stored_file.file_path_relative,
                        original_filename=stored_file.original_filename,
                        mime_type=stored_file.mime_type,
                        file_size_bytes=stored_file.file_size_bytes,
                        file_checksum=stored_file.file_checksum,
                    )

                notification_id = request_repo.create_hr_notification(
                    employee_user_id=employee_user_id,
                    request_id=request_id,
                    employee_full_name=employee_full_name,
                    section_name=str(section_row["name"]),
                    file_attached=bool(stored_file),
                )

                hr_user_ids = request_repo.get_active_hr_user_ids()
                request_repo.add_notification_recipients(
                    notification_id=notification_id,
                    recipient_user_ids=hr_user_ids,
                )

            return ResumeChangeRequestResult(
                success=True,
                message=(
                    "Заявка успешно отправлена HR. "
                    "Изменения сохранены в базе как запрос на обновление резюме."
                ),
            )

        except ValueError as exc:
            if stored_file:
                self._remove_stored_file_safely(stored_file.file_path_absolute)

            return ResumeChangeRequestResult(
                success=False,
                message=str(exc),
            )

        except SQLAlchemyError:
            if stored_file:
                self._remove_stored_file_safely(stored_file.file_path_absolute)

            return ResumeChangeRequestResult(
                success=False,
                message=(
                    "Не удалось сохранить заявку: база данных недоступна "
                    "или вернула ошибку при записи."
                ),
            )

        except OSError:
            return ResumeChangeRequestResult(
                success=False,
                message=(
                    "Не удалось сохранить прикреплённый файл. "
                    "Проверьте права доступа к папке uploads и повторите попытку."
                ),
            )

        except Exception as exc:
            if stored_file:
                self._remove_stored_file_safely(stored_file.file_path_absolute)

            return ResumeChangeRequestResult(
                success=False,
                message=f"Непредвиденная ошибка при отправке заявки: {exc}",
            )

    # =========================================================
    # Внутренние методы форматирования резюме
    # =========================================================
    def _format_gender(self, value: str | None) -> str:
        mapping = {
            "male": "Мужской",
            "female": "Женский",
            "other": "Другое",
            "unspecified": "Не указано",
        }
        return mapping.get((value or "").strip().lower(), "Не указано")

    def _format_date_or_placeholder(self, value: date | datetime | None) -> str:
        if not value:
            return "Не указано"

        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")

        return value.strftime("%d.%m.%Y")

    def _format_optional_text(self, value: str | None) -> str:
        normalized = (value or "").strip()
        return normalized if normalized else "Не указано"

    def _format_driver_license(self, value: str | None) -> str:
        normalized = (value or "").strip()
        if not normalized:
            return "Не указано"

        return f"Категории: {normalized}"

    def _format_criminal_record(self, has_criminal_record, details: str | None) -> str:
        if bool(has_criminal_record):
            normalized_details = (details or "").strip()
            if normalized_details:
                return f"Есть сведения: {normalized_details}"
            return "Есть сведения"

        return "Отсутствует"

    def _format_education_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        level_mapping = {
            "secondary_special": "Среднее специальное",
            "bachelor": "Бакалавриат",
            "specialist": "Специалитет",
            "master": "Магистратура",
            "postgraduate": "Аспирантура",
            "other": "Иное",
        }

        lines: list[str] = []

        for row in rows:
            parts = []

            level = level_mapping.get(str(row.get("education_level") or "").lower(), "Образование")
            institution_name = row.get("institution_name")
            specialization = row.get("specialization")
            faculty = row.get("faculty")
            graduation_year = row.get("graduation_year")
            is_current = bool(row.get("is_current"))

            parts.append(level)

            if institution_name:
                parts.append(str(institution_name))

            if specialization:
                parts.append(str(specialization))

            if faculty:
                parts.append(f"факультет: {faculty}")

            if graduation_year:
                parts.append(f"год выпуска: {graduation_year}")
            elif is_current:
                parts.append("обучение продолжается")

            lines.append(" — ".join(parts))

        return lines

    def _format_diploma_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        honors_mapping = {
            "none": "",
            "red": "с отличием",
            "gold": "золотой диплом",
            "other": "с отличием",
        }

        lines: list[str] = []

        for row in rows:
            parts = []

            qualification_title = row.get("qualification_title")
            diploma_series = row.get("diploma_series")
            diploma_number = row.get("diploma_number")
            honors_type = honors_mapping.get(str(row.get("honors_type") or "").lower(), "")
            issued_at = row.get("issued_at")

            if qualification_title:
                parts.append(str(qualification_title))

            number_parts = []
            if diploma_series:
                number_parts.append(f"серия {diploma_series}")
            if diploma_number:
                number_parts.append(f"№ {diploma_number}")

            if number_parts:
                parts.append(" ".join(number_parts))

            if honors_type:
                parts.append(honors_type)

            if issued_at:
                parts.append(f"выдан {self._format_date_or_placeholder(issued_at)}")

            lines.append(" — ".join(parts) if parts else "Диплом без подробностей")

        return lines

    def _format_work_experience_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        lines: list[str] = []

        for row in rows:
            company_name = str(row.get("company_name") or "Компания не указана")
            position_title = str(row.get("position_title") or "Должность не указана")
            start_date = row.get("start_date")
            end_date = row.get("end_date")
            is_current = bool(row.get("is_current"))

            period_text = self._format_period(start_date, end_date, is_current)
            main_line = f"{company_name} — {position_title} ({period_text})"
            lines.append(main_line)

            achievements = (row.get("achievements") or "").strip()
            if achievements:
                lines.append(f"   Достижения: {achievements}")

            responsibilities = (row.get("responsibilities") or "").strip()
            if responsibilities:
                lines.append(f"   Ответственность: {responsibilities}")

        return lines

    def _format_competition_participation_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        lines: list[str] = []

        for row in rows:
            competition_name = str(row.get("competition_name") or "Соревнование")
            competition_level = str(row.get("competition_level") or "").strip()
            event_date = row.get("event_date")

            suffix = []
            if competition_level:
                suffix.append(competition_level)
            if event_date:
                suffix.append(self._format_date_or_placeholder(event_date))

            if suffix:
                lines.append(f"{competition_name} ({', '.join(suffix)})")
            else:
                lines.append(competition_name)

        return lines

    def _format_competition_awards_lines(self, rows) -> list[str]:
        if not rows:
            return ["Подтверждённых призовых мест пока нет."]

        lines: list[str] = []

        for row in rows:
            competition_name = str(row.get("competition_name") or "Соревнование")
            placement_name = (row.get("placement_name") or "").strip()
            award_title = (row.get("award_title") or "").strip()
            event_date = row.get("event_date")

            pieces = [competition_name]

            award_details = []
            if placement_name:
                award_details.append(placement_name)
            if award_title:
                award_details.append(award_title)
            if event_date:
                award_details.append(self._format_date_or_placeholder(event_date))

            if award_details:
                pieces.append(" — " + ", ".join(award_details))

            lines.append("".join(pieces))

        return lines

    def _format_skill_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        proficiency_mapping = {
            "beginner": "начальный уровень",
            "junior": "junior",
            "middle": "middle",
            "senior": "senior",
            "expert": "expert",
        }

        lines: list[str] = []

        for row in rows:
            skill_name = str(row.get("skill_name") or "Навык")
            proficiency_level = proficiency_mapping.get(
                str(row.get("proficiency_level") or "").lower(),
                "уровень не указан",
            )
            years_experience = row.get("years_experience")

            if years_experience is not None:
                lines.append(f"{skill_name} — {proficiency_level}, опыт: {years_experience} лет")
            else:
                lines.append(f"{skill_name} — {proficiency_level}")

        return lines

    def _format_additional_course_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        lines: list[str] = []

        for row in rows:
            course_name = str(row.get("course_name") or "Курс")
            provider_name = (row.get("provider_name") or "").strip()
            completed_at = row.get("completed_at")
            status = str(row.get("status") or "").strip()

            parts = [course_name]

            if provider_name:
                parts.append(provider_name)
            if completed_at:
                parts.append(f"завершён {self._format_date_or_placeholder(completed_at)}")
            if status:
                parts.append(f"статус: {status}")

            lines.append(" — ".join(parts))

        return lines

    def _format_qualification_course_lines(self, rows) -> list[str]:
        if not rows:
            return ["Данные пока не заполнены."]

        lines: list[str] = []

        for row in rows:
            course_name = str(row.get("course_name") or "Курс")
            provider_name = (row.get("provider_name") or "").strip()
            completed_at = row.get("completed_at")
            valid_until = row.get("valid_until")
            status = str(row.get("status") or "").strip()

            parts = [course_name]

            if provider_name:
                parts.append(provider_name)
            if completed_at:
                parts.append(f"пройден {self._format_date_or_placeholder(completed_at)}")
            if valid_until:
                parts.append(f"действует до {self._format_date_or_placeholder(valid_until)}")
            if status:
                parts.append(f"статус: {status}")

            lines.append(" — ".join(parts))

        return lines

    def _format_period(
        self,
        start_date: date | datetime | None,
        end_date: date | datetime | None,
        is_current: bool,
    ) -> str:
        start_text = self._format_date_or_placeholder(start_date) if start_date else "дата не указана"
        end_text = "н.в." if is_current else (self._format_date_or_placeholder(end_date) if end_date else "дата не указана")
        return f"{start_text} — {end_text}"

    # =========================================================
    # Работа с файлами
    # =========================================================
    def _store_uploaded_file(self, employee_user_id: int, source_file_path: str) -> _StoredFileMeta:
        """
        Копирует файл из временного каталога Gradio в постоянную папку проекта.
        """
        source_path = Path(source_file_path)
        if not source_path.exists():
            raise OSError("Загруженный файл не найден во временной папке Gradio.")

        # Формируем "безопасное" имя файла.
        safe_name = self._sanitize_filename(source_path.name)
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}_{safe_name}"

        destination_dir = (
            self.settings.uploads_root_dir
            / "resume_change_requests"
            / str(employee_user_id)
        )
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination_path = destination_dir / unique_name

        # Копируем файл в проект.
        shutil.copy2(source_path, destination_path)

        file_size_bytes = destination_path.stat().st_size
        file_checksum = self._calculate_sha256(destination_path)
        mime_type = mimetypes.guess_type(destination_path.name)[0]

        # Храним в БД относительный путь, чтобы проект был переносимее.
        relative_path = destination_path.relative_to(self.settings.base_dir).as_posix()

        return _StoredFileMeta(
            file_path_relative=relative_path,
            original_filename=source_path.name,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            file_checksum=file_checksum,
            file_path_absolute=destination_path,
        )

    def _remove_stored_file_safely(self, path: Path) -> None:
        """
        Аккуратно удаляет файл, если после его копирования произошла ошибка.
        """
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    def _sanitize_filename(self, filename: str) -> str:
        """
        Делает имя файла безопасным для хранения.
        """
        sanitized = re.sub(r"[^0-9A-Za-zА-Яа-я._-]+", "_", filename).strip("._")
        return sanitized or "uploaded_file"
    
    def _calculate_sha256(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()