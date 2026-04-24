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