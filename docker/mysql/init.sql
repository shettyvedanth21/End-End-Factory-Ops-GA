CREATE DATABASE IF NOT EXISTS factoryops;
USE factoryops;
-- Telemetry Service Tables (Factory, Device, Property)
CREATE TABLE IF NOT EXISTS factories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    settings JSON
);

CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), 
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    metadata JSON,
    FOREIGN KEY (factory_id) REFERENCES factories(id)
);

CREATE TABLE IF NOT EXISTS device_properties (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    property_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50),
    unit VARCHAR(20),
    FOREIGN KEY (device_id) REFERENCES devices(id),
    UNIQUE(device_id, property_name)
);

-- Rule Engine Service Tables (Rule, Alert)
CREATE TABLE IF NOT EXISTS rules (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    conditions JSON NOT NULL,
    condition_operator ENUM('AND', 'OR') DEFAULT 'AND',
    schedule_start VARCHAR(8),
    schedule_end VARCHAR(8),
    cooldown_seconds INT DEFAULT 300,
    auto_resolve BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (factory_id) REFERENCES factories(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    rule_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36) NOT NULL,
    status ENUM('open', 'acknowledged', 'resolved') DEFAULT 'open',
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    trigger_values JSON,
    FOREIGN KEY (rule_id) REFERENCES rules(id)
);

-- Analytics Service Tables (AnalyticsJob, AnalyticsModel)
CREATE TABLE IF NOT EXISTS analytics_jobs (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status ENUM('queued', 'running', 'completed', 'failed') DEFAULT 'queued',
    job_type ENUM('training', 'inference') NOT NULL,
    model_name VARCHAR(255),
    target_variable VARCHAR(255),
    features JSON,
    algorithm VARCHAR(50),
    hyperparameters JSON,
    data_range_start DATETIME,
    data_range_end DATETIME,
    device_ids JSON,
    dataset_s3_key VARCHAR(512),
    artifact_s3_prefix VARCHAR(512),
    metrics JSON,
    error_message VARCHAR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_models (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    version INT DEFAULT 1,
    description VARCHAR(1024),
    algorithm VARCHAR(50) NOT NULL,
    hyperparameters JSON,
    training_metrics JSON,
    s3_key VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_id VARCHAR(36),
    FOREIGN KEY (job_id) REFERENCES analytics_jobs(id)
);

-- Reporting Service Tables (Report)
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status ENUM('queued', 'generating', 'completed', 'failed') DEFAULT 'queued',
    type ENUM('energy', 'production', 'alerts', 'custom') NOT NULL,
    format ENUM('pdf', 'excel', 'json') DEFAULT 'pdf',
    time_range_start DATETIME NOT NULL,
    time_range_end DATETIME NOT NULL,
    device_ids JSON,
    include_analytics INT DEFAULT 0,
    s3_key VARCHAR(512),
    error_message VARCHAR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_at TIMESTAMP
);

-- Notification Service Tables (NotificationLog, User)
CREATE TABLE IF NOT EXISTS notification_logs (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36) NOT NULL,
    alert_id VARCHAR(36) NOT NULL,
    channel ENUM('email', 'whatsapp') NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message_body TEXT NOT NULL,
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    factory_id VARCHAR(36),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    role VARCHAR(50),
    FOREIGN KEY (factory_id) REFERENCES factories(id)
);

-- Seed defaults
INSERT INTO factories (id, name, industry, settings) VALUES 
('fct-001', 'Factory Alpha', 'Automotive', '{"timezone": "UTC"}');

INSERT INTO users (id, factory_id, email, phone_number, role) VALUES 
('usr-admin-1', 'fct-001', 'admin@factory-alpha.com', '+15550101', 'admin');
