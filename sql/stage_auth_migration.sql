USE elbrus;

ALTER TABLE users
    ADD COLUMN username VARCHAR(100) NULL AFTER email,
    ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT FALSE AFTER is_active;

CREATE UNIQUE INDEX uq_users_username ON users(username);