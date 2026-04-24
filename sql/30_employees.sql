USE elbrus;

-- =========================================================
-- 30 сотрудников с разными данными
-- =========================================================

DROP TEMPORARY TABLE IF EXISTS tmp_employee_seed;

CREATE TEMPORARY TABLE tmp_employee_seed (
    user_id BIGINT UNSIGNED PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    department_id BIGINT UNSIGNED NOT NULL,
    position_id BIGINT UNSIGNED NOT NULL,
    manager_user_id BIGINT UNSIGNED NULL,
    hire_date DATE NOT NULL,
    birth_date DATE NOT NULL,
    city VARCHAR(120) NOT NULL,
    career_summary TEXT NOT NULL,
    desired_roles TEXT NOT NULL,
    english_level VARCHAR(50) NOT NULL,
    gender ENUM('male', 'female', 'other', 'unspecified') NOT NULL,
    marital_status VARCHAR(100) NULL,
    citizenship VARCHAR(120) NULL,
    driver_license_categories VARCHAR(100) NULL,
    has_criminal_record BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tmp_employee_seed (
    user_id, username, first_name, last_name, middle_name, email,
    department_id, position_id, manager_user_id,
    hire_date, birth_date, city, career_summary, desired_roles, english_level,
    gender, marital_status, citizenship, driver_license_categories, has_criminal_record
) VALUES
(2101, 'employee01', 'Алексей', 'Орлов', 'Игоревич', 'employee01@elbrus.local', 2, 2, 1001, '2021-02-15', '1992-04-12', 'Нижний Новгород', 'Backend-разработчик с опытом интеграций и внутренних сервисов.', 'Тимлид backend / архитектор', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2102, 'employee02', 'Мария', 'Кузнецова', 'Андреевна', 'employee02@elbrus.local', 2, 3, 1001, '2022-06-10', '1995-08-21', 'Москва', 'QA-инженер, специализация на автотестах и smoke regression.', 'QA Lead / Release Manager', 'B1', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2103, 'employee03', 'Дмитрий', 'Соколов', 'Павлович', 'employee03@elbrus.local', 2, 4, 1001, '2020-11-02', '1991-01-30', 'Казань', 'Аналитик данных, строит отчёты и витрины для внутренних сервисов.', 'Lead Analyst / BI Manager', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2104, 'employee04', 'Елена', 'Волкова', 'Сергеевна', 'employee04@elbrus.local', 3, 5, 1001, '2019-09-16', '1990-12-05', 'Санкт-Петербург', 'Product manager внутренних продуктов и цифровых инициатив.', 'Senior Product Manager', 'C1', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2105, 'employee05', 'Илья', 'Фёдоров', 'Олегович', 'employee05@elbrus.local', 2, 2, 1001, '2023-03-01', '1997-03-17', 'Самара', 'Python backend разработчик с фокусом на API и БД.', 'Backend Lead', 'B1', 'male', 'Не женат', 'Российская Федерация', 'B', FALSE),
(2106, 'employee06', 'Анна', 'Морозова', 'Ильинична', 'employee06@elbrus.local', 2, 3, 1001, '2021-07-12', '1994-07-09', 'Ярославль', 'QA engineer, ручное и автотестирование корпоративных систем.', 'QA Automation Lead', 'B2', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2107, 'employee07', 'Сергей', 'Павлов', 'Денисович', 'employee07@elbrus.local', 2, 4, 1001, '2018-05-21', '1989-11-25', 'Екатеринбург', 'Data analyst, SQL, отчётность, продуктовая аналитика.', 'Head of Analytics', 'B2', 'male', 'Женат', 'Российская Федерация', 'B, C', FALSE),
(2108, 'employee08', 'Ольга', 'Лебедева', 'Викторовна', 'employee08@elbrus.local', 3, 5, 1001, '2020-01-13', '1993-05-14', 'Пермь', 'Product manager по внутренним сервисам развития сотрудников.', 'Group Product Manager', 'B2', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2109, 'employee09', 'Никита', 'Зайцев', 'Романович', 'employee09@elbrus.local', 2, 2, 1001, '2022-02-07', '1996-09-03', 'Тула', 'Backend engineer, внутренние платформы и сервисная архитектура.', 'Senior Backend Developer', 'B1', 'male', 'Не женат', 'Российская Федерация', 'B', FALSE),
(2110, 'employee10', 'Татьяна', 'Новикова', 'Алексеевна', 'employee10@elbrus.local', 2, 3, 1001, '2024-01-15', '1998-02-27', 'Воронеж', 'QA engineer, тест-кейсы, регресс, контроль качества релизов.', 'Middle QA / QA Lead', 'B1', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2111, 'employee11', 'Кирилл', 'Белов', 'Максимович', 'employee11@elbrus.local', 2, 4, 1001, '2021-10-04', '1994-10-18', 'Новосибирск', 'Аналитик данных, SQL и визуализация показателей.', 'Senior Data Analyst', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2112, 'employee12', 'Юлия', 'Крылова', 'Евгеньевна', 'employee12@elbrus.local', 3, 5, 1001, '2019-04-22', '1991-06-01', 'Уфа', 'Product manager, discovery и развитие внутренних цифровых сервисов.', 'Lead Product Manager', 'C1', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2113, 'employee13', 'Роман', 'Жуков', 'Ильич', 'employee13@elbrus.local', 2, 2, 1001, '2020-08-19', '1993-01-11', 'Нижний Новгород', 'Python backend developer, интеграции и внутренние API.', 'Tech Lead', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2114, 'employee14', 'Светлана', 'Виноградова', 'Петровна', 'employee14@elbrus.local', 2, 3, 1001, '2021-03-29', '1992-03-06', 'Москва', 'QA automation engineer, Selenium, Pytest, релизный контроль.', 'QA Lead', 'B2', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2115, 'employee15', 'Артём', 'Герасимов', 'Олегович', 'employee15@elbrus.local', 2, 4, 1001, '2023-05-08', '1997-12-14', 'Казань', 'Data analyst по операционным и продуктовым метрикам.', 'Analytics Lead', 'B1', 'male', 'Не женат', 'Российская Федерация', 'B', FALSE),
(2116, 'employee16', 'Наталья', 'Тихонова', 'Игоревна', 'employee16@elbrus.local', 3, 5, 1001, '2022-09-05', '1995-07-19', 'Самара', 'Product manager по внутренним платформам и автоматизации процессов.', 'Senior Product Owner', 'B2', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2117, 'employee17', 'Владислав', 'Макаров', 'Андреевич', 'employee17@elbrus.local', 2, 2, 1001, '2018-12-03', '1988-09-22', 'Екатеринбург', 'Backend-разработчик, Python, MySQL, интеграции.', 'Архитектор внутренних сервисов', 'C1', 'male', 'Женат', 'Российская Федерация', 'B, C', FALSE),
(2118, 'employee18', 'Ирина', 'Полякова', 'Станиславовна', 'employee18@elbrus.local', 2, 3, 1001, '2020-06-18', '1993-04-28', 'Пермь', 'QA engineer, релизный контроль и smoke/regression.', 'Senior QA Engineer', 'B1', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2119, 'employee19', 'Павел', 'Ершов', 'Николаевич', 'employee19@elbrus.local', 2, 4, 1001, '2021-01-11', '1992-02-09', 'Ярославль', 'Data analyst, SQL, внутренние BI-отчёты.', 'Lead Analyst', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2120, 'employee20', 'Ксения', 'Богданова', 'Романовна', 'employee20@elbrus.local', 3, 5, 1001, '2024-02-12', '1999-01-23', 'Тула', 'Product manager, цифровые продукты для сотрудников.', 'Product Manager / Product Owner', 'B1', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2121, 'employee21', 'Егор', 'Савельев', 'Дмитриевич', 'employee21@elbrus.local', 2, 2, 1001, '2022-11-14', '1996-05-30', 'Воронеж', 'Backend developer, API, базы данных, корпоративные сервисы.', 'Senior Backend Developer', 'B1', 'male', 'Не женат', 'Российская Федерация', 'B', FALSE),
(2122, 'employee22', 'Алёна', 'Комарова', 'Павловна', 'employee22@elbrus.local', 2, 3, 1001, '2021-08-02', '1994-08-13', 'Уфа', 'QA automation engineer, автотесты и стабильность релизов.', 'QA Lead', 'B2', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2123, 'employee23', 'Максим', 'Голубев', 'Сергеевич', 'employee23@elbrus.local', 2, 4, 1001, '2019-06-24', '1991-10-16', 'Новосибирск', 'Аналитик данных, SQL, витрины и отчёты.', 'Senior Data Analyst', 'B2', 'male', 'Женат', 'Российская Федерация', 'B, C', FALSE),
(2124, 'employee24', 'Дарья', 'Ефимова', 'Владимировна', 'employee24@elbrus.local', 3, 5, 1001, '2020-10-19', '1992-11-29', 'Санкт-Петербург', 'Product manager по внутренним цифровым инициативам.', 'Lead Product Manager', 'C1', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2125, 'employee25', 'Степан', 'Тарасов', 'Игоревич', 'employee25@elbrus.local', 2, 2, 1001, '2023-07-03', '1998-06-18', 'Москва', 'Python backend developer, внутренние API и сервисы.', 'Backend Lead', 'B1', 'male', 'Не женат', 'Российская Федерация', 'B', FALSE),
(2126, 'employee26', 'Вероника', 'Дорофеева', 'Олеговна', 'employee26@elbrus.local', 2, 3, 1001, '2022-04-04', '1995-12-04', 'Казань', 'QA engineer, функциональное и автоматизированное тестирование.', 'Senior QA Engineer', 'B1', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE),
(2127, 'employee27', 'Тимофей', 'Андреев', 'Максимович', 'employee27@elbrus.local', 2, 4, 1001, '2020-03-17', '1993-07-07', 'Самара', 'Data analyst, SQL и продуктовая аналитика.', 'Lead Analyst', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2128, 'employee28', 'Людмила', 'Фролова', 'Алексеевна', 'employee28@elbrus.local', 3, 5, 1001, '2018-11-26', '1990-09-20', 'Нижний Новгород', 'Product manager с сильным опытом discovery и приоритизации.', 'Group Product Manager', 'C1', 'female', 'Замужем', 'Российская Федерация', NULL, FALSE),
(2129, 'employee29', 'Глеб', 'Никитин', 'Евгеньевич', 'employee29@elbrus.local', 2, 2, 1001, '2021-09-27', '1994-03-01', 'Пермь', 'Backend engineer, Python, MySQL, сервисная архитектура.', 'Senior Backend / Architect', 'B2', 'male', 'Женат', 'Российская Федерация', 'B', FALSE),
(2130, 'employee30', 'Полина', 'Киселёва', 'Ильинична', 'employee30@elbrus.local', 2, 3, 1001, '2024-03-11', '1999-05-25', 'Екатеринбург', 'QA engineer по внутренним системам и контролю качества.', 'QA Lead / Release Manager', 'B1', 'female', 'Не замужем', 'Российская Федерация', NULL, FALSE);

INSERT INTO users (
    id,
    role_id,
    first_name,
    last_name,
    middle_name,
    email,
    username,
    password_hash,
    is_active,
    is_locked,
    created_at,
    updated_at
)
SELECT
    t.user_id,
    r.id,
    t.first_name,
    t.last_name,
    t.middle_name,
    t.email,
    t.username,
    'Employee123!',
    TRUE,
    FALSE,
    NOW(),
    NOW()
FROM tmp_employee_seed t
INNER JOIN roles r
    ON r.code = 'EMPLOYEE'
ON DUPLICATE KEY UPDATE
    role_id = VALUES(role_id),
    first_name = VALUES(first_name),
    last_name = VALUES(last_name),
    middle_name = VALUES(middle_name),
    email = VALUES(email),
    username = VALUES(username),
    password_hash = VALUES(password_hash),
    is_active = VALUES(is_active),
    is_locked = VALUES(is_locked),
    updated_at = NOW();

INSERT INTO employee_profiles (
    user_id,
    employee_code,
    anonymous_profile_code,
    position_id,
    manager_user_id,
    hire_date,
    birth_date,
    city,
    employment_status,
    career_summary,
    desired_roles,
    english_level,
    points_balance,
    completed_achievements_count,
    avatar_path,
    resume_version,
    is_candidate_visible,
    gender,
    marital_status,
    citizenship,
    driver_license_categories,
    has_criminal_record,
    criminal_record_details
)
SELECT
    t.user_id,
    CONCAT('E-', LPAD(t.user_id, 4, '0')),
    CONCAT('CAND-', t.user_id),
    t.position_id,
    t.manager_user_id,
    t.hire_date,
    t.birth_date,
    t.city,
    'active',
    t.career_summary,
    t.desired_roles,
    t.english_level,
    100 + ((t.user_id - 2100) * 15),
    ((t.user_id - 2100) MOD 8) + 1,
    CONCAT('/uploads/avatars/', t.user_id, '.png'),
    ((t.user_id - 2100) MOD 4) + 1,
    TRUE,
    t.gender,
    t.marital_status,
    t.citizenship,
    t.driver_license_categories,
    t.has_criminal_record,
    NULL
FROM tmp_employee_seed t
ON DUPLICATE KEY UPDATE
    employee_code = VALUES(employee_code),
    anonymous_profile_code = VALUES(anonymous_profile_code),
    position_id = VALUES(position_id),
    manager_user_id = VALUES(manager_user_id),
    hire_date = VALUES(hire_date),
    birth_date = VALUES(birth_date),
    city = VALUES(city),
    employment_status = VALUES(employment_status),
    career_summary = VALUES(career_summary),
    desired_roles = VALUES(desired_roles),
    english_level = VALUES(english_level),
    points_balance = VALUES(points_balance),
    completed_achievements_count = VALUES(completed_achievements_count),
    avatar_path = VALUES(avatar_path),
    resume_version = VALUES(resume_version),
    is_candidate_visible = VALUES(is_candidate_visible),
    gender = VALUES(gender),
    marital_status = VALUES(marital_status),
    citizenship = VALUES(citizenship),
    driver_license_categories = VALUES(driver_license_categories),
    has_criminal_record = VALUES(has_criminal_record),
    criminal_record_details = VALUES(criminal_record_details),
    updated_at = NOW();

INSERT INTO education_records (
    employee_user_id,
    education_level,
    institution_name,
    faculty,
    specialization,
    start_date,
    end_date,
    graduation_year,
    is_current,
    description
)
SELECT
    t.user_id,
    CASE
        WHEN t.position_id IN (2, 4) THEN 'master'
        WHEN t.position_id = 3 THEN 'bachelor'
        ELSE 'specialist'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'ННГУ им. Лобачевского'
        WHEN t.position_id = 3 THEN 'МГТУ им. Баумана'
        WHEN t.position_id = 4 THEN 'НИУ ВШЭ'
        ELSE 'СПбГУ'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Институт информационных технологий'
        WHEN t.position_id = 3 THEN 'Информатика и системы управления'
        WHEN t.position_id = 4 THEN 'Факультет компьютерных наук'
        ELSE 'Экономический факультет'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Программная инженерия'
        WHEN t.position_id = 3 THEN 'Информационные системы и технологии'
        WHEN t.position_id = 4 THEN 'Прикладная аналитика данных'
        ELSE 'Менеджмент'
    END,
    DATE_SUB(t.hire_date, INTERVAL 7 YEAR),
    DATE_SUB(t.hire_date, INTERVAL 3 YEAR),
    YEAR(DATE_SUB(t.hire_date, INTERVAL 3 YEAR)),
    FALSE,
    CONCAT('Seed education для ', t.username)
FROM tmp_employee_seed t
LEFT JOIN education_records er
    ON er.employee_user_id = t.user_id
WHERE er.id IS NULL;

INSERT INTO education_diplomas (
    education_id,
    diploma_series,
    diploma_number,
    qualification_title,
    honors_type,
    issued_at,
    file_path,
    original_filename,
    mime_type,
    file_size_bytes
)
SELECT
    er.id,
    CONCAT('DS', RIGHT(t.user_id, 2)),
    CONCAT('DN', t.user_id, '01'),
    CASE
        WHEN t.position_id = 2 THEN 'Магистр программной инженерии'
        WHEN t.position_id = 3 THEN 'Бакалавр информационных технологий'
        WHEN t.position_id = 4 THEN 'Магистр аналитики данных'
        ELSE 'Специалист по менеджменту'
    END,
    CASE
        WHEN MOD(t.user_id, 3) = 0 THEN 'red'
        WHEN MOD(t.user_id, 5) = 0 THEN 'gold'
        ELSE 'none'
    END,
    DATE_SUB(t.hire_date, INTERVAL 3 YEAR),
    CONCAT('/uploads/diplomas/', t.user_id, '.pdf'),
    CONCAT('diploma_', t.user_id, '.pdf'),
    'application/pdf',
    245000
FROM tmp_employee_seed t
INNER JOIN education_records er
    ON er.employee_user_id = t.user_id
LEFT JOIN education_diplomas ed
    ON ed.education_id = er.id
WHERE ed.id IS NULL;

INSERT INTO work_experience_records (
    employee_user_id,
    company_name,
    company_industry,
    position_title,
    start_date,
    end_date,
    is_current,
    responsibilities,
    achievements,
    technologies_text
)
SELECT
    t.user_id,
    CASE
        WHEN t.position_id = 2 THEN 'ООО Бэкенд Плюс'
        WHEN t.position_id = 3 THEN 'ООО Контроль Качества'
        WHEN t.position_id = 4 THEN 'ООО Дата Лаб'
        ELSE 'ООО Продуктовые Решения'
    END,
    CASE
        WHEN t.position_id IN (2, 3, 4) THEN 'IT'
        ELSE 'Digital'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Python Developer'
        WHEN t.position_id = 3 THEN 'QA Engineer'
        WHEN t.position_id = 4 THEN 'Data Analyst'
        ELSE 'Product Manager'
    END,
    DATE_SUB(t.hire_date, INTERVAL 4 YEAR),
    DATE_SUB(t.hire_date, INTERVAL 1 DAY),
    FALSE,
    CASE
        WHEN t.position_id = 2 THEN 'Разработка backend-сервисов и REST API'
        WHEN t.position_id = 3 THEN 'Ручное тестирование и автоматизация регресса'
        WHEN t.position_id = 4 THEN 'Подготовка SQL-отчётов и аналитики'
        ELSE 'Discovery, roadmap и управление цифровым продуктом'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Ускорил внутренние интеграции'
        WHEN t.position_id = 3 THEN 'Снизил количество дефектов в релизах'
        WHEN t.position_id = 4 THEN 'Собрал витрины и отчётность'
        ELSE 'Запустил внутренние цифровые инициативы'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Python, FastAPI, MySQL'
        WHEN t.position_id = 3 THEN 'Python, Selenium, Pytest, SQL'
        WHEN t.position_id = 4 THEN 'SQL, Python, Dashboarding'
        ELSE 'Product Discovery, SQL, Dashboarding'
    END
FROM tmp_employee_seed t
LEFT JOIN work_experience_records w
    ON w.employee_user_id = t.user_id
   AND w.is_current = FALSE
WHERE w.id IS NULL;

INSERT INTO work_experience_records (
    employee_user_id,
    company_name,
    company_industry,
    position_title,
    start_date,
    end_date,
    is_current,
    responsibilities,
    achievements,
    technologies_text
)
SELECT
    t.user_id,
    'АО ПРОМИС',
    CASE
        WHEN t.department_id = 2 THEN 'IT'
        ELSE 'Production'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Python Backend Developer'
        WHEN t.position_id = 3 THEN 'QA Engineer'
        WHEN t.position_id = 4 THEN 'Data Analyst'
        ELSE 'Product Manager'
    END,
    t.hire_date,
    NULL,
    TRUE,
    CASE
        WHEN t.position_id = 2 THEN 'Разработка backend-части внутренних платформ, интеграции с AI-сервисами'
        WHEN t.position_id = 3 THEN 'Тестирование внутренних систем и релизный контроль'
        WHEN t.position_id = 4 THEN 'Аналитика данных и построение внутренней отчётности'
        ELSE 'Развитие цифровых сервисов для внутренних заказчиков'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Участвовал в развитии платформы Эльбрус'
        WHEN t.position_id = 3 THEN 'Выстроил стабильный smoke regression pipeline'
        WHEN t.position_id = 4 THEN 'Собрал аналитические дашборды для HR-процессов'
        ELSE 'Запустил несколько сервисов автоматизации HR-процессов'
    END,
    CASE
        WHEN t.position_id = 2 THEN 'Python, Gradio, MySQL, LangChain, API integrations'
        WHEN t.position_id = 3 THEN 'Python, Pytest, Selenium, SQL, CI/CD'
        WHEN t.position_id = 4 THEN 'Python, SQL, Dashboarding'
        ELSE 'Product Discovery, SQL, Dashboarding'
    END
FROM tmp_employee_seed t
LEFT JOIN work_experience_records w
    ON w.employee_user_id = t.user_id
   AND w.is_current = TRUE
WHERE w.id IS NULL;

INSERT INTO employee_skills (
    employee_user_id,
    skill_id,
    proficiency_level,
    years_experience
)
SELECT
    t.user_id,
    s.id,
    CASE
        WHEN t.position_id = 2 AND s.name IN ('Python', 'FastAPI', 'MySQL', 'LangChain') THEN 'senior'
        WHEN t.position_id = 3 AND s.name IN ('Python', 'Pytest', 'Selenium', 'SQL') THEN 'middle'
        WHEN t.position_id = 4 AND s.name IN ('Python', 'SQL', 'Dashboarding') THEN 'middle'
        WHEN t.position_id = 5 AND s.name IN ('Product Discovery', 'SQL', 'Dashboarding') THEN 'middle'
        ELSE 'junior'
    END,
    CASE
        WHEN t.position_id = 2 THEN 5.0
        WHEN t.position_id = 3 THEN 4.0
        WHEN t.position_id = 4 THEN 4.0
        ELSE 3.0
    END
FROM tmp_employee_seed t
INNER JOIN skills s
    ON (
        (t.position_id = 2 AND s.name IN ('Python', 'FastAPI', 'MySQL', 'LangChain'))
        OR
        (t.position_id = 3 AND s.name IN ('Python', 'Pytest', 'Selenium', 'SQL'))
        OR
        (t.position_id = 4 AND s.name IN ('Python', 'SQL', 'Dashboarding'))
        OR
        (t.position_id = 5 AND s.name IN ('Product Discovery', 'SQL', 'Dashboarding'))
    )
LEFT JOIN employee_skills es
    ON es.employee_user_id = t.user_id
   AND es.skill_id = s.id
WHERE es.employee_user_id IS NULL;

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
    t.user_id,
    NULL,
    CASE
        WHEN t.position_id = 2 THEN 'Продвинутый Python для backend-разработки'
        WHEN t.position_id = 3 THEN 'Автоматизация тестирования на Python'
        WHEN t.position_id = 4 THEN 'SQL и аналитика данных'
        ELSE 'Product Discovery и управление внутренними продуктами'
    END,
    CASE
        WHEN MOD(t.user_id, 2) = 0 THEN 'Skillbox'
        ELSE 'Яндекс Практикум'
    END,
    DATE_SUB(CURDATE(), INTERVAL 180 DAY),
    DATE_SUB(CURDATE(), INTERVAL 120 DAY),
    'completed'
FROM tmp_employee_seed t
LEFT JOIN employee_additional_courses eac
    ON eac.employee_user_id = t.user_id
WHERE eac.id IS NULL;

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
    t.user_id,
    NULL,
    CASE
        WHEN t.position_id IN (2, 3) THEN 'Информационная безопасность'
        WHEN t.position_id = 4 THEN 'Обработка персональных данных'
        ELSE 'Управление внутренними цифровыми инициативами'
    END,
    'Корпоративный учебный центр',
    DATE_SUB(CURDATE(), INTERVAL 150 DAY),
    DATE_SUB(CURDATE(), INTERVAL 90 DAY),
    DATE_ADD(CURDATE(), INTERVAL (90 + ((t.user_id - 2100) * 7)) DAY),
    'completed'
FROM tmp_employee_seed t
LEFT JOIN employee_qualification_courses eqc
    ON eqc.employee_user_id = t.user_id
WHERE eqc.id IS NULL;

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
    t.user_id,
    rs.id,
    NULL,
    NULL,
    CONCAT('Seed request от ', t.username, ': обновление резюме'),
    JSON_OBJECT('seed', TRUE, 'employee', t.username),
    CASE
        WHEN MOD(t.user_id, 3) = 0 THEN 'approved'
        WHEN MOD(t.user_id, 3) = 1 THEN 'pending'
        ELSE 'rejected'
    END,
    DATE_SUB(CURDATE(), INTERVAL ((t.user_id - 2100) * 2) DAY),
    NULL,
    NULL,
    NULL
FROM tmp_employee_seed t
INNER JOIN resume_sections rs
    ON rs.code = CASE
        WHEN t.position_id = 2 THEN 'skills'
        WHEN t.position_id = 3 THEN 'work_experience'
        WHEN t.position_id = 4 THEN 'education'
        ELSE 'additional_courses'
    END
LEFT JOIN resume_change_requests rcr
    ON rcr.employee_user_id = t.user_id
   AND rcr.change_description = CONCAT('Seed request от ', t.username, ': обновление резюме')
WHERE rcr.id IS NULL;

SELECT
    u.id,
    u.username,
    CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS full_name,
    ep.employee_code,
    ep.anonymous_profile_code,
    ep.position_id,
    ep.city
FROM users u
INNER JOIN employee_profiles ep
    ON ep.user_id = u.id
WHERE u.id BETWEEN 2101 AND 2130
ORDER BY u.id;

DROP TEMPORARY TABLE IF EXISTS tmp_employee_seed;
