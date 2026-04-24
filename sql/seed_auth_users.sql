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