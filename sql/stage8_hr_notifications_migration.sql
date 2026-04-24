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