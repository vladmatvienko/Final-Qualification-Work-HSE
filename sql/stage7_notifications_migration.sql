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