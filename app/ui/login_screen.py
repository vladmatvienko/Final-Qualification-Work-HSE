"""
UI стартового окна входа.
"""

from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from html import escape

import gradio as gr

from app.core.config import get_settings


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
    Брендовый блок "Эльбрус" для экрана входа.
    """
    return f"""
    <div class="brand-box">
        <div class="brand-row">
            <div class="brand-logo">
                <img src="{LOGO_DATA_URI}" alt="Логотип Эльбрус">
            </div>
            <div>
                <div class="brand-title">{escape(app_title)}</div>
                <div class="brand-subtitle">Корпоративная платформа развития сотрудников</div>
            </div>
        </div>
    </div>
    """


def render_login_message_html(
    message: str,
    is_error: bool | None = None,
    is_success: bool | None = None,
) -> str:
    """
    Рисует HTML-блок сообщения на экране логина.
    """
    if not message:
        return ""

    if is_error is None:
        if is_success is not None:
            is_error = not is_success
        else:
            is_error = False

    css_class = "status-card error" if is_error else "status-card success"

    return f"""
    <div class="{css_class}">
        {escape(message)}
    </div>
    """


def build_login_screen(app_title: str = "Эльбрус"):
    """
    Собирает экран входа.
    """
    settings = get_settings()

    with gr.Column(visible=True) as container:
        with gr.Column(elem_classes=["login-shell"]):
            gr.HTML(_render_brand_html(settings.app_title))

            with gr.Column(elem_classes=["login-card"]):
                gr.HTML(
                    """
                    <div class="login-card-title">Вход в систему</div>
                    <div class="login-card-subtitle">
                        Введите логин и пароль, чтобы открыть рабочий интерфейс.
                    </div>
                    """
                )

                message_html = gr.HTML(value="", elem_classes=["auth-message"])

                username_input = gr.Textbox(
                    label="Логин",
                    placeholder="Введите логин",
                    lines=1,
                )

                password_input = gr.Textbox(
                    label="Пароль",
                    placeholder="Введите пароль",
                    lines=1,
                    type="password",
                )

                login_button = gr.Button(
                    value="Войти",
                    elem_classes=["login-button"],
                )

    return {
        "container": container,
        "message_html": message_html,
        "username_input": username_input,
        "password_input": password_input,
        "login_button": login_button,
    }