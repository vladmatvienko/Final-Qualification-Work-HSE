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