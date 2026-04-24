"""
Моковый сервис HR-менеджера.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.models.hr_view_models import (
    CandidateTableRow,
    HRDashboardViewModel,
    HRNotificationCard,
)


def get_mock_hr_dashboard() -> HRDashboardViewModel:
    """
    Возвращает моковые данные для HR-экрана.
    """
    settings = get_settings()

    return HRDashboardViewModel(
        full_name=settings.demo_hr_name,
        role_label="HR-менеджер",
        unread_notifications_count=3,
        default_requirements_text=(
            "Нужен сотрудник на позицию Python Backend Developer: "
            "опыт Python, MySQL, API-интеграций, понимание внутренних платформ "
            "и готовность работать с AI/RAG-направлением."
        ),
        candidates=[
            CandidateTableRow(
                anonymous_code="CAND-001",
                target_position="Python Backend Developer",
                fit_score="94%",
                key_strengths="Python, MySQL, API, backend-архитектура",
                readiness_status="Сильное совпадение",
            ),
            CandidateTableRow(
                anonymous_code="CAND-002",
                target_position="Python Backend Developer",
                fit_score="81%",
                key_strengths="Python, QA automation, SQL, процессы качества",
                readiness_status="Хорошее совпадение",
            ),
            CandidateTableRow(
                anonymous_code="CAND-003",
                target_position="Python Backend Developer",
                fit_score="73%",
                key_strengths="Product mindset, SQL, внутренние сервисы",
                readiness_status="Частичное совпадение",
            ),
        ],
        notifications=[
            HRNotificationCard(
                title="Новая заявка на изменение резюме",
                description=(
                    "Сотрудник отправил обновление по блоку образования и прикрепил "
                    "подтверждающий файл. На следующем этапе здесь будет ссылка на детальный просмотр."
                ),
                priority_label="Высокий приоритет",
                status_label="Новое",
            ),
            HRNotificationCard(
                title="Новая заявка на покупку бонуса",
                description=(
                    "В магазин поступила новая заявка на покупку бонуса за очки. "
                    "Позже здесь появится кнопка согласования / отклонения."
                ),
                priority_label="Обычный приоритет",
                status_label="Новое",
            ),
            HRNotificationCard(
                title="Сотрудникам нужно напомнить об истечении курсов",
                description=(
                    "Система обнаружила сотрудников, у которых скоро истекает срок действия "
                    "курсов повышения квалификации. На следующих этапах уведомления станут живыми."
                ),
                priority_label="Инфо",
                status_label="Системное",
            ),
        ],
    )