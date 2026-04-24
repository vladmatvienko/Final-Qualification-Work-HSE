"""
Service-слой вкладки HR "Уведомления".
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session
from app.models.hr_notification_models import (
    HRNotificationActionResult,
    HRNotificationCardViewModel,
    HRNotificationsDashboardViewModel,
)
from app.repositories.hr_notification_repository import HRNotificationRepository


_QUEUE_STATUS_LABELS = {
    "unread": "Новое",
    "read": "Прочитано",
    "archived": "Обработано",
}

_RESUME_STATUS_LABELS = {
    "pending": "Ожидает рассмотрения",
    "approved": "Одобрено",
    "rejected": "Отклонено",
    "needs_clarification": "Нужно уточнение",
    "implemented": "Внедрено",
}

_BONUS_STATUS_LABELS = {
    "pending_hr": "Ожидает решения HR",
    "approved": "Одобрено",
    "rejected": "Отклонено",
    "cancelled": "Отменено",
}

_NOTIFICATION_TYPE_LABELS = {
    "resume_change_request": "Изменение резюме",
    "bonus_purchase": "Покупка бонуса",
    "course_expiry": "Истекающий курс",
}


class HRNotificationService:
    """
    Главный сервис вкладки HR "Уведомления".
    """

    COURSE_DAYS_BEFORE_EXPIRY = 30

    # =========================================================
    # ПУБЛИЧНЫЕ МЕТОДЫ
    # =========================================================
    def get_dashboard(
        self,
        hr_user_id: int,
        type_filter: str = "all",
        status_filter: str = "all",
    ) -> HRNotificationsDashboardViewModel:
        """
        Загружает dashboard HR-уведомлений.
        """
        if not hr_user_id:
            return HRNotificationsDashboardViewModel(
                total_count=0,
                unread_count=0,
                items=[],
                db_available=False,
                load_error_message="HR-пользователь не определён.",
            )

        try:
            with get_db_session() as session:
                repo = HRNotificationRepository(session)

                self._generate_course_expiry_notifications(repo)

                items: list[HRNotificationCardViewModel] = []
                items.extend(self._build_resume_items(repo.get_resume_change_notifications(hr_user_id)))
                items.extend(self._build_bonus_items(repo.get_bonus_purchase_notifications(hr_user_id)))
                items.extend(self._build_course_items(repo.get_course_expiry_notifications(hr_user_id)))

                filtered_items = [
                    item
                    for item in items
                    if self._matches_filters(item, type_filter=type_filter, status_filter=status_filter)
                ]

                filtered_items.sort(
                    key=lambda item: (
                        0 if item.queue_status_code == "unread" else 1,
                        item.event_date_label,
                        item.queue_record_id,
                    ),
                    reverse=False,
                )

                unread_count = sum(1 for item in items if item.queue_status_code == "unread")

                return HRNotificationsDashboardViewModel(
                    total_count=len(filtered_items),
                    unread_count=unread_count,
                    items=filtered_items,
                    db_available=True,
                    load_error_message=None,
                )

        except SQLAlchemyError:
            return HRNotificationsDashboardViewModel(
                total_count=0,
                unread_count=0,
                items=[],
                db_available=False,
                load_error_message="База данных недоступна. HR-уведомления сейчас не удалось загрузить.",
            )

    def mark_as_read(
        self,
        hr_user_id: int,
        source_type_code: str,
        queue_record_id: int,
    ) -> HRNotificationActionResult:
        """
        Помечает уведомление как прочитанное.
        """
        if not hr_user_id:
            return HRNotificationActionResult(
                success=False,
                message="HR-пользователь не определён.",
            )

        try:
            with get_db_session() as session:
                repo = HRNotificationRepository(session)

                if source_type_code == "resume_change_request":
                    existing = repo.get_resume_change_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) != "unread":
                        return HRNotificationActionResult(True, "Уведомление уже открывалось ранее.")
                    repo.mark_resume_change_notification_as_read(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Уведомление помечено как прочитанное.")

                if source_type_code == "bonus_purchase":
                    existing = repo.get_bonus_purchase_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) != "unread":
                        return HRNotificationActionResult(True, "Уведомление уже открывалось ранее.")
                    repo.mark_bonus_purchase_notification_as_read(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Уведомление помечено как прочитанное.")

                if source_type_code == "course_expiry":
                    existing = repo.get_course_expiry_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) != "unread":
                        return HRNotificationActionResult(True, "Уведомление уже открывалось ранее.")
                    repo.mark_course_expiry_notification_as_read(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Уведомление помечено как прочитанное.")

                return HRNotificationActionResult(False, "Неизвестный тип уведомления.")

        except SQLAlchemyError:
            return HRNotificationActionResult(
                success=False,
                message="База данных недоступна. Не удалось обновить статус уведомления.",
            )

    def mark_as_processed(
        self,
        hr_user_id: int,
        source_type_code: str,
        queue_record_id: int,
    ) -> HRNotificationActionResult:
        """
        Переводит уведомление в статус 'обработано'.
        """
        if not hr_user_id:
            return HRNotificationActionResult(
                success=False,
                message="HR-пользователь не определён.",
            )

        try:
            with get_db_session() as session:
                repo = HRNotificationRepository(session)

                if source_type_code == "resume_change_request":
                    existing = repo.get_resume_change_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) == "archived":
                        return HRNotificationActionResult(True, "Уведомление уже отмечено как обработанное.")
                    repo.archive_resume_change_notification(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Resume-уведомление отмечено как обработанное.")

                if source_type_code == "bonus_purchase":
                    existing = repo.get_bonus_purchase_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) == "archived":
                        return HRNotificationActionResult(True, "Уведомление уже отмечено как обработанное.")
                    repo.archive_bonus_purchase_notification(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Уведомление по покупке бонуса отмечено как обработанное.")

                if source_type_code == "course_expiry":
                    existing = repo.get_course_expiry_notification_by_queue_id(hr_user_id, queue_record_id)
                    if not existing:
                        return HRNotificationActionResult(False, "Уведомление не найдено.")
                    if str(existing["queue_status"]) == "archived":
                        return HRNotificationActionResult(True, "Уведомление уже отмечено как обработанное.")
                    repo.archive_course_expiry_notification(hr_user_id, queue_record_id)
                    return HRNotificationActionResult(True, "Уведомление по курсу отмечено как обработанное.")

                return HRNotificationActionResult(False, "Неизвестный тип уведомления.")

        except SQLAlchemyError:
            return HRNotificationActionResult(
                success=False,
                message="База данных недоступна. Не удалось отметить уведомление как обработанное.",
            )

    def send_course_reminder_to_employee(
        self,
        hr_user_id: int,
        queue_record_id: int,
    ) -> HRNotificationActionResult:
        """
        Отправляет сотруднику универсальное уведомление по истекающему курсу.
        """
        if not hr_user_id:
            return HRNotificationActionResult(
                success=False,
                message="HR-пользователь не определён.",
            )

        try:
            with get_db_session() as session:
                repo = HRNotificationRepository(session)
                row = repo.get_course_expiry_notification_by_queue_id(hr_user_id, queue_record_id)

                if not row:
                    return HRNotificationActionResult(
                        success=False,
                        message="Уведомление по курсу не найдено.",
                    )

                qualification_course_id = int(row["qualification_course_id"])
                employee_user_id = int(row["employee_user_id"])
                course_name = str(row["course_name"] or "Курс повышения квалификации")
                valid_until = row["valid_until"]

                if repo.employee_course_reminder_exists_today(
                    employee_user_id=employee_user_id,
                    qualification_course_id=qualification_course_id,
                ):
                    return HRNotificationActionResult(
                        success=True,
                        message="Напоминание по этому курсу уже отправлялось сегодня. Дубликат предотвращён.",
                    )

                if valid_until:
                    valid_until_text = valid_until.strftime("%d.%m.%Y")
                else:
                    valid_until_text = "дата не указана"

                title = "Пора обновить курс повышения квалификации"
                message = (
                    f"Срок действия курса «{course_name}» подходит к завершению "
                    f"({valid_until_text}). Пожалуйста, запланируйте обновление заранее."
                )

                repo.create_employee_course_reminder(
                    hr_user_id=hr_user_id,
                    employee_user_id=employee_user_id,
                    qualification_course_id=qualification_course_id,
                    title=title,
                    message=message,
                )
                repo.mark_course_employee_reminder_sent(hr_user_id, queue_record_id)

                return HRNotificationActionResult(
                    success=True,
                    message="Напоминание сотруднику отправлено.",
                )

        except SQLAlchemyError:
            return HRNotificationActionResult(
                success=False,
                message="База данных недоступна. Не удалось отправить напоминание сотруднику.",
            )

    # =========================================================
    # ГЕНЕРАЦИЯ HR-УВЕДОМЛЕНИЙ ПО КУРСАМ
    # =========================================================
    def _generate_course_expiry_notifications(self, repo: HRNotificationRepository) -> int:
        """
        Генерирует недостающие HR-уведомления по истекающим курсам.
        """
        created_count = 0
        hr_user_ids = repo.get_active_hr_user_ids()
        expiring_rows = repo.get_expiring_qualification_courses_for_generation(
            self.COURSE_DAYS_BEFORE_EXPIRY
        )

        for row in expiring_rows:
            qualification_course_id = int(row["qualification_course_id"])
            employee_user_id = int(row["employee_user_id"])
            employee_full_name = str(row["employee_full_name"] or f"Сотрудник #{employee_user_id}")
            course_name = str(row["course_name"] or f"Курс #{qualification_course_id}")
            valid_until = row["valid_until"]
            days_left = int(row["days_left"] or 0)

            if days_left == 0:
                days_part = "сегодня"
            elif days_left == 1:
                days_part = "через 1 день"
            else:
                days_part = f"через {days_left} дн."

            valid_until_text = valid_until.strftime("%d.%m.%Y") if valid_until else "дата не указана"

            title = "Истекает срок действия курса"
            message = (
                f"У сотрудника {employee_full_name} скоро заканчивается курс "
                f"«{course_name}»: {valid_until_text} ({days_part}). "
                f"При необходимости отправьте сотруднику напоминание."
            )

            for hr_user_id in hr_user_ids:
                created = repo.create_hr_course_expiry_notification_if_missing(
                    qualification_course_id=qualification_course_id,
                    hr_user_id=hr_user_id,
                    employee_user_id=employee_user_id,
                    title=title,
                    message=message,
                )
                if created:
                    created_count += 1

        return created_count

    # =========================================================
    # СБОРКА VIEW-MODEL
    # =========================================================
    def _build_resume_items(self, rows) -> list[HRNotificationCardViewModel]:
        items: list[HRNotificationCardViewModel] = []

        for row in rows:
            queue_status_code = str(row["queue_status"])
            request_status_code = str(row["request_status"])

            submitted_at = row["submitted_at"] or row["notification_created_at"]
            event_date_label = self._format_datetime(submitted_at)

            attachment_name = row["attachment_original_filename"]
            has_attachment_text = (
                f"Вложение: {attachment_name}"
                if attachment_name
                else "Вложение не приложено"
            )

            summary_text = (
                f"Раздел: {row['section_name']}. "
                f"{has_attachment_text}."
            )

            items.append(
                HRNotificationCardViewModel(
                    queue_record_id=int(row["queue_record_id"]),
                    source_type_code="resume_change_request",
                    source_type_label=_NOTIFICATION_TYPE_LABELS["resume_change_request"],
                    queue_status_code=queue_status_code,
                    queue_status_label=_QUEUE_STATUS_LABELS.get(queue_status_code, queue_status_code),
                    business_status_code=request_status_code,
                    business_status_label=_RESUME_STATUS_LABELS.get(request_status_code, request_status_code),
                    employee_user_id=int(row["employee_user_id"]),
                    employee_full_name=str(row["employee_full_name"] or "Неизвестный сотрудник"),
                    title=str(row["notification_title"]),
                    summary_text=summary_text,
                    event_date_label=event_date_label,
                    can_mark_processed=True,
                    can_send_reminder=False,
                    resume_request_id=int(row["request_id"]),
                    resume_section_name=str(row["section_name"]),
                    resume_change_description=str(row["change_description"]),
                    attachment_original_filename=str(attachment_name) if attachment_name else None,
                    attachment_file_path=str(row["attachment_file_path"]) if row["attachment_file_path"] else None,
                    attachment_mime_type=str(row["attachment_mime_type"]) if row["attachment_mime_type"] else None,
                    attachment_size_bytes=int(row["attachment_size_bytes"]) if row["attachment_size_bytes"] is not None else None,
                )
            )

        return items

    def _build_bonus_items(self, rows) -> list[HRNotificationCardViewModel]:
        items: list[HRNotificationCardViewModel] = []

        for row in rows:
            queue_status_code = str(row["queue_status"])
            purchase_status_code = str(row["purchase_status"])
            requested_at = row["requested_at"] or row["queue_created_at"]

            summary_text = (
                f"Бонус: {row['bonus_name']}. "
                f"Стоимость: {int(row['bonus_cost_points'])} баллов."
            )

            items.append(
                HRNotificationCardViewModel(
                    queue_record_id=int(row["queue_record_id"]),
                    source_type_code="bonus_purchase",
                    source_type_label=_NOTIFICATION_TYPE_LABELS["bonus_purchase"],
                    queue_status_code=queue_status_code,
                    queue_status_label=_QUEUE_STATUS_LABELS.get(queue_status_code, queue_status_code),
                    business_status_code=purchase_status_code,
                    business_status_label=_BONUS_STATUS_LABELS.get(purchase_status_code, purchase_status_code),
                    employee_user_id=int(row["employee_user_id"]),
                    employee_full_name=str(row["employee_full_name"] or "Неизвестный сотрудник"),
                    title=str(row["notification_title"]),
                    summary_text=summary_text,
                    event_date_label=self._format_datetime(requested_at),
                    can_mark_processed=True,
                    can_send_reminder=False,
                    bonus_purchase_id=int(row["purchase_id"]),
                    bonus_name=str(row["bonus_name"]),
                    bonus_cost_points=int(row["bonus_cost_points"]),
                    bonus_requested_at_label=self._format_datetime(requested_at),
                )
            )

        return items

    def _build_course_items(self, rows) -> list[HRNotificationCardViewModel]:
        items: list[HRNotificationCardViewModel] = []

        for row in rows:
            queue_status_code = str(row["queue_status"])
            reminder_sent = row["reminder_sent_at"] is not None
            valid_until = row["valid_until"]

            reminder_needed_label = (
                "Напоминание уже отправлено"
                if reminder_sent
                else "Нужно напомнить сотруднику"
            )

            items.append(
                HRNotificationCardViewModel(
                    queue_record_id=int(row["queue_record_id"]),
                    source_type_code="course_expiry",
                    source_type_label=_NOTIFICATION_TYPE_LABELS["course_expiry"],
                    queue_status_code=queue_status_code,
                    queue_status_label=_QUEUE_STATUS_LABELS.get(queue_status_code, queue_status_code),
                    business_status_code="reminder_sent" if reminder_sent else "reminder_needed",
                    business_status_label="Напоминание отправлено" if reminder_sent else "Нужно напомнить",
                    employee_user_id=int(row["employee_user_id"]),
                    employee_full_name=str(row["employee_full_name"] or "Неизвестный сотрудник"),
                    title=str(row["notification_title"]),
                    summary_text=f"Курс: {row['course_name']}.",
                    event_date_label=self._format_datetime(row["queue_created_at"]),
                    can_mark_processed=True,
                    can_send_reminder=not reminder_sent,
                    reminder_sent=reminder_sent,
                    reminder_sent_label=(
                        self._format_datetime(row["reminder_sent_at"])
                        if row["reminder_sent_at"] is not None
                        else None
                    ),
                    qualification_course_id=int(row["qualification_course_id"]),
                    qualification_course_name=str(row["course_name"]),
                    qualification_valid_until_label=self._format_date(valid_until),
                    reminder_needed_label=reminder_needed_label,
                )
            )

        return items

    # =========================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =========================================================
    def _matches_filters(
        self,
        item: HRNotificationCardViewModel,
        type_filter: str,
        status_filter: str,
    ) -> bool:
        """
        Проверяет, проходит ли карточка под выбранные фильтры.
        """
        normalized_type = (type_filter or "all").strip().lower()
        normalized_status = (status_filter or "all").strip().lower()

        if normalized_type != "all" and item.source_type_code != normalized_type:
            return False

        if normalized_status == "all":
            return True

        candidate_status_codes = {item.queue_status_code}
        if item.business_status_code:
            candidate_status_codes.add(item.business_status_code)

        return normalized_status in candidate_status_codes

    def _format_datetime(self, value) -> str:
        """
        Форматирует datetime в UI.
        """
        if value is None:
            return "Дата неизвестна"

        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y %H:%M")

        if isinstance(value, date):
            return value.strftime("%d.%m.%Y")

        return str(value)

    def _format_date(self, value) -> str:
        """
        Форматирует дату без времени.
        """
        if value is None:
            return "Дата неизвестна"

        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")

        if isinstance(value, date):
            return value.strftime("%d.%m.%Y")

        return str(value)