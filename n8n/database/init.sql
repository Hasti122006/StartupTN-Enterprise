-- ============================================================
-- StartupTN Enterprise Scraper — Database Schema
-- MySQL 8.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS startuptn_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE startuptn_db;

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    full_name     VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'operator', 'viewer') NOT NULL DEFAULT 'viewer',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- JOBS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    status              ENUM('pending','running','paused','completed','failed','stopped') NOT NULL DEFAULT 'pending',
    current_page        INT UNSIGNED NOT NULL DEFAULT 0,
    current_company     VARCHAR(500) DEFAULT NULL,
    total_pages         INT UNSIGNED NOT NULL DEFAULT 0,
    total_companies     INT UNSIGNED NOT NULL DEFAULT 0,
    scraped_companies   INT UNSIGNED NOT NULL DEFAULT 0,
    failed_companies    INT UNSIGNED NOT NULL DEFAULT 0,
    start_page          INT UNSIGNED NOT NULL DEFAULT 1,
    end_page            INT UNSIGNED NOT NULL DEFAULT 0,
    workers             TINYINT UNSIGNED NOT NULL DEFAULT 2,
    delay_min           FLOAT NOT NULL DEFAULT 1.0,
    delay_max           FLOAT NOT NULL DEFAULT 3.0,
    retry_count         TINYINT UNSIGNED NOT NULL DEFAULT 3,
    timeout             INT UNSIGNED NOT NULL DEFAULT 30,
    headless            BOOLEAN NOT NULL DEFAULT TRUE,
    output_excel        BOOLEAN NOT NULL DEFAULT TRUE,
    output_csv          BOOLEAN NOT NULL DEFAULT TRUE,
    output_database     BOOLEAN NOT NULL DEFAULT TRUE,
    error_message       TEXT DEFAULT NULL,
    start_time          DATETIME DEFAULT NULL,
    end_time            DATETIME DEFAULT NULL,
    duration            INT UNSIGNED DEFAULT NULL COMMENT 'seconds',
    created_by          INT UNSIGNED DEFAULT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- COMPANIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_name        VARCHAR(500) NOT NULL,
    founders            TEXT DEFAULT NULL,
    sector              VARCHAR(255) DEFAULT NULL,
    current_stage       VARCHAR(255) DEFAULT NULL,
    team_size           VARCHAR(100) DEFAULT NULL,
    member_since        VARCHAR(100) DEFAULT NULL,
    key_highlights      TEXT DEFAULT NULL,
    about               LONGTEXT DEFAULT NULL,
    website             VARCHAR(1000) DEFAULT NULL,
    linkedin            VARCHAR(1000) DEFAULT NULL,
    email               VARCHAR(500) DEFAULT NULL,
    phone               VARCHAR(255) DEFAULT NULL,
    location            VARCHAR(500) DEFAULT NULL,
    engagement_level    VARCHAR(255) DEFAULT NULL,
    smart_card_number   VARCHAR(255) DEFAULT NULL,
    startup_type        VARCHAR(255) DEFAULT NULL,
    profile_url         VARCHAR(2000) NOT NULL,
    logo_url            VARCHAR(2000) DEFAULT NULL,
    job_id              INT UNSIGNED DEFAULT NULL,
    scraped_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_companies_profile_url (profile_url(500)),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    INDEX idx_companies_company_name (company_name(100)),
    INDEX idx_companies_sector (sector),
    INDEX idx_companies_stage (current_stage),
    INDEX idx_companies_location (location(100)),
    INDEX idx_companies_scraped_at (scraped_at),
    FULLTEXT INDEX ft_companies_search (company_name, founders, about, sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS logs (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_id      INT UNSIGNED DEFAULT NULL,
    level       ENUM('DEBUG','INFO','WARNING','ERROR','CRITICAL') NOT NULL DEFAULT 'INFO',
    message     TEXT NOT NULL,
    page        INT UNSIGNED DEFAULT NULL,
    company     VARCHAR(500) DEFAULT NULL,
    created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    INDEX idx_logs_job_id (job_id),
    INDEX idx_logs_level (level),
    INDEX idx_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- EXPORTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS exports (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    filename        VARCHAR(500) NOT NULL,
    file_type       ENUM('excel','csv') NOT NULL,
    file_path       VARCHAR(1000) NOT NULL,
    file_size       BIGINT UNSIGNED DEFAULT NULL COMMENT 'bytes',
    total_records   INT UNSIGNED DEFAULT NULL,
    job_id          INT UNSIGNED DEFAULT NULL,
    created_by      INT UNSIGNED DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_exports_file_type (file_type),
    INDEX idx_exports_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- SETTINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    key_name    VARCHAR(255) NOT NULL UNIQUE,
    value       TEXT DEFAULT NULL,
    description VARCHAR(1000) DEFAULT NULL,
    updated_by  INT UNSIGNED DEFAULT NULL,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_settings_key (key_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default settings
INSERT INTO settings (key_name, value, description) VALUES
('scraper_base_url',      'https://startuptn.in/ecosystem-info', 'Target scraper URL'),
('scraper_start_page',    '1',    'Default start page'),
('scraper_end_page',      '0',    'Default end page (0 = auto)'),
('scraper_workers',       '2',    'Default parallel workers'),
('scraper_delay_min',     '1.0',  'Minimum delay between requests (seconds)'),
('scraper_delay_max',     '3.0',  'Maximum delay between requests (seconds)'),
('scraper_retry_count',   '3',    'Number of retries on failure'),
('scraper_timeout',       '30',   'Page timeout in seconds'),
('scraper_headless',      'true', 'Run browser in headless mode'),
('notification_email',    '',     'Email to receive notifications'),
('notification_slack',    '',     'Slack webhook URL'),
('export_path',           '/app/exports', 'Directory to save export files')
ON DUPLICATE KEY UPDATE value=VALUES(value);
