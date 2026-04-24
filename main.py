from __future__ import annotations

import os

from gradio.themes import Soft

from app.core.config import get_settings
from app.ui.app import create_app
from app.ui.auth_styles import AUTH_CSS
from app.ui.styles import APP_CSS

APP_THEME = Soft(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="slate",
)

FULL_APP_CSS = APP_CSS + "\n" + AUTH_CSS


def _normalize_gradio_env() -> None:
    """
    Нормализует переменные окружения Gradio.
    """
    raw_debug = os.getenv("GRADIO_DEBUG")

    if raw_debug is None:
        return

    normalized = raw_debug.strip().lower()

    if normalized in {"true", "yes", "on"}:
        os.environ["GRADIO_DEBUG"] = "1"
    elif normalized in {"false", "no", "off"}:
        os.environ["GRADIO_DEBUG"] = "0"


def main() -> None:
    """
    Точка входа в приложение.
    """
    _normalize_gradio_env()

    settings = get_settings()
    demo = create_app()

    server_name = getattr(settings, "gradio_server_name", "127.0.0.1")
    server_port = int(getattr(settings, "gradio_server_port", 7860))

    inbrowser = bool(
        getattr(
            settings,
            "gradio_inbrowser",
            getattr(
                settings,
                "gradio_in_browser",
                getattr(settings, "open_in_browser", False),
            ),
        )
    )

    demo.launch(
        server_name=server_name,
        server_port=server_port,
        inbrowser=inbrowser,
        theme=APP_THEME,
        css=FULL_APP_CSS,
    )


if __name__ == "__main__":
    main()