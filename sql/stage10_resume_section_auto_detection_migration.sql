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
-- employee_documents.extracted_text
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
-- employee_documents.extraction_status
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