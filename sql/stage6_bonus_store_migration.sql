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