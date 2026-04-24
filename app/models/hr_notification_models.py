"""
View-модели для вкладки HR "Уведомления".
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HRNotificationCardViewModel:
    """
    Одна карточка уведомления HR в единой ленте.
    """
    queue_record_id: int
    source_type_code: str
    source_type_label: str

    queue_status_code: str
    queue_status_label: str

    business_status_code: str | None
    business_status_label: str | None

    employee_user_id: int
    employee_full_name: str

    title: str
    summary_text: str
    event_date_label: str

    can_mark_processed: bool
    can_send_reminder: bool

    reminder_sent: bool = False
    reminder_sent_label: str | None = None

    # Поля для уведомления по изменению резюме
    resume_request_id: int | None = None
    resume_section_name: str | None = None
    resume_change_description: str | None = None
    attachment_original_filename: str | None = None
    attachment_file_path: str | None = None
    attachment_mime_type: str | None = None
    attachment_size_bytes: int | None = None

    # Поля для уведомления о покупке бонуса
    bonus_purchase_id: int | None = None
    bonus_name: str | None = None
    bonus_cost_points: int | None = None
    bonus_requested_at_label: str | None = None

    # Поля для уведомления по курсу
    qualification_course_id: int | None = None
    qualification_course_name: str | None = None
    qualification_valid_until_label: str | None = None
    reminder_needed_label: str | None = None


@dataclass(frozen=True)
class HRNotificationsDashboardViewModel:
    """
    Полный dashboard вкладки HR "Уведомления".
    """
    total_count: int
    unread_count: int
    items: list[HRNotificationCardViewModel] = field(default_factory=list)
    db_available: bool = True
    load_error_message: str | None = None


@dataclass(frozen=True)
class HRNotificationActionResult:
    """
    Результат пользовательского действия HR над уведомлением.
    """
    success: bool
    message: str