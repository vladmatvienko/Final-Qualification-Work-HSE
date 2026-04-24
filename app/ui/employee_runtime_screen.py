from __future__ import annotations

import uuid
from base64 import b64encode
from pathlib import Path
from html import escape

import gradio as gr

from app.auth.session_state import AuthSession
from app.models.employee_view_models import (
    TAB_ACHIEVEMENTS,
    TAB_NOTIFICATIONS,
    TAB_PERSONAL,
    TAB_STORE,
)
from app.services.employee_achievement_service import EmployeeAchievementService
from app.services.employee_mock_service import get_mock_employee_dashboard
from app.services.employee_notification_service import EmployeeNotificationService
from app.services.employee_personal_data_service import EmployeePersonalDataService
from app.services.employee_store_service import EmployeeStoreService


PERSONAL_DATA_SERVICE = EmployeePersonalDataService()
ACHIEVEMENT_SERVICE = EmployeeAchievementService()
STORE_SERVICE = EmployeeStoreService()
NOTIFICATION_SERVICE = EmployeeNotificationService()

MAX_STORE_SLOTS = 15
MAX_NOTIFICATION_SLOTS = 20


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = PROJECT_ROOT / "assets" / "Logo.png"


def _get_logo_data_uri() -> str:
    """
    Загружает логотип приложения из assets/Logo.png
    """
    if not LOGO_PATH.exists():
        return ""

    encoded = b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


LOGO_DATA_URI = _get_logo_data_uri()


def _render_employee_active_tab_style(selected_tab_code: str | None) -> str:
    """
    CSS-переключатель вкладок сотрудника.
    """
    selected_tab_code = selected_tab_code or TAB_PERSONAL
    allowed_tabs = {TAB_PERSONAL, TAB_ACHIEVEMENTS, TAB_STORE, TAB_NOTIFICATIONS}
    if selected_tab_code not in allowed_tabs:
        selected_tab_code = TAB_PERSONAL

    def display_for(tab_code: str) -> str:
        return "block" if selected_tab_code == tab_code else "none"

    return f"""
    <style id="employee-active-tab-style">
        #employee-tab-personal {{ display: {display_for(TAB_PERSONAL)} !important; }}
        #employee-tab-achievements {{ display: {display_for(TAB_ACHIEVEMENTS)} !important; }}
        #employee-tab-store {{ display: {display_for(TAB_STORE)} !important; }}
        #employee-tab-notifications {{ display: {display_for(TAB_NOTIFICATIONS)} !important; }}
    </style>
    """


def _render_brand_html(app_title: str) -> str:
    return f"""
    <div class="brand-box">
        <div class="brand-row">
            <div class="brand-logo">
                <img src="{LOGO_DATA_URI}" alt="Логотип Эльбрус">
            </div>
            <div>
                <div class="brand-title">{escape(app_title)}</div>
                <div class="brand-subtitle">Платформа развития сотрудника</div>
            </div>
        </div>
    </div>
    """


def _render_header_html(full_name: str, achievements_done: int, achievements_total: int, points: int) -> str:
    return f"""
    <div class="employee-header">
        <div class="employee-header-main">
            <div class="employee-header-label">Профиль сотрудника</div>
            <div class="employee-name">{escape(full_name)}</div>
            <div class="employee-header-subtitle">
                Вы авторизованы в системе. Данные вкладок загружаются из MySQL.
            </div>
        </div>
        <div class="employee-metrics">
            <div class="metric-chip">
                <div class="metric-label">Достижения</div>
                <div class="metric-value">{achievements_done}/{achievements_total}</div>
            </div>
            <div class="metric-chip">
                <div class="metric-label">Очки</div>
                <div class="metric-value">{points}</div>
            </div>
        </div>
    </div>
    """


def _render_page_header(title: str, subtitle: str) -> str:
    return f"""
    <div class="page-title-row">
        <div class="page-title">{escape(title)}</div>
        <div class="page-subtitle">{escape(subtitle)}</div>
    </div>
    """


def _render_stub_banner(text: str) -> str:
    return f'<div class="stub-banner">{escape(text)}</div>'


def _render_feedback_html(message: str, kind: str) -> str:
    if not message:
        return ""

    normalized_kind = kind if kind in {"success", "error", "info"} else "info"
    return f'<div class="feedback-box feedback-box--{normalized_kind}">{escape(message)}</div>'


def _render_resume_sections_html(personal_data) -> str:
    if not personal_data.sections:
        return '<div class="resume-line">Данные пока недоступны.</div>'

    sections_html_parts: list[str] = []

    for section in personal_data.sections:
        lines_html = "".join(
            f'<div class="resume-line">{escape(line)}</div>'
            for line in section.lines
        )

        sections_html_parts.append(
            f"""
            <div class="resume-section">
                <div class="resume-section-title">{escape(section.title)}</div>
                {lines_html}
            </div>
            """
        )

    return "".join(sections_html_parts)


def _render_achievement_card(card) -> str:
    card_class = (
        "achievement-card achievement-card--completed"
        if card.completed
        else "achievement-card achievement-card--locked"
    )
    pill_class = (
        "status-pill status-pill--done"
        if card.completed
        else "status-pill status-pill--todo"
    )

    return f"""
    <div class="{card_class}">
        <div class="card-icon">{escape(card.icon)}</div>
        <div class="card-title">{escape(card.title)} ({card.points})</div>
        <div class="card-text">{escape(card.description)}</div>
        <div class="{pill_class}">{escape(card.status_label)}</div>
    </div>
    """


def _render_achievements_page_html(achievement_dashboard) -> str:
    cards_html = "".join(_render_achievement_card(card) for card in achievement_dashboard.cards)

    return f"""
    <div class="page-card">
        {_render_page_header("Достижения", "Все достижения из каталога MySQL.")}
        {_render_stub_banner("Выполненные и невыполненные достижения различаются визуально. Повторяемые достижения могут выдаваться несколько раз.")}
        <div class="card-grid">
            {cards_html}
        </div>
    </div>
    """


def _render_store_summary_html(store_dashboard) -> str:
    if not store_dashboard.db_available:
        info_block = _render_feedback_html(
            store_dashboard.load_error_message or "Каталог магазина сейчас недоступен.",
            "error",
        )
    else:
        info_block = _render_stub_banner(
            f"Текущий баланс: {store_dashboard.points_balance} баллов. "
            f"Выберите бонус ниже. После подтверждения покупка уйдёт HR на обработку."
        )

    return f"""
    <div class="page-card">
        {_render_page_header("Магазин бонусов", "Каталог бонусов загружается из MySQL.")}
        {info_block}
    </div>
    """


def _render_store_bonus_card_html(item: dict) -> str:
    return f"""
    <div class="store-card store-card--uniform">
        <div class="card-icon">{escape(item["icon"])}</div>
        <div class="store-price">{item["cost_points"]} очков</div>
        <div class="card-title">{escape(item["title"])}</div>
        <div class="card-text">{escape(item["description"])}</div>
    </div>
    """


def _render_store_placeholder_card_html() -> str:
    return """
    <div class="store-card store-card--uniform store-card--placeholder">
        <div class="card-icon">🎁</div>
        <div class="store-price">0 очков</div>
        <div class="card-title">Пустой слот</div>
        <div class="card-text">Placeholder</div>
    </div>
    """


def _render_notifications_summary_html(notification_dashboard) -> str:
    """
    Верхний блок вкладки "Уведомления".
    """
    if not notification_dashboard.db_available:
        info_block = _render_feedback_html(
            notification_dashboard.load_error_message or "Уведомления сейчас недоступны.",
            "error",
        )
    elif notification_dashboard.total_count == 0:
        info_block = _render_stub_banner(
            "Сейчас уведомлений нет. Когда срок действия курса повышения квалификации будет подходить к концу, система создаст уведомление автоматически."
        )
    else:
        info_block = _render_stub_banner(
            f"Всего уведомлений: {notification_dashboard.total_count}. "
            f"Новых: {notification_dashboard.unread_count}. "
            f"Новые уведомления можно пометить как прочитанные."
        )

    return f"""
    <div class="page-card">
        {_render_page_header("Уведомления", "Уведомления сотрудника загружаются из MySQL.")}
        {info_block}
    </div>
    """


def _render_notification_card_html(item: dict) -> str:
    """
    HTML одной карточки уведомления.
    """
    status_class = (
        "status-pill status-pill--done"
        if item["is_read"]
        else "status-pill status-pill--todo"
    )

    return f"""
    <div class="notification-card">
        <div class="notification-top">
            <div class="notification-title">{escape(item["title"])}</div>
            <div class="notification-meta">
                <div class="priority-pill">{escape(item["date_label"])}</div>
                <div class="{status_class}">{escape(item["status_label"])}</div>
            </div>
        </div>
        <div class="notification-text">{escape(item["message"])}</div>
    </div>
    """


def _build_form_unavailable_reason(personal_data, request_section_choices: list[tuple[str, str]]) -> str:
    reasons: list[str] = []

    if not personal_data.db_available:
        reasons.append("База данных недоступна")

    if not request_section_choices:
        reasons.append("Справочник разделов резюме не загружен")

    return " | ".join(reasons)


def _build_header_html_for_user(auth_state_dict: dict | None) -> str:
    auth_session = AuthSession.from_state(auth_state_dict)

    if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
        return ""

    try:
        personal_data = PERSONAL_DATA_SERVICE.get_personal_data(auth_session.user_id)
        achievement_dashboard = ACHIEVEMENT_SERVICE.get_dashboard(auth_session.user_id)

        full_name = personal_data.full_name or auth_session.full_name or "Сотрудник"

        return _render_header_html(
            full_name=full_name,
            achievements_done=achievement_dashboard.completed_possible_count,
            achievements_total=achievement_dashboard.total_possible_count,
            points=achievement_dashboard.points_balance,
        )
    except Exception:
        full_name = auth_session.full_name or "Сотрудник"
        return _render_header_html(
            full_name=full_name,
            achievements_done=0,
            achievements_total=0,
            points=0,
        )


def _store_state_items_from_dashboard(store_dashboard) -> list[dict]:
    return [
        {
            "bonus_id": item.bonus_id,
            "code": item.code,
            "title": item.title,
            "description": item.description,
            "cost_points": item.cost_points,
            "icon": item.icon,
            "level_label": item.level_label,
            "is_affordable": item.is_affordable,
            "points_snapshot": store_dashboard.points_balance,
        }
        for item in store_dashboard.items
    ]


def _store_slot_updates_from_dashboard(store_dashboard):
    state_items = _store_state_items_from_dashboard(store_dashboard)
    updates: list = []

    for slot_index in range(MAX_STORE_SLOTS):
        if slot_index < len(state_items):
            item = state_items[slot_index]
            updates.extend(
                [
                    gr.update(visible=True),
                    _render_store_bonus_card_html(item),
                    gr.update(visible=True, interactive=True),
                ]
            )
        else:
            updates.extend(
                [
                    gr.update(visible=True),
                    _render_store_placeholder_card_html(),
                    gr.update(visible=False, interactive=False),
                ]
            )

    return state_items, updates


def _notification_state_items_from_dashboard(notification_dashboard) -> list[dict]:
    return [
        {
            "notification_id": item.notification_id,
            "title": item.title,
            "message": item.message,
            "date_label": item.date_label,
            "status_code": item.status_code,
            "status_label": item.status_label,
            "is_read": item.is_read,
        }
        for item in notification_dashboard.items
    ]


def _notification_slot_updates_from_dashboard(notification_dashboard):
    state_items = _notification_state_items_from_dashboard(notification_dashboard)
    updates: list = []

    for slot_index in range(MAX_NOTIFICATION_SLOTS):
        if slot_index < len(state_items):
            item = state_items[slot_index]
            updates.extend(
                [
                    gr.update(visible=True),
                    _render_notification_card_html(item),
                    gr.update(
                        visible=not bool(item["is_read"]),
                        interactive=not bool(item["is_read"]),
                    ),
                ]
            )
        else:
            updates.extend(
                [
                    gr.update(visible=False),
                    "",
                    gr.update(visible=False, interactive=False),
                ]
            )

    return state_items, updates


def prepare_employee_screen_payload(auth_state_dict: dict | None) -> dict:
    auth_session = AuthSession.from_state(auth_state_dict)
    mock_dashboard = get_mock_employee_dashboard()

    if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
        return {
            "nav_radio": TAB_PERSONAL,
            "active_tab_style": _render_employee_active_tab_style(TAB_PERSONAL),
            "personal_container_visible": True,
            "achievements_container_visible": True,
            "store_container_visible": True,
            "notifications_container_visible": True,
            "action_panel_visible": True,
            "form_container_visible": False,
            "form_feedback": "",
            "header_html": "",
            "personal_page_feedback_html": "",
            "personal_resume_html": "",
            "achievements_html": """
                <div class="page-card">
                    <div class="page-title-row">
                        <div class="page-title">Достижения</div>
                        <div class="page-subtitle">Сначала выполните вход.</div>
                    </div>
                </div>
            """,
            "store_html": """
                <div class="page-card">
                    <div class="page-title-row">
                        <div class="page-title">Магазин бонусов</div>
                        <div class="page-subtitle">Сначала выполните вход.</div>
                    </div>
                </div>
            """,
            "notifications_html": """
                <div class="page-card">
                    <div class="page-title-row">
                        <div class="page-title">Уведомления</div>
                        <div class="page-subtitle">Сначала выполните вход.</div>
                    </div>
                </div>
            """,
            "section_choices": [],
            "form_submit_enabled": False,
            "form_unavailable_reason": "Пользователь не авторизован как сотрудник.",
        }

    personal_data = PERSONAL_DATA_SERVICE.get_personal_data(auth_session.user_id)
    achievement_dashboard = ACHIEVEMENT_SERVICE.get_dashboard(auth_session.user_id)
    store_dashboard = STORE_SERVICE.get_dashboard(auth_session.user_id)
    notification_dashboard = NOTIFICATION_SERVICE.get_dashboard(auth_session.user_id)

    full_name = personal_data.full_name or auth_session.full_name or mock_dashboard.full_name

    section_choices = [
        (option.label, str(option.section_id))
        for option in personal_data.request_section_options
    ]

    form_submit_enabled = personal_data.db_available and bool(section_choices)

    return {
        "nav_radio": TAB_PERSONAL,
        "active_tab_style": _render_employee_active_tab_style(TAB_PERSONAL),
        "personal_container_visible": True,
        "achievements_container_visible": True,
        "store_container_visible": True,
        "notifications_container_visible": True,
        "action_panel_visible": True,
        "form_container_visible": False,
        "form_feedback": "",
        "header_html": _render_header_html(
            full_name=full_name,
            achievements_done=achievement_dashboard.completed_possible_count,
            achievements_total=achievement_dashboard.total_possible_count,
            points=achievement_dashboard.points_balance,
        ),
        "personal_page_feedback_html": (
            _render_feedback_html(personal_data.load_error_message, "error")
            if personal_data.load_error_message
            else ""
        ),
        "personal_resume_html": _render_resume_sections_html(personal_data),
        "achievements_html": _render_achievements_page_html(achievement_dashboard),
        "store_html": _render_store_summary_html(store_dashboard),
        "notifications_html": _render_notifications_summary_html(notification_dashboard),
        "section_choices": section_choices,
        "form_submit_enabled": form_submit_enabled,
        "form_unavailable_reason": _build_form_unavailable_reason(personal_data, section_choices),
    }


def get_employee_screen_reset_payload() -> dict:
    return {
        "nav_radio": TAB_PERSONAL,
        "active_tab_style": _render_employee_active_tab_style(TAB_PERSONAL),
        "personal_container_visible": True,
        "achievements_container_visible": True,
        "store_container_visible": True,
        "notifications_container_visible": True,
        "action_panel_visible": True,
        "form_container_visible": False,
        "form_feedback": "",
        "header_html": "",
        "personal_page_feedback_html": "",
        "personal_resume_html": "",
        "achievements_html": """
            <div class="page-card">
                <div class="page-title-row">
                    <div class="page-title">Достижения</div>
                    <div class="page-subtitle">Сначала выполните вход.</div>
                </div>
            </div>
        """,
        "store_html": """
            <div class="page-card">
                <div class="page-title-row">
                    <div class="page-title">Магазин бонусов</div>
                    <div class="page-subtitle">Сначала выполните вход.</div>
                </div>
            </div>
        """,
        "notifications_html": """
            <div class="page-card">
                <div class="page-title-row">
                    <div class="page-title">Уведомления</div>
                    <div class="page-subtitle">Сначала выполните вход.</div>
                </div>
            </div>
        """,
        "section_choices": [],
        "form_submit_enabled": False,
        "form_unavailable_reason": "Сессия отсутствует.",
    }


def build_employee_screen(auth_state: gr.State, app_title: str) -> dict[str, gr.components.Component]:
    def _switch_employee_tab(selected_tab_code: str):
        """
        Мгновенно переключает вкладку через CSS, не размонтируя панели Gradio.
        """
        selected_tab_code = selected_tab_code or TAB_PERSONAL
        is_personal_tab = selected_tab_code == TAB_PERSONAL

        return (
            _render_employee_active_tab_style(selected_tab_code),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=is_personal_tab),
            gr.update(visible=False),
            "",
            gr.update(value=None),
            gr.update(value=""),
            gr.update(value=None),
        )

    def _refresh_active_employee_tab(
        selected_tab_code: str,
        auth_state_dict: dict | None,
        current_store_items_state: list[dict] | None,
        current_notification_items_state: list[dict] | None,
    ):
        """
        Обновляет данные выбранной вкладки после того, как CSS уже показал панель.
        """
        selected_tab_code = selected_tab_code or TAB_PERSONAL

        personal_feedback_update, personal_resume_update = _refresh_personal_when_needed(
            selected_tab_code=selected_tab_code,
            auth_state_dict=auth_state_dict,
        )
        achievements_update = _refresh_achievements_when_needed(
            selected_tab_code=selected_tab_code,
            auth_state_dict=auth_state_dict,
        )
        store_updates = _refresh_store_when_needed(
            selected_tab_code=selected_tab_code,
            auth_state_dict=auth_state_dict,
            current_store_items_state=current_store_items_state,
        )
        notification_updates = _refresh_notifications_when_needed(
            selected_tab_code=selected_tab_code,
            auth_state_dict=auth_state_dict,
            current_notification_items_state=current_notification_items_state,
        )

        return (
            personal_feedback_update,
            personal_resume_update,
            achievements_update,
            *store_updates,
            *notification_updates,
        )

    def _open_form(auth_state_dict: dict | None):
        auth_session = AuthSession.from_state(auth_state_dict)

        section_choices: list[tuple[str, str]] = []
        form_submit_enabled = False
        unavailable_reason = "Сессия отсутствует."

        if auth_session.is_authenticated and auth_session.role == "employee" and auth_session.user_id:
            personal_data = PERSONAL_DATA_SERVICE.get_personal_data(auth_session.user_id)
            section_choices = [
                (option.label, str(option.section_id))
                for option in personal_data.request_section_options
            ]
            form_submit_enabled = personal_data.db_available and bool(section_choices)
            unavailable_reason = _build_form_unavailable_reason(personal_data, section_choices)
        else:
            unavailable_reason = "Сессия пользователя недействительна. Выполните вход заново."

        form_message = ""
        if not form_submit_enabled:
            form_message = _render_feedback_html(
                f"Форма открыта, но отправка сейчас недоступна. Причина: {unavailable_reason or 'Форма временно недоступна'}",
                "info",
            )

        return (
            gr.update(visible=True),
            gr.update(visible=True),
            "",
            form_message,
            gr.update(choices=section_choices, value=None, interactive=form_submit_enabled),
            gr.update(value="", interactive=form_submit_enabled),
            gr.update(value=None, interactive=form_submit_enabled),
            gr.update(interactive=form_submit_enabled),
            form_submit_enabled,
            unavailable_reason,
        )

    def _cancel_form():
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "",
            gr.update(value=None),
            gr.update(value=""),
            gr.update(value=None),
            gr.update(interactive=False),
            False,
            "",
        )

    def _submit_form(
        auth_state_dict: dict | None,
        form_submit_enabled: bool,
        unavailable_reason: str,
        selected_section_id: str | None,
        description_text: str | None,
        attached_file_path: str | None,
    ):
        auth_session = AuthSession.from_state(auth_state_dict)

        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                "",
                _render_feedback_html(
                    "Сессия пользователя недействительна. Выполните вход заново.",
                    "error",
                ),
                gr.update(value=selected_section_id),
                gr.update(value=description_text),
                gr.update(),
                gr.update(interactive=False),
                False,
                "Сессия пользователя недействительна. Выполните вход заново.",
            )

        if not form_submit_enabled:
            reason = (unavailable_reason or "").strip() or "Форма временно недоступна"
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                "",
                _render_feedback_html(
                    f"Отправка сейчас недоступна. Причина: {reason}",
                    "error",
                ),
                gr.update(value=selected_section_id),
                gr.update(value=description_text),
                gr.update(),
                gr.update(interactive=False),
                False,
                reason,
            )

        result = PERSONAL_DATA_SERVICE.submit_resume_change_request(
            employee_user_id=auth_session.user_id,
            section_id_raw=selected_section_id,
            change_description=description_text,
            uploaded_file_path=attached_file_path,
        )

        if result.success:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                _render_feedback_html(result.message, "success"),
                "",
                gr.update(value=None),
                gr.update(value=""),
                gr.update(value=None),
                gr.update(interactive=False),
                False,
                "",
            )

        reason = (unavailable_reason or "").strip()
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            "",
            _render_feedback_html(result.message, "error"),
            gr.update(value=selected_section_id, interactive=form_submit_enabled),
            gr.update(value=description_text, interactive=form_submit_enabled),
            gr.update(interactive=form_submit_enabled),
            gr.update(interactive=form_submit_enabled),
            form_submit_enabled,
            reason,
        )

    def _render_auth_required_page(title: str) -> str:
        return f"""
        <div class="page-card">
            <div class="page-title-row">
                <div class="page-title">{escape(title)}</div>
                <div class="page-subtitle">Сначала выполните вход.</div>
            </div>
        </div>
        """

    def _refresh_personal_when_needed(
        selected_tab_code: str,
        auth_state_dict: dict | None,
    ):
        if selected_tab_code != TAB_PERSONAL:
            return gr.update(), gr.update()

        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            return (
                _render_feedback_html("Сессия пользователя недействительна. Выполните вход заново.", "error"),
                "",
            )

        try:
            personal_data = PERSONAL_DATA_SERVICE.get_personal_data(auth_session.user_id)
            feedback_html = (
                _render_feedback_html(personal_data.load_error_message, "error")
                if personal_data.load_error_message
                else ""
            )
            return feedback_html, _render_resume_sections_html(personal_data)
        except Exception as exc:
            return (
                _render_feedback_html(f"Не удалось загрузить личные данные: {exc}", "error"),
                "",
            )

    def _refresh_achievements_when_needed(
        selected_tab_code: str,
        auth_state_dict: dict | None,
    ):
        if selected_tab_code != TAB_ACHIEVEMENTS:
            return gr.update()

        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            return _render_auth_required_page("Достижения")

        try:
            achievement_dashboard = ACHIEVEMENT_SERVICE.get_dashboard(auth_session.user_id)
            return _render_achievements_page_html(achievement_dashboard)
        except Exception as exc:
            return f"""
            <div class="page-card">
                {_render_page_header("Достижения", "Данные временно недоступны.")}
                {_render_feedback_html(f"Не удалось загрузить достижения: {exc}", "error")}
            </div>
            """

    def _refresh_store_when_needed(
        selected_tab_code: str,
        auth_state_dict: dict | None,
        current_store_items_state: list[dict] | None,
    ):
        if selected_tab_code != TAB_STORE:
            no_change_updates = []
            for _ in range(MAX_STORE_SLOTS):
                no_change_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                gr.update(),
                gr.update(),
                current_store_items_state or [],
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                *no_change_updates,
            )

        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            empty_updates = []
            for _ in range(MAX_STORE_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(visible=True),
                        _render_store_placeholder_card_html(),
                        gr.update(visible=False, interactive=False),
                    ]
                )

            return (
                """
                <div class="page-card">
                    <div class="page-title-row">
                        <div class="page-title">Магазин бонусов</div>
                        <div class="page-subtitle">Сначала выполните вход.</div>
                    </div>
                </div>
                """,
                "",
                [],
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                *empty_updates,
            )

        store_dashboard = STORE_SERVICE.get_dashboard(auth_session.user_id)
        state_items, slot_updates = _store_slot_updates_from_dashboard(store_dashboard)

        return (
            _render_store_summary_html(store_dashboard),
            "",
            state_items,
            None,
            gr.update(visible=False),
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            *slot_updates,
        )

    def _refresh_notifications_when_needed(
        selected_tab_code: str,
        auth_state_dict: dict | None,
        current_notification_items_state: list[dict] | None,
    ):
        if selected_tab_code != TAB_NOTIFICATIONS:
            no_change_updates = []
            for _ in range(MAX_NOTIFICATION_SLOTS):
                no_change_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                gr.update(),
                gr.update(),
                current_notification_items_state or [],
                *no_change_updates,
            )

        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            empty_updates = []
            for _ in range(MAX_NOTIFICATION_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(visible=False),
                        "",
                        gr.update(visible=False, interactive=False),
                    ]
                )

            return (
                """
                <div class="page-card">
                    <div class="page-title-row">
                        <div class="page-title">Уведомления</div>
                        <div class="page-subtitle">Сначала выполните вход.</div>
                    </div>
                </div>
                """,
                "",
                [],
                *empty_updates,
            )

        notification_dashboard = NOTIFICATION_SERVICE.get_dashboard(auth_session.user_id)
        state_items, slot_updates = _notification_slot_updates_from_dashboard(notification_dashboard)

        return (
            _render_notifications_summary_html(notification_dashboard),
            "",
            state_items,
            *slot_updates,
        )

    def _prime_store_from_auth(auth_state_dict: dict | None):
        return _refresh_store_when_needed(TAB_STORE, auth_state_dict, [])

    def _prime_notifications_from_auth(auth_state_dict: dict | None):
        return _refresh_notifications_when_needed(TAB_NOTIFICATIONS, auth_state_dict, [])

    def _select_bonus_for_purchase(
        slot_index: int,
        store_items_state: list[dict] | None,
        auth_state_dict: dict | None,
    ):
        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee":
            return (
                _render_feedback_html("Сначала выполните вход в систему.", "error"),
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
            )

        items = store_items_state or []
        if slot_index < 0 or slot_index >= len(items):
            return (
                _render_feedback_html("Выбранный бонус не найден в текущем каталоге.", "error"),
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
            )

        item = items[slot_index]
        bonus_name = item["title"]
        cost_points = int(item["cost_points"])
        points_snapshot = int(item["points_snapshot"])

        if not bool(item["is_affordable"]):
            message = (
                f"Для покупки бонуса «{bonus_name}» нужно {cost_points} баллов, "
                f"а у вас сейчас только {points_snapshot}."
            )
            return (
                "",
                None,
                gr.update(visible=True),
                _render_feedback_html(message, "error"),
                gr.update(visible=True),
                gr.update(visible=False),
            )

        future_balance = points_snapshot - cost_points
        purchase_intent_state = {
            "bonus_id": int(item["bonus_id"]),
            "bonus_name": bonus_name,
            "cost_points": cost_points,
            "points_snapshot": points_snapshot,
            "purchase_token": str(uuid.uuid4()),
        }

        message = (
            f"Подтвердить покупку бонуса «{bonus_name}» за {cost_points} баллов? "
            f"После покупки в шапке останется {future_balance} баллов. "
            f"Заявка будет отправлена HR-менеджеру."
        )

        return (
            "",
            purchase_intent_state,
            gr.update(visible=True),
            _render_feedback_html(message, "info"),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def _close_purchase_panel():
        return (
            None,
            gr.update(visible=False),
            "",
            gr.update(visible=False),
            gr.update(visible=False),
        )

    def _confirm_bonus_purchase(
        auth_state_dict: dict | None,
        purchase_intent_state: dict | None,
    ):
        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            empty_updates = []
            for _ in range(MAX_STORE_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                "",
                gr.update(),
                _render_feedback_html("Сессия истекла. Выполните вход заново.", "error"),
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                [],
                *empty_updates,
            )

        if not purchase_intent_state:
            empty_updates = []
            for _ in range(MAX_STORE_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                _build_header_html_for_user(auth_state_dict),
                gr.update(),
                _render_feedback_html("Подтверждение покупки не найдено. Выберите бонус заново.", "error"),
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                [],
                *empty_updates,
            )

        result = STORE_SERVICE.purchase_bonus(
            employee_user_id=auth_session.user_id,
            bonus_id=int(purchase_intent_state["bonus_id"]),
            purchase_token=str(purchase_intent_state["purchase_token"]),
            expected_points_snapshot=int(purchase_intent_state["points_snapshot"]),
        )

        store_dashboard = STORE_SERVICE.get_dashboard(auth_session.user_id)
        state_items, slot_updates = _store_slot_updates_from_dashboard(store_dashboard)

        feedback_kind = "success"
        if result.already_processed:
            feedback_kind = "info"
        elif not result.success:
            feedback_kind = "error"

        return (
            _build_header_html_for_user(auth_state_dict),
            _render_store_summary_html(store_dashboard),
            _render_feedback_html(result.message, feedback_kind),
            None,
            gr.update(visible=False),
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            state_items,
            *slot_updates,
        )

    def _mark_notification_as_read(
        slot_index: int,
        notification_items_state: list[dict] | None,
        auth_state_dict: dict | None,
    ):
        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "employee" or not auth_session.user_id:
            empty_updates = []
            for _ in range(MAX_NOTIFICATION_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                gr.update(),
                _render_feedback_html("Сессия истекла. Выполните вход заново.", "error"),
                notification_items_state or [],
                *empty_updates,
            )

        items = notification_items_state or []
        if slot_index < 0 or slot_index >= len(items):
            empty_updates = []
            for _ in range(MAX_NOTIFICATION_SLOTS):
                empty_updates.extend(
                    [
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ]
                )

            return (
                gr.update(),
                _render_feedback_html("Уведомление не найдено в текущем списке.", "error"),
                notification_items_state or [],
                *empty_updates,
            )

        selected_item = items[slot_index]
        result = NOTIFICATION_SERVICE.mark_as_read(
            employee_user_id=auth_session.user_id,
            notification_id=int(selected_item["notification_id"]),
        )

        dashboard = NOTIFICATION_SERVICE.get_dashboard(auth_session.user_id)
        state_items, slot_updates = _notification_slot_updates_from_dashboard(dashboard)

        feedback_kind = "success" if result.success else "error"

        return (
            _render_notifications_summary_html(dashboard),
            _render_feedback_html(result.message, feedback_kind),
            state_items,
            *slot_updates,
        )

    with gr.Row(visible=False, elem_id="employee-root", elem_classes=["employee-shell"]) as container:
        with gr.Column(scale=3, min_width=280, elem_classes=["sidebar-column"]):
            gr.HTML(_render_brand_html(app_title), elem_classes=["brand-card"])

            logout_button = gr.Button(
                value="Выйти",
                elem_classes=["logout-button"],
            )

            gr.HTML('<div class="nav-title">Навигация</div>', elem_classes=["nav-box"])

            nav_radio = gr.Radio(
                choices=[
                    ("Личные данные", TAB_PERSONAL),
                    ("Достижения", TAB_ACHIEVEMENTS),
                    ("Магазин", TAB_STORE),
                    ("Уведомления", TAB_NOTIFICATIONS),
                ],
                value=TAB_PERSONAL,
                show_label=False,
                container=False,
                elem_id="employee-nav",
            )

        with gr.Column(scale=10, min_width=720, elem_classes=["content-column"]):
            active_tab_style = gr.HTML(
                value=_render_employee_active_tab_style(TAB_PERSONAL),
                visible=True,
            )
            header_html = gr.HTML(value="", elem_classes=["header-card"])

            with gr.Column(elem_classes=["content-stack"]):
                # -------------------------------------------------
                # ЛИЧНЫЕ ДАННЫЕ
                # -------------------------------------------------
                with gr.Column(visible=True, elem_id="employee-tab-personal", elem_classes=["content-view", "main-tab-view"]) as personal_container:
                    with gr.Column(elem_classes=["page-card", "personal-data-page-card"]):
                        gr.HTML(
                            _render_page_header(
                                "Личные данные / Резюме",
                                "Данные загружаются из MySQL. Изменения отправляются HR в виде заявки.",
                            )
                        )

                        gr.HTML(
                            _render_stub_banner(
                                "Изменения через форму ниже не обновляют резюме мгновенно: "
                                "они создают заявку на проверку HR и сохраняются в БД."
                            )
                        )

                        personal_resume_html = gr.HTML(value="")

                        personal_page_feedback = gr.HTML(
                            value="",
                            elem_classes=["resume-action-feedback"],
                        )

                        with gr.Column(visible=True, elem_classes=["runtime-action-panel"]) as action_panel:
                            with gr.Row(elem_classes=["page-footer-actions"]):
                                open_form_button = gr.Button(
                                    value="Добавить информацию",
                                    interactive=True,
                                    elem_classes=["action-button"],
                                )

                        with gr.Column(
                            visible=False,
                            elem_classes=["resume-change-form", "runtime-form-panel"],
                        ) as form_container:
                            gr.HTML(
                                """
                                <div class="resume-change-form-title">Запрос на изменение резюме</div>
                                <div class="resume-change-form-subtitle">
                                    Выберите раздел, опишите изменение и при необходимости приложите подтверждающий файл.
                                </div>
                                """
                            )

                            form_feedback = gr.HTML(value="")

                            section_dropdown = gr.Dropdown(
                                label="Раздел резюме",
                                choices=[],
                                value=None,
                                allow_custom_value=False,
                                interactive=False,
                            )

                            description_text = gr.Textbox(
                                label="Описание изменений",
                                lines=6,
                                interactive=False,
                            )

                            attachment_file = gr.File(
                                label="Подтверждающий файл",
                                file_count="single",
                                type="filepath",
                                interactive=False,
                            )

                            with gr.Row(elem_classes=["form-actions-row"]):
                                cancel_button = gr.Button(
                                    value="Отмена",
                                    elem_classes=["form-cancel-button"],
                                )
                                submit_button = gr.Button(
                                    value="Отправить",
                                    interactive=False,
                                    elem_classes=["form-submit-button"],
                                )

                # -------------------------------------------------
                # ДОСТИЖЕНИЯ
                # -------------------------------------------------
                with gr.Column(visible=True, elem_id="employee-tab-achievements", elem_classes=["content-view", "main-tab-view"]) as achievements_container:
                    achievements_html = gr.HTML(
                        value="""
                            <div class="page-card">
                                <div class="page-title-row">
                                    <div class="page-title">Достижения</div>
                                    <div class="page-subtitle">Каталог достижений будет загружен после входа.</div>
                                </div>
                            </div>
                        """
                    )

                # -------------------------------------------------
                # МАГАЗИН
                # -------------------------------------------------
                with gr.Column(visible=True, elem_id="employee-tab-store", elem_classes=["content-view", "main-tab-view"]) as store_container:
                    store_html = gr.HTML(
                        value="""
                            <div class="page-card">
                                <div class="page-title-row">
                                    <div class="page-title">Магазин бонусов</div>
                                    <div class="page-subtitle">Каталог будет загружен после входа.</div>
                                </div>
                            </div>
                        """
                    )

                    store_feedback_html = gr.HTML(value="")
                    store_items_state = gr.State([])
                    purchase_intent_state = gr.State(None)

                    with gr.Column(
                        visible=False,
                        elem_classes=["page-card", "store-purchase-panel"],
                    ) as purchase_panel:
                        purchase_message_html = gr.HTML(value="")

                        with gr.Row(visible=False, elem_classes=["form-actions-row"]) as purchase_insufficient_row:
                            insufficient_cancel_button = gr.Button(
                                value="Отменить",
                                elem_classes=["form-cancel-button"],
                            )

                        with gr.Row(visible=False, elem_classes=["form-actions-row"]) as purchase_confirm_row:
                            confirm_purchase_button = gr.Button(
                                value="Подтверждаю",
                                elem_classes=["form-submit-button"],
                            )
                            cancel_purchase_button = gr.Button(
                                value="Отменить",
                                elem_classes=["form-cancel-button"],
                            )

                    store_slot_containers = []
                    store_card_html_components = []
                    store_select_buttons = []

                    for _row_index in range(5):
                        with gr.Row(elem_classes=["store-grid-row"]):
                            for _col_index in range(3):
                                with gr.Column(
                                    scale=1,
                                    min_width=0,
                                    visible=True,
                                    elem_classes=["store-slot-column"],
                                ) as slot_container:
                                    card_html = gr.HTML(
                                        value=_render_store_placeholder_card_html(),
                                        elem_classes=["store-slot-html"],
                                    )
                                    select_button = gr.Button(
                                        value="Выбрать бонус",
                                        interactive=False,
                                        visible=False,
                                        elem_classes=["action-button", "store-select-button"],
                                    )

                                store_slot_containers.append(slot_container)
                                store_card_html_components.append(card_html)
                                store_select_buttons.append(select_button)

                    store_slot_outputs = sum(
                        [
                            [store_slot_containers[i], store_card_html_components[i], store_select_buttons[i]]
                            for i in range(MAX_STORE_SLOTS)
                        ],
                        [],
                    )

                # -------------------------------------------------
                # УВЕДОМЛЕНИЯ
                # -------------------------------------------------
                with gr.Column(visible=True, elem_id="employee-tab-notifications", elem_classes=["content-view", "main-tab-view"]) as notifications_container:
                    notifications_html = gr.HTML(
                        value="""
                            <div class="page-card">
                                <div class="page-title-row">
                                    <div class="page-title">Уведомления</div>
                                    <div class="page-subtitle">Уведомления будут загружены после входа.</div>
                                </div>
                            </div>
                        """
                    )

                    notifications_feedback_html = gr.HTML(value="")
                    notification_items_state = gr.State([])

                    notification_slot_containers = []
                    notification_card_html_components = []
                    notification_read_buttons = []

                    for _index in range(MAX_NOTIFICATION_SLOTS):
                        with gr.Column(visible=False, elem_classes=["notification-slot"]) as slot_container:
                            card_html = gr.HTML(value="")
                            read_button = gr.Button(
                                value="Пометить как прочитанное",
                                visible=False,
                                interactive=False,
                                elem_classes=["action-button"],
                            )

                        notification_slot_containers.append(slot_container)
                        notification_card_html_components.append(card_html)
                        notification_read_buttons.append(read_button)

                    notification_slot_outputs = sum(
                        [
                            [notification_slot_containers[i], notification_card_html_components[i], notification_read_buttons[i]]
                            for i in range(MAX_NOTIFICATION_SLOTS)
                        ],
                        [],
                    )

        form_submit_enabled_state = gr.State(False)
        form_unavailable_reason_state = gr.State("")

        nav_radio.change(
            fn=_switch_employee_tab,
            inputs=[nav_radio],
            outputs=[
                active_tab_style,
                personal_container,
                achievements_container,
                store_container,
                notifications_container,
                action_panel,
                form_container,
                form_feedback,
                section_dropdown,
                description_text,
                attachment_file,
            ],
            queue=False,
            show_progress="hidden",
        ).then(
            fn=_refresh_active_employee_tab,
            inputs=[nav_radio, auth_state, store_items_state, notification_items_state],
            outputs=[
                personal_page_feedback,
                personal_resume_html,
                achievements_html,
                store_html,
                store_feedback_html,
                store_items_state,
                purchase_intent_state,
                purchase_panel,
                purchase_message_html,
                purchase_insufficient_row,
                purchase_confirm_row,
                *store_slot_outputs,
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                *notification_slot_outputs,
            ],
            show_progress="hidden",
        )

        auth_state.change(
            fn=_prime_store_from_auth,
            inputs=[auth_state],
            outputs=[
                store_html,
                store_feedback_html,
                store_items_state,
                purchase_intent_state,
                purchase_panel,
                purchase_message_html,
                purchase_insufficient_row,
                purchase_confirm_row,
                *store_slot_outputs,
            ],
            show_progress="hidden",
        )

        auth_state.change(
            fn=_prime_notifications_from_auth,
            inputs=[auth_state],
            outputs=[
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                *notification_slot_outputs,
            ],
            show_progress="hidden",
        )

        # ---------------------------------------------------------
        # Форма личных данных
        # ---------------------------------------------------------
        open_form_button.click(
            fn=_open_form,
            inputs=[auth_state],
            outputs=[
                action_panel,
                form_container,
                personal_page_feedback,
                form_feedback,
                section_dropdown,
                description_text,
                attachment_file,
                submit_button,
                form_submit_enabled_state,
                form_unavailable_reason_state,
            ],
            show_progress="hidden",
        )

        cancel_button.click(
            fn=_cancel_form,
            inputs=None,
            outputs=[
                action_panel,
                form_container,
                form_feedback,
                section_dropdown,
                description_text,
                attachment_file,
                submit_button,
                form_submit_enabled_state,
                form_unavailable_reason_state,
            ],
            show_progress="hidden",
        )

        submit_button.click(
            fn=_submit_form,
            inputs=[
                auth_state,
                form_submit_enabled_state,
                form_unavailable_reason_state,
                section_dropdown,
                description_text,
                attachment_file,
            ],
            outputs=[
                action_panel,
                form_container,
                personal_page_feedback,
                form_feedback,
                section_dropdown,
                description_text,
                attachment_file,
                submit_button,
                form_submit_enabled_state,
                form_unavailable_reason_state,
            ],
            show_progress="hidden",
        )

        # ---------------------------------------------------------
        # Логика карточек магазина
        # ---------------------------------------------------------
        for slot_index, select_button in enumerate(store_select_buttons):
            select_button.click(
                fn=lambda store_state, state, idx=slot_index: _select_bonus_for_purchase(idx, store_state, state),
                inputs=[store_items_state, auth_state],
                outputs=[
                    store_feedback_html,
                    purchase_intent_state,
                    purchase_panel,
                    purchase_message_html,
                    purchase_insufficient_row,
                    purchase_confirm_row,
                ],
                show_progress="hidden",
            )

        insufficient_cancel_button.click(
            fn=_close_purchase_panel,
            inputs=None,
            outputs=[
                purchase_intent_state,
                purchase_panel,
                purchase_message_html,
                purchase_insufficient_row,
                purchase_confirm_row,
            ],
            show_progress="hidden",
        )

        cancel_purchase_button.click(
            fn=_close_purchase_panel,
            inputs=None,
            outputs=[
                purchase_intent_state,
                purchase_panel,
                purchase_message_html,
                purchase_insufficient_row,
                purchase_confirm_row,
            ],
            show_progress="hidden",
        )

        confirm_purchase_button.click(
            fn=_confirm_bonus_purchase,
            inputs=[auth_state, purchase_intent_state],
            outputs=[
                header_html,
                store_html,
                store_feedback_html,
                purchase_intent_state,
                purchase_panel,
                purchase_message_html,
                purchase_insufficient_row,
                purchase_confirm_row,
                store_items_state,
                *store_slot_outputs,
            ],
            show_progress="hidden",
        )

        # ---------------------------------------------------------
        # Логика карточек уведомлений
        # ---------------------------------------------------------
        for slot_index, read_button in enumerate(notification_read_buttons):
            read_button.click(
                fn=lambda notification_state, state, idx=slot_index: _mark_notification_as_read(idx, notification_state, state),
                inputs=[notification_items_state, auth_state],
                outputs=[
                    notifications_html,
                    notifications_feedback_html,
                    notification_items_state,
                    *notification_slot_outputs,
                ],
                show_progress="hidden",
            )

    return {
        "container": container,
        "logout_button": logout_button,
        "active_tab_style": active_tab_style,
        "header_html": header_html,
        "nav_radio": nav_radio,
        "personal_container": personal_container,
        "achievements_container": achievements_container,
        "store_container": store_container,
        "notifications_container": notifications_container,
        "personal_page_feedback": personal_page_feedback,
        "personal_resume_html": personal_resume_html,
        "achievements_html": achievements_html,
        "store_html": store_html,
        "notifications_html": notifications_html,
        "section_dropdown": section_dropdown,
        "description_text": description_text,
        "attachment_file": attachment_file,
        "submit_button": submit_button,
        "form_submit_enabled_state": form_submit_enabled_state,
        "form_unavailable_reason_state": form_unavailable_reason_state,
        "form_submit_enabled": form_submit_enabled_state,
        "form_unavailable_reason": form_unavailable_reason_state,
        "personal_page_feedback_html": personal_page_feedback,
        "action_panel": action_panel,
        "form_container": form_container,
        "form_feedback": form_feedback,
        "store_feedback_html": store_feedback_html,
        "notifications_feedback_html": notifications_feedback_html,
        "store_items_state": store_items_state,
        "notification_items_state": notification_items_state,
        "purchase_intent_state": purchase_intent_state,
    }
