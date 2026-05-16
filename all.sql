CREATE DATABASE IF NOT EXISTS elbrus
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE elbrus;

-- =========================================================
-- 1. Роли пользователей
-- =========================================================
CREATE TABLE roles (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE COMMENT 'Системный код роли: HR_MANAGER, EMPLOYEE',
    name VARCHAR(100) NOT NULL COMMENT 'Человеко-понятное название роли',
    description VARCHAR(255) NULL COMMENT 'Описание назначения роли',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Справочник ролей пользователей системы';

-- =========================================================
-- 2. Подразделения компании
-- =========================================================
CREATE TABLE departments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL COMMENT 'Название подразделения',
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Короткий код подразделения',
    parent_department_id BIGINT UNSIGNED NULL COMMENT 'Родительское подразделение для иерархии',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Активно ли подразделение',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_departments_parent
        FOREIGN KEY (parent_department_id) REFERENCES departments(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Оргструктура компании. Нужна для профилей, HR и вакансий';

CREATE INDEX idx_departments_active ON departments(is_active);

-- =========================================================
-- 3. Справочник должностей
-- =========================================================
CREATE TABLE positions_catalog (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    department_id BIGINT UNSIGNED NULL COMMENT 'Подразделение, к которому относится должность',
    title VARCHAR(150) NOT NULL COMMENT 'Название должности',
    grade VARCHAR(50) NULL COMMENT 'Грейд / уровень: Junior, Middle, Senior и т.д.',
    description TEXT NULL COMMENT 'Описание должности',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Можно ли использовать должность в новых профилях и вакансиях',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_positions_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Справочник типовых должностей';

CREATE INDEX idx_positions_department ON positions_catalog(department_id);
CREATE INDEX idx_positions_active ON positions_catalog(is_active);
CREATE UNIQUE INDEX uq_positions_title_grade_department ON positions_catalog(department_id, title, grade);

-- =========================================================
-- 4. Пользователи
-- =========================================================
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role_id TINYINT UNSIGNED NOT NULL COMMENT 'Роль пользователя',
    department_id BIGINT UNSIGNED NULL COMMENT 'Текущее подразделение пользователя',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT 'Логин пользователя',
    password_hash VARCHAR(255) NULL COMMENT 'Хеш пароля. Может быть NULL при SSO/LDAP',
    auth_provider ENUM('local', 'ldap', 'sso') NOT NULL DEFAULT 'local' COMMENT 'Способ авторизации',
    external_auth_id VARCHAR(255) NULL COMMENT 'Внешний идентификатор в SSO/LDAP',
    phone VARCHAR(30) NULL COMMENT 'Телефон пользователя',
    last_name VARCHAR(100) NOT NULL COMMENT 'Фамилия',
    first_name VARCHAR(100) NOT NULL COMMENT 'Имя',
    middle_name VARCHAR(100) NULL COMMENT 'Отчество',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Активна ли учетная запись',
    failed_login_attempts SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Количество неудачных попыток входа',
    locked_until DATETIME NULL COMMENT 'Время блокировки пользователя после серии ошибок',
    last_login_at DATETIME NULL COMMENT 'Последний успешный вход',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id) REFERENCES roles(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_users_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Учетные записи пользователей: и HR, и сотрудники';

CREATE INDEX idx_users_role_active ON users(role_id, is_active);
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_users_external_auth ON users(auth_provider, external_auth_id);

-- =========================================================
-- 5. Сессии пользователей
-- =========================================================
CREATE TABLE user_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL COMMENT 'Пользователь, которому принадлежит сессия',
    refresh_token_hash CHAR(64) NOT NULL UNIQUE COMMENT 'Хеш refresh token, а не сам токен',
    ip_address VARCHAR(45) NULL COMMENT 'IP-адрес при создании сессии',
    user_agent VARCHAR(255) NULL COMMENT 'Браузер/клиент пользователя',
    expires_at DATETIME NOT NULL COMMENT 'Когда сессия истекает',
    revoked_at DATETIME NULL COMMENT 'Когда сессия была принудительно отозвана',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Активные сессии пользователя. Нужны для авторизации и последующего logout';

CREATE INDEX idx_user_sessions_user_expires ON user_sessions(user_id, expires_at);
CREATE INDEX idx_user_sessions_revoked ON user_sessions(revoked_at);

-- =========================================================
-- 6. Профиль сотрудника
-- =========================================================
CREATE TABLE employee_profiles (
    user_id BIGINT UNSIGNED PRIMARY KEY COMMENT 'PK = FK на users.id. Один пользователь -> один профиль сотрудника',
    employee_code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Табельный номер / внутренний код сотрудника',
    anonymous_profile_code VARCHAR(32) NOT NULL UNIQUE COMMENT 'Анонимный код кандидата для HR-рейтинга',
    position_id BIGINT UNSIGNED NULL COMMENT 'Текущая должность сотрудника',
    manager_user_id BIGINT UNSIGNED NULL COMMENT 'Руководитель сотрудника',
    hire_date DATE NULL COMMENT 'Дата приема на работу',
    birth_date DATE NULL COMMENT 'Дата рождения. Можно не использовать в UI, но полезно для HR-учета',
    city VARCHAR(120) NULL COMMENT 'Город сотрудника',
    employment_status ENUM('active', 'on_leave', 'dismissed') NOT NULL DEFAULT 'active' COMMENT 'Статус занятости',
    career_summary TEXT NULL COMMENT 'Краткая выжимка резюме / self-summary',
    desired_roles TEXT NULL COMMENT 'Желаемые роли или направления развития',
    english_level VARCHAR(50) NULL COMMENT 'Уровень английского или иного языка',
    points_balance INT NOT NULL DEFAULT 0 COMMENT 'Текущий остаток очков сотрудника',
    completed_achievements_count INT NOT NULL DEFAULT 0 COMMENT 'Количество выполненных достижений',
    avatar_path VARCHAR(500) NULL COMMENT 'Путь к аватару',
    resume_version INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Версия резюме, удобна для контроля изменений',
    is_candidate_visible BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Можно ли показывать сотрудника в подборе',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_profiles_position
        FOREIGN KEY (position_id) REFERENCES positions_catalog(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_profiles_manager
        FOREIGN KEY (manager_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT chk_employee_points_non_negative CHECK (points_balance >= 0),
    CONSTRAINT chk_employee_achievements_non_negative CHECK (completed_achievements_count >= 0)
) ENGINE=InnoDB
COMMENT='Расширенный профиль сотрудника. Здесь же быстрые счетчики очков и достижений';

CREATE INDEX idx_employee_profiles_position ON employee_profiles(position_id);
CREATE INDEX idx_employee_profiles_manager ON employee_profiles(manager_user_id);
CREATE INDEX idx_employee_profiles_status_visible ON employee_profiles(employment_status, is_candidate_visible);
CREATE INDEX idx_employee_profiles_points ON employee_profiles(points_balance);

-- =========================================================
-- 7. Профиль HR
-- =========================================================
CREATE TABLE hr_profiles (
    user_id BIGINT UNSIGNED PRIMARY KEY COMMENT 'PK = FK на users.id. Один HR-пользователь -> один HR-профиль',
    position_id BIGINT UNSIGNED NULL COMMENT 'Должность HR',
    hr_scope VARCHAR(120) NULL COMMENT 'Зона ответственности: подбор, обучение, внутренние проекты и т.д.',
    notes TEXT NULL COMMENT 'Технические заметки',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_hr_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_hr_profiles_position
        FOREIGN KEY (position_id) REFERENCES positions_catalog(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Расширенный профиль HR-менеджера';

-- =========================================================
-- 8. Разделы резюме
-- =========================================================
CREATE TABLE resume_sections (
    id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Системный код раздела',
    name VARCHAR(150) NOT NULL COMMENT 'Название раздела для UI',
    description VARCHAR(255) NULL COMMENT 'Подсказка для UI и маршрутизации'
) ENGINE=InnoDB
COMMENT='Справочник разделов резюме';

-- =========================================================
-- 9. Образование сотрудника
-- =========================================================
CREATE TABLE education_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник, к которому относится запись',
    education_level ENUM('secondary_special', 'bachelor', 'specialist', 'master', 'postgraduate', 'other')
        NOT NULL COMMENT 'Уровень образования',
    institution_name VARCHAR(255) NOT NULL COMMENT 'Учебное заведение',
    faculty VARCHAR(255) NULL COMMENT 'Факультет',
    specialization VARCHAR(255) NULL COMMENT 'Специальность',
    start_date DATE NULL COMMENT 'Дата начала обучения',
    end_date DATE NULL COMMENT 'Дата окончания обучения',
    graduation_year SMALLINT UNSIGNED NULL COMMENT 'Год выпуска, если точная дата не важна',
    is_current BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Продолжается ли обучение сейчас',
    description TEXT NULL COMMENT 'Свободное описание, например темы проектов',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_education_records_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Записи об образовании сотрудника';

CREATE INDEX idx_education_employee ON education_records(employee_user_id);
CREATE INDEX idx_education_employee_year ON education_records(employee_user_id, graduation_year);

-- =========================================================
-- 10. Дипломы и файлы по образованию
-- =========================================================
CREATE TABLE education_diplomas (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    education_id BIGINT UNSIGNED NOT NULL COMMENT 'Запись об образовании, к которой относится диплом',
    diploma_series VARCHAR(50) NULL COMMENT 'Серия диплома',
    diploma_number VARCHAR(100) NULL COMMENT 'Номер диплома',
    qualification_title VARCHAR(255) NULL COMMENT 'Квалификация по диплому',
    honors_type ENUM('none', 'red', 'gold', 'other') NOT NULL DEFAULT 'none' COMMENT 'Тип отличия',
    issued_at DATE NULL COMMENT 'Дата выдачи диплома',
    file_path VARCHAR(500) NULL COMMENT 'Путь к файлу диплома',
    original_filename VARCHAR(255) NULL COMMENT 'Оригинальное имя файла, загруженного пользователем',
    mime_type VARCHAR(100) NULL COMMENT 'Тип файла',
    file_size_bytes BIGINT UNSIGNED NULL COMMENT 'Размер файла в байтах',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_education_diplomas_education
        FOREIGN KEY (education_id) REFERENCES education_records(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Дипломы и их файлы. Один education_record может иметь несколько связанных документов';

CREATE INDEX idx_education_diplomas_education ON education_diplomas(education_id);

-- =========================================================
-- 11. Опыт работы
-- =========================================================
CREATE TABLE work_experience_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник, чей опыт работы хранится',
    company_name VARCHAR(255) NOT NULL COMMENT 'Название компании',
    company_industry VARCHAR(120) NULL COMMENT 'Отрасль компании',
    position_title VARCHAR(255) NOT NULL COMMENT 'Должность',
    start_date DATE NOT NULL COMMENT 'Дата начала работы',
    end_date DATE NULL COMMENT 'Дата окончания. NULL, если работает по сей день',
    is_current BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Текущее место работы',
    responsibilities TEXT NULL COMMENT 'Зона ответственности',
    achievements TEXT NULL COMMENT 'Достижения на этом месте работы',
    technologies_text TEXT NULL COMMENT 'Какие технологии и инструменты использовались',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_work_experience_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Опыт работы сотрудника';

CREATE INDEX idx_work_experience_employee_dates ON work_experience_records(employee_user_id, start_date, end_date);

-- =========================================================
-- 12. Справочник навыков
-- =========================================================
CREATE TABLE skills (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE COMMENT 'Название навыка',
    category VARCHAR(100) NULL COMMENT 'Категория навыка: backend, analytics, soft skill и т.д.',
    description VARCHAR(255) NULL COMMENT 'Короткое пояснение',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Можно ли использовать навык в новых анкетах',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Справочник навыков';

CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_active ON skills(is_active);

-- =========================================================
-- 13. Навыки конкретного сотрудника
-- =========================================================
CREATE TABLE employee_skills (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник',
    skill_id BIGINT UNSIGNED NOT NULL COMMENT 'Навык из справочника',
    proficiency_level ENUM('beginner', 'junior', 'middle', 'senior', 'expert')
        NOT NULL DEFAULT 'beginner' COMMENT 'Уровень владения навыком',
    years_experience DECIMAL(4,1) NULL COMMENT 'Стаж использования навыка в годах',
    last_used_year SMALLINT UNSIGNED NULL COMMENT 'Последний год практического использования навыка',
    notes TEXT NULL COMMENT 'Пояснение сотрудника или HR по навыку',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_skills_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_skills_skill
        FOREIGN KEY (skill_id) REFERENCES skills(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Навыки сотрудника. Связующая таблица между сотрудником и справочником навыков';

CREATE UNIQUE INDEX uq_employee_skill ON employee_skills(employee_user_id, skill_id);
CREATE INDEX idx_employee_skills_skill_level ON employee_skills(skill_id, proficiency_level);
CREATE INDEX idx_employee_skills_employee ON employee_skills(employee_user_id);

-- =========================================================
-- 14. Справочник соревнований
-- =========================================================
CREATE TABLE competitions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT 'Название соревнования или конкурса',
    organizer VARCHAR(255) NULL COMMENT 'Организатор',
    competition_level ENUM('company', 'city', 'regional', 'national', 'international', 'other')
        NOT NULL DEFAULT 'company' COMMENT 'Масштаб соревнования',
    description TEXT NULL COMMENT 'Описание соревнования',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Справочник соревнований и конкурсов';

CREATE INDEX idx_competitions_level ON competitions(competition_level);

-- =========================================================
-- 15. Справочник призовых мест
-- =========================================================
CREATE TABLE competition_placements (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE COMMENT 'Системный код: WINNER, SECOND, THIRD, FINALIST',
    name VARCHAR(100) NOT NULL COMMENT 'Название места для отображения',
    rank_value SMALLINT UNSIGNED NOT NULL COMMENT 'Чем меньше значение, тем выше место'
) ENGINE=InnoDB
COMMENT='Справочник призовых мест и результатов соревнований';

CREATE INDEX idx_competition_placements_rank ON competition_placements(rank_value);

-- =========================================================
-- 16. Результаты сотрудника в соревнованиях
-- =========================================================
CREATE TABLE employee_competition_results (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник',
    competition_id BIGINT UNSIGNED NOT NULL COMMENT 'Соревнование',
    placement_id TINYINT UNSIGNED NULL COMMENT 'Призовое место / результат',
    event_date DATE NULL COMMENT 'Дата проведения события',
    award_title VARCHAR(255) NULL COMMENT 'Название награды / номинации',
    description TEXT NULL COMMENT 'Пояснение по результату',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_competition_results_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_competition_results_competition
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_competition_results_placement
        FOREIGN KEY (placement_id) REFERENCES competition_placements(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Результаты сотрудников в соревнованиях';

CREATE INDEX idx_employee_competition_employee_date ON employee_competition_results(employee_user_id, event_date);
CREATE INDEX idx_employee_competition_competition ON employee_competition_results(competition_id);

-- =========================================================
-- 17. Справочник дополнительных курсов
-- =========================================================
CREATE TABLE additional_courses_catalog (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT 'Название курса',
    provider VARCHAR(255) NULL COMMENT 'Провайдер / площадка обучения',
    hours INT UNSIGNED NULL COMMENT 'Продолжительность в часах',
    description TEXT NULL COMMENT 'Описание курса',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Можно ли выбирать курс в системе',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Справочник дополнительных курсов';

CREATE INDEX idx_additional_courses_active ON additional_courses_catalog(is_active);

-- =========================================================
-- 18. Дополнительные курсы сотрудника
-- =========================================================
CREATE TABLE employee_additional_courses (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник',
    course_id BIGINT UNSIGNED NULL COMMENT 'Курс из справочника, если выбран из каталога',
    course_name_override VARCHAR(255) NULL COMMENT 'Название курса вручную, если курса нет в каталоге',
    provider_override VARCHAR(255) NULL COMMENT 'Провайдер вручную',
    started_at DATE NULL COMMENT 'Дата начала',
    completed_at DATE NULL COMMENT 'Дата окончания',
    status ENUM('planned', 'in_progress', 'completed', 'cancelled')
        NOT NULL DEFAULT 'completed' COMMENT 'Статус прохождения курса',
    certificate_number VARCHAR(100) NULL COMMENT 'Номер сертификата',
    result_text TEXT NULL COMMENT 'Результат, комментарий, ссылка на сертификат',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_additional_courses_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_additional_courses_catalog
        FOREIGN KEY (course_id) REFERENCES additional_courses_catalog(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Дополнительные курсы сотрудника';

CREATE INDEX idx_employee_additional_courses_employee_status ON employee_additional_courses(employee_user_id, status);
CREATE INDEX idx_employee_additional_courses_completed ON employee_additional_courses(completed_at);

-- =========================================================
-- 19. Справочник курсов повышения квалификации
-- =========================================================
CREATE TABLE qualification_courses_catalog (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT 'Название курса повышения квалификации',
    provider VARCHAR(255) NULL COMMENT 'Провайдер курса',
    hours INT UNSIGNED NULL COMMENT 'Продолжительность в часах',
    validity_months INT UNSIGNED NOT NULL DEFAULT 12 COMMENT 'Срок действия результата в месяцах',
    description TEXT NULL COMMENT 'Описание курса',
    is_mandatory BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Обязателен ли курс',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Можно ли использовать курс в системе',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Справочник курсов повышения квалификации';

CREATE INDEX idx_qualification_courses_active ON qualification_courses_catalog(is_active);
CREATE INDEX idx_qualification_courses_mandatory ON qualification_courses_catalog(is_mandatory);

-- =========================================================
-- 20. Курсы повышения квалификации сотрудника
-- =========================================================
CREATE TABLE employee_qualification_courses (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник',
    course_id BIGINT UNSIGNED NULL COMMENT 'Курс из справочника, если он есть в каталоге',
    course_name_override VARCHAR(255) NULL COMMENT 'Название вручную, если курса нет в каталоге',
    provider_override VARCHAR(255) NULL COMMENT 'Провайдер вручную',
    started_at DATE NULL COMMENT 'Дата начала',
    completed_at DATE NULL COMMENT 'Дата завершения',
    valid_until DATE NULL COMMENT 'До какой даты курс считается действующим',
    status ENUM('planned', 'in_progress', 'completed', 'expired', 'cancelled')
        NOT NULL DEFAULT 'planned' COMMENT 'Статус курса',
    certificate_number VARCHAR(100) NULL COMMENT 'Номер удостоверения / сертификата',
    result_text TEXT NULL COMMENT 'Примечание или результат',
    last_reminder_sent_at DATETIME NULL COMMENT 'Когда последний раз отправлялось напоминание',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_qualification_courses_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_qualification_courses_catalog
        FOREIGN KEY (course_id) REFERENCES qualification_courses_catalog(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Курсы повышения квалификации сотрудника со сроком действия';

CREATE INDEX idx_employee_qualification_courses_employee_status
    ON employee_qualification_courses(employee_user_id, status);
CREATE INDEX idx_employee_qualification_courses_valid_until
    ON employee_qualification_courses(valid_until);
CREATE INDEX idx_employee_qualification_courses_employee_valid_until
    ON employee_qualification_courses(employee_user_id, valid_until);

-- =========================================================
-- 21. Справочник достижений
-- =========================================================
CREATE TABLE achievements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Системный код достижения',
    name VARCHAR(150) NOT NULL COMMENT 'Название достижения',
    description TEXT NULL COMMENT 'Описание достижения',
    icon_name VARCHAR(100) NULL COMMENT 'Имя иконки или путь к ней',
    points_reward INT NOT NULL DEFAULT 0 COMMENT 'Сколько очков дается за выполнение',
    criteria_type VARCHAR(100) NULL COMMENT 'Тип критерия: manual, course_completed, competition_medal и т.д.',
    criteria_config JSON NULL COMMENT 'Гибкая JSON-конфигурация условий достижения',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Доступно ли достижение сейчас',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
COMMENT='Шаблоны достижений для системы геймификации';

CREATE INDEX idx_achievements_active ON achievements(is_active);

-- =========================================================
-- 22. Достижения сотрудника
-- =========================================================
CREATE TABLE employee_achievements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник',
    achievement_id BIGINT UNSIGNED NOT NULL COMMENT 'Достижение из справочника',
    status ENUM('locked', 'in_progress', 'completed') NOT NULL DEFAULT 'locked' COMMENT 'Статус достижения',
    progress_value DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Прогресс по достижению',
    completed_at DATETIME NULL COMMENT 'Когда достижение было выполнено',
    points_awarded INT NOT NULL DEFAULT 0 COMMENT 'Сколько очков реально начислено',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_achievements_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_employee_achievements_achievement
        FOREIGN KEY (achievement_id) REFERENCES achievements(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Статус достижения у конкретного сотрудника';

CREATE UNIQUE INDEX uq_employee_achievement ON employee_achievements(employee_user_id, achievement_id);
CREATE INDEX idx_employee_achievements_employee_status ON employee_achievements(employee_user_id, status);

-- =========================================================
-- 23. Журнал движения очков
-- =========================================================
CREATE TABLE points_ledger (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник, по чьему счету идет движение',
    transaction_type ENUM('achievement_reward', 'bonus_purchase', 'manual_adjustment', 'course_reward', 'refund', 'other')
        NOT NULL COMMENT 'Тип операции',
    points_delta INT NOT NULL COMMENT 'Изменение баланса: плюс или минус',
    balance_after INT NOT NULL COMMENT 'Баланс после операции',
    reference_entity_type VARCHAR(50) NULL COMMENT 'Тип связанной сущности: achievement, purchase, course и т.д.',
    reference_entity_id BIGINT UNSIGNED NULL COMMENT 'ID связанной сущности',
    comment_text VARCHAR(500) NULL COMMENT 'Пояснение к операции',
    created_by_user_id BIGINT UNSIGNED NULL COMMENT 'Кто инициировал операцию',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_points_ledger_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_points_ledger_created_by
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Финансовый журнал для очков. Полезен для истории и разбирательств "куда делись баллы"';

CREATE INDEX idx_points_ledger_employee_created ON points_ledger(employee_user_id, created_at);
CREATE INDEX idx_points_ledger_reference ON points_ledger(reference_entity_type, reference_entity_id);

-- =========================================================
-- 24. Магазин бонусов
-- =========================================================
CREATE TABLE bonus_catalog (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Системный код бонуса',
    name VARCHAR(150) NOT NULL COMMENT 'Название бонуса',
    description TEXT NULL COMMENT 'Описание бонуса',
    icon_name VARCHAR(100) NULL COMMENT 'Иконка бонуса',
    cost_points INT UNSIGNED NOT NULL COMMENT 'Стоимость бонуса в очках',
    requires_hr_approval BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Нужно ли согласование HR',
    stock_qty INT NULL COMMENT 'Остаток, если бонус лимитированный',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Доступен ли бонус к покупке',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_bonus_cost_positive CHECK (cost_points >= 0)
) ENGINE=InnoDB
COMMENT='Каталог бонусов, которые можно купить за очки';

CREATE INDEX idx_bonus_catalog_active ON bonus_catalog(is_active);

-- =========================================================
-- 25. Покупки бонусов
-- =========================================================
CREATE TABLE bonus_purchases (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кто оформил покупку',
    bonus_id BIGINT UNSIGNED NOT NULL COMMENT 'Какой бонус купили',
    quantity INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Количество единиц бонуса',
    unit_cost_points INT UNSIGNED NOT NULL COMMENT 'Цена одной единицы на момент покупки',
    total_cost_points INT UNSIGNED NOT NULL COMMENT 'Итоговая стоимость покупки',
    status ENUM('pending', 'approved', 'rejected', 'fulfilled', 'cancelled')
        NOT NULL DEFAULT 'pending' COMMENT 'Статус покупки',
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда сотрудник отправил заявку',
    processed_by_hr_user_id BIGINT UNSIGNED NULL COMMENT 'Какой HR обработал заявку',
    processed_at DATETIME NULL COMMENT 'Когда заявка была обработана',
    hr_comment VARCHAR(500) NULL COMMENT 'Комментарий HR',
    CONSTRAINT fk_bonus_purchases_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_bonus_purchases_bonus
        FOREIGN KEY (bonus_id) REFERENCES bonus_catalog(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_bonus_purchases_hr
        FOREIGN KEY (processed_by_hr_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT chk_bonus_purchase_quantity CHECK (quantity >= 1),
    CONSTRAINT chk_bonus_purchase_total_cost CHECK (total_cost_points >= 0)
) ENGINE=InnoDB
COMMENT='Покупки бонусов сотрудниками. HR может подтверждать или отклонять заявку';

CREATE INDEX idx_bonus_purchases_employee_status ON bonus_purchases(employee_user_id, status);
CREATE INDEX idx_bonus_purchases_status_requested ON bonus_purchases(status, requested_at);
CREATE INDEX idx_bonus_purchases_bonus ON bonus_purchases(bonus_id);

-- =========================================================
-- 26. Заявки на изменение резюме
-- =========================================================
CREATE TABLE resume_change_requests (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кто подал заявку',
    section_id SMALLINT UNSIGNED NOT NULL COMMENT 'Какой раздел резюме меняется',
    target_entity_type VARCHAR(50) NULL COMMENT 'Тип изменяемой сущности: skill, education, work_experience и т.д.',
    target_entity_id BIGINT UNSIGNED NULL COMMENT 'ID изменяемой сущности, если правится существующая запись',
    change_description TEXT NOT NULL COMMENT 'Описание изменения обычным текстом',
    proposed_payload JSON NULL COMMENT 'Структурированные данные изменения для будущих форм',
    status ENUM('pending', 'approved', 'rejected', 'needs_clarification', 'implemented')
        NOT NULL DEFAULT 'pending' COMMENT 'Статус заявки',
    review_comment VARCHAR(500) NULL COMMENT 'Комментарий HR по результату рассмотрения',
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда заявка отправлена',
    reviewed_by_hr_user_id BIGINT UNSIGNED NULL COMMENT 'Кто рассмотрел заявку',
    reviewed_at DATETIME NULL COMMENT 'Когда HR рассмотрел заявку',
    CONSTRAINT fk_resume_change_requests_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_resume_change_requests_section
        FOREIGN KEY (section_id) REFERENCES resume_sections(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_resume_change_requests_reviewed_by
        FOREIGN KEY (reviewed_by_hr_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Заявки сотрудников на изменение или дополнение резюме';

CREATE INDEX idx_resume_change_requests_employee_status ON resume_change_requests(employee_user_id, status);
CREATE INDEX idx_resume_change_requests_status_submitted ON resume_change_requests(status, submitted_at);
CREATE INDEX idx_resume_change_requests_section ON resume_change_requests(section_id);

-- =========================================================
-- 27. Документы сотрудников
-- =========================================================
CREATE TABLE employee_documents (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    owner_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Владелец документа',
    document_type ENUM(
        'resume_change_attachment',
        'diploma_file',
        'additional_course_certificate',
        'qualification_course_certificate',
        'competition_proof',
        'resume_snapshot',
        'job_opening_attachment',
        'other'
    ) NOT NULL COMMENT 'Тип документа',
    source_entity_type VARCHAR(50) NOT NULL COMMENT 'Тип сущности-источника: resume_change_request, education, qualification_course и т.д.',
    source_entity_id BIGINT UNSIGNED NOT NULL COMMENT 'ID сущности-источника',
    file_path VARCHAR(500) NOT NULL COMMENT 'Путь к файлу в файловой системе или object storage',
    original_filename VARCHAR(255) NOT NULL COMMENT 'Имя исходного файла',
    mime_type VARCHAR(100) NULL COMMENT 'MIME-тип файла',
    file_size_bytes BIGINT UNSIGNED NULL COMMENT 'Размер файла',
    file_checksum CHAR(64) NULL COMMENT 'Контрольная сумма файла',
    extracted_text LONGTEXT NULL COMMENT 'Извлеченный текст из документа для поиска и RAG',
    extraction_status ENUM('pending', 'processed', 'failed')
        NOT NULL DEFAULT 'pending' COMMENT 'Статус извлечения текста',
    indexed_at DATETIME NULL COMMENT 'Когда документ был отправлен в индексирование',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_documents_owner
        FOREIGN KEY (owner_user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Файлы сотрудников и извлеченный из них текст для поиска и RAG';

CREATE INDEX idx_employee_documents_owner ON employee_documents(owner_user_id);
CREATE INDEX idx_employee_documents_source ON employee_documents(source_entity_type, source_entity_id);
CREATE INDEX idx_employee_documents_extraction_status ON employee_documents(extraction_status);
CREATE INDEX idx_employee_documents_checksum ON employee_documents(file_checksum);
CREATE FULLTEXT INDEX ft_employee_documents_extracted_text
ON employee_documents(extracted_text);

-- =========================================================
-- 28. Уведомления
-- =========================================================
CREATE TABLE notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    notification_type ENUM(
        'employee_course_reminder',
        'hr_resume_change_request',
        'hr_bonus_purchase_request',
        'job_invitation',
        'system',
        'other'
    ) NOT NULL COMMENT 'Тип уведомления',
    title VARCHAR(255) NOT NULL COMMENT 'Короткий заголовок',
    message TEXT NOT NULL COMMENT 'Текст уведомления',
    sender_user_id BIGINT UNSIGNED NULL COMMENT 'Кто инициировал уведомление',
    related_entity_type VARCHAR(50) NULL COMMENT 'Тип связанной сущности',
    related_entity_id BIGINT UNSIGNED NULL COMMENT 'ID связанной сущности',
    priority ENUM('low', 'normal', 'high', 'critical')
        NOT NULL DEFAULT 'normal' COMMENT 'Приоритет уведомления',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NULL COMMENT 'До какого времени уведомление актуально',
    CONSTRAINT fk_notifications_sender
        FOREIGN KEY (sender_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Универсальные уведомления для сотрудников и HR';

CREATE INDEX idx_notifications_type_priority_created ON notifications(notification_type, priority, created_at);
CREATE INDEX idx_notifications_related_entity ON notifications(related_entity_type, related_entity_id);

-- =========================================================
-- 29. Получатели уведомлений
-- =========================================================
CREATE TABLE notification_recipients (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    notification_id BIGINT UNSIGNED NOT NULL COMMENT 'Уведомление',
    recipient_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Получатель',
    status ENUM('unread', 'read', 'archived')
        NOT NULL DEFAULT 'unread' COMMENT 'Статус уведомления для конкретного пользователя',
    read_at DATETIME NULL COMMENT 'Когда пользователь прочитал уведомление',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notification_recipients_notification
        FOREIGN KEY (notification_id) REFERENCES notifications(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_notification_recipients_user
        FOREIGN KEY (recipient_user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Связь уведомлений с конкретными пользователями и статус их прочтения';

CREATE UNIQUE INDEX uq_notification_recipient ON notification_recipients(notification_id, recipient_user_id);
CREATE INDEX idx_notification_recipients_user_status_created ON notification_recipients(recipient_user_id, status, created_at);

-- =========================================================
-- 30. Вакансии / позиции для подбора
-- =========================================================
CREATE TABLE job_openings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    position_id BIGINT UNSIGNED NULL COMMENT 'Ссылка на справочник должностей',
    department_id BIGINT UNSIGNED NULL COMMENT 'Подразделение вакансии',
    title VARCHAR(255) NOT NULL COMMENT 'Название вакансии',
    requirements_text LONGTEXT NOT NULL COMMENT 'Требования к кандидату',
    responsibilities_text LONGTEXT NULL COMMENT 'Описание задач',
    location_text VARCHAR(255) NULL COMMENT 'Локация / формат работы',
    employment_type ENUM('office', 'remote', 'hybrid', 'project', 'part_time', 'full_time', 'other')
        NOT NULL DEFAULT 'office' COMMENT 'Формат занятости',
    status ENUM('draft', 'open', 'closed', 'archived')
        NOT NULL DEFAULT 'draft' COMMENT 'Статус вакансии',
    created_by_hr_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Какой HR создал вакансию',
    published_at DATETIME NULL COMMENT 'Когда вакансия опубликована',
    closed_at DATETIME NULL COMMENT 'Когда вакансия закрыта',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_openings_position
        FOREIGN KEY (position_id) REFERENCES positions_catalog(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_job_openings_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_job_openings_created_by
        FOREIGN KEY (created_by_hr_user_id) REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Вакансии и позиции, по которым HR запускает подбор кандидатов';

CREATE INDEX idx_job_openings_status ON job_openings(status);
CREATE INDEX idx_job_openings_department ON job_openings(department_id);
CREATE INDEX idx_job_openings_position ON job_openings(position_id);
CREATE FULLTEXT INDEX ft_job_openings_text
ON job_openings(title, requirements_text, responsibilities_text);

-- =========================================================
-- 31. Приглашения сотрудникам на должность
-- =========================================================
CREATE TABLE job_invitations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    opening_id BIGINT UNSIGNED NOT NULL COMMENT 'На какую вакансию идет приглашение',
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кого пригласили',
    hr_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кто отправил приглашение',
    message_text TEXT NULL COMMENT 'Сообщение сотруднику',
    status ENUM('sent', 'viewed', 'accepted', 'declined', 'expired')
        NOT NULL DEFAULT 'sent' COMMENT 'Статус приглашения',
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда приглашение отправлено',
    responded_at DATETIME NULL COMMENT 'Когда сотрудник ответил',
    CONSTRAINT fk_job_invitations_opening
        FOREIGN KEY (opening_id) REFERENCES job_openings(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_job_invitations_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_job_invitations_hr
        FOREIGN KEY (hr_user_id) REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Приглашения сотрудников на вакансии';

CREATE UNIQUE INDEX uq_job_invitation_opening_employee ON job_invitations(opening_id, employee_user_id);
CREATE INDEX idx_job_invitations_employee_status ON job_invitations(employee_user_id, status);
CREATE INDEX idx_job_invitations_opening_status ON job_invitations(opening_id, status);

-- =========================================================
-- 32. Поисковый профиль кандидата
-- =========================================================
CREATE TABLE candidate_search_profiles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL UNIQUE COMMENT 'Сотрудник, которому принадлежит поисковый профиль',
    profile_text LONGTEXT NOT NULL COMMENT 'Склеенный текстовый профиль для полнотекстового поиска',
    normalized_skills_text TEXT NULL COMMENT 'Нормализованный список навыков строкой',
    total_experience_months INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Стаж в месяцах, вычисляемый сервисом',
    source_checksum CHAR(64) NULL COMMENT 'Контрольная сумма исходных данных резюме',
    index_status ENUM('pending', 'ready', 'failed') NOT NULL DEFAULT 'pending' COMMENT 'Статус подготовки профиля к поиску',
    last_error_text VARCHAR(500) NULL COMMENT 'Последняя ошибка индексатора',
    last_built_at DATETIME NULL COMMENT 'Когда профиль был собран',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidate_search_profiles_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Денормализованный поисковый профиль кандидата для подборов и RAG';

CREATE INDEX idx_candidate_search_profiles_status ON candidate_search_profiles(index_status);
CREATE INDEX idx_candidate_search_profiles_experience ON candidate_search_profiles(total_experience_months);
CREATE FULLTEXT INDEX ft_candidate_search_profiles_text
ON candidate_search_profiles(profile_text, normalized_skills_text);

-- =========================================================
-- 33. Чанки документов для RAG
-- =========================================================
CREATE TABLE rag_chunks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    search_profile_id BIGINT UNSIGNED NULL COMMENT 'Поисковый профиль, в рамках которого был собран чанк',
    document_id BIGINT UNSIGNED NULL COMMENT 'Документ, из которого нарезан чанк',
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кандидат, к которому относится чанк',
    chunk_no INT UNSIGNED NOT NULL COMMENT 'Порядковый номер чанка внутри документа',
    chunk_text MEDIUMTEXT NOT NULL COMMENT 'Текст чанка для поиска и генерации',
    chunk_checksum CHAR(64) NULL COMMENT 'Контрольная сумма чанка',
    embedding_model VARCHAR(100) NULL COMMENT 'Название модели эмбеддингов',
    external_vector_id VARCHAR(255) NULL COMMENT 'ID в внешнем vector store',
    vector_status ENUM('pending', 'ready', 'failed') NOT NULL DEFAULT 'pending' COMMENT 'Статус векторизации',
    tokens_count INT UNSIGNED NULL COMMENT 'Примерное число токенов в чанке',
    last_indexed_at DATETIME NULL COMMENT 'Когда чанк был отправлен в индекс',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rag_chunks_search_profile
        FOREIGN KEY (search_profile_id) REFERENCES candidate_search_profiles(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_rag_chunks_document
        FOREIGN KEY (document_id) REFERENCES employee_documents(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_rag_chunks_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Чанки документов и профилей кандидатов для RAG-поиска';

CREATE UNIQUE INDEX uq_rag_chunks_document_chunk_no ON rag_chunks(document_id, chunk_no);
CREATE INDEX idx_rag_chunks_employee_status ON rag_chunks(employee_user_id, vector_status);
CREATE INDEX idx_rag_chunks_vector_external_id ON rag_chunks(external_vector_id);
CREATE FULLTEXT INDEX ft_rag_chunks_text
ON rag_chunks(chunk_text);

-- =========================================================
-- 34. Запуск подбора кандидатов
-- =========================================================
CREATE TABLE candidate_match_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    opening_id BIGINT UNSIGNED NULL COMMENT 'Вакансия, по которой делается подбор. Может быть NULL для ad-hoc запроса',
    hr_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Какой HR запустил подбор',
    requirements_text LONGTEXT NOT NULL COMMENT 'Текст требований, введенный HR',
    filters_json JSON NULL COMMENT 'Дополнительные фильтры: отдел, уровень, обязательные навыки и т.д.',
    top_k INT UNSIGNED NOT NULL DEFAULT 20 COMMENT 'Сколько кандидатов хотим вернуть',
    status ENUM('queued', 'running', 'completed', 'failed')
        NOT NULL DEFAULT 'queued' COMMENT 'Статус выполнения подбора',
    llm_model VARCHAR(120) NULL COMMENT 'Какая LLM использовалась',
    embedding_model VARCHAR(120) NULL COMMENT 'Какая модель эмбеддингов использовалась',
    graph_version VARCHAR(50) NULL COMMENT 'Версия LangGraph-конвейера',
    error_text VARCHAR(500) NULL COMMENT 'Ошибка, если подбор завершился неуспешно',
    started_at DATETIME NULL COMMENT 'Когда фактически началось выполнение',
    completed_at DATETIME NULL COMMENT 'Когда выполнение завершилось',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidate_match_runs_opening
        FOREIGN KEY (opening_id) REFERENCES job_openings(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_candidate_match_runs_hr
        FOREIGN KEY (hr_user_id) REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='История запусков поиска и ранжирования кандидатов';

CREATE INDEX idx_candidate_match_runs_hr_status_created ON candidate_match_runs(hr_user_id, status, created_at);
CREATE INDEX idx_candidate_match_runs_opening ON candidate_match_runs(opening_id);

-- =========================================================
-- 35. Результаты ранжирования кандидатов
-- =========================================================
CREATE TABLE candidate_match_results (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    run_id BIGINT UNSIGNED NOT NULL COMMENT 'Запуск подбора',
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Кандидат',
    rank_position INT UNSIGNED NOT NULL COMMENT 'Позиция кандидата в рейтинге',
    score DECIMAL(8,4) NOT NULL COMMENT 'Итоговый score релевантности',
    decision_label ENUM('strong_match', 'match', 'partial_match', 'weak_match')
        NOT NULL DEFAULT 'partial_match' COMMENT 'Категоризация результата для UI',
    fit_summary TEXT NULL COMMENT 'Короткое резюме, почему кандидат подходит',
    strengths_text TEXT NULL COMMENT 'Сильные стороны кандидата',
    gaps_text TEXT NULL COMMENT 'Пробелы / дефициты',
    model_output_json JSON NULL COMMENT 'Сырой результат модели, если нужно сохранить дополнительные детали',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidate_match_results_run
        FOREIGN KEY (run_id) REFERENCES candidate_match_runs(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_candidate_match_results_employee
        FOREIGN KEY (employee_user_id) REFERENCES employee_profiles(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Результаты конкретного запуска подбора кандидатов';

CREATE UNIQUE INDEX uq_candidate_match_results_run_employee ON candidate_match_results(run_id, employee_user_id);
CREATE INDEX idx_candidate_match_results_run_rank ON candidate_match_results(run_id, rank_position);
CREATE INDEX idx_candidate_match_results_employee_score ON candidate_match_results(employee_user_id, score);

-- =========================================================
-- 36. Аудит действий
-- =========================================================
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_user_id BIGINT UNSIGNED NULL COMMENT 'Кто совершил действие',
    action_type VARCHAR(100) NOT NULL COMMENT 'Тип действия: LOGIN_SUCCESS, PURCHASE_CREATED, INVITATION_SENT и т.д.',
    entity_type VARCHAR(50) NOT NULL COMMENT 'Над какой сущностью было действие',
    entity_id BIGINT UNSIGNED NULL COMMENT 'ID сущности',
    entity_label VARCHAR(255) NULL COMMENT 'Человеко-понятная подпись сущности',
    ip_address VARCHAR(45) NULL COMMENT 'IP-адрес, если есть',
    user_agent VARCHAR(255) NULL COMMENT 'Клиент пользователя',
    details_json JSON NULL COMMENT 'Дополнительные детали в JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
COMMENT='Журнал важных действий пользователей и системных процессов';

CREATE INDEX idx_audit_logs_actor_created ON audit_logs(actor_user_id, created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action_created ON audit_logs(action_type, created_at);

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

USE elbrus;

ALTER TABLE users
    ADD COLUMN username VARCHAR(100) NULL AFTER email,
    ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT FALSE AFTER is_active;

CREATE UNIQUE INDEX uq_users_username ON users(username);

USE elbrus;

-- ---------------------------------------------------------
-- employee1 / Employee123!
-- hr1       / HR12345!
-- ---------------------------------------------------------

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
    2001,
    r.id,
    'Матвей',
    'Матвиенко',
    'Матвеевич',
    'employee1@elbrus.local',
    'employee1',
    'Employee123!',
    TRUE,
    FALSE,
    NOW(),
    NOW()
FROM roles r
WHERE r.code = 'EMPLOYEE'
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
    1001,
    r.id,
    'Марина',
    'Соколова',
    'Игоревна',
    'hr1@elbrus.local',
    'hr1',
    'HR12345!',
    TRUE,
    FALSE,
    NOW(),
    NOW()
FROM roles r
WHERE r.code = 'HR_MANAGER'
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

-- =========================================================
-- Расширение профиля сотрудника под "Личные данные"
-- =========================================================

USE elbrus;

-- ---------------------------------------------------------
-- 1. Добавляем недостающие поля в employee_profiles
-- ---------------------------------------------------------
ALTER TABLE employee_profiles
    ADD COLUMN gender ENUM('male', 'female', 'other', 'unspecified') NULL AFTER birth_date,
    ADD COLUMN marital_status VARCHAR(100) NULL AFTER gender,
    ADD COLUMN citizenship VARCHAR(120) NULL AFTER marital_status,
    ADD COLUMN driver_license_categories VARCHAR(100) NULL AFTER citizenship,
    ADD COLUMN has_criminal_record BOOLEAN NOT NULL DEFAULT FALSE AFTER driver_license_categories,
    ADD COLUMN criminal_record_details TEXT NULL AFTER has_criminal_record;

-- ---------------------------------------------------------
-- 2. Добавляем недостающие разделы в справочник resume_sections
-- ---------------------------------------------------------
INSERT INTO resume_sections (code, name, description) VALUES
('diplomas', 'Дипломы', 'Дипломы и подтверждающие документы по образованию'),
('competition_awards', 'Призёр/Победитель соревнований', 'Призовые места и награды в соревнованиях')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description);

-- ---------------------------------------------------------
-- 3. Наполняем тестовыми данными профиль сотрудника 2001
-- ---------------------------------------------------------
UPDATE employee_profiles
SET
    gender = 'male',
    marital_status = 'Женат, 2 детей',
    citizenship = 'Российская Федерация',
    driver_license_categories = 'B',
    has_criminal_record = FALSE,
    criminal_record_details = NULL
WHERE user_id = 2001;

-- ---------------------------------------------------------
-- 4. Для наглядности можно обновить и второго сотрудника
-- ---------------------------------------------------------
UPDATE employee_profiles
SET
    gender = 'female',
    marital_status = 'Не замужем',
    citizenship = 'Российская Федерация',
    driver_license_categories = NULL,
    has_criminal_record = FALSE,
    criminal_record_details = NULL
WHERE user_id = 2002;

-- =========================================================
-- Достижения
-- =========================================================

USE elbrus;

-- ---------------------------------------------------------
-- 1. Журнал входов
-- ---------------------------------------------------------
DROP TABLE IF EXISTS user_login_events;

CREATE TABLE user_login_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    logged_in_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(64) NULL,
    user_agent VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_login_events_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_user_login_events_user_id (user_id),
    INDEX idx_user_login_events_logged_in_at (logged_in_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- 2. Таблица фактов начисления очков
-- ---------------------------------------------------------
DROP TABLE IF EXISTS employee_point_transactions;

CREATE TABLE employee_point_transactions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL,
    transaction_type ENUM(
        'achievement_award',
        'achievement_reversal',
        'manual_adjustment',
        'store_purchase'
    ) NOT NULL,
    points_delta INT NOT NULL,
    source_entity_type VARCHAR(50) NULL,
    source_entity_id BIGINT NULL,
    comment TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_point_transactions_user
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_employee_point_transactions_user_id (employee_user_id),
    INDEX idx_employee_point_transactions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- 3. Таблица фактов выдачи достижений
-- ---------------------------------------------------------
DROP TABLE IF EXISTS employee_achievement_awards;

CREATE TABLE employee_achievement_awards (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL,
    achievement_id INT NOT NULL,
    award_key VARCHAR(120) NOT NULL,
    achievement_counter INT NOT NULL DEFAULT 1,
    points_awarded INT NOT NULL,
    awarded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_entity_type VARCHAR(50) NULL,
    source_entity_id BIGINT NULL,
    awarded_by_user_id BIGINT UNSIGNED NULL,
    status ENUM('awarded', 'revoked') NOT NULL DEFAULT 'awarded',
    rule_snapshot_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_achievement_awards_user
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_employee_achievement_awards_awarded_by
        FOREIGN KEY (awarded_by_user_id) REFERENCES users(id)
        ON DELETE SET NULL,

    UNIQUE KEY uq_employee_achievement_award_once
        (employee_user_id, achievement_id, award_key),

    INDEX idx_employee_achievement_awards_user_id (employee_user_id),
    INDEX idx_employee_achievement_awards_achievement_id (achievement_id),
    INDEX idx_employee_achievement_awards_awarded_at (awarded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- 4. Удаляем старую legacy-таблицу достижений сотрудника
-- ---------------------------------------------------------
DROP TABLE IF EXISTS employee_achievements;

-- ---------------------------------------------------------
-- 5. Каталог достижений
-- ---------------------------------------------------------
DROP TABLE IF EXISTS achievements;

CREATE TABLE achievements (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    points INT NOT NULL,
    icon VARCHAR(16) NULL,
    category_code VARCHAR(50) NOT NULL,
    verification_type ENUM('automatic', 'manual_hr', 'hybrid', 'todo') NOT NULL DEFAULT 'automatic',
    rule_type VARCHAR(100) NOT NULL,
    rule_config_json JSON NULL,
    is_repeatable BOOLEAN NOT NULL DEFAULT FALSE,
    repeat_period ENUM('once', 'source', 'month', 'quarter', 'year') NOT NULL DEFAULT 'once',
    sort_order INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_achievements_code (code),
    INDEX idx_achievements_category_code (category_code),
    INDEX idx_achievements_is_active (is_active),
    INDEX idx_achievements_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

USE elbrus;

-- =========================================================
-- Магазин бонусов
-- =========================================================

DROP TABLE IF EXISTS bonus_purchase_notifications;
DROP TABLE IF EXISTS bonus_purchases;
DROP TABLE IF EXISTS bonus_catalog;

-- ---------------------------------------------------------
-- 1. Каталог бонусов
-- ---------------------------------------------------------
CREATE TABLE bonus_catalog (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500) NOT NULL,
    price_points INT NOT NULL,
    icon VARCHAR(16) NULL,
    level_label VARCHAR(100) NOT NULL,
    sort_order INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_bonus_catalog_code (code),
    INDEX idx_bonus_catalog_is_active (is_active),
    INDEX idx_bonus_catalog_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- 2. Заказы на бонусы
-- ---------------------------------------------------------
CREATE TABLE bonus_purchases (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL,
    bonus_id INT NOT NULL,
    purchase_token CHAR(36) NOT NULL,
    bonus_snapshot_name VARCHAR(255) NOT NULL,
    bonus_snapshot_price_points INT NOT NULL,
    status ENUM('pending_hr', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending_hr',
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    processed_by_hr_user_id BIGINT UNSIGNED NULL,
    hr_comment TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_bonus_purchases_employee
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_bonus_purchases_bonus
        FOREIGN KEY (bonus_id) REFERENCES bonus_catalog(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_bonus_purchases_hr_user
        FOREIGN KEY (processed_by_hr_user_id) REFERENCES users(id)
        ON DELETE SET NULL,

    UNIQUE KEY uq_bonus_purchases_purchase_token (purchase_token),

    INDEX idx_bonus_purchases_employee_user_id (employee_user_id),
    INDEX idx_bonus_purchases_bonus_id (bonus_id),
    INDEX idx_bonus_purchases_status (status),
    INDEX idx_bonus_purchases_requested_at (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- 3. Очередь уведомлений для HR по заказам бонусов
-- ---------------------------------------------------------
CREATE TABLE bonus_purchase_notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bonus_purchase_id BIGINT UNSIGNED NOT NULL,
    hr_user_id BIGINT UNSIGNED NOT NULL,
    employee_user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_status ENUM('unread', 'read') NOT NULL DEFAULT 'unread',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME NULL,

    CONSTRAINT fk_bonus_purchase_notifications_purchase
        FOREIGN KEY (bonus_purchase_id) REFERENCES bonus_purchases(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_bonus_purchase_notifications_hr_user
        FOREIGN KEY (hr_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_bonus_purchase_notifications_employee_user
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE KEY uq_bonus_purchase_notifications_recipient
        (bonus_purchase_id, hr_user_id),

    INDEX idx_bonus_purchase_notifications_hr_user_id (hr_user_id),
    INDEX idx_bonus_purchase_notifications_employee_user_id (employee_user_id),
    INDEX idx_bonus_purchase_notifications_status (notification_status),
    INDEX idx_bonus_purchase_notifications_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

USE elbrus;

-- =========================================================
-- Наполнение каталога бонусов
-- =========================================================

INSERT INTO bonus_catalog (
    code,
    name,
    description,
    price_points,
    icon,
    level_label,
    sort_order,
    is_active
) VALUES
(
    'PARTNER_SUBSCRIPTION',
    'Подписка на сервис партнёра',
    'Подписка на сервис партнёра: музыка, кино, сериалы или экосистема наподобие Яндекс Плюс.',
    500,
    '📰',
    'Уровень 1',
    10,
    TRUE
),
(
    'INDUSTRY_CONFERENCE',
    'Участие в отраслевой конференции (билет + проезд)',
    'Билет на отраслевую конференцию и компенсация расходов на поездку.',
    300,
    '🎤',
    'Уровень 1',
    20,
    TRUE
),
(
    'FOOD_CERTIFICATE',
    'Сертификат на обед в партнёрском кафе/доставку еды',
    'Небольшой приятный бонус на питание у партнёра или доставку еды.',
    250,
    '🍽️',
    'Уровень 1',
    30,
    TRUE
),
(
    'GIFT_CARD_500',
    'Подарочная карта партнёра на 500 рублей',
    'Подарочная карта номиналом 500 рублей от партнёрской сети.',
    250,
    '🎁',
    'Уровень 1',
    40,
    TRUE
),
(
    'COURSE_DISCOUNT',
    'Скидка на курсы партнёра (онлайн-платформа)',
    'Скидка на обучающие онлайн-курсы партнёрской платформы.',
    200,
    '🎓',
    'Уровень 1',
    50,
    TRUE
),
(
    'CORPORATE_MERCH',
    'Корпоративный мерч (футболка/худи с логотипом)',
    'Фирменный мерч компании: футболка, худи или аналогичный сувенир.',
    150,
    '👕',
    'Уровень 1',
    60,
    TRUE
),
(
    'SPORT_HEALTH_COMPENSATION',
    'Компенсация расходов на спорт/здоровье (до 15 тыс. ₽/год)',
    'Компенсация части затрат на спорт, фитнес или программы здоровья.',
    1400,
    '🏃',
    'Уровень 2',
    70,
    TRUE
),
(
    'EXTRA_PAID_DAY_OFF',
    'Дополнительный оплачиваемый день отпуска',
    'Один дополнительный оплачиваемый день отдыха.',
    800,
    '🌴',
    'Уровень 2',
    80,
    TRUE
),
(
    'GIFT_CARD_1500',
    'Подарочная карта партнёра на 1500 рублей',
    'Подарочная карта повышенного номинала на 1500 рублей.',
    800,
    '🎁',
    'Уровень 2',
    90,
    TRUE
),
(
    'SALARY_INDEXATION_5_10',
    'Индексация оклада на 5–10%',
    'Инициирование повышения дохода в пределах внутреннего диапазона по правилам компании.',
    5000,
    '💰',
    'Уровень 3',
    100,
    TRUE
),
(
    'PERSONAL_PROJECT_FUNDING',
    'Финансирование личного проекта/исследования',
    'Поддержка личного профессионального проекта, исследования или инициативы.',
    5000,
    '🚀',
    'Уровень 3',
    110,
    TRUE
),
(
    'SANATORIUM_3_DAYS',
    'Отдых в санатории 3 дня',
    'Короткий восстановительный отдых в санатории на 3 дня.',
    4000,
    '🌿',
    'Уровень 3',
    120,
    TRUE
),
(
    'EXTRA_PAID_WEEK_OFF',
    'Дополнительная неделя оплачиваемого отпуска',
    'Дополнительная оплачиваемая неделя отдыха.',
    4000,
    '🗓️',
    'Уровень 3',
    130,
    TRUE
);

USE elbrus;

-- =========================================================
-- Уведомления сотрудника
-- =========================================================


DROP TABLE IF EXISTS employee_notifications;

CREATE TABLE employee_notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_user_id BIGINT UNSIGNED NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    notification_key VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_status ENUM('new', 'read') NOT NULL DEFAULT 'new',
    related_entity_type VARCHAR(50) NULL,
    related_entity_id BIGINT NULL,
    expires_at DATE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_notifications_user
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE KEY uq_employee_notifications_user_key (
        employee_user_id,
        notification_key
    ),

    INDEX idx_employee_notifications_user_id (employee_user_id),
    INDEX idx_employee_notifications_status (notification_status),
    INDEX idx_employee_notifications_created_at (created_at),
    INDEX idx_employee_notifications_type (notification_type),
    INDEX idx_employee_notifications_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

USE elbrus;

-- =========================================================
-- HR-уведомления
-- =========================================================

-- ---------------------------------------------------------
-- 1. Расширяем статусы очереди по бонусам
-- ---------------------------------------------------------
ALTER TABLE bonus_purchase_notifications
    MODIFY COLUMN notification_status ENUM('unread', 'read', 'archived')
    NOT NULL DEFAULT 'unread';

-- ---------------------------------------------------------
-- 2. Очередь HR по истекающим курсам повышения квалификации
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS hr_course_expiry_notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    qualification_course_id BIGINT UNSIGNED NOT NULL,
    hr_user_id BIGINT UNSIGNED NOT NULL,
    employee_user_id BIGINT UNSIGNED NOT NULL,

    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    notification_status ENUM('unread', 'read', 'archived')
        NOT NULL DEFAULT 'unread',

    reminder_sent_at DATETIME NULL COMMENT 'Когда HR уже отправил напоминание сотруднику',
    read_at DATETIME NULL COMMENT 'Когда HR открыл / прочитал уведомление',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_hr_course_expiry_notifications_course
        FOREIGN KEY (qualification_course_id) REFERENCES employee_qualification_courses(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_hr_course_expiry_notifications_hr_user
        FOREIGN KEY (hr_user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_hr_course_expiry_notifications_employee_user
        FOREIGN KEY (employee_user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    UNIQUE KEY uq_hr_course_expiry_notifications_course_hr (
        qualification_course_id,
        hr_user_id
    ),

    INDEX idx_hr_course_expiry_notifications_hr_status (
        hr_user_id,
        notification_status,
        created_at
    ),
    INDEX idx_hr_course_expiry_notifications_employee (
        employee_user_id
    ),
    INDEX idx_hr_course_expiry_notifications_course (
        qualification_course_id
    ),
    INDEX idx_hr_course_expiry_notifications_reminder_sent (
        reminder_sent_at
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- HR: Рейтинговая анонимная таблица кандидатов
-- =========================================================


CREATE TABLE IF NOT EXISTS candidate_search_documents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Технический PK',
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник, для которого собран поисковый документ',
    anonymous_code VARCHAR(32) NOT NULL COMMENT 'Стабильный анонимный код кандидата, который видит HR',
    source_hash CHAR(64) NOT NULL COMMENT 'SHA-256 хэш агрегированного resume-текста. Помогает отслеживать изменения',
    profile_text LONGTEXT NULL COMMENT 'Нормализованный текст личных данных',
    skills_text LONGTEXT NULL COMMENT 'Нормализованный текст навыков',
    experience_text LONGTEXT NULL COMMENT 'Нормализованный текст опыта',
    education_text LONGTEXT NULL COMMENT 'Нормализованный текст образования и дипломов',
    courses_text LONGTEXT NULL COMMENT 'Нормализованный текст курсов и повышения квалификации',
    aggregated_text LONGTEXT NOT NULL COMMENT 'Единый поисковый текст документа кандидата',
    structured_payload JSON NOT NULL COMMENT 'Структурированный JSON-снимок документа для UI и ranking',
    last_indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда документ последний раз собран',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда запись впервые появилась',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Когда запись обновлялась',

    PRIMARY KEY (id),
    UNIQUE KEY uq_candidate_search_documents_employee (employee_user_id),
    UNIQUE KEY uq_candidate_search_documents_anon_code (anonymous_code),
    KEY idx_candidate_search_documents_updated_at (updated_at),

    CONSTRAINT fk_candidate_search_documents_user
        FOREIGN KEY (employee_user_id)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Кэш поисковых документов сотрудников для HR-подбора';

CREATE TABLE IF NOT EXISTS job_invitations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK приглашения',
    hr_user_id BIGINT UNSIGNED NOT NULL COMMENT 'HR, который отправил приглашение',
    employee_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Сотрудник, которому отправлено приглашение',
    anonymous_code_snapshot VARCHAR(32) NOT NULL COMMENT 'Анонимный код кандидата на момент отправки приглашения',
    position_title VARCHAR(255) NOT NULL COMMENT 'Короткое название роли / должности',
    requirements_text LONGTEXT NOT NULL COMMENT 'Текст требований, по которым делался поиск',
    comment_text TEXT NULL COMMENT 'Комментарий HR к приглашению',
    invitation_status VARCHAR(50) NOT NULL DEFAULT 'sent' COMMENT 'Текущий статус приглашения',
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда приглашение было отправлено',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Когда запись создана',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Когда запись обновлялась',

    PRIMARY KEY (id),
    KEY idx_job_invitations_hr_user_id (hr_user_id),
    KEY idx_job_invitations_employee_user_id (employee_user_id),
    KEY idx_job_invitations_status (invitation_status),
    KEY idx_job_invitations_sent_at (sent_at),

    CONSTRAINT fk_job_invitations_hr_user
        FOREIGN KEY (hr_user_id)
        REFERENCES users (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_job_invitations_employee_user
        FOREIGN KEY (employee_user_id)
        REFERENCES users (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Приглашения сотрудников на роли / должности по результатам HR-подбора';

  USE elbrus;

-- =========================================================
-- Stage 10. Автоматическое определение раздела резюме
-- =========================================================

-- ---------------------------------------------------------
-- predicted_section_id
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND column_name = 'predicted_section_id'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE resume_change_requests
        ADD COLUMN predicted_section_id SMALLINT UNSIGNED NULL
        COMMENT ''Раздел, предсказанный semantic routing''
        AFTER section_id',
    'SELECT ''predicted_section_id already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- predicted_section_confidence
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND column_name = 'predicted_section_confidence'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE resume_change_requests
        ADD COLUMN predicted_section_confidence DECIMAL(8,6) NULL
        COMMENT ''Confidence автоопределения раздела''
        AFTER predicted_section_id',
    'SELECT ''predicted_section_confidence already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- predicted_section_reason
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND column_name = 'predicted_section_reason'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE resume_change_requests
        ADD COLUMN predicted_section_reason VARCHAR(1000) NULL
        COMMENT ''Пояснение выбора раздела''
        AFTER predicted_section_confidence',
    'SELECT ''predicted_section_reason already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- section_detection_source
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND column_name = 'section_detection_source'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE resume_change_requests
        ADD COLUMN section_detection_source VARCHAR(20) NOT NULL DEFAULT ''manual''
        COMMENT ''Источник выбора раздела: ai/manual''
        AFTER predicted_section_reason',
    'SELECT ''section_detection_source already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- section_detection_candidates_json
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND column_name = 'section_detection_candidates_json'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE resume_change_requests
        ADD COLUMN section_detection_candidates_json JSON NULL
        COMMENT ''Top-k кандидаты semantic routing''
        AFTER section_detection_source',
    'SELECT ''section_detection_candidates_json already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- employee_documents.extracted_text, если схема старая
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'employee_documents'
      AND column_name = 'extracted_text'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE employee_documents
        ADD COLUMN extracted_text LONGTEXT NULL
        COMMENT ''Извлеченный текст из документа для поиска и RAG''
        AFTER file_checksum',
    'SELECT ''employee_documents.extracted_text already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- employee_documents.extraction_status, если схема старая
-- ---------------------------------------------------------
SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'employee_documents'
      AND column_name = 'extraction_status'
);

SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE employee_documents
        ADD COLUMN extraction_status ENUM(''pending'', ''processed'', ''failed'')
        NOT NULL DEFAULT ''pending''
        COMMENT ''Статус извлечения текста''
        AFTER extracted_text',
    'SELECT ''employee_documents.extraction_status already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------
-- Индексы
-- ---------------------------------------------------------
SET @index_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND index_name = 'idx_resume_change_requests_predicted_section'
);

SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX idx_resume_change_requests_predicted_section
        ON resume_change_requests(predicted_section_id)',
    'SELECT ''idx_resume_change_requests_predicted_section already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'resume_change_requests'
      AND index_name = 'idx_resume_change_requests_detection_source'
);

SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX idx_resume_change_requests_detection_source
        ON resume_change_requests(section_detection_source)',
    'SELECT ''idx_resume_change_requests_detection_source already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'employee_documents'
      AND index_name = 'idx_employee_documents_extraction_status'
);

SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX idx_employee_documents_extraction_status
        ON employee_documents(extraction_status)',
    'SELECT ''idx_employee_documents_extraction_status already exists'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;