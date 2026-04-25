"""
Дополнительные стили для авторизации и runtime-панелей.
"""

AUTH_CSS = """
/* ---------------------------------------------------------
   Экран входа
--------------------------------------------------------- */


.login-shell {
    width: 100%;
    max-width: 520px;
    margin: 32px auto 0 auto;
}

/* Карточка логина */
.login-card {
    width: 100%;
    max-width: 460px;
    margin: 0 auto;
    border: 2px solid #4d7de8;
    border-radius: 28px;
    background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%);
    padding: 24px;
    box-shadow: 0 16px 36px rgba(77, 125, 232, 0.12);
}

.login-card-title {
    font-size: 28px;
    font-weight: 700;
    color: #2557bf;
    margin-bottom: 6px;
    text-align: center;
}

.login-card-subtitle {
    font-size: 14px;
    color: #7080a0;
    text-align: center;
    margin-bottom: 18px;
}

.login-button button {
    border-radius: 16px !important;
    border: 2px solid #2f65d6 !important;
    background: #2f65d6 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    min-height: 48px;
}

.auth-message {
    margin-bottom: 14px;
}

/* ---------------------------------------------------------
   Кнопка выхода
--------------------------------------------------------- */
.logout-button button {
    border-radius: 14px !important;
    border: 2px solid #bfd4ff !important;
    background: #ffffff !important;
    color: #2c5fc9 !important;
    font-weight: 700 !important;
    width: 100%;
}

/* ---------------------------------------------------------
   Runtime-экраны
--------------------------------------------------------- */

.runtime-action-panel,
.runtime-form-panel {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.runtime-form-panel {
    margin-top: 14px !important;
}

#employee-root {
    margin-top: 0 !important;
    padding-top: 8px !important;
}

.gradio-container {
    padding-top: 0 !important;
}

#employee-root > .column:first-child,
#employee-root > .column:last-child {
    margin-top: 0 !important;
}

.hr-notification-slot:empty {
    display: none !important;
}

.hr-notification-slot[style*="visibility: hidden"] {
    display: none !important;
}
"""