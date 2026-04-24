USE elbrus;

-- ---------------------------------------------------------
-- Роли
-- ---------------------------------------------------------
INSERT INTO roles (id, code, name, description) VALUES
(1, 'HR_MANAGER', 'HR-менеджер', 'Пользователь, который работает с рейтингом кандидатов, уведомлениями и приглашениями'),
(2, 'EMPLOYEE', 'Сотрудник', 'Обычный сотрудник компании, который развивает профиль и покупает бонусы');

-- ---------------------------------------------------------
-- Подразделения
-- ---------------------------------------------------------
INSERT INTO departments (id, name, code, parent_department_id, is_active) VALUES
(1, 'HR', 'HR', NULL, TRUE),
(2, 'ИТ', 'IT', NULL, TRUE),
(3, 'Производство', 'PROD', NULL, TRUE);

-- ---------------------------------------------------------
-- Справочник должностей
-- ---------------------------------------------------------
INSERT INTO positions_catalog (id, department_id, title, grade, description, is_active) VALUES
(1, 1, 'HR-менеджер', 'Middle', 'Ведет подбор, кадровые процессы и развитие сотрудников', TRUE),
(2, 2, 'Python Backend Developer', 'Senior', 'Разработка backend-сервисов на Python', TRUE),
(3, 2, 'QA Engineer', 'Middle', 'Тестирование, автоматизация и контроль качества', TRUE),
(4, 2, 'Data Analyst', 'Middle', 'Аналитика данных и построение отчетов', TRUE),
(5, 3, 'Product Manager', 'Middle', 'Управление продуктом и развитием функционала', TRUE);

-- ---------------------------------------------------------
-- Пользователи
-- ---------------------------------------------------------
INSERT INTO users (
    id, role_id, department_id, email, password_hash, auth_provider, external_auth_id,
    phone, last_name, first_name, middle_name, is_active, failed_login_attempts, locked_until, last_login_at
) VALUES
(
    1001, 1, 1, 'hr.manager@elbrus.local',
    '$2b$12$demoHashForHrManager000000000000000000000000000000000',
    'local', NULL,
    '+79990000001', 'Соколова', 'Марина', 'Игоревна', TRUE, 0, NULL, '2026-03-16 08:30:00'
),
(
    2001, 2, 2, 'ivan.petrov@elbrus.local',
    '$2b$12$demoHashForEmployee0000000000000000000000000000000001',
    'local', NULL,
    '+79990000002', 'Петров', 'Иван', 'Алексеевич', TRUE, 0, NULL, '2026-03-15 19:10:00'
),
(
    2002, 2, 2, 'anna.smirnova@elbrus.local',
    '$2b$12$demoHashForEmployee0000000000000000000000000000000002',
    'local', NULL,
    '+79990000003', 'Смирнова', 'Анна', 'Сергеевна', TRUE, 0, NULL, '2026-03-15 18:55:00'
),
(
    2003, 2, 3, 'sergey.ivanov@elbrus.local',
    '$2b$12$demoHashForEmployee0000000000000000000000000000000003',
    'local', NULL,
    '+79990000004', 'Иванов', 'Сергей', 'Павлович', TRUE, 0, NULL, '2026-03-14 21:15:00'
);


-- ---------------------------------------------------------
-- Профили сотрудников
-- ---------------------------------------------------------
INSERT INTO employee_profiles (
    user_id, employee_code, anonymous_profile_code, position_id, manager_user_id,
    hire_date, birth_date, city, employment_status, career_summary, desired_roles,
    english_level, points_balance, completed_achievements_count, avatar_path,
    resume_version, is_candidate_visible
) VALUES
(
    2001, 'E-0001', 'CAND-001', 2, 1001,
    '2022-04-11', '1993-06-18', 'Нижний Новгород', 'active',
    'Senior Python backend разработчик. Опыт в MySQL, FastAPI, интеграциях и AI-проектах.',
    'Тимлид backend / архитектор внутренних платформ',
    'B2', 150, 1, '/uploads/avatars/2001.png', 3, TRUE
),
(
    2002, 'E-0002', 'CAND-002', 3, 1001,
    '2023-01-20', '1996-09-07', 'Москва', 'active',
    'QA engineer. Специализируется на автотестах, регрессе и контроле качества релизов.',
    'Senior QA / QA Lead',
    'B1', 80, 1, '/uploads/avatars/2002.png', 2, TRUE
),
(
    2003, 'E-0003', 'CAND-003', 5, 1001,
    '2021-09-01', '1991-12-03', 'Санкт-Петербург', 'active',
    'Product manager с опытом запуска внутренних цифровых сервисов и аналитики процессов.',
    'Product Lead / Product Owner',
    'B2', 30, 0, '/uploads/avatars/2003.png', 1, TRUE
);

-- ---------------------------------------------------------
-- Профиль HR
-- ---------------------------------------------------------
INSERT INTO hr_profiles (user_id, position_id, hr_scope, notes) VALUES
(1001, 1, 'Подбор и развитие сотрудников', 'Основной HR для пилотного контура Эльбрус');

-- ---------------------------------------------------------
-- Разделы резюме
-- ---------------------------------------------------------
INSERT INTO resume_sections (id, code, name, description) VALUES
(1, 'personal_data', 'Личные данные', 'Общая информация о сотруднике'),
(2, 'education', 'Образование', 'Вузы, специальности, дипломы'),
(3, 'work_experience', 'Опыт работы', 'История работы и проекты'),
(4, 'skills', 'Навыки', 'Профессиональные и личные навыки'),
(5, 'competitions', 'Соревнования', 'Участие в конкурсах и хакатонах'),
(6, 'additional_courses', 'Дополнительные курсы', 'Курсы без обязательного срока действия'),
(7, 'qualification_courses', 'Курсы повышения квалификации', 'Курсы со сроком действия');

-- ---------------------------------------------------------
-- Образование
-- ---------------------------------------------------------
INSERT INTO education_records (
    id, employee_user_id, education_level, institution_name, faculty, specialization,
    start_date, end_date, graduation_year, is_current, description
) VALUES
(
    1, 2001, 'master', 'ННГУ им. Лобачевского', 'Институт информационных технологий',
    'Прикладная информатика', '2011-09-01', '2017-06-30', 2017, FALSE,
    'Магистратура по разработке корпоративных информационных систем'
),
(
    2, 2002, 'bachelor', 'МГТУ им. Баумана', 'Информатика и системы управления',
    'Программная инженерия', '2014-09-01', '2018-06-30', 2018, FALSE,
    'Фокус на тестировании, качественной инженерии и автоматизации'
),
(
    3, 2003, 'specialist', 'СПбГУ', 'Экономический факультет',
    'Менеджмент', '2009-09-01', '2014-06-30', 2014, FALSE,
    'Экономика, управление проектами и организационное развитие'
);

-- ---------------------------------------------------------
-- Дипломы
-- ---------------------------------------------------------
INSERT INTO education_diplomas (
    id, education_id, diploma_series, diploma_number, qualification_title, honors_type,
    issued_at, file_path, original_filename, mime_type, file_size_bytes
) VALUES
(
    1, 1, 'AA', '123456', 'Магистр прикладной информатики', 'red',
    '2017-07-10', '/uploads/diplomas/2001_master.pdf', 'petrov_master.pdf', 'application/pdf', 245670
),
(
    2, 2, 'BB', '654321', 'Бакалавр программной инженерии', 'none',
    '2018-07-05', '/uploads/diplomas/2002_bachelor.pdf', 'smirnova_bachelor.pdf', 'application/pdf', 198220
);

-- ---------------------------------------------------------
-- Опыт работы
-- ---------------------------------------------------------
INSERT INTO work_experience_records (
    id, employee_user_id, company_name, company_industry, position_title,
    start_date, end_date, is_current, responsibilities, achievements, technologies_text
) VALUES
(
    1, 2001, 'ООО ТехПлатформа', 'IT', 'Python Developer',
    '2017-08-01', '2022-04-10', FALSE,
    'Разработка внутренних сервисов, API и интеграций',
    'Сократил время генерации отчетов на 40%',
    'Python, FastAPI, MySQL, Redis, Docker'
),
(
    2, 2001, 'АО ПРОМИС', 'IT', 'Senior Python Backend Developer',
    '2022-04-11', NULL, TRUE,
    'Разработка backend-части внутренних платформ, интеграции с AI-сервисами',
    'Участвовал в создании прототипа платформы развития сотрудников',
    'Python, Gradio, MySQL, LangChain, API integrations'
),
(
    3, 2002, 'ООО Качество+', 'IT', 'QA Engineer',
    '2018-08-01', '2023-01-15', FALSE,
    'Ручное тестирование и автоматизация регресса',
    'Снизила количество дефектов в проде на 25%',
    'Python, Selenium, Postman, SQL'
),
(
    4, 2002, 'АО ПРОМИС', 'IT', 'QA Engineer',
    '2023-01-20', NULL, TRUE,
    'Тестирование внутренних систем и релизный контроль',
    'Выстроила стабильный smoke regression pipeline',
    'Python, Pytest, Selenium, SQL, CI/CD'
),
(
    5, 2003, 'ООО Интегро', 'Digital', 'Product Manager',
    '2019-01-10', '2021-08-15', FALSE,
    'Вёл внутренние цифровые продукты и аналитику',
    'Запустил портал самообслуживания сотрудников',
    'Product analytics, SQL, BPMN'
),
(
    6, 2003, 'АО ПРОМИС', 'Production', 'Product Manager',
    '2021-09-01', NULL, TRUE,
    'Развитие цифровых сервисов для внутренних заказчиков',
    'Запустил несколько сервисов автоматизации HR-процессов',
    'Product discovery, SQL, dashboards, Jira'
);

-- ---------------------------------------------------------
-- Справочник навыков
-- ---------------------------------------------------------
INSERT INTO skills (id, name, category, description, is_active) VALUES
(1, 'Python', 'backend', 'Язык программирования Python', TRUE),
(2, 'FastAPI', 'backend', 'Фреймворк для разработки API', TRUE),
(3, 'MySQL', 'database', 'Реляционная база данных MySQL', TRUE),
(4, 'LangChain', 'ai', 'Интеграция LLM и RAG-конвейеров', TRUE),
(5, 'Selenium', 'qa', 'Автоматизация UI-тестирования', TRUE),
(6, 'Pytest', 'qa', 'Фреймворк тестирования на Python', TRUE),
(7, 'SQL', 'analytics', 'Язык запросов к БД', TRUE),
(8, 'Product Discovery', 'product', 'Исследование потребностей и формирование гипотез', TRUE),
(9, 'Dashboarding', 'analytics', 'Отчетность и визуализация', TRUE);

-- ---------------------------------------------------------
-- Навыки сотрудников
-- ---------------------------------------------------------
INSERT INTO employee_skills (
    id, employee_user_id, skill_id, proficiency_level, years_experience, last_used_year, notes
) VALUES
(1, 2001, 1, 'expert', 8.0, 2026, 'Основной стек разработки'),
(2, 2001, 2, 'senior', 4.0, 2026, 'Использует для внутренних API'),
(3, 2001, 3, 'senior', 6.0, 2026, 'Проектирование схем и оптимизация SQL'),
(4, 2001, 4, 'middle', 1.5, 2026, 'Пилотные AI/RAG-проекты'),
(5, 2002, 1, 'middle', 4.0, 2026, 'Для автотестов и скриптов'),
(6, 2002, 5, 'senior', 5.0, 2026, 'Автоматизация UI-тестов'),
(7, 2002, 6, 'senior', 4.5, 2026, 'Pytest + regression suites'),
(8, 2002, 7, 'middle', 3.0, 2026, 'Проверка данных и подготовка тест-кейсов'),
(9, 2003, 7, 'middle', 5.0, 2026, 'Аналитика требований и витрин'),
(10, 2003, 8, 'senior', 4.0, 2026, 'Проводит исследования и интервью'),
(11, 2003, 9, 'middle', 3.5, 2026, 'Дашборды для внутренних процессов');

-- ---------------------------------------------------------
-- Соревнования
-- ---------------------------------------------------------
INSERT INTO competitions (id, name, organizer, competition_level, description) VALUES
(1, 'Хакатон AI HR 2025', 'Внутренний корпоративный центр инноваций', 'company', 'Хакатон по AI-решениям для HR'),
(2, 'Чемпионат качества 2024', 'Корпоративный учебный центр', 'company', 'Конкурс по качеству процессов и тестированию');

-- ---------------------------------------------------------
-- Призовые места
-- ---------------------------------------------------------
INSERT INTO competition_placements (id, code, name, rank_value) VALUES
(1, 'WINNER', '1 место', 1),
(2, 'SECOND', '2 место', 2),
(3, 'THIRD', '3 место', 3),
(4, 'FINALIST', 'Финалист', 10);

-- ---------------------------------------------------------
-- Результаты сотрудников в соревнованиях
-- ---------------------------------------------------------
INSERT INTO employee_competition_results (
    id, employee_user_id, competition_id, placement_id, event_date, award_title, description
) VALUES
(
    1, 2001, 1, 1, '2025-11-14', 'Победитель хакатона',
    'Проект по интеллектуальному подбору внутренних кандидатов'
),
(
    2, 2002, 2, 2, '2024-10-10', 'Призер чемпионата качества',
    'Кейс по повышению стабильности smoke regression'
);

-- ---------------------------------------------------------
-- Дополнительные курсы
-- ---------------------------------------------------------
INSERT INTO additional_courses_catalog (id, name, provider, hours, description, is_active) VALUES
(1, 'Продвинутая backend-разработка на Python', 'Stepik / Internal', 48, 'Курс по архитектуре backend-сервисов', TRUE),
(2, 'Управление продуктом для инженеров', 'Internal Academy', 24, 'Курс по продуктовой логике для технических сотрудников', TRUE);

INSERT INTO employee_additional_courses (
    id, employee_user_id, course_id, course_name_override, provider_override,
    started_at, completed_at, status, certificate_number, result_text
) VALUES
(
    1, 2001, 1, NULL, NULL,
    '2025-03-01', '2025-04-15', 'completed', 'CERT-ADD-001',
    'Успешно завершил курс, итоговая оценка 95/100'
),
(
    2, 2003, 2, NULL, NULL,
    '2025-06-01', '2025-06-30', 'completed', 'CERT-ADD-002',
    'Курс помог усилить продуктовую экспертизу в цифровых сервисах'
);

-- ---------------------------------------------------------
-- Курсы повышения квалификации
-- ---------------------------------------------------------
INSERT INTO qualification_courses_catalog (
    id, name, provider, hours, validity_months, description, is_mandatory, is_active
) VALUES
(1, 'Информационная безопасность', 'Корпоративный учебный центр', 16, 12, 'Обязательный курс по ИБ', TRUE, TRUE),
(2, 'Охрана труда', 'Корпоративный учебный центр', 8, 12, 'Обязательный курс по охране труда', TRUE, TRUE);

INSERT INTO employee_qualification_courses (
    id, employee_user_id, course_id, course_name_override, provider_override,
    started_at, completed_at, valid_until, status, certificate_number, result_text, last_reminder_sent_at
) VALUES
(
    1, 2001, 1, NULL, NULL,
    '2025-12-10', '2025-12-20', '2026-12-20', 'completed',
    'QUAL-001', 'Курс пройден вовремя', '2025-12-21 10:00:00'
),
(
    2, 2002, 1, NULL, NULL,
    '2025-03-10', '2025-03-20', '2026-03-25', 'completed',
    'QUAL-002', 'Срок действия скоро заканчивается', '2026-03-15 09:00:00'
),
(
    3, 2003, 2, NULL, NULL,
    '2025-02-01', '2025-02-08', '2026-02-28', 'expired',
    'QUAL-003', 'Курс просрочен, нужно обновление', '2026-03-01 08:00:00'
);

-- ---------------------------------------------------------
-- Достижения
-- ---------------------------------------------------------
INSERT INTO achievements (
    id, code, name, description, icon_name, points_reward, criteria_type, criteria_config, is_active
) VALUES
(
    1, 'FIRST_RESUME_UPDATE', 'Первое обновление резюме',
    'Сотрудник впервые отправил корректную заявку на обновление резюме',
    'badge_resume', 50, 'resume_change_request',
    JSON_OBJECT('required_status', 'implemented'), TRUE
),
(
    2, 'QUALIFICATION_ON_TIME', 'Курс вовремя',
    'Сотрудник вовремя обновил обязательный курс повышения квалификации',
    'badge_course', 100, 'qualification_course_completed',
    JSON_OBJECT('mandatory_only', TRUE), TRUE
),
(
    3, 'HACKATHON_MEDALIST', 'Медалист хакатона',
    'Сотрудник занял призовое место в соревновании',
    'badge_hackathon', 150, 'competition_result',
    JSON_OBJECT('max_rank_value', 3), TRUE
);

-- ---------------------------------------------------------
-- Достижения сотрудников
-- ---------------------------------------------------------
INSERT INTO employee_achievements (
    id, employee_user_id, achievement_id, status, progress_value, completed_at, points_awarded
) VALUES
(1, 2001, 3, 'completed', 100.00, '2025-11-14 18:00:00', 150),
(2, 2002, 2, 'completed', 100.00, '2025-03-20 17:00:00', 100),
(3, 2003, 1, 'in_progress', 60.00, NULL, 0);

-- ---------------------------------------------------------
-- Журнал движения очков
-- ---------------------------------------------------------
INSERT INTO points_ledger (
    id, employee_user_id, transaction_type, points_delta, balance_after,
    reference_entity_type, reference_entity_id, comment_text, created_by_user_id, created_at
) VALUES
(
    1, 2001, 'achievement_reward', 150, 150,
    'employee_achievement', 1, 'Начисление за победу в хакатоне', 1001, '2025-11-14 18:05:00'
),
(
    2, 2002, 'achievement_reward', 100, 100,
    'employee_achievement', 2, 'Начисление за своевременное прохождение курса', 1001, '2025-03-20 17:05:00'
),
(
    3, 2002, 'manual_adjustment', -20, 80,
    'manual', NULL, 'Корректировка баланса после тестовой операции', 1001, '2025-03-21 09:00:00'
),
(
    4, 2003, 'manual_adjustment', 30, 30,
    'manual', NULL, 'Стартовые баллы для пилотной группы', 1001, '2025-10-01 10:00:00'
);

-- ---------------------------------------------------------
-- Магазин бонусов
-- ---------------------------------------------------------
INSERT INTO bonus_catalog (
    id, code, name, description, icon_name, cost_points, requires_hr_approval, stock_qty, is_active
) VALUES
(1, 'EXTRA_DAY_OFF', 'Дополнительный выходной', 'Один дополнительный оплачиваемый выходной день', 'gift_day_off', 120, TRUE, NULL, TRUE),
(2, 'CONFERENCE_BUDGET', 'Бюджет на конференцию', 'Компенсация участия в профессиональном мероприятии', 'gift_conf', 200, TRUE, 10, TRUE),
(3, 'MERCH_BOX', 'Корпоративный мерч-бокс', 'Футболка, кружка и стикеры компании', 'gift_merch', 60, TRUE, 100, TRUE);

-- ---------------------------------------------------------
-- Покупки бонусов
-- ---------------------------------------------------------
INSERT INTO bonus_purchases (
    id, employee_user_id, bonus_id, quantity, unit_cost_points, total_cost_points,
    status, requested_at, processed_by_hr_user_id, processed_at, hr_comment
) VALUES
(
    1, 2001, 3, 1, 60, 60,
    'pending', '2026-03-16 09:15:00', NULL, NULL, NULL
);

-- ---------------------------------------------------------
-- Заявки на изменение резюме
-- ---------------------------------------------------------
INSERT INTO resume_change_requests (
    id, employee_user_id, section_id, target_entity_type, target_entity_id,
    change_description, proposed_payload, status, review_comment,
    submitted_at, reviewed_by_hr_user_id, reviewed_at
) VALUES
(
    1, 2002, 7, 'employee_qualification_courses', 2,
    'Прошу добавить обновленный сертификат по информационной безопасности и заменить дату valid_until.',
    JSON_OBJECT(
        'course_id', 1,
        'new_valid_until', '2027-03-25',
        'certificate_number', 'QUAL-002-NEW'
    ),
    'pending', NULL, '2026-03-16 09:05:00', NULL, NULL
),
(
    2, 2001, 4, 'employee_skills', NULL,
    'Прошу добавить новый навык "LangGraph" в профиль.',
    JSON_OBJECT(
        'skill_name', 'LangGraph',
        'category', 'ai',
        'proficiency_level', 'beginner'
    ),
    'approved', 'Согласовано, будет заведено в справочник навыков.', '2026-03-10 15:00:00', 1001, '2026-03-10 18:00:00'
);

-- ---------------------------------------------------------
-- Документы сотрудников
-- ---------------------------------------------------------
INSERT INTO employee_documents (
    id, owner_user_id, document_type, source_entity_type, source_entity_id,
    file_path, original_filename, mime_type, file_size_bytes, file_checksum,
    extracted_text, extraction_status, indexed_at
) VALUES
(
    1, 2002, 'resume_change_attachment', 'resume_change_request', 1,
    '/uploads/change_requests/2002_qual_update.pdf', 'anna_infosec_update.pdf',
    'application/pdf', 120450,
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'Удостоверение о прохождении курса Информационная безопасность. Новый срок действия до 25.03.2027.',
    'processed', '2026-03-16 09:06:00'
),
(
    2, 2001, 'resume_snapshot', 'employee_profile', 2001,
    '/uploads/resume_snapshots/2001_resume.txt', 'petrov_resume_snapshot.txt',
    'text/plain', 8450,
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'Senior Python backend разработчик. Навыки: Python, FastAPI, MySQL, LangChain. Опыт в API, архитектуре, интеграциях и AI-проектах.',
    'processed', '2026-03-15 22:00:00'
),
(
    3, 2002, 'resume_snapshot', 'employee_profile', 2002,
    '/uploads/resume_snapshots/2002_resume.txt', 'smirnova_resume_snapshot.txt',
    'text/plain', 7210,
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'QA engineer. Автоматизация тестирования на Python, Selenium, Pytest. Опыт в SQL и контроле качества релизов.',
    'processed', '2026-03-15 22:01:00'
),
(
    4, 2003, 'resume_snapshot', 'employee_profile', 2003,
    '/uploads/resume_snapshots/2003_resume.txt', 'ivanov_resume_snapshot.txt',
    'text/plain', 6900,
    'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
    'Product manager. Product discovery, SQL, dashboards, запуск внутренних цифровых сервисов.',
    'processed', '2026-03-15 22:02:00'
),
(
    5, 2001, 'diploma_file', 'education', 1,
    '/uploads/diplomas/2001_master.pdf', 'petrov_master.pdf',
    'application/pdf', 245670,
    'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
    'Диплом магистра прикладной информатики.',
    'processed', '2026-03-15 21:30:00'
);

-- ---------------------------------------------------------
-- Уведомления
-- ---------------------------------------------------------
INSERT INTO notifications (
    id, notification_type, title, message, sender_user_id,
    related_entity_type, related_entity_id, priority, created_at, expires_at
) VALUES
(
    1, 'hr_bonus_purchase_request', 'Новая заявка на покупку бонуса',
    'Сотрудник Иван Петров хочет купить бонус "Корпоративный мерч-бокс".',
    2001, 'bonus_purchase', 1, 'normal', '2026-03-16 09:15:30', NULL
),
(
    2, 'employee_course_reminder', 'Пора обновить курс',
    'Срок действия курса "Информационная безопасность" скоро закончится. Пожалуйста, запланируйте обновление.',
    1001, 'employee_qualification_course', 2, 'critical', '2026-03-15 09:00:00', '2026-03-25 23:59:59'
),
(
    3, 'job_invitation', 'Приглашение на внутреннюю роль',
    'Вам отправлено приглашение на позицию Python Backend Developer (RAG / AI).',
    1001, 'job_invitation', 1, 'high', '2026-03-16 10:30:00', '2026-04-01 23:59:59'
);

-- ---------------------------------------------------------
-- Получатели уведомлений
-- ---------------------------------------------------------
INSERT INTO notification_recipients (
    id, notification_id, recipient_user_id, status, read_at, created_at
) VALUES
(1, 1, 1001, 'unread', NULL, '2026-03-16 09:15:30'),
(2, 2, 2002, 'unread', NULL, '2026-03-15 09:00:00'),
(3, 3, 2001, 'unread', NULL, '2026-03-16 10:30:00');

-- ---------------------------------------------------------
-- Вакансии
-- ---------------------------------------------------------
INSERT INTO job_openings (
    id, position_id, department_id, title, requirements_text, responsibilities_text,
    location_text, employment_type, status, created_by_hr_user_id,
    published_at, closed_at, created_at, updated_at
) VALUES
(
    1, 2, 2, 'Python Backend Developer (RAG / AI)',
    'Нужен сотрудник с сильным Python, опытом работы с MySQL, API-интеграциями, пониманием RAG и AI-оркестрации.',
    'Разработка backend-части HR-платформы, интеграция LLM API, работа с поиском кандидатов и внутренними сервисами.',
    'Нижний Новгород / гибрид', 'hybrid', 'open', 1001,
    '2026-03-16 10:00:00', NULL, '2026-03-16 09:50:00', '2026-03-16 10:00:00'
);

-- ---------------------------------------------------------
-- Приглашения на вакансию
-- ---------------------------------------------------------
INSERT INTO job_invitations (
    id, opening_id, employee_user_id, hr_user_id, message_text, status, sent_at, responded_at
) VALUES
(
    1, 1, 2001, 1001,
    'Иван, по вашему профилю вы выглядите сильным кандидатом на внутреннюю роль. Посмотрите описание и дайте обратную связь.',
    'sent', '2026-03-16 10:30:00', NULL
);

-- ---------------------------------------------------------
-- Поисковые профили кандидатов
-- ---------------------------------------------------------
INSERT INTO candidate_search_profiles (
    id, employee_user_id, profile_text, normalized_skills_text,
    total_experience_months, source_checksum, index_status, last_error_text, last_built_at
) VALUES
(
    1, 2001,
    'Senior Python backend developer. Опыт 8+ лет. Навыки: Python, FastAPI, MySQL, LangChain. Работал с AI-проектами, внутренними платформами, API и архитектурой сервисов.',
    'python fastapi mysql langchain api backend architecture rag ai',
    104,
    '1111aaaaaaaa1111aaaaaaaa1111aaaaaaaa1111aaaaaaaa1111aaaaaaaa1111',
    'ready', NULL, '2026-03-15 22:10:00'
),
(
    2, 2002,
    'QA engineer. Опыт автоматизации тестирования на Python, Selenium, Pytest. Хорошо работает с SQL и процессами качества релизов.',
    'python selenium pytest sql qa automation regression testing',
    92,
    '2222bbbbbbbb2222bbbbbbbb2222bbbbbbbb2222bbbbbbbb2222bbbbbbbb2222',
    'ready', NULL, '2026-03-15 22:11:00'
),
(
    3, 2003,
    'Product manager. Product discovery, SQL, dashboards, запуск внутренних цифровых сервисов, аналитика процессов.',
    'product discovery sql dashboards analytics internal products',
    86,
    '3333cccccccc3333cccccccc3333cccccccc3333cccccccc3333cccccccc3333',
    'ready', NULL, '2026-03-15 22:12:00'
);

-- ---------------------------------------------------------
-- Аудит действий
-- ---------------------------------------------------------
INSERT INTO audit_logs (
    id, actor_user_id, action_type, entity_type, entity_id, entity_label,
    ip_address, user_agent, details_json, created_at
) VALUES
(
    1, 1001, 'LOGIN_SUCCESS', 'user', 1001, 'Марина Соколова',
    '10.10.1.15', 'Chrome / Windows',
    JSON_OBJECT('auth_provider', 'local'),
    '2026-03-16 08:30:00'
),
(
    2, 2002, 'RESUME_CHANGE_REQUEST_CREATED', 'resume_change_request', 1, 'Заявка на обновление курса ИБ',
    '10.10.2.33', 'Chrome / macOS',
    JSON_OBJECT('section_code', 'qualification_courses'),
    '2026-03-16 09:05:00'
),
(
    3, 2001, 'BONUS_PURCHASE_CREATED', 'bonus_purchase', 1, 'Покупка бонуса MERCH_BOX',
    '10.10.2.25', 'Chrome / macOS',
    JSON_OBJECT('bonus_code', 'MERCH_BOX', 'total_cost_points', 60),
    '2026-03-16 09:15:00'
),
(
    4, 1001, 'JOB_INVITATION_SENT', 'job_invitation', 1, 'Приглашение Ивану Петрову',
    '10.10.1.15', 'Chrome / Windows',
    JSON_OBJECT('opening_id', 1, 'employee_user_id', 2001),
    '2026-03-16 10:30:00'
);

INSERT INTO resume_sections (code, name, description) VALUES
('personal_data', 'Личные данные', 'Общая информация о сотруднике'),
('education', 'Образование', 'Вузы, специальности, дипломы'),
('diplomas', 'Дипломы', 'Дипломы и подтверждающие документы по образованию'),
('work_experience', 'Опыт работы', 'История работы и проекты'),
('skills', 'Личные навыки', 'Профессиональные и личные навыки'),
('competitions', 'Участие в соревнованиях', 'Участие в конкурсах и хакатонах'),
('competition_awards', 'Призёр/Победитель соревнований', 'Призовые места и награды в соревнованиях'),
('additional_courses', 'Пройденные дополнительные курсы', 'Курсы без обязательного срока действия'),
('qualification_courses', 'Пройденные курсы повышения квалификации', 'Курсы со сроком действия')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description);