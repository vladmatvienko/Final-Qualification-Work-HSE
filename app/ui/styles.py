"""
Кастомные CSS-стили проекта "Эльбрус".
"""

APP_CSS = """
/* ---------------------------------------------
   Общие настройки контейнера Gradio
--------------------------------------------- */
.gradio-container {
    background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%);
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Корневой контейнер экрана */
#employee-root {
    max-width: 1380px;
    margin: 0 auto;
    padding: 24px 20px 28px 20px;
}

/* ---------------------------------------------
   Основной shell
--------------------------------------------- */
.employee-shell {
    gap: 20px;
    align-items: stretch;
}

/* Левая колонка */
.sidebar-column {
    background: #fdfefe;
    border: 1px solid #c8d8fb;
    border-radius: 24px;
    padding: 18px;
    box-shadow: 0 10px 30px rgba(64, 102, 194, 0.08);
    min-height: 760px;
}

/* Правая колонка */
.content-column {
    gap: 18px;
}

/* ---------------------------------------------
   Брендовый блок
--------------------------------------------- */
.brand-card {
    margin-bottom: 18px;
}

.brand-box {
    border: 2px solid #4d7de8;
    border-radius: 22px;
    background: linear-gradient(180deg, #ffffff 0%, #f3f8ff 100%);
    padding: 18px 16px;
    box-shadow: 0 8px 20px rgba(77, 125, 232, 0.10);
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-logo {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    flex-shrink: 0;
}

.brand-logo img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}

.brand-title {
    font-size: 28px;
    font-weight: 700;
    color: #2d63d1;
    line-height: 1.1;
}

.brand-subtitle {
    margin-top: 8px;
    color: #5f6f8f;
    font-size: 13px;
}

.login-logo {
    width: 96px;
    height: 96px;
}

.login-logo img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}

/* ---------------------------------------------
   Левое меню / вкладки
--------------------------------------------- */
.nav-box {
    border: 1px solid #d8e4ff;
    border-radius: 22px;
    background: #f8fbff;
    padding: 14px;
}

.nav-title {
    font-size: 14px;
    font-weight: 700;
    color: #5270aa;
    margin-bottom: 10px;
    padding-left: 4px;
}

#employee-nav {
    width: 100%;
}

#employee-nav .wrap {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

#employee-nav label {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    width: 100%;
    cursor: pointer;
}

#employee-nav label input {
    display: none !important;
}

#employee-nav label span {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 15px 16px;
    border-radius: 16px;
    border: 2px solid #2f65d6;
    background: #ffffff;
    color: #24324d;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 4px 10px rgba(48, 90, 185, 0.06);
}

#employee-nav label:hover span {
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(48, 90, 185, 0.10);
}

#employee-nav label input:checked + span {
    border-color: #33c46c;
    background: linear-gradient(180deg, #eefdf4 0%, #ddfaea 100%);
    color: #125538;
    box-shadow: 0 8px 18px rgba(51, 196, 108, 0.16);
}

/* ---------------------------------------------
   Верхний блок справа
--------------------------------------------- */
.header-card {
    border: 2px solid #4d7de8;
    border-radius: 24px;
    background: linear-gradient(180deg, #ffffff 0%, #f2f7ff 100%);
    padding: 18px 22px;
    box-shadow: 0 10px 24px rgba(77, 125, 232, 0.10);
}

.employee-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.employee-header-main {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.employee-header-label {
    font-size: 15px;
    color: #5b6c90;
    font-weight: 600;
}

.employee-name {
    font-size: 30px;
    font-weight: 700;
    color: #224ea8;
    line-height: 1.15;
}

.employee-header-subtitle {
    font-size: 14px;
    color: #6c7c9b;
}

.employee-metrics {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.metric-chip {
    min-width: 200px;
    padding: 14px 16px;
    border-radius: 18px;
    border: 1px solid #bfd4ff;
    background: #fdfefe;
    box-shadow: 0 8px 18px rgba(61, 101, 188, 0.08);
}

.metric-label {
    font-size: 13px;
    color: #6d7a96;
    margin-bottom: 4px;
    font-weight: 600;
}

.metric-value {
    font-size: 24px;
    color: #2558bf;
    font-weight: 800;
}

/* ---------------------------------------------
   Общая обёртка контента справа
--------------------------------------------- */
.content-stack {
    gap: 18px;
}

.content-view {
    min-height: 0;
}

.main-tab-view {
    min-height: 590px;
}

.notification-slot,
.hr-notification-slot {
    min-height: 0 !important;
    margin-bottom: 16px !important;
}

.hr-notification-slot > .block,
.notification-slot > .block {
    min-height: 0 !important;
}

.action-button-row {
    margin-top: 12px;
}

.action-button button {
    border-radius: 14px !important;
    border: 2px solid #4d7de8 !important;
    background: #e8f0ff !important;
    color: #2c5fc9 !important;
    font-weight: 700 !important;
}

/* ---------------------------------------------
   Карточка содержимого вкладки
--------------------------------------------- */
.page-card {
    border: 2px solid #4d7de8;
    border-radius: 24px;
    background: #fdfefe;
    padding: 22px;
    box-shadow: 0 12px 28px rgba(77, 125, 232, 0.10);
    max-height: none;
    overflow: visible;
}

.page-card--scroll {
    max-height: 620px;
    overflow-y: auto;
}

.page-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}

.page-title {
    font-size: 26px;
    font-weight: 700;
    color: #2557bf;
}

.page-subtitle {
    color: #7182a3;
    font-size: 14px;
}

.stub-banner {
    background: #eef5ff;
    border: 1px dashed #8bb1ff;
    color: #4c6598;
    border-radius: 16px;
    padding: 12px 14px;
    font-size: 14px;
    margin-bottom: 18px;
}

/* ---------------------------------------------
   Разделы резюме
--------------------------------------------- */
.resume-section {
    margin-bottom: 18px;
}

.resume-section-title {
    font-size: 20px;
    font-weight: 700;
    color: #2d5fca;
    margin-bottom: 8px;
}

.resume-line {
    font-size: 17px;
    color: #3b4a67;
    line-height: 1.55;
    margin-bottom: 3px;
    white-space: pre-wrap;
}

/* ---------------------------------------------
   Сетки карточек
--------------------------------------------- */
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
}

@media (max-width: 1200px) {
    .card-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 820px) {
    .card-grid {
        grid-template-columns: 1fr;
    }
}

/* ---------------------------------------------
   Карточки достижений
--------------------------------------------- */
.achievement-card {
    border-radius: 20px;
    padding: 18px;
    border: 2px solid #d4e0ff;
    background: #ffffff;
    box-shadow: 0 8px 18px rgba(69, 109, 201, 0.08);
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.achievement-card--completed {
    border-color: #42bf74;
    background: linear-gradient(180deg, #f3fff7 0%, #ebfff2 100%);
}

.achievement-card--locked {
    border-color: #c7d6f5;
    background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
    opacity: 0.95;
}

.card-icon {
    font-size: 28px;
}

.card-points {
    font-size: 14px;
    font-weight: 800;
    color: #4b63a3;
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    color: #244ca6;
}

.card-text {
    font-size: 14px;
    line-height: 1.5;
    color: #556784;
}

.status-pill {
    align-self: flex-start;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

.status-pill--done {
    background: #ddfaea;
    color: #10623a;
    border: 1px solid #8be0b0;
}

.status-pill--todo {
    background: #edf2ff;
    color: #4362a8;
    border: 1px solid #baceff;
}

/* ---------------------------------------------
   Карточки магазина
--------------------------------------------- */
.store-card {
    border-radius: 20px;
    padding: 18px;
    border: 2px solid #d8e4ff;
    background: #ffffff;
    box-shadow: 0 8px 18px rgba(69, 109, 201, 0.08);
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.store-price {
    font-size: 20px;
    font-weight: 800;
    color: #2558bf;
}

.store-action {
    margin-top: auto;
    padding: 10px 12px;
    border-radius: 12px;
    background: #edf3ff;
    border: 1px solid #bfd2ff;
    color: #315eb7;
    font-weight: 700;
    text-align: center;
    font-size: 14px;
}

/* ---------------------------------------------
   Уведомления
--------------------------------------------- */
.notifications-stack {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.notification-card {
    border-radius: 20px;
    padding: 18px;
    border: 2px solid #d8e4ff;
    background: #ffffff;
    box-shadow: 0 8px 18px rgba(69, 109, 201, 0.08);
}

.notification-top {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}

.notification-title {
    font-size: 18px;
    font-weight: 700;
    color: #244ea8;
}

.notification-meta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.priority-pill,
.read-pill {
    padding: 7px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

.priority-pill {
    background: #fff4dd;
    color: #8c6400;
    border: 1px solid #ffd77d;
}

.read-pill {
    background: #edf2ff;
    color: #4969ab;
    border: 1px solid #bfd0ff;
}

.notification-text {
    font-size: 15px;
    line-height: 1.55;
    color: #586986;
}

/* ---------------------------------------------
   Сообщения об успехе / ошибке
--------------------------------------------- */
.feedback-box {
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 16px;
    font-size: 14px;
    line-height: 1.55;
    border: 1px solid transparent;
}

.feedback-box--success {
    background: #ebfff2;
    border-color: #96e2b3;
    color: #125d37;
}

.feedback-box--error {
    background: #fff1f1;
    border-color: #f2a3a3;
    color: #8f2020;
}

.feedback-box--info {
    background: #eef5ff;
    border-color: #bfd4ff;
    color: #38588f;
}

/* ---------------------------------------------
   Нижняя правая зона действий на странице резюме
--------------------------------------------- */
.page-footer-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
    gap: 12px;
}

/* ---------------------------------------------
   Псевдо-модальная форма внутри блока
--------------------------------------------- */
.resume-change-form {
    margin-top: 18px;
    border: 2px solid #9dbdff;
    border-radius: 22px;
    background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
    padding: 18px;
    box-shadow: 0 12px 26px rgba(77, 125, 232, 0.12);
}

.resume-change-form-title {
    font-size: 22px;
    font-weight: 700;
    color: #2759bf;
    margin-bottom: 6px;
}

.resume-change-form-subtitle {
    font-size: 14px;
    color: #6a7a98;
    margin-bottom: 14px;
}

.form-actions-row {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 6px;
}

.form-cancel-button button {
    border-radius: 14px !important;
    border: 2px solid #c0cce7 !important;
    background: #ffffff !important;
    color: #486182 !important;
    font-weight: 700 !important;
}

.form-submit-button button {
    border-radius: 14px !important;
    border: 2px solid #2f65d6 !important;
    background: #2f65d6 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Немного усилим стиль полей формы */
.resume-change-form .gradio-dropdown,
.resume-change-form .gradio-textbox,
.resume-change-form .gradio-file {
    border-radius: 16px;
}

/* ---------------------------------------------
   Адаптивность
--------------------------------------------- */
@media (max-width: 980px) {
    .employee-name {
        font-size: 24px;
    }

    .page-title {
        font-size: 22px;
    }

    .metric-chip {
        min-width: 160px;
    }

    .page-footer-actions {
        justify-content: stretch;
    }
}

/* ---------------------------------------------
   Отдельный scroll-блок для резюме, чтобы кнопка и форма были всегда ниже и видны
--------------------------------------------- */
.personal-data-page-card {
    max-height: none !important;
    overflow: visible !important;
}

.resume-scroll-box {
    max-height: 360px;
    overflow-y: auto;
    padding-right: 8px;
    margin-bottom: 18px;
    border-radius: 16px;
}

.resume-scroll-box::-webkit-scrollbar {
    width: 8px;
}

.resume-scroll-box::-webkit-scrollbar-thumb {
    background: #b9c9eb;
    border-radius: 999px;
}

.resume-scroll-box::-webkit-scrollbar-track {
    background: transparent;
}

/* =========================================================
   Магазин бонусов — компактные карточки
   ========================================================= */

.store-grid-row {
    gap: 16px !important;
    align-items: stretch !important;
}

.store-slot-column {
    min-width: 0 !important;
}

.store-slot-html {
    margin-bottom: 10px !important;
}

.store-card--uniform {
    min-height: 230px;
    height: 230px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    overflow: hidden;
    padding: 16px !important;
}

.store-card--uniform .card-icon {
    font-size: 22px !important;
    margin-bottom: 10px !important;
}

.store-card--uniform .store-price {
    font-size: 16px !important;
    line-height: 1.2 !important;
    margin-bottom: 10px !important;
}

.store-card--uniform .card-title {
    font-size: 14px !important;
    line-height: 1.35 !important;
    margin-bottom: 10px !important;
    font-weight: 700 !important;
}

.store-card--uniform .card-text {
    font-size: 12px !important;
    line-height: 1.4 !important;
    color: #5f6f93 !important;
}

.store-card--placeholder {
    visibility: hidden;
    pointer-events: none;
}

.store-select-button button {
    width: 100% !important;
    min-height: 48px !important;
}

.store-purchase-panel {
    margin-bottom: 16px !important;
}

/* =========================================================
   HR-меню в том же стиле, что и меню сотрудника
   ========================================================= */

#hr-nav {
    width: 100%;
}

#hr-nav .wrap {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

#hr-nav label {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    width: 100%;
    cursor: pointer;
}

#hr-nav label input {
    display: none !important;
}

#hr-nav label span {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 15px 16px;
    border-radius: 16px;
    border: 2px solid #2f65d6;
    background: #ffffff;
    color: #24324d;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 4px 10px rgba(48, 90, 185, 0.06);
}

#hr-nav label:hover span {
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(48, 90, 185, 0.10);
}

#hr-nav label input:checked + span {
    border-color: #33c46c;
    background: linear-gradient(180deg, #eefdf4 0%, #ddfaea 100%);
    color: #125538;
    box-shadow: 0 8px 18px rgba(51, 196, 108, 0.16);
}

#hr-requirements-block {
    display: block !important;
    width: 100% !important;
    margin: 8px 0 16px 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

#hr-requirements-input {
    display: block !important;
    width: 100% !important;
    min-height: 170px !important;
    visibility: visible !important;
    opacity: 1 !important;
}

#hr-requirements-input > label,
#hr-requirements-input label {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #5F7093 !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin-bottom: 10px !important;
}

#hr-requirements-input textarea,
#hr-requirements-input textarea.scroll-hide,
#hr-requirements-input .scroll-hide textarea,
.hr-requirements-input textarea {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;

    width: 100% !important;
    min-height: 150px !important;
    height: 150px !important;
    max-height: none !important;

    padding: 14px 16px !important;
    border: 1px solid #BFD0F3 !important;
    border-radius: 16px !important;

    background: #F7FAFF !important;
    color: #24324D !important;

    resize: vertical !important;
    overflow: auto !important;
    box-sizing: border-box !important;
    box-shadow: none !important;

    line-height: 1.45 !important;
    font-size: 16px !important;
}

#hr-requirements-input textarea::placeholder,
.hr-requirements-input textarea::placeholder {
    color: #7B8BA8 !important;
    opacity: 1 !important;
}

#hr-requirements-input .wrap,
#hr-requirements-input .wrap-inner,
#hr-requirements-input .form,
#hr-requirements-input .input-container,
#hr-requirements-input .scroll-hide {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    height: auto !important;
    min-height: 150px !important;
}

#hr-candidate-selector input,
#hr-candidate-selector .secondary-wrap,
#hr-candidate-selector [role="combobox"],
#hr-candidate-selector .wrap-inner,
#hr-candidate-selector button {
    color: #F4F7FF !important;
}

#hr-candidate-selector input::placeholder {
    color: #D9E4FF !important;
    opacity: 1 !important;
}

#hr-candidate-selector [role="option"],
#hr-candidate-selector li {
    color: #24324D !important;
    background: #FFFFFF !important;
}
"""
