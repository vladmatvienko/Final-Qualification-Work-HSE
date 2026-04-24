from __future__ import annotations

from dataclasses import asdict
from base64 import b64encode
from pathlib import Path
from html import escape

import gradio as gr

from app.auth.session_state import AuthSession
from app.models.hr_notification_models import HRNotificationCardViewModel
from app.models.hr_view_models import HR_TABS, TAB_NOTIFICATIONS, TAB_RATING
from app.services.hr_notification_service import HRNotificationService
from app.ui.hr_candidate_search_view import build_hr_candidate_search_view


# =========================================================
# Глобальные настройки экрана HR
# =========================================================
hr_notification_service = HRNotificationService()

MAX_NOTIFICATION_SLOTS = 20

# =========================================================
# HTML-хелперы
# =========================================================

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

def _render_brand_html(app_title: str) -> str:
    """
    Рендерит брендовый блок слева сверху.
    """
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


def _render_header_html(
    full_name: str,
    role_label: str,
    unread_notifications_count: int,
) -> str:
    """
    Рендерит верхнюю шапку HR-экрана.
    """
    return f"""
    <div class="employee-header">
        <div class="employee-header-main">
            <div class="employee-header-label">Профиль HR</div>
            <div class="employee-name">{escape(full_name)}</div>
            <div class="employee-header-subtitle">
                {escape(role_label)}. Рабочий интерфейс HR-менеджера.
            </div>
        </div>
        <div class="employee-metrics">
            <div class="metric-chip">
                <div class="metric-label">Новых уведомлений</div>
                <div class="metric-value">{int(unread_notifications_count)}</div>
            </div>
        </div>
    </div>
    """


def _render_page_header(title: str, subtitle: str) -> str:
    """
    Универсальный заголовок секции внутри правого контента.
    """
    return f"""
    <div class="page-title-row">
        <div class="page-title">{escape(title)}</div>
        <div class="page-subtitle">{escape(subtitle)}</div>
    </div>
    """


def _render_feedback_html(message: str, kind: str = "info") -> str:
    """
    Универсальный HTML-блок обратной связи.
    """
    if not message:
        return ""

    normalized_kind = kind if kind in {"success", "error", "info"} else "info"
    return f'<div class="feedback-box feedback-box--{normalized_kind}">{escape(message)}</div>'


def _render_notifications_summary_html(dashboard_data) -> str:
    """
    Рендерит сводный блок по HR-уведомлениям.
    """
    if not dashboard_data.db_available and dashboard_data.load_error_message:
        return f"""
        <div class="page-card">
            {_render_page_header("Уведомления", "Лента HR-уведомлений")}
            {_render_feedback_html(dashboard_data.load_error_message, "error")}
        </div>
        """

    return f"""
    <div class="page-card">
        {_render_page_header("Уведомления", "Лента HR-уведомлений по изменениям резюме, бонусам и истекающим курсам")}
        <div class="dashboard-stats-grid">
            <div class="dashboard-metric-card">
                <div class="dashboard-metric-label">Всего в текущем фильтре</div>
                <div class="dashboard-metric-value">{int(dashboard_data.total_count)}</div>
            </div>
            <div class="dashboard-metric-card">
                <div class="dashboard-metric-label">Новых уведомлений</div>
                <div class="dashboard-metric-value">{int(dashboard_data.unread_count)}</div>
            </div>
        </div>
    </div>
    """


def _render_notification_card_html(item: HRNotificationCardViewModel) -> str:
    """
    Рендерит короткую карточку HR-уведомления.
    """
    business_status_html = ""
    if item.business_status_label:
        business_status_html = f"""
        <div class="priority-pill">{escape(item.business_status_label)}</div>
        """

    return f"""
    <div class="notification-card">
        <div class="notification-top">
            <div>
                <div class="notification-title">{escape(item.title)}</div>
                <div class="notification-text">
                    {escape(item.employee_full_name)} · {escape(item.source_type_label)}
                </div>
            </div>
            <div class="notification-meta">
                <div class="read-pill">{escape(item.queue_status_label)}</div>
                {business_status_html}
            </div>
        </div>
        <div class="notification-text">{escape(item.summary_text)}</div>
        <div class="notification-text">Дата: {escape(item.event_date_label)}</div>
    </div>
    """


def _detail_row(label: str, value: str) -> str:
    """
    Одна строка внутри детальной карточки уведомления.
    """
    return f"""
    <div style="margin-bottom: 10px; line-height: 1.45;">
        <span style="font-weight: 700; color: #2f4f86;">{escape(label)}:</span>
        <span style="color: #24324d;"> {escape(value)}</span>
    </div>
    """


def _render_notification_details_html(item: HRNotificationCardViewModel) -> str:
    """
    Рендерит подробности выбранного уведомления.
    """
    if item.source_type_code == "resume_change_request":
        file_block = "Файл не приложен"

        if item.attachment_original_filename:
            lines: list[str] = [f"Файл: {item.attachment_original_filename}"]

            if item.attachment_mime_type:
                lines.append(f"MIME: {item.attachment_mime_type}")

            if item.attachment_size_bytes is not None:
                lines.append(f"Размер: {int(item.attachment_size_bytes)} байт")

            if item.attachment_file_path:
                lines.append(f"Путь: {item.attachment_file_path}")

            file_block = "<br>".join(escape(line) for line in lines)

        return f"""
        <div class="page-card" style="margin-top: 14px;">
            <div class="page-title" style="margin-bottom: 18px;">Подробности заявки на изменение резюме</div>
            {_detail_row("Сотрудник", item.employee_full_name)}
            {_detail_row("Раздел", item.resume_section_name or "Не указан")}
            {_detail_row("Описание", item.resume_change_description or "Нет описания")}
            {_detail_row("Дата заявки", item.event_date_label)}
            {_detail_row("Статус заявки", item.business_status_label or "Не указан")}
            <div style="margin-top: 10px;">
                <div style="font-weight: 700; color: #2f4f86; margin-bottom: 8px;">Вложение:</div>
                <div style="color: #24324d; line-height: 1.5;">{file_block}</div>
            </div>
        </div>
        """

    if item.source_type_code == "bonus_purchase":
        return f"""
        <div class="page-card" style="margin-top: 14px;">
            <div class="page-title" style="margin-bottom: 18px;">Подробности покупки бонуса</div>
            {_detail_row("Сотрудник", item.employee_full_name)}
            {_detail_row("Бонус", item.bonus_name or "Не указан")}
            {_detail_row("Стоимость", f"{int(item.bonus_cost_points or 0)} баллов")}
            {_detail_row("Дата", item.bonus_requested_at_label or item.event_date_label)}
            {_detail_row("Статус", item.business_status_label or "Не указан")}
        </div>
        """

    if item.source_type_code == "course_expiry":
        reminder_sent_line = item.reminder_sent_label if item.reminder_sent_label else "ещё не отправлялось"

        return f"""
        <div class="page-card" style="margin-top: 14px;">
            <div class="page-title" style="margin-bottom: 18px;">Подробности по истекающему курсу</div>
            {_detail_row("Сотрудник", item.employee_full_name)}
            {_detail_row("Курс / сертификат", item.qualification_course_name or "Не указан")}
            {_detail_row("Дата окончания", item.qualification_valid_until_label or "Не указана")}
            {_detail_row("Нужно ли напомнить", item.reminder_needed_label or "Не указано")}
            {_detail_row("Когда уже напоминали", reminder_sent_line)}
        </div>
        """

    return """
    <div class="page-card" style="margin-top: 14px;">
        <div class="page-title">Подробности</div>
        <div style="color: #24324d;">Тип уведомления пока не поддерживается.</div>
    </div>
    """


# =========================================================
# Хелперы для state / идентичности / порядка
# =========================================================
def _serialize_items(items: list[HRNotificationCardViewModel]) -> list[dict]:
    """
    Преобразует dataclass-модели в dict-структуры, удобные для хранения в gr.State.
    """
    return [asdict(item) for item in items]


def _deserialize_item(item_state: dict | None) -> HRNotificationCardViewModel | None:
    """
    Восстанавливает dataclass-модель из состояния gr.State.
    """
    if not item_state:
        return None
    return HRNotificationCardViewModel(**item_state)


def _find_item_by_identity(
    items_state: list[dict] | None,
    source_type_code: str,
    queue_record_id: int,
) -> HRNotificationCardViewModel | None:
    """
    Ищет уведомление по стабильной идентичности:
    - source_type_code
    - queue_record_id
    """
    for raw_item in items_state or []:
        item = _deserialize_item(raw_item)
        if not item:
            continue
        if item.source_type_code == source_type_code and item.queue_record_id == queue_record_id:
            return item
    return None


def _get_item_identity(item: HRNotificationCardViewModel | None) -> tuple[str, int] | None:
    """
    Возвращает компактный ID уведомления.
    """
    if not item:
        return None
    return (item.source_type_code, item.queue_record_id)


def _preserve_items_order(
    previous_items_state: list[dict] | None,
    fresh_items_state: list[dict],
) -> list[dict]:
    if not previous_items_state:
        return fresh_items_state

    fresh_map: dict[tuple[str, int], dict] = {}
    fresh_ordered_identities: list[tuple[str, int]] = []

    for raw_item in fresh_items_state:
        item = _deserialize_item(raw_item)
        if not item:
            continue

        identity = _get_item_identity(item)
        if not identity:
            continue

        fresh_map[identity] = raw_item
        fresh_ordered_identities.append(identity)

    ordered_result: list[dict] = []
    used_identities: set[tuple[str, int]] = set()

    for old_raw_item in previous_items_state:
        old_item = _deserialize_item(old_raw_item)
        if not old_item:
            continue

        identity = _get_item_identity(old_item)
        if not identity:
            continue

        fresh_raw_item = fresh_map.get(identity)
        if fresh_raw_item is not None:
            ordered_result.append(fresh_raw_item)
            used_identities.add(identity)

    for identity in fresh_ordered_identities:
        if identity not in used_identities:
            fresh_raw_item = fresh_map.get(identity)
            if fresh_raw_item is not None:
                ordered_result.append(fresh_raw_item)

    return ordered_result


# =========================================================
# Хелперы для файлов и action-кнопок
# =========================================================
def _resolve_download_path(raw_path: str | None) -> str | None:
    """
    Преобразует путь из БД в реальный путь на диске сервера.
    """
    if not raw_path:
        return None

    normalized_raw_path = raw_path.strip()
    if not normalized_raw_path:
        return None

    candidate = Path(normalized_raw_path)

    if candidate.is_absolute() and candidate.exists():
        return str(candidate)

    relative_candidate = normalized_raw_path.lstrip("/\\")
    local_path = Path.cwd() / relative_candidate

    if local_path.exists():
        return str(local_path)

    return None


def _should_show_mark_processed(item: HRNotificationCardViewModel, is_selected: bool) -> bool:
    """
    Кнопка "Отметить как обработано" показывается только у выбранной карточки.
    """
    if not is_selected:
        return False

    return bool(item.can_mark_processed)


def _should_show_send_reminder(item: HRNotificationCardViewModel, is_selected: bool) -> bool:
    """
    Напоминание можно отправлять только у выбранного уведомления об истекающем курсе.
    """
    if not is_selected:
        return False

    return bool(item.can_send_reminder)


def _get_download_path_for_selected_item(
    item: HRNotificationCardViewModel,
    is_selected: bool,
) -> str | None:
    """
    Скачать файл
    """
    if not is_selected:
        return None

    if item.source_type_code != "resume_change_request":
        return None

    return _resolve_download_path(item.attachment_file_path)


# =========================================================
# Хелперы генерации update-ов для карточек
# =========================================================
def _build_inline_slot_updates(
    items_state: list[dict],
    selected_item_state: dict | None,
    inline_feedback_html: str = "",
) -> list:
    """
    Генерирует update-ы сразу для всех слотов уведомлений.
    """
    updates: list = []

    selected_item = _deserialize_item(selected_item_state)
    selected_identity = _get_item_identity(selected_item)

    for index in range(MAX_NOTIFICATION_SLOTS):
        if index < len(items_state):
            item = _deserialize_item(items_state[index])

            if not item:
                updates.extend(
                    [
                        gr.update(visible=False),
                        gr.update(value=""),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(value=""),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False, value=None),
                    ]
                )
                continue

            item_identity = _get_item_identity(item)
            is_selected = item_identity == selected_identity

            if is_selected:
                detail_html = f"{inline_feedback_html}{_render_notification_details_html(item)}"
            else:
                detail_html = ""

            show_mark_processed = _should_show_mark_processed(item, is_selected)
            show_send_reminder = _should_show_send_reminder(item, is_selected)
            download_path = _get_download_path_for_selected_item(item, is_selected)

            updates.extend(
                [
                    gr.update(visible=True),
                    gr.update(value=_render_notification_card_html(item)),
                    gr.update(visible=True),
                    gr.update(visible=is_selected),
                    gr.update(value=detail_html),
                    gr.update(visible=show_mark_processed),
                    gr.update(visible=show_send_reminder),
                    gr.update(visible=is_selected),
                    gr.update(visible=bool(download_path), value=download_path),
                ]
            )
        else:
            updates.extend(
                [
                    gr.update(visible=False),
                    gr.update(value=""),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=""),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False, value=None),
                ]
            )

    return updates


def _slot_output_components(
    slot_containers: list,
    slot_card_htmls: list,
    slot_open_buttons: list,
    slot_detail_containers: list,
    slot_detail_htmls: list,
    slot_mark_buttons: list,
    slot_reminder_buttons: list,
    slot_close_buttons: list,
    slot_download_buttons: list,
) -> list:
    """
    Собирает плоский outputs-список для всех карточек.
    """
    flattened: list = []

    for i in range(MAX_NOTIFICATION_SLOTS):
        flattened.extend(
            [
                slot_containers[i],
                slot_card_htmls[i],
                slot_open_buttons[i],
                slot_detail_containers[i],
                slot_detail_htmls[i],
                slot_mark_buttons[i],
                slot_reminder_buttons[i],
                slot_close_buttons[i],
                slot_download_buttons[i],
            ]
        )

    return flattened


# =========================================================
# Payload для app.py
# =========================================================
def prepare_hr_screen_payload(auth_state_dict: dict | None) -> dict:
    """
    Подготавливает начальный payload для HR-экрана после логина.
    """
    auth_session = AuthSession.from_state(auth_state_dict)

    if not auth_session.is_authenticated or auth_session.role != "hr":
        return {
            "header_html": "",
            "requirements_text": "",
            "search_status": "",
            "candidate_rows": [],
            "action_status": "",
            "notifications_html": "",
            "notifications_filter_type_value": "all",
            "notifications_filter_status_value": "all",
            "notifications_feedback_html": "",
            "notification_detail_panel_visible": False,
            "notification_detail_html": "",
            "notification_items_state": [],
            "selected_notification_state": None,
            "mark_processed_button_visible": False,
            "send_reminder_button_visible": False,
        }

    notification_dashboard = hr_notification_service.get_dashboard(
        hr_user_id=int(auth_session.user_id or 0),
        type_filter="all",
        status_filter="all",
    )

    full_name = auth_session.full_name or "HR-менеджер"
    role_label = auth_session.role_display_name or "HR-менеджер"

    return {
        "header_html": _render_header_html(
            full_name=full_name,
            role_label=role_label,
            unread_notifications_count=notification_dashboard.unread_count,
        ),
        "requirements_text": "",
        "search_status": _render_feedback_html(
            "Введите требования к должности и запустите подбор кандидатов.",
            "info",
        ),
        "candidate_rows": [],
        "action_status": "",
        "notifications_html": _render_notifications_summary_html(notification_dashboard),
        "notifications_filter_type_value": "all",
        "notifications_filter_status_value": "all",
        "notifications_feedback_html": "",
        "notification_detail_panel_visible": False,
        "notification_detail_html": "",
        "notification_items_state": _serialize_items(notification_dashboard.items),
        "selected_notification_state": None,
        "mark_processed_button_visible": False,
        "send_reminder_button_visible": False,
    }


def get_hr_screen_reset_payload() -> dict:
    """
    Пустой payload для logout/reset.
    """
    return {
        "header_html": "",
        "requirements_text": "",
        "search_status": "",
        "candidate_rows": [],
        "action_status": "",
        "notifications_html": "",
        "notifications_filter_type_value": "all",
        "notifications_filter_status_value": "all",
        "notifications_feedback_html": "",
        "notification_detail_panel_visible": False,
        "notification_detail_html": "",
        "notification_items_state": [],
        "selected_notification_state": None,
        "mark_processed_button_visible": False,
        "send_reminder_button_visible": False,
    }


# =========================================================
# Основной runtime-экран HR
# =========================================================
def build_hr_screen(auth_state: gr.State, app_title: str) -> dict[str, gr.components.Component]:
    """
    Собирает runtime-экран HR.
    """

    # -----------------------------------------------------
    # Внутренние функции управления вкладками / уведомлениями
    # -----------------------------------------------------
    def _prime_notifications_from_auth(auth_state_dict: dict | None):
        """
        Предзагружает HR-уведомления сразу после логина/смены auth_state, чтобы первая отрисовка вкладки работала с первого клика.
        """
        auth_session = AuthSession.from_state(auth_state_dict)
        if not auth_session.is_authenticated or auth_session.role != "hr":
            empty_updates = _build_inline_slot_updates([], None)
            return (
                "",
                "",
                "",
                [],
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                *empty_updates,
            )

        return _refresh_notifications(
            auth_state_dict=auth_state_dict,
            type_filter="all",
            status_filter="all",
        )

    def _switch_hr_tab(selected_tab_code: str):
        """
        Переключает видимость двух основных вкладок HR.
        """
        return [
            gr.update(visible=(selected_tab_code == TAB_RATING)),
            gr.update(visible=(selected_tab_code == TAB_NOTIFICATIONS)),
        ]

    def _pin_selected_item_if_filtered_out(
        items_state: list[dict],
        selected_item_state: dict | None,
        previous_items_state: list[dict] | None,
    ) -> list[dict]:
        selected_item = _deserialize_item(selected_item_state)
        if not selected_item:
            return items_state

        selected_identity = _get_item_identity(selected_item)
        if not selected_identity:
            return items_state

        already_present = _find_item_by_identity(
            items_state=items_state,
            source_type_code=selected_item.source_type_code,
            queue_record_id=selected_item.queue_record_id,
        )
        if already_present:
            return items_state

        insert_index = 0
        for old_index, old_raw_item in enumerate(previous_items_state or []):
            old_item = _deserialize_item(old_raw_item)
            if _get_item_identity(old_item) == selected_identity:
                insert_index = min(old_index, len(items_state))
                break

        pinned_items = list(items_state)
        pinned_items.insert(insert_index, selected_item_state)
        return pinned_items

    def _compose_notifications_response(
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
        feedback_message: str = "",
        feedback_kind: str = "info",
        selected_item_state: dict | None = None,
        previous_items_state: list[dict] | None = None,
    ):
        """
        Единая сборка ответа для вкладки HR "Уведомления".
        """
        auth_session = AuthSession.from_state(auth_state_dict)

        if not auth_session.is_authenticated or auth_session.role != "hr":
            empty_dashboard = hr_notification_service.get_dashboard(0)

            return (
                "",
                _render_notifications_summary_html(empty_dashboard),
                _render_feedback_html("HR-сессия неактивна.", "error"),
                [],
                None,
                gr.update(visible=False),
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                *_build_inline_slot_updates([], None),
            )

        dashboard = hr_notification_service.get_dashboard(
            hr_user_id=int(auth_session.user_id or 0),
            type_filter=type_filter,
            status_filter=status_filter,
        )

        header_html_value = _render_header_html(
            full_name=auth_session.full_name or "HR",
            role_label=auth_session.role_display_name or "HR-менеджер",
            unread_notifications_count=dashboard.unread_count,
        )

        fresh_items_state = _serialize_items(dashboard.items)

        items_state = _preserve_items_order(
            previous_items_state=previous_items_state,
            fresh_items_state=fresh_items_state,
        )
        items_state = _pin_selected_item_if_filtered_out(
            items_state=items_state,
            selected_item_state=selected_item_state,
            previous_items_state=previous_items_state,
        )

        actual_selected_state = None
        selected_item = _deserialize_item(selected_item_state)
        if selected_item:
            actual_item = _find_item_by_identity(
                items_state=items_state,
                source_type_code=selected_item.source_type_code,
                queue_record_id=selected_item.queue_record_id,
            )
            if actual_item:
                actual_selected_state = asdict(actual_item)

        inline_feedback_html = ""
        if dashboard.load_error_message:
            final_feedback_html = _render_feedback_html(dashboard.load_error_message, "error")
        elif feedback_message and actual_selected_state:
            final_feedback_html = ""
            inline_feedback_html = _render_feedback_html(feedback_message, feedback_kind)
        elif feedback_message:
            final_feedback_html = _render_feedback_html(feedback_message, feedback_kind)
        else:
            final_feedback_html = ""

        return (
            header_html_value,
            _render_notifications_summary_html(dashboard),
            final_feedback_html,
            items_state,
            actual_selected_state,
            gr.update(visible=False),
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            *_build_inline_slot_updates(items_state, actual_selected_state, inline_feedback_html),
        )

    def _refresh_notifications(
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
    ):
        """
        Полное обновление списка уведомлений без открытия деталей.
        """
        return _compose_notifications_response(
            auth_state_dict=auth_state_dict,
            type_filter=type_filter,
            status_filter=status_filter,
            feedback_message="",
            feedback_kind="info",
            selected_item_state=None,
            previous_items_state=None,
        )

    def _open_notification_details(
        slot_index: int,
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
        items_state: list[dict] | None,
    ):
        """
        Открывает детали уведомления прямо под выбранной карточкой.
        """
        auth_session = AuthSession.from_state(auth_state_dict)
        safe_items_state = items_state or []

        if not auth_session.is_authenticated or auth_session.role != "hr":
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="HR-сессия неактивна.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        if slot_index < 0 or slot_index >= len(safe_items_state):
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Карточка уведомления не найдена.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        selected_item = _deserialize_item(safe_items_state[slot_index])
        if not selected_item:
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Не удалось прочитать карточку уведомления.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        action_result = hr_notification_service.mark_as_read(
            hr_user_id=int(auth_session.user_id or 0),
            source_type_code=selected_item.source_type_code,
            queue_record_id=selected_item.queue_record_id,
        )

        selected_item_state = asdict(selected_item)
        if action_result.success:
            selected_item_state["queue_status_code"] = "read"
            selected_item_state["queue_status_label"] = "Прочитано"

        return _compose_notifications_response(
            auth_state_dict=auth_state_dict,
            type_filter=type_filter,
            status_filter=status_filter,
            feedback_message=action_result.message,
            feedback_kind="success" if action_result.success else "error",
            selected_item_state=selected_item_state,
            previous_items_state=safe_items_state,
        )

    def _mark_selected_notification_processed_by_slot(
        slot_index: int,
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
        items_state: list[dict] | None,
    ):
        """
        Обрабатывает уведомление по кнопке конкретной карточки.
        """
        auth_session = AuthSession.from_state(auth_state_dict)
        safe_items_state = items_state or []

        if not auth_session.is_authenticated or auth_session.role != "hr":
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="HR-сессия неактивна.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        if slot_index < 0 or slot_index >= len(safe_items_state):
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Сначала откройте уведомление.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        selected_item = _deserialize_item(safe_items_state[slot_index])
        if not selected_item:
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Сначала откройте уведомление.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        result = hr_notification_service.mark_as_processed(
            hr_user_id=int(auth_session.user_id or 0),
            source_type_code=selected_item.source_type_code,
            queue_record_id=selected_item.queue_record_id,
        )

        return _compose_notifications_response(
            auth_state_dict=auth_state_dict,
            type_filter=type_filter,
            status_filter=status_filter,
            feedback_message=result.message,
            feedback_kind="success" if result.success else "error",
            selected_item_state=asdict(selected_item),
            previous_items_state=safe_items_state,
        )

    def _send_reminder_for_selected_notification_by_slot(
        slot_index: int,
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
        items_state: list[dict] | None,
    ):
        """
        Отправляет напоминание сотруднику только по карточке истекающего курса.
        """
        auth_session = AuthSession.from_state(auth_state_dict)
        safe_items_state = items_state or []

        if not auth_session.is_authenticated or auth_session.role != "hr":
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="HR-сессия неактивна.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        if slot_index < 0 or slot_index >= len(safe_items_state):
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Сначала откройте уведомление.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        selected_item = _deserialize_item(safe_items_state[slot_index])
        if not selected_item:
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Сначала откройте уведомление.",
                feedback_kind="error",
                selected_item_state=None,
                previous_items_state=safe_items_state,
            )

        if selected_item.source_type_code != "course_expiry":
            return _compose_notifications_response(
                auth_state_dict=auth_state_dict,
                type_filter=type_filter,
                status_filter=status_filter,
                feedback_message="Напоминание можно отправлять только по уведомлению об истекающем курсе.",
                feedback_kind="error",
                selected_item_state=asdict(selected_item),
                previous_items_state=safe_items_state,
            )

        result = hr_notification_service.send_course_reminder_to_employee(
            hr_user_id=int(auth_session.user_id or 0),
            queue_record_id=selected_item.queue_record_id,
        )

        return _compose_notifications_response(
            auth_state_dict=auth_state_dict,
            type_filter=type_filter,
            status_filter=status_filter,
            feedback_message=result.message,
            feedback_kind="success" if result.success else "error",
            selected_item_state=asdict(selected_item),
            previous_items_state=safe_items_state,
        )

    def _close_notification_details(
        auth_state_dict: dict | None,
        type_filter: str,
        status_filter: str,
    ):
        """
        Закрывает все открытые детали уведомлений.
        """
        return _compose_notifications_response(
            auth_state_dict=auth_state_dict,
            type_filter=type_filter,
            status_filter=status_filter,
            feedback_message="",
            feedback_kind="info",
            selected_item_state=None,
            previous_items_state=None,
        )

    # -----------------------------------------------------
    # Layout
    # -----------------------------------------------------
    with gr.Row(visible=False, elem_id="hr-root", elem_classes=["employee-shell"]) as root:
        # =================================================
        # Левая колонка
        # =================================================
        with gr.Column(scale=3, min_width=280, elem_classes=["sidebar-column"]):
            gr.HTML(_render_brand_html(app_title), elem_classes=["brand-card"])

            logout_button = gr.Button(
                value="Выйти",
                elem_classes=["logout-button"],
            )

            gr.HTML('<div class="nav-title">Навигация</div>', elem_classes=["nav-box"])

            nav_radio = gr.Radio(
                choices=[(tab.label, tab.code) for tab in HR_TABS],
                value=TAB_RATING,
                show_label=False,
                container=False,
                elem_id="hr-nav",
            )

        # =================================================
        # Правая колонка
        # =================================================
        with gr.Column(scale=10, min_width=720, elem_classes=["content-column"]):
            header_html = gr.HTML(value="", elem_classes=["header-card"])

            with gr.Column(elem_classes=["content-stack"]):
                with gr.Column(visible=True, elem_classes=["content-view", "main-tab-view"]) as rating_container:
                    rating_view = build_hr_candidate_search_view(auth_state)


                    requirements_input = rating_view["requirements_input"]
                    search_status = rating_view["search_status"]
                    candidates_table = rating_view["candidates_table"]
                    action_status = rating_view["action_status"]

                with gr.Column(visible=False, elem_classes=["content-view", "main-tab-view"]) as notifications_container:
                    notifications_html = gr.HTML(value="")

                    with gr.Column(elem_classes=["page-card"]):
                        with gr.Row():
                            notifications_filter_type = gr.Dropdown(
                                label="Тип уведомления",
                                choices=[
                                    ("Все типы", "all"),
                                    ("Изменение резюме", "resume_change_request"),
                                    ("Покупка бонуса", "bonus_purchase"),
                                    ("Истекающий курс", "course_expiry"),
                                ],
                                value="all",
                            )

                            notifications_filter_status = gr.Dropdown(
                                label="Статус",
                                choices=[
                                    ("Все статусы", "all"),
                                    ("Новое", "unread"),
                                    ("Прочитано", "read"),
                                    ("Обработано", "archived"),
                                    ("Ожидает рассмотрения", "pending"),
                                    ("Одобрено", "approved"),
                                    ("Отклонено", "rejected"),
                                    ("Нужно уточнение", "needs_clarification"),
                                    ("Внедрено", "implemented"),
                                    ("Ожидает решения HR", "pending_hr"),
                                    ("Отменено", "cancelled"),
                                    ("Нужно напомнить", "reminder_needed"),
                                    ("Напоминание отправлено", "reminder_sent"),
                                ],
                                value="all",
                            )

                    notifications_feedback_html = gr.HTML(value="")
                    notification_items_state = gr.State([])
                    selected_notification_state = gr.State(None)

                    with gr.Column(visible=False) as notification_detail_panel:
                        notification_detail_html = gr.HTML(value="")
                        mark_processed_button = gr.Button(value="legacy", visible=False)
                        send_reminder_button = gr.Button(value="legacy", visible=False)

                    notification_slot_containers: list = []
                    notification_card_html_components: list = []
                    notification_open_buttons: list = []
                    notification_inline_detail_containers: list = []
                    notification_inline_detail_html_components: list = []
                    notification_mark_processed_buttons: list = []
                    notification_send_reminder_buttons: list = []
                    notification_close_buttons: list = []
                    notification_download_buttons: list = []

                    for index in range(MAX_NOTIFICATION_SLOTS):
                        with gr.Column(elem_classes=["page-card", "hr-notification-slot"], visible=False) as slot_container:
                            notification_card_html = gr.HTML(value="")

                            notification_open_button = gr.Button(
                                f"Открыть подробности #{index + 1}",
                                visible=False,
                                elem_classes=["action-button"],
                            )

                            with gr.Column(visible=False) as inline_detail_container:
                                inline_detail_html = gr.HTML(value="")

                                with gr.Row(elem_classes=["notification-actions-row"]):
                                    mark_button = gr.Button(
                                        "Отметить как обработано",
                                        visible=False,
                                        elem_classes=["action-button", "notification-action-button"],
                                    )

                                    reminder_button = gr.Button(
                                        "Отправить напоминание сотруднику",
                                        visible=False,
                                        elem_classes=["action-button", "notification-action-button"],
                                    )

                                    download_button = gr.DownloadButton(
                                        label="Скачать файл",
                                        value=None,
                                        visible=False,
                                        elem_classes=["action-button", "notification-action-button"],
                                    )

                                    close_button = gr.Button(
                                        "Закрыть",
                                        visible=False,
                                        elem_classes=["form-cancel-button", "notification-action-button"],
                                    )

                        notification_slot_containers.append(slot_container)
                        notification_card_html_components.append(notification_card_html)
                        notification_open_buttons.append(notification_open_button)
                        notification_inline_detail_containers.append(inline_detail_container)
                        notification_inline_detail_html_components.append(inline_detail_html)
                        notification_mark_processed_buttons.append(mark_button)
                        notification_send_reminder_buttons.append(reminder_button)
                        notification_close_buttons.append(close_button)
                        notification_download_buttons.append(download_button)

        inline_slot_outputs = _slot_output_components(
            slot_containers=notification_slot_containers,
            slot_card_htmls=notification_card_html_components,
            slot_open_buttons=notification_open_buttons,
            slot_detail_containers=notification_inline_detail_containers,
            slot_detail_htmls=notification_inline_detail_html_components,
            slot_mark_buttons=notification_mark_processed_buttons,
            slot_reminder_buttons=notification_send_reminder_buttons,
            slot_close_buttons=notification_close_buttons,
            slot_download_buttons=notification_download_buttons,
        )

        auth_state.change(
            fn=_prime_notifications_from_auth,
            inputs=[auth_state],
            outputs=[
                header_html,
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                selected_notification_state,
                notification_detail_panel,
                notification_detail_html,
                mark_processed_button,
                send_reminder_button,
                *inline_slot_outputs,
            ],
            show_progress="hidden",
        )

        nav_radio.change(
            fn=_switch_hr_tab,
            inputs=[nav_radio],
            outputs=[rating_container, notifications_container],
            show_progress="hidden",
        ).then(
            fn=_refresh_notifications,
            inputs=[auth_state, notifications_filter_type, notifications_filter_status],
            outputs=[
                header_html,
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                selected_notification_state,
                notification_detail_panel,
                notification_detail_html,
                mark_processed_button,
                send_reminder_button,
                *inline_slot_outputs,
            ],
            show_progress="hidden",
        )

        notifications_filter_type.change(
            fn=_refresh_notifications,
            inputs=[auth_state, notifications_filter_type, notifications_filter_status],
            outputs=[
                header_html,
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                selected_notification_state,
                notification_detail_panel,
                notification_detail_html,
                mark_processed_button,
                send_reminder_button,
                *inline_slot_outputs,
            ],
            show_progress="hidden",
        )

        notifications_filter_status.change(
            fn=_refresh_notifications,
            inputs=[auth_state, notifications_filter_type, notifications_filter_status],
            outputs=[
                header_html,
                notifications_html,
                notifications_feedback_html,
                notification_items_state,
                selected_notification_state,
                notification_detail_panel,
                notification_detail_html,
                mark_processed_button,
                send_reminder_button,
                *inline_slot_outputs,
            ],
            show_progress="hidden",
        )

        # -----------------------------------------------------
        # Открыть подробности
        # -----------------------------------------------------
        for index, open_button in enumerate(notification_open_buttons):
            open_button.click(
                fn=lambda auth_state_dict, type_filter, status_filter, items_state, slot_index=index: _open_notification_details(
                    slot_index=slot_index,
                    auth_state_dict=auth_state_dict,
                    type_filter=type_filter,
                    status_filter=status_filter,
                    items_state=items_state,
                ),
                inputs=[
                    auth_state,
                    notifications_filter_type,
                    notifications_filter_status,
                    notification_items_state,
                ],
                outputs=[
                    header_html,
                    notifications_html,
                    notifications_feedback_html,
                    notification_items_state,
                    selected_notification_state,
                    notification_detail_panel,
                    notification_detail_html,
                    mark_processed_button,
                    send_reminder_button,
                    *inline_slot_outputs,
                ],
                show_progress="hidden",
            )

        # -----------------------------------------------------
        # Отметить как обработано
        # -----------------------------------------------------
        for index, mark_button in enumerate(notification_mark_processed_buttons):
            mark_button.click(
                fn=lambda auth_state_dict, type_filter, status_filter, items_state, slot_index=index: _mark_selected_notification_processed_by_slot(
                    slot_index=slot_index,
                    auth_state_dict=auth_state_dict,
                    type_filter=type_filter,
                    status_filter=status_filter,
                    items_state=items_state,
                ),
                inputs=[
                    auth_state,
                    notifications_filter_type,
                    notifications_filter_status,
                    notification_items_state,
                ],
                outputs=[
                    header_html,
                    notifications_html,
                    notifications_feedback_html,
                    notification_items_state,
                    selected_notification_state,
                    notification_detail_panel,
                    notification_detail_html,
                    mark_processed_button,
                    send_reminder_button,
                    *inline_slot_outputs,
                ],
                show_progress="hidden",
            )

        # -----------------------------------------------------
        # Отправить напоминание сотруднику
        # -----------------------------------------------------
        for index, reminder_button in enumerate(notification_send_reminder_buttons):
            reminder_button.click(
                fn=lambda auth_state_dict, type_filter, status_filter, items_state, slot_index=index: _send_reminder_for_selected_notification_by_slot(
                    slot_index=slot_index,
                    auth_state_dict=auth_state_dict,
                    type_filter=type_filter,
                    status_filter=status_filter,
                    items_state=items_state,
                ),
                inputs=[
                    auth_state,
                    notifications_filter_type,
                    notifications_filter_status,
                    notification_items_state,
                ],
                outputs=[
                    header_html,
                    notifications_html,
                    notifications_feedback_html,
                    notification_items_state,
                    selected_notification_state,
                    notification_detail_panel,
                    notification_detail_html,
                    mark_processed_button,
                    send_reminder_button,
                    *inline_slot_outputs,
                ],
                show_progress="hidden",
            )

        # -----------------------------------------------------
        # Закрыть подробности
        # -----------------------------------------------------
        for close_button in notification_close_buttons:
            close_button.click(
                fn=_close_notification_details,
                inputs=[
                    auth_state,
                    notifications_filter_type,
                    notifications_filter_status,
                ],
                outputs=[
                    header_html,
                    notifications_html,
                    notifications_feedback_html,
                    notification_items_state,
                    selected_notification_state,
                    notification_detail_panel,
                    notification_detail_html,
                    mark_processed_button,
                    send_reminder_button,
                    *inline_slot_outputs,
                ],
                show_progress="hidden",
            )

    return {
        "root": root,
        "container": root,
        "logout_button": logout_button,
        "header_html": header_html,
        "nav_radio": nav_radio,
        "rating_container": rating_container,
        "notifications_container": notifications_container,
        "requirements_input": requirements_input,
        "search_status": search_status,
        "candidates_table": candidates_table,
        "action_status": action_status,
        "notifications_html": notifications_html,
        "notifications_filter_type": notifications_filter_type,
        "notifications_filter_status": notifications_filter_status,
        "notifications_feedback_html": notifications_feedback_html,
        "notification_items_state": notification_items_state,
        "selected_notification_state": selected_notification_state,
        "notification_detail_panel": notification_detail_panel,
        "notification_detail_html": notification_detail_html,
        "mark_processed_button": mark_processed_button,
        "send_reminder_button": send_reminder_button,
    }

