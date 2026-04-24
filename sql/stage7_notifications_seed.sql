USE elbrus;

-- =========================================================
-- Тестовые данные для уведомлений
-- =========================================================

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
    'Актуализация требований по охране труда',
    'Корпоративный учебный центр',
    DATE_SUB(CURDATE(), INTERVAL 330 DAY),
    DATE_SUB(CURDATE(), INTERVAL 300 DAY),
    DATE_ADD(CURDATE(), INTERVAL 10 DAY),
    'completed'
WHERE NOT EXISTS (
    SELECT 1
    FROM employee_qualification_courses
    WHERE employee_user_id = 2001
      AND course_name_override = 'Актуализация требований по охране труда'
);