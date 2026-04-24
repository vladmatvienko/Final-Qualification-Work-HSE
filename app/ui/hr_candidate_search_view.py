from __future__ import annotations

from html import escape

import gradio as gr

from app.auth.session_state import AuthSession
from app.services.hr_candidate_search_service import HRCandidateSearchService
from app.services.job_invitation_service import JobInvitationService


candidate_search_service = HRCandidateSearchService()
job_invitation_service = JobInvitationService()


def _render_feedback_html(message: str, kind: str = "info") -> str:
    """
    Универсальный HTML-блок обратной связи.
    """
    if not message:
        return ""

    normalized_kind = kind if kind in {"success", "error", "info"} else "info"
    return f'<div class="feedback-box feedback-box--{normalized_kind}">{escape(message)}</div>'


def _render_results_table_html(rows: list[list[str]] | None) -> str:
    """
    Рисует таблицу результатов как обычный HTML.
    """
    safe_rows = rows or []

    if not safe_rows:
        return """
        <div class="hr-search-results-wrap">
            <div class="hr-search-results-label">Результаты подбора</div>
            <div class="hr-search-empty-state">
                Пока результатов нет. Введите требования к должности и нажмите
                «Запустить подбор кандидатов».
            </div>
        </div>
        """

    header_html = """
    <thead>
        <tr>
            <th>Анонимный ID</th>
            <th>Score</th>
            <th>Ключевые навыки</th>
            <th>Релевантный опыт</th>
            <th>Курсы / образование</th>
        </tr>
    </thead>
    """

    body_rows: list[str] = []
    for row in safe_rows:
        padded_row = list(row) + [""] * (5 - len(row))
        body_rows.append(
            f"""
            <tr>
                <td>{escape(str(padded_row[0]))}</td>
                <td>{escape(str(padded_row[1]))}</td>
                <td>{escape(str(padded_row[2]))}</td>
                <td>{escape(str(padded_row[3]))}</td>
                <td>{escape(str(padded_row[4]))}</td>
            </tr>
            """
        )

    body_html = "<tbody>" + "".join(body_rows) + "</tbody>"

    return f"""
    <div class="hr-search-results-wrap">
        <div class="hr-search-results-label">Результаты подбора</div>
        <div class="hr-search-table-scroll">
            <table class="hr-search-results-table">
                {header_html}
                {body_html}
            </table>
        </div>
    </div>
    """


def build_hr_candidate_search_view(auth_state: gr.State) -> dict[str, gr.components.Component]:
    """
    UI вкладки HR «Рейтинговая анонимная таблица».
    """

    def _run_candidate_search(auth_state_dict: dict | None, requirements_text: str):
        session = AuthSession.from_state(auth_state_dict)

        if not session.is_authenticated or session.role != "hr":
            return (
                _render_feedback_html("HR-сессия неактивна.", "error"),
                _render_results_table_html([]),
                gr.update(
                    choices=[],
                    value=None,
                    interactive=False,
                ),
                "",
                "",
                _render_feedback_html("Сначала авторизуйтесь как HR.", "error"),
            )

        result = candidate_search_service.search(requirements_text)

        if result.is_error:
            return (
                _render_feedback_html(result.message_text, "error"),
                _render_results_table_html([]),
                gr.update(
                    choices=[],
                    value=None,
                    interactive=False,
                ),
                "",
                "",
                _render_feedback_html(result.message_text, "error"),
            )

        selected_candidate_message = ""
        if result.default_candidate_code:
            selected_candidate_message = _render_feedback_html(
                f"Для просмотра профиля выбран кандидат {result.default_candidate_code}. "
                f"При необходимости выберите другого кандидата ниже.",
                "info",
            )

        return (
            _render_feedback_html(result.message_text, "success"),
            _render_results_table_html(result.table_rows),
            gr.update(
                choices=result.dropdown_choices,
                value=result.default_candidate_code,
                interactive=bool(result.dropdown_choices),
            ),
            "",
            "",
            selected_candidate_message,
        )

    def _show_candidate_resume(auth_state_dict: dict | None, anonymous_code: str):
        session = AuthSession.from_state(auth_state_dict)

        if not session.is_authenticated or session.role != "hr":
            return (
                "",
                _render_feedback_html("HR-сессия неактивна.", "error"),
            )

        anonymous_code = (anonymous_code or "").strip()
        if not anonymous_code:
            return (
                "",
                _render_feedback_html(
                    "Сначала выберите кандидата в блоке «Выбор кандидата для просмотра профиля».",
                    "error",
                ),
            )

        resume_html = candidate_search_service.get_full_resume_html(anonymous_code)

        return (
            resume_html,
            _render_feedback_html(
                f"Открыт анонимизированный профиль кандидата {anonymous_code}.",
                "success",
            ),
        )

    def _send_candidate_invitation(
        auth_state_dict: dict | None,
        anonymous_code: str,
        requirements_text: str,
        comment_text: str,
    ):
        session = AuthSession.from_state(auth_state_dict)

        if not session.is_authenticated or session.role != "hr":
            return (
                _render_feedback_html("HR-сессия неактивна.", "error"),
                gr.update(value=comment_text),
            )

        anonymous_code = (anonymous_code or "").strip()
        if not anonymous_code:
            return (
                _render_feedback_html(
                    "Сначала выберите кандидата в блоке «Выбор кандидата для просмотра профиля».",
                    "error",
                ),
                gr.update(value=comment_text),
            )

        result = job_invitation_service.send_invitation(
            hr_user_id=int(session.user_id or 0),
            anonymous_code=anonymous_code,
            requirements_text=requirements_text,
            comment_text=comment_text,
        )

        if result.success:
            return (
                _render_feedback_html(result.message, "success"),
                gr.update(value=""),
            )

        return (
            _render_feedback_html(result.message, "error"),
            gr.update(value=comment_text),
        )

    with gr.Column(elem_classes=["page-card"]):
        gr.HTML(
            """
            <style>
                .hr-search-field-title {
                    color: #24324D !important;
                    font-size: 16px !important;
                    font-weight: 700 !important;
                    line-height: 1.35 !important;
                    margin: 10px 0 10px 0 !important;
                }

                .hr-search-input-wrap {
                    margin: 6px 0 18px 0;
                }

                .hr-search-input-wrap input,
                .hr-search-input-wrap textarea {
                    width: 100% !important;
                    background: #44597C !important;
                    color: #FFFFFF !important;
                    border: 1px solid #5B739D !important;
                    border-radius: 14px !important;
                    padding: 14px 16px !important;
                    min-height: 56px !important;
                    height: 56px !important;
                    font-size: 16px !important;
                    line-height: 1.4 !important;
                    box-shadow: none !important;
                }

                .hr-search-input-wrap input::placeholder,
                .hr-search-input-wrap textarea::placeholder {
                    color: #D2DDF0 !important;
                    opacity: 1 !important;
                }

                .hr-search-results-wrap {
                    margin-top: 12px;
                }

                .hr-search-results-label {
                    color: #24324D !important;
                    font-size: 16px !important;
                    font-weight: 700 !important;
                    line-height: 1.35 !important;
                    margin: 0 0 10px 0 !important;
                }

                .hr-search-table-scroll {
                    width: 100%;
                    overflow-x: auto;
                    border-radius: 16px;
                    border: 1px solid #D7E2F7;
                    background: #FFFFFF;
                }

                .hr-search-results-table {
                    width: 100%;
                    border-collapse: collapse;
                    min-width: 980px;
                    background: #FFFFFF;
                }

                .hr-search-results-table thead th {
                    background: #071731 !important;
                    color: #FFFFFF !important;
                    text-align: left;
                    font-weight: 700;
                    padding: 14px 12px;
                    border-right: 1px solid #24324D;
                    font-size: 15px;
                }

                .hr-search-results-table thead th:last-child {
                    border-right: none;
                }

                .hr-search-results-table tbody td {
                    background: #FFFFFF !important;
                    color: #24324D !important;
                    padding: 14px 12px;
                    border-top: 1px solid #D7E2F7;
                    border-right: 1px solid #E3ECFB;
                    vertical-align: top;
                    line-height: 1.5;
                    font-size: 14px;
                }

                .hr-search-results-table tbody td:last-child {
                    border-right: none;
                }

                .hr-search-results-table tbody tr:nth-child(even) td {
                    background: #F7FAFF !important;
                }

                .hr-search-empty-state {
                    background: #F7FAFF;
                    color: #48648F;
                    border: 1px dashed #BFD0F3;
                    border-radius: 14px;
                    padding: 16px;
                    line-height: 1.5;
                }

                .hr-candidate-selector-wrap {
                    margin-top: 16px;
                    margin-bottom: 12px;
                }

                .hr-candidate-selector-wrap .wrap,
                .hr-candidate-selector-wrap input,
                .hr-candidate-selector-wrap textarea {
                    color: #FFFFFF !important;
                }
            </style>
            """
        )

        gr.HTML(
            """
            <div class="page-title-row">
                <div class="page-title">Рейтинговая анонимная таблица</div>
                <div class="page-subtitle">
                    Поиск и ранжирование кандидатов по требованиям к должности.
                </div>
            </div>
            """
        )

        gr.HTML('<div class="hr-search-field-title">Требования к должности</div>')

        with gr.Column(elem_classes=["hr-search-input-wrap"]):
            requirements_input = gr.Textbox(
                show_label=False,
                value="",
                lines=1,
                max_lines=1,
                placeholder=(
                    "Например: Python backend developer, MySQL, API, интеграции, внутренние сервисы, обучение, релевантный опыт"
                ),
                interactive=True,
                container=True,
            )

        search_button = gr.Button(
            value="Запустить подбор кандидатов",
            elem_classes=["action-button"],
        )

        search_status = gr.HTML(
            value=_render_feedback_html(
                "Введите требования к должности и запустите подбор кандидатов.",
                "info",
            )
        )

        candidates_table = gr.HTML(
            value=_render_results_table_html([]),
        )

        gr.HTML('<div class="hr-search-field-title">Выбор кандидата для просмотра профиля и отправки приглашения</div>')

        candidate_selector_status = gr.HTML(
            value=_render_feedback_html(
                "После подбора здесь появится список анонимных кандидатов.",
                "info",
            )
        )

        with gr.Column(elem_classes=["hr-candidate-selector-wrap"]):
            candidate_selector = gr.Dropdown(
                show_label=False,
                choices=[],
                value=None,
                interactive=False,
                allow_custom_value=False,
            )

        with gr.Row():
            open_resume_button = gr.Button(
                value="Посмотреть профиль выбранного кандидата",
                elem_classes=["action-button"],
            )
            send_invitation_button = gr.Button(
                value="Отправить приглашение выбранному кандидату",
                elem_classes=["action-button"],
            )

        invitation_comment_input = gr.Textbox(
            label="Комментарий к приглашению (необязательно)",
            lines=3,
            placeholder="Например: приглашаем вас на внутреннюю роль backend-разработчика в продуктовую команду.",
        )

        action_status = gr.HTML(value="")
        full_resume_html = gr.HTML(value="")

        search_button.click(
            fn=_run_candidate_search,
            inputs=[auth_state, requirements_input],
            outputs=[
                search_status,
                candidates_table,
                candidate_selector,
                action_status,
                full_resume_html,
                candidate_selector_status,
            ],
            show_progress="hidden",
        )

        open_resume_button.click(
            fn=_show_candidate_resume,
            inputs=[auth_state, candidate_selector],
            outputs=[
                full_resume_html,
                action_status,
            ],
            show_progress="hidden",
        )

        send_invitation_button.click(
            fn=_send_candidate_invitation,
            inputs=[auth_state, candidate_selector, requirements_input, invitation_comment_input],
            outputs=[
                action_status,
                invitation_comment_input,
            ],
            show_progress="hidden",
        )

    return {
        "requirements_input": requirements_input,
        "search_status": search_status,
        "candidates_table": candidates_table,
        "candidate_selector": candidate_selector,
        "candidate_selector_status": candidate_selector_status,
        "action_status": action_status,
    }