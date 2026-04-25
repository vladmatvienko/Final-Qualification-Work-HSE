from app.models.hr_notification_models import HRNotificationCardViewModel
from app.ui.hr_runtime_screen import _should_show_send_reminder


def test_bonus_purchase_never_shows_send_reminder_button():
    item = HRNotificationCardViewModel(
        queue_record_id=1,
        source_type_code="bonus_purchase",
        source_type_label="Покупка бонуса",
        queue_status_code="read",
        queue_status_label="Прочитано",
        business_status_code="pending_hr",
        business_status_label="Ожидает решения HR",
        employee_user_id=2001,
        employee_full_name="Тестовый сотрудник",
        title="Новая заявка на бонус",
        summary_text="Бонус",
        event_date_label="25.04.2026",
        can_mark_processed=True,
        can_send_reminder=True,
    )

    assert _should_show_send_reminder(item, is_selected=True) is False


def test_course_expiry_can_show_send_reminder_button():
    item = HRNotificationCardViewModel(
        queue_record_id=2,
        source_type_code="course_expiry",
        source_type_label="Истекающий курс",
        queue_status_code="read",
        queue_status_label="Прочитано",
        business_status_code="reminder_needed",
        business_status_label="Нужно напомнить",
        employee_user_id=2001,
        employee_full_name="Тестовый сотрудник",
        title="Истекает курс",
        summary_text="Курс",
        event_date_label="25.04.2026",
        can_mark_processed=True,
        can_send_reminder=True,
    )

    assert _should_show_send_reminder(item, is_selected=True) is True