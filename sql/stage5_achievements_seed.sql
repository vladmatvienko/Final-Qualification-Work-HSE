USE elbrus;

-- =========================================================
-- Наполнение каталога достижений
-- =========================================================

INSERT INTO achievements (
    code,
    name,
    description,
    points,
    icon,
    category_code,
    verification_type,
    rule_type,
    rule_config_json,
    is_repeatable,
    repeat_period,
    sort_order,
    is_active
) VALUES
-- ---------------------------------------------------------
-- Онбординг / стартовые
-- ---------------------------------------------------------
(
    'PROFILE_ACTIVATED',
    'Профиль активирован',
    'Выдаётся сразу при первом заходе пользователя.',
    300,
    '🚀',
    'onboarding',
    'automatic',
    'login_once',
    JSON_OBJECT(),
    FALSE,
    'once',
    10,
    TRUE
),
(
    'FIRST_FIVE',
    'Первая пятёрка',
    'Выдаётся после получения пользователем 5 достижений.',
    300,
    '✋',
    'onboarding',
    'automatic',
    'achievement_count_threshold',
    JSON_OBJECT('threshold', 5),
    FALSE,
    'once',
    20,
    TRUE
),
(
    'FIFTEEN_REASONS',
    '15 причин остаться',
    'Выдаётся после получения пользователем 15 достижений.',
    500,
    '🎯',
    'onboarding',
    'automatic',
    'achievement_count_threshold',
    JSON_OBJECT('threshold', 15),
    FALSE,
    'once',
    30,
    TRUE
),
(
    'THIRTY_JOYS',
    '30 поводов для счастья',
    'Выдаётся после получения пользователем 30 достижений.',
    800,
    '🌟',
    'onboarding',
    'automatic',
    'achievement_count_threshold',
    JSON_OBJECT('threshold', 30),
    FALSE,
    'once',
    40,
    TRUE
),
(
    'FIFTY_WINS',
    '50 побед 0 поражений',
    'Выдаётся после получения пользователем 50 достижений.',
    1200,
    '🏆',
    'onboarding',
    'automatic',
    'achievement_count_threshold',
    JSON_OBJECT('threshold', 50),
    FALSE,
    'once',
    50,
    TRUE
),

-- ---------------------------------------------------------
-- Образовательные / компетенционные
-- ---------------------------------------------------------
(
    'EXTERNAL_EXPERT',
    'Внешний эксперт',
    'Выдаётся после подтверждения HR менеджером истинности прохождения дополнительных курсов или получения нового образования и диплома.',
    300,
    '🎓',
    'education',
    'hybrid',
    'education_or_additional_course',
    JSON_OBJECT(),
    TRUE,
    'source',
    60,
    TRUE
),
(
    'CHAMPIONSHIP_WINNER',
    'Призёр чемпионата',
    'Выдаётся после подтверждения HR менеджером истинности грамот о призёрстве/победе в соревновании.',
    300,
    '🥇',
    'education',
    'hybrid',
    'competition_prize',
    JSON_OBJECT(),
    TRUE,
    'source',
    70,
    TRUE
),
(
    'COURSE_COMPLETED',
    'Курс завершён',
    'Выдаётся после подтверждения HR менеджером истинности прохождения курсов повышения квалификации.',
    150,
    '📘',
    'education',
    'automatic',
    'qualification_course_completed',
    JSON_OBJECT(),
    TRUE,
    'source',
    80,
    TRUE
),
(
    'KNOWLEDGE_MENTOR',
    'Ментор знаний',
    'Выдаётся после подтверждения HR менеджером истинности приобретения новых навыков или увеличения опыта работы.',
    150,
    '🧠',
    'education',
    'manual_hr',
    'skill_or_experience_growth',
    JSON_OBJECT(),
    TRUE,
    'source',
    90,
    TRUE
),
(
    'COMPETITION_PARTICIPANT',
    'Участник соревнований',
    'Выдаётся после подтверждения HR менеджером истинности участия в соревновании.',
    100,
    '🏅',
    'education',
    'automatic',
    'competition_participation',
    JSON_OBJECT(),
    TRUE,
    'source',
    100,
    TRUE
),

-- ---------------------------------------------------------
-- Поведенческие / регулярные
-- ---------------------------------------------------------
(
    'HOW_DID_YOU_MANAGE_IT',
    'Когда ты всё это успел',
    'Выдаётся раз в квартал, если в этом квартале сотрудник обновлял данные в личном резюме 6 и более раз.',
    900,
    '⚡',
    'engagement',
    'automatic',
    'resume_updates_quarter_threshold',
    JSON_OBJECT('min', 6, 'max', 999999),
    TRUE,
    'quarter',
    110,
    TRUE
),
(
    'ACTIVE_PARTICIPANT',
    'Активный участник',
    'Выдаётся раз в квартал, если в этом квартале сотрудник обновлял данные в личном резюме от 3 до 5 раз.',
    300,
    '🔄',
    'engagement',
    'automatic',
    'resume_updates_quarter_threshold',
    JSON_OBJECT('min', 3, 'max', 5),
    TRUE,
    'quarter',
    120,
    TRUE
),
(
    'SKILLS_UP_TO_DATE',
    'Навыки в актуальном состоянии',
    'Выдаётся раз в квартал, если в этом квартале сотрудник обновлял данные в личном резюме 1 или 2 раза.',
    100,
    '🛠️',
    'engagement',
    'automatic',
    'resume_updates_quarter_threshold',
    JSON_OBJECT('min', 1, 'max', 2),
    TRUE,
    'quarter',
    130,
    TRUE
),
(
    'FEEDBACK_PROVIDER',
    'Обратная связь',
    'Выдаётся за оставление 3 конструктивных оценок коллегам за месяц.',
    50,
    '💬',
    'engagement',
    'todo',
    'peer_feedback_month_threshold',
    JSON_OBJECT('threshold', 3),
    TRUE,
    'month',
    140,
    TRUE
),

-- ---------------------------------------------------------
-- Карьерные / долгосрочные
-- ---------------------------------------------------------
(
    'SERVICE_3_YEARS',
    'Выслуга 3 года',
    'Выдаётся HR, когда сотрудник проработает в компании 3 года.',
    1000,
    '🕰️',
    'career',
    'automatic',
    'work_anniversary_years',
    JSON_OBJECT('years', 3),
    FALSE,
    'once',
    150,
    TRUE
),
(
    'MENTOR_OF_THE_YEAR',
    'Наставник года',
    'Выдаётся HR, при соблюдении условия что в течении года сотрудник проявил себя как хороший наставник.',
    500,
    '👥',
    'career',
    'manual_hr',
    'mentor_of_year',
    JSON_OBJECT(),
    FALSE,
    'year',
    160,
    TRUE
),
(
    'PROCESS_OPTIMIZED',
    'Процесс оптимизирован',
    'Выдаётся HR, при соблюдении условия что сотрудник реализует предложение, подтверждённое метрикой (KPI, экономия, время).',
    500,
    '📈',
    'career',
    'manual_hr',
    'process_optimized',
    JSON_OBJECT(),
    FALSE,
    'once',
    170,
    TRUE
),
(
    'CROSS_FUNCTIONAL_TRANSFER',
    'Кросс-функциональный переход',
    'Выдаётся HR, при соблюдении условия что сотрудника успешно переведут в смежное подразделение после оценки RAG-моделью.',
    300,
    '🔀',
    'career',
    'manual_hr',
    'cross_functional_transfer',
    JSON_OBJECT(),
    FALSE,
    'once',
    180,
    TRUE
),
(
    'PROJECT_RESPONSIBILITY',
    'Проектная ответственность',
    'Выдаётся HR, при соблюдении условия что сотрудника назначат как Lead/Owner на внутренний проект.',
    250,
    '📌',
    'career',
    'manual_hr',
    'project_responsibility',
    JSON_OBJECT(),
    FALSE,
    'once',
    190,
    TRUE
);

-- =========================================================
-- ТЕСТОВЫЕ ДАННЫЕ ДЛЯ СОТРУДНИКА
-- =========================================================

UPDATE employee_profiles
SET hire_date = DATE_SUB(CURDATE(), INTERVAL 4 YEAR)
WHERE user_id = 2001;

INSERT INTO employee_additional_courses (
    employee_user_id,
    course_id,
    course_name_override,
    provider_override,
    started_at,
    completed_at,
    status
)
SELECT
    2001,
    NULL,
    'Python для аналитики',
    'Открытая платформа',
    DATE_SUB(CURDATE(), INTERVAL 60 DAY),
    DATE_SUB(CURDATE(), INTERVAL 30 DAY),
    'completed'
WHERE NOT EXISTS (
    SELECT 1
    FROM employee_additional_courses
    WHERE employee_user_id = 2001
      AND course_name_override = 'Python для аналитики'
);

INSERT INTO employee_qualification_courses (
    employee_user_id,
    course_id,
    course_name_override,
    provider_override,
    started_at,
    completed_at,
    valid_until,
    status
)
SELECT
    2001,
    NULL,
    'Информационная безопасность',
    'Корпоративный учебный центр',
    DATE_SUB(CURDATE(), INTERVAL 120 DAY),
    DATE_SUB(CURDATE(), INTERVAL 90 DAY),
    DATE_ADD(CURDATE(), INTERVAL 270 DAY),
    'completed'
WHERE NOT EXISTS (
    SELECT 1
    FROM employee_qualification_courses
    WHERE employee_user_id = 2001
      AND course_name_override = 'Информационная безопасность'
);

INSERT INTO resume_change_requests (
    employee_user_id,
    section_id,
    target_entity_type,
    target_entity_id,
    change_description,
    proposed_payload,
    status,
    submitted_at,
    reviewed_by_hr_user_id,
    reviewed_at,
    review_comment
)
SELECT
    2001,
    (SELECT id FROM resume_sections ORDER BY id LIMIT 1),
    NULL,
    NULL,
    'Seed: обновление резюме #1',
    JSON_OBJECT('seed', TRUE),
    'approved',
    DATE_SUB(CURDATE(), INTERVAL 15 DAY),
    NULL,
    NULL,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM resume_change_requests
    WHERE employee_user_id = 2001
      AND change_description = 'Seed: обновление резюме #1'
);

INSERT INTO resume_change_requests (
    employee_user_id,
    section_id,
    target_entity_type,
    target_entity_id,
    change_description,
    proposed_payload,
    status,
    submitted_at,
    reviewed_by_hr_user_id,
    reviewed_at,
    review_comment
)
SELECT
    2001,
    (SELECT id FROM resume_sections ORDER BY id LIMIT 1),
    NULL,
    NULL,
    'Seed: обновление резюме #2',
    JSON_OBJECT('seed', TRUE),
    'approved',
    DATE_SUB(CURDATE(), INTERVAL 10 DAY),
    NULL,
    NULL,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM resume_change_requests
    WHERE employee_user_id = 2001
      AND change_description = 'Seed: обновление резюме #2'
);

INSERT INTO resume_change_requests (
    employee_user_id,
    section_id,
    target_entity_type,
    target_entity_id,
    change_description,
    proposed_payload,
    status,
    submitted_at,
    reviewed_by_hr_user_id,
    reviewed_at,
    review_comment
)
SELECT
    2001,
    (SELECT id FROM resume_sections ORDER BY id LIMIT 1),
    NULL,
    NULL,
    'Seed: обновление резюме #3',
    JSON_OBJECT('seed', TRUE),
    'approved',
    DATE_SUB(CURDATE(), INTERVAL 5 DAY),
    NULL,
    NULL,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM resume_change_requests
    WHERE employee_user_id = 2001
      AND change_description = 'Seed: обновление резюме #3'
);