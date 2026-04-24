from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from app.auth.session_state import AuthSession
from app.core.config import get_settings
from app.services.auth_service import AuthService
from app.ui.employee_runtime_screen import (
    build_employee_screen,
    get_employee_screen_reset_payload,
    prepare_employee_screen_payload,
)
from app.ui.hr_runtime_screen import (
    build_hr_screen,
    get_hr_screen_reset_payload,
    prepare_hr_screen_payload,
)
from app.ui.login_screen import build_login_screen


# =========================================================
# Локальные dataclass / helper-структуры
# =========================================================
@dataclass
class PayloadBinding:
    """
    Описывает, как один ключ payload-а связан с конкретным UI-компонентом.
    """

    payload_key: str
    component_key: str
    component: Any
    mode: str


# =========================================================
# HTML helper для сообщения на login-экране
# =========================================================
def _render_login_message_html(message: str, kind: str = "info") -> str:
    """
    Возвращает единый HTML-блок для сообщений на экране авторизации.
    """
    if not message:
        return ""

    normalized_kind = kind if kind in {"success", "error", "info"} else "info"
    return f'<div class="feedback-box feedback-box--{normalized_kind}">{message}</div>'


# =========================================================
# Поиск компонента по нескольким возможным ключам
# =========================================================
def _get_component(component_map: dict[str, Any], *candidate_keys: str) -> Any:
    """
    Возвращает компонент по первому найденному ключу.
    """
    for key in candidate_keys:
        if key in component_map:
            return component_map[key]

    available_keys = ", ".join(sorted(component_map.keys()))
    requested_keys = ", ".join(candidate_keys)

    raise KeyError(
        f"Не найден компонент ни по одному из ключей: [{requested_keys}]. "
        f"Доступные ключи: [{available_keys}]"
    )


# =========================================================
# Построение binding-ов между payload и компонентами
# =========================================================
def _build_payload_bindings(
    view_map: dict[str, Any],
    payload_example: dict[str, Any],
    alias_map: dict[str, tuple[str, str]] | None = None,
) -> list[PayloadBinding]:
    """
    Автоматически строит binding-список для экрана.
    """
    bindings: list[PayloadBinding] = []
    alias_map = alias_map or {}

    for payload_key in payload_example.keys():
        component_key: str | None = None
        mode = "value"

        if payload_key in alias_map:
            alias_component_key, alias_mode = alias_map[payload_key]
            if alias_component_key in view_map:
                component_key = alias_component_key
                mode = alias_mode

        elif payload_key in view_map:
            component_key = payload_key
            mode = "value"

        elif payload_key.endswith("_value"):
            base_key = payload_key[: -len("_value")]
            if base_key in view_map:
                component_key = base_key
                mode = "value"

        elif payload_key.endswith("_visible"):
            base_key = payload_key[: -len("_visible")]
            if base_key in view_map:
                component_key = base_key
                mode = "visible"

        if component_key is None:
            continue

        bindings.append(
            PayloadBinding(
                payload_key=payload_key,
                component_key=component_key,
                component=view_map[component_key],
                mode=mode,
            )
        )

    return bindings


def _payload_output_components(bindings: list[PayloadBinding]) -> list[Any]:
    """
    Возвращает список компонентов в том же порядке, в котором будут возвращаться update-значения из _updates_from_payload(...).
    """
    return [binding.component for binding in bindings]


def _build_component_update(component: Any, mode: str, value: Any):
    """
    Строит корректный update-объект для конкретного компонента.
    """
    if isinstance(component, gr.State):
        return value

    if mode == "visible":
        return gr.update(visible=bool(value))

    return gr.update(value=value)


def _updates_from_payload(payload: dict[str, Any], bindings: list[PayloadBinding]) -> list[Any]:
    """
    Превращает payload dict в список update-ов под конкретный экран.
    """
    updates: list[Any] = []

    for binding in bindings:
        value = payload.get(binding.payload_key)
        updates.append(_build_component_update(binding.component, binding.mode, value))

    return updates


# =========================================================
# Основная фабрика приложения
# =========================================================
def create_app() -> gr.Blocks:
    """
    Собирает всё приложение "Эльбрус".
    """
    settings = get_settings()
    auth_service = AuthService()

    hr_alias_map: dict[str, tuple[str, str]] = {
        "requirements_text": ("requirements_input", "value"),
        "candidate_rows": ("candidates_table", "value"),
        "notifications_filter_type_value": ("notifications_filter_type", "value"),
        "notifications_filter_status_value": ("notifications_filter_status", "value"),
        "notification_detail_panel_visible": ("notification_detail_panel", "visible"),
        "mark_processed_button_visible": ("mark_processed_button", "visible"),
        "send_reminder_button_visible": ("send_reminder_button", "visible"),
    }

    employee_alias_map: dict[str, tuple[str, str]] = {
    }

    with gr.Blocks(title=settings.app_title) as demo:
        # -------------------------------------------------
        # Глобальное auth-state всего приложения
        # -------------------------------------------------
        auth_state = gr.State(AuthSession.anonymous().to_state())

        # -------------------------------------------------
        # Сборка трёх основных экранов
        # -------------------------------------------------
        login_view = build_login_screen()
        employee_view = build_employee_screen(auth_state, settings.app_title)
        hr_view = build_hr_screen(auth_state, settings.app_title)

        # -------------------------------------------------
        # Базовые компоненты login screen
        # -------------------------------------------------
        login_root = _get_component(login_view, "root", "container")
        login_username = _get_component(login_view, "username_input", "username", "login_input")
        login_password = _get_component(login_view, "password_input", "password", "password")
        login_button = _get_component(login_view, "login_button", "submit_button")
        login_message_html = _get_component(login_view, "message_html", "login_message_html", "message")

        # -------------------------------------------------
        # Корневые runtime screen-компоненты
        # -------------------------------------------------
        employee_root = _get_component(employee_view, "root", "container")
        employee_logout_button = _get_component(employee_view, "logout_button")

        hr_root = _get_component(hr_view, "root", "container")
        hr_logout_button = _get_component(hr_view, "logout_button")

        # -------------------------------------------------
        # Строим binding-и payload
        # -------------------------------------------------
        employee_reset_payload = get_employee_screen_reset_payload()
        hr_reset_payload = get_hr_screen_reset_payload()

        employee_bindings = _build_payload_bindings(
            view_map=employee_view,
            payload_example=employee_reset_payload,
            alias_map=employee_alias_map,
        )

        hr_bindings = _build_payload_bindings(
            view_map=hr_view,
            payload_example=hr_reset_payload,
            alias_map=hr_alias_map,
        )

        employee_payload_outputs = _payload_output_components(employee_bindings)
        hr_payload_outputs = _payload_output_components(hr_bindings)

        # -------------------------------------------------
        # Общие outputs для login/logout
        # -------------------------------------------------
        login_outputs = [
            auth_state,
            login_message_html,
            login_root,
            employee_root,
            hr_root,
            *employee_payload_outputs,
            *hr_payload_outputs,
        ]

        logout_outputs = [
            auth_state,
            login_message_html,
            login_root,
            employee_root,
            hr_root,
            login_username,
            login_password,
            *employee_payload_outputs,
            *hr_payload_outputs,
        ]

        # =================================================
        # Helper-ответы для безопасной маршрутизации
        # =================================================
        def _build_login_screen_response(
            message_text: str,
            kind: str = "error",
            session_state: dict | None = None,
        ):
            """
            Возвращает приложение в login-screen.
            """
            safe_session = session_state or AuthSession.anonymous().to_state()

            employee_reset = get_employee_screen_reset_payload()
            hr_reset = get_hr_screen_reset_payload()

            return (
                safe_session,
                _render_login_message_html(message_text, kind=kind),
                gr.update(visible=True),   # login_root
                gr.update(visible=False),  # employee_root
                gr.update(visible=False),  # hr_root
                *_updates_from_payload(employee_reset, employee_bindings),
                *_updates_from_payload(hr_reset, hr_bindings),
            )

        def _build_logout_response(message_text: str):
            """
            Ответ для logout.
            """
            employee_reset = get_employee_screen_reset_payload()
            hr_reset = get_hr_screen_reset_payload()

            return (
                AuthSession.anonymous().to_state(),
                _render_login_message_html(message_text, kind="success"),
                gr.update(visible=True),   # login_root
                gr.update(visible=False),  # employee_root
                gr.update(visible=False),  # hr_root
                gr.update(value=""),       # login_username
                gr.update(value=""),       # login_password
                *_updates_from_payload(employee_reset, employee_bindings),
                *_updates_from_payload(hr_reset, hr_bindings),
            )

        # =================================================
        # Логин
        # =================================================
        def _handle_login(username: str, password: str):
            """
            Обработчик входа в систему.
            """
            try:
                result = auth_service.authenticate(username, password)
            except Exception as exc:
                return _build_login_screen_response(
                    message_text=f"Ошибка авторизации: {escape(str(exc))}",
                    kind="error",
                )

            if not result.success:
                return _build_login_screen_response(
                    message_text=result.message,
                    kind="error",
                    session_state=result.session.to_state(),
                )

            if result.session.role == "employee":
                try:
                    employee_payload = prepare_employee_screen_payload(result.session.to_state())
                    hr_reset = get_hr_screen_reset_payload()

                    return (
                        result.session.to_state(),
                        _render_login_message_html(result.message, kind="success"),
                        gr.update(visible=False),  # login_root
                        gr.update(visible=True),   # employee_root
                        gr.update(visible=False),  # hr_root
                        *_updates_from_payload(employee_payload, employee_bindings),
                        *_updates_from_payload(hr_reset, hr_bindings),
                    )
                except Exception as exc:
                    return _build_login_screen_response(
                        message_text=f"Не удалось открыть экран сотрудника: {escape(str(exc))}",
                        kind="error",
                    )

            if result.session.role == "hr":
                try:
                    hr_payload = prepare_hr_screen_payload(result.session.to_state())
                    employee_reset = get_employee_screen_reset_payload()

                    return (
                        result.session.to_state(),
                        _render_login_message_html(result.message, kind="success"),
                        gr.update(visible=False),  # login_root
                        gr.update(visible=False),  # employee_root
                        gr.update(visible=True),   # hr_root
                        *_updates_from_payload(employee_reset, employee_bindings),
                        *_updates_from_payload(hr_payload, hr_bindings),
                    )
                except Exception as exc:
                    return _build_login_screen_response(
                        message_text=f"Не удалось открыть экран HR: {escape(str(exc))}",
                        kind="error",
                    )

            return _build_login_screen_response(
                message_text="Не удалось определить роль пользователя.",
                kind="error",
            )

        # =================================================
        # Logout
        # =================================================
        def _handle_logout():
            """
            Универсальный обработчик выхода.
            """
            try:
                auth_service.logout()
            except Exception:
                pass

            return _build_logout_response("Вы вышли из системы.")

        # -------------------------------------------------
        # События login
        # -------------------------------------------------
        login_button.click(
            fn=_handle_login,
            inputs=[login_username, login_password],
            outputs=login_outputs,
            queue=False,
            show_progress="hidden",
        )

        # -------------------------------------------------
        # События logout employee
        # -------------------------------------------------
        employee_logout_event = employee_logout_button.click(
            fn=_handle_logout,
            outputs=logout_outputs,
            queue=False,
            show_progress="hidden",
        )

        employee_logout_event.then(
            fn=None,
            inputs=None,
            outputs=None,
            js="""
            () => {
                setTimeout(() => {
                    window.location.replace(window.location.pathname);
                }, 80);
            }
            """,
        )

        # -------------------------------------------------
        # События logout HR
        # -------------------------------------------------
        hr_logout_event = hr_logout_button.click(
            fn=_handle_logout,
            outputs=logout_outputs,
            queue=False,
            show_progress="hidden",
        )

        hr_logout_event.then(
            fn=None,
            inputs=None,
            outputs=None,
            js="""
            () => {
                setTimeout(() => {
                    window.location.replace(window.location.pathname);
                }, 80);
            }
            """,
        )

    return demo