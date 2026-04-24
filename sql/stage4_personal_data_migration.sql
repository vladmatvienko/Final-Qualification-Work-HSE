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