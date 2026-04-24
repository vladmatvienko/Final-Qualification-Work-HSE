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