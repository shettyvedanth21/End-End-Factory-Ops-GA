# FACTORYOPS AI ENGINEERING

## Enterprise Low-Level Design (LLD)

**Version:** 1.0  
**Date:** 2026-02-17  
**Based on HLD Version:** 1.0  
**Status:** Draft

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Database Schemas](#2-database-schemas)
3. [API Endpoint Specifications](#3-api-endpoint-specifications)
4. [Service Logic & Internal Flows](#4-service-logic--internal-flows)
5. [Security & Authentication Design](#5-security--authentication-design)
6. [MQTT & Telemetry Processing Detail](#6-mqtt--telemetry-processing-detail)
7. [Rule Engine Internals](#7-rule-engine-internals)
8. [Analytics Pipeline Detail](#8-analytics-pipeline-detail)
9. [Reporting Service Detail](#9-reporting-service-detail)
10. [Failure Handling Internals](#10-failure-handling-internals)
11. [Infrastructure & Deployment](#11-infrastructure--deployment)

---

## 1. Introduction

This Low-Level Design document translates the FactoryOps AI Engineering HLD into concrete implementation specifications. It defines exact database table schemas, full API contracts, inter-service communication flows, security enforcement mechanics, and error handling logic.

All designs conform to the five architectural principles established in the HLD: Factory-First Isolation, Firmware-Adaptive Telemetry, Event-Driven Processing, Asynchronous Analytics, and Open-Source Infrastructure.

---

## 2. Database Schemas

### 2.1 MySQL — Relational Store

MySQL serves as the source of truth for structured metadata: users, devices, rules, alerts, analytics results, and reports. Every tenant-scoped table includes a `factory_id` column that is enforced at both application and query level.

---

#### 2.1.1 `factories`

Stores top-level factory entities, created and managed by Platform Root only.

```sql
CREATE TABLE factories (
    id            VARCHAR(36)   NOT NULL PRIMARY KEY,  -- UUID
    name          VARCHAR(255)  NOT NULL,
    slug          VARCHAR(100)  NOT NULL UNIQUE,
    timezone      VARCHAR(64)   NOT NULL DEFAULT 'UTC',
    is_active     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

#### 2.1.2 `users`

All users belong to exactly one factory. Platform Root users have `factory_id = NULL`.

```sql
CREATE TABLE users (
    id              VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id      VARCHAR(36)   NULL,          -- NULL for Platform Root
    email           VARCHAR(255)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,       -- bcrypt
    role            ENUM('platform_root','super_admin','admin') NOT NULL,
    can_write       BOOLEAN       NOT NULL DEFAULT FALSE,  -- for admin role
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    last_login_at   DATETIME      NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    INDEX idx_users_factory (factory_id)
);
```

---

#### 2.1.3 `devices`

Static device metadata. Dynamic telemetry values are stored in InfluxDB only.

```sql
CREATE TABLE devices (
    id            VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id    VARCHAR(36)   NOT NULL,
    name          VARCHAR(255)  NOT NULL,
    type          VARCHAR(100)  NOT NULL,
    location      VARCHAR(255)  NULL,
    status        ENUM('active','inactive','maintenance') NOT NULL DEFAULT 'active',
    last_seen_at  DATETIME      NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_devices_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    INDEX idx_devices_factory (factory_id),
    INDEX idx_devices_status (factory_id, status)
);
```

---

#### 2.1.4 `device_properties`

Auto-discovered firmware metrics registered when first seen. Records are never deleted to preserve historical integrity.

```sql
CREATE TABLE device_properties (
    id              VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id      VARCHAR(36)   NOT NULL,
    device_id       VARCHAR(36)   NOT NULL,
    property_name   VARCHAR(255)  NOT NULL,
    unit            VARCHAR(50)   NULL,
    data_type       ENUM('float','integer','boolean','string') NOT NULL DEFAULT 'float',
    first_seen_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_dp_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    CONSTRAINT fk_dp_device  FOREIGN KEY (device_id)  REFERENCES devices(id),
    UNIQUE KEY uq_dp_device_property (device_id, property_name),
    INDEX idx_dp_factory (factory_id)
);
```

---

#### 2.1.5 `rules`

Rule definitions with multi-condition logic and schedule support.

```sql
CREATE TABLE rules (
    id                  VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id          VARCHAR(36)   NOT NULL,
    device_id           VARCHAR(36)   NOT NULL,
    name                VARCHAR(255)  NOT NULL,
    description         TEXT          NULL,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    conditions          JSON          NOT NULL,  -- array of condition objects (see note)
    condition_operator  ENUM('AND','OR') NOT NULL DEFAULT 'AND',
    schedule_start      TIME          NULL,      -- NULL = always active
    schedule_end        TIME          NULL,
    cooldown_seconds    INT           NOT NULL DEFAULT 300,
    auto_resolve        BOOLEAN       NOT NULL DEFAULT FALSE,
    created_by          VARCHAR(36)   NOT NULL,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_rules_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    CONSTRAINT fk_rules_device  FOREIGN KEY (device_id)  REFERENCES devices(id),
    INDEX idx_rules_factory_device (factory_id, device_id),
    INDEX idx_rules_active (factory_id, is_active)
);

-- conditions JSON structure example:
-- [
--   { "property": "temperature", "operator": "GT", "threshold": 85.0 },
--   { "property": "pressure",    "operator": "LT", "threshold": 10.0 }
-- ]
-- Supported operators: GT, LT, GTE, LTE, EQ, NEQ
```

---

#### 2.1.6 `alerts`

Tracks open, acknowledged, and resolved alert lifecycle per rule.

```sql
CREATE TABLE alerts (
    id                  VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id          VARCHAR(36)   NOT NULL,
    rule_id             VARCHAR(36)   NOT NULL,
    device_id           VARCHAR(36)   NOT NULL,
    status              ENUM('open','acknowledged','resolved') NOT NULL DEFAULT 'open',
    triggered_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at     DATETIME      NULL,
    acknowledged_by     VARCHAR(36)   NULL,
    resolved_at         DATETIME      NULL,
    trigger_values      JSON          NULL,  -- snapshot of property values at trigger time
    notes               TEXT          NULL,

    CONSTRAINT fk_alerts_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    CONSTRAINT fk_alerts_rule    FOREIGN KEY (rule_id)    REFERENCES rules(id),
    INDEX idx_alerts_factory_status (factory_id, status),
    INDEX idx_alerts_rule (rule_id),
    INDEX idx_alerts_triggered (factory_id, triggered_at)
);
```

---

#### 2.1.7 `notification_logs`

Audit trail for all outbound notifications.

```sql
CREATE TABLE notification_logs (
    id              VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id      VARCHAR(36)   NOT NULL,
    alert_id        VARCHAR(36)   NOT NULL,
    channel         ENUM('email','whatsapp') NOT NULL,
    recipient       VARCHAR(255)  NOT NULL,
    status          ENUM('sent','failed','pending') NOT NULL DEFAULT 'pending',
    sent_at         DATETIME      NULL,
    error_message   TEXT          NULL,
    retry_count     INT           NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notif_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    CONSTRAINT fk_notif_alert   FOREIGN KEY (alert_id)   REFERENCES alerts(id),
    INDEX idx_notif_factory (factory_id),
    INDEX idx_notif_alert (alert_id)
);
```

---

#### 2.1.8 `analytics_jobs`

Tracks lifecycle and metadata for each analytics execution.

```sql
CREATE TABLE analytics_jobs (
    id                  VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id          VARCHAR(36)   NOT NULL,
    name                VARCHAR(255)  NOT NULL,
    mode                ENUM('standard','ai_copilot') NOT NULL,
    analysis_type       VARCHAR(100)  NOT NULL,   -- e.g. "anomaly_detection", "forecast"
    status              ENUM('queued','running','completed','failed') NOT NULL DEFAULT 'queued',
    model_name          VARCHAR(255)  NULL,
    model_version       VARCHAR(50)   NULL,
    dataset_s3_key      VARCHAR(512)  NULL,
    artifact_s3_prefix  VARCHAR(512)  NULL,
    hyperparameters     JSON          NULL,
    metrics             JSON          NULL,
    error_message       TEXT          NULL,
    started_at          DATETIME      NULL,
    completed_at        DATETIME      NULL,
    created_by          VARCHAR(36)   NOT NULL,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_jobs_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    INDEX idx_jobs_factory_status (factory_id, status),
    INDEX idx_jobs_factory_created (factory_id, created_at)
);
```

---

#### 2.1.9 `analytics_models`

Registry of reusable trained models.

```sql
CREATE TABLE analytics_models (
    id                  VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id          VARCHAR(36)   NOT NULL,
    name                VARCHAR(255)  NOT NULL,
    version             VARCHAR(50)   NOT NULL,
    analysis_type       VARCHAR(100)  NOT NULL,
    source_job_id       VARCHAR(36)   NOT NULL,
    artifact_s3_key     VARCHAR(512)  NOT NULL,
    hyperparameters     JSON          NULL,
    metrics             JSON          NULL,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_models_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    UNIQUE KEY uq_model_version (factory_id, name, version),
    INDEX idx_models_factory (factory_id)
);
```

---

#### 2.1.10 `reports`

Tracks generated report requests and their output locations.

```sql
CREATE TABLE reports (
    id              VARCHAR(36)   NOT NULL PRIMARY KEY,
    factory_id      VARCHAR(36)   NOT NULL,
    name            VARCHAR(255)  NOT NULL,
    type            ENUM('energy','alerts','analytics','custom') NOT NULL,
    format          ENUM('pdf','excel','json') NOT NULL,
    status          ENUM('queued','generating','completed','failed') NOT NULL DEFAULT 'queued',
    s3_key          VARCHAR(512)  NULL,
    period_start    DATETIME      NOT NULL,
    period_end      DATETIME      NOT NULL,
    parameters      JSON          NULL,
    error_message   TEXT          NULL,
    generated_at    DATETIME      NULL,
    created_by      VARCHAR(36)   NOT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reports_factory FOREIGN KEY (factory_id) REFERENCES factories(id),
    INDEX idx_reports_factory_status (factory_id, status),
    INDEX idx_reports_factory_created (factory_id, created_at)
);
```

---

#### 2.1.11 `audit_logs`

Immutable ledger for all significant system actions.

```sql
CREATE TABLE audit_logs (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    factory_id      VARCHAR(36)   NULL,
    user_id         VARCHAR(36)   NULL,
    action          VARCHAR(100)  NOT NULL,  -- e.g. "user.created", "rule.updated"
    entity_type     VARCHAR(100)  NULL,
    entity_id       VARCHAR(36)   NULL,
    payload         JSON          NULL,
    ip_address      VARCHAR(45)   NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_factory (factory_id),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_created (created_at)
);
```

---

### 2.2 InfluxDB — Time-Series Store

InfluxDB stores all telemetry. There is a single measurement `device_metrics`. Schema is firmware-driven; no migration is required when new metrics appear.

**Measurement:** `device_metrics`

| Component      | Name            | Type   | Description                        |
|----------------|-----------------|--------|------------------------------------|
| Tag            | `factory_id`    | string | Factory namespace for isolation    |
| Tag            | `device_id`     | string | Device identifier                  |
| Tag            | `property_name` | string | Firmware-defined metric name       |
| Field          | `value`         | float  | Numeric reading                    |
| Timestamp      | `_time`         | time   | Nanosecond precision ingest time   |

**Example write (Line Protocol):**
```
device_metrics,factory_id=fct-001,device_id=dev-abc,property_name=temperature value=87.4 1708173600000000000
```

**Retention policy:**  
Default: 90 days at full resolution. Downsampled 1h aggregates retained for 2 years via InfluxDB continuous queries.

**Example query (Flux):**
```flux
from(bucket: "factoryops")
  |> range(start: -1h)
  |> filter(fn: (r) => r.factory_id == "fct-001" and r.device_id == "dev-abc" and r.property_name == "temperature")
  |> mean()
```

---

### 2.3 MinIO — Object Storage

Objects are organized under a strict path hierarchy to enforce factory-level isolation.

| Path Pattern                                                    | Content                        |
|-----------------------------------------------------------------|--------------------------------|
| `factoryops/{factory_id}/datasets/{job_id}/dataset.parquet`    | Exported analytics dataset     |
| `factoryops/{factory_id}/analytics/{job_id}/model.pkl`         | Serialized model artifact      |
| `factoryops/{factory_id}/analytics/{job_id}/results.json`      | Analytics output summary       |
| `factoryops/{factory_id}/reports/{report_id}/report.pdf`       | Generated PDF report           |
| `factoryops/{factory_id}/reports/{report_id}/report.xlsx`      | Generated Excel report         |

All bucket access is enforced via per-factory IAM policies. No service may access a path unless its session carries the matching `factory_id`.

---

## 3. API Endpoint Specifications

All API routes are prefixed with `/api/v1`. All requests require a valid JWT in the `Authorization: Bearer <token>` header unless marked as public. Every response follows a consistent envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "RULE_NOT_FOUND",
    "message": "No rule found with the given ID in this factory."
  }
}
```

---

### 3.1 Authentication

#### `POST /api/v1/auth/login`

Authenticates a user against a specific factory context. No JWT required.

**Request:**
```json
{
  "factory_slug": "plant-munich",
  "email": "operator@plant-munich.com",
  "password": "SecurePassword123"
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": "usr-001",
      "email": "operator@plant-munich.com",
      "role": "admin",
      "factory_id": "fct-001",
      "can_write": true
    }
  }
}
```

**Error `401 Unauthorized`:**
```json
{
  "success": false,
  "error": { "code": "INVALID_CREDENTIALS", "message": "Invalid email or password." }
}
```

---

#### `POST /api/v1/auth/logout`

Invalidates the session token server-side (added to deny-list).

**Response `200 OK`:**
```json
{ "success": true, "data": { "message": "Logged out successfully." } }
```

---

#### `GET /api/v1/auth/me`

Returns the authenticated user's profile.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "usr-001",
    "email": "operator@plant-munich.com",
    "role": "admin",
    "factory_id": "fct-001",
    "can_write": true,
    "last_login_at": "2026-02-17T12:00:00Z"
  }
}
```

---

### 3.2 Factory Management (Platform Root Only)

#### `POST /api/v1/platform/factories`

Creates a new factory.

**Request:**
```json
{
  "name": "Plant Munich",
  "slug": "plant-munich",
  "timezone": "Europe/Berlin"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "fct-001",
    "name": "Plant Munich",
    "slug": "plant-munich",
    "timezone": "Europe/Berlin",
    "is_active": true,
    "created_at": "2026-02-17T14:00:00Z"
  }
}
```

---

#### `POST /api/v1/platform/factories/{factory_id}/admins`

Assigns a Super Admin to a factory.

**Request:**
```json
{
  "email": "admin@plant-munich.com",
  "password": "InitialPass456"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "usr-002",
    "email": "admin@plant-munich.com",
    "role": "super_admin",
    "factory_id": "fct-001"
  }
}
```

---

### 3.3 User Management (Super Admin Only)

#### `GET /api/v1/users`

Returns all users in the authenticated factory.

**Query Params:** `?role=admin&is_active=true&page=1&per_page=20`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "usr-001",
        "email": "operator@plant-munich.com",
        "role": "admin",
        "can_write": true,
        "is_active": true,
        "last_login_at": "2026-02-17T12:00:00Z"
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 1 }
  }
}
```

---

#### `POST /api/v1/users`

Creates a new Admin user in the factory.

**Request:**
```json
{
  "email": "new.operator@plant-munich.com",
  "password": "SecurePass789",
  "role": "admin",
  "can_write": false
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "usr-010",
    "email": "new.operator@plant-munich.com",
    "role": "admin",
    "can_write": false,
    "factory_id": "fct-001"
  }
}
```

---

#### `PATCH /api/v1/users/{user_id}`

Updates user attributes (e.g. toggle write permission).

**Request:**
```json
{
  "can_write": true,
  "is_active": false
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "usr-010",
    "can_write": true,
    "is_active": false,
    "updated_at": "2026-02-17T15:00:00Z"
  }
}
```

---

### 3.4 Device Management

#### `GET /api/v1/devices`

Lists all devices in the factory.

**Query Params:** `?status=active&type=compressor&page=1&per_page=20`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "dev-abc",
        "name": "Compressor Unit A",
        "type": "compressor",
        "location": "Hall B",
        "status": "active",
        "last_seen_at": "2026-02-17T14:59:00Z"
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 1 }
  }
}
```

---

#### `POST /api/v1/devices`

Registers a new device.

**Request:**
```json
{
  "id": "dev-abc",
  "name": "Compressor Unit A",
  "type": "compressor",
  "location": "Hall B"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "dev-abc",
    "factory_id": "fct-001",
    "name": "Compressor Unit A",
    "type": "compressor",
    "location": "Hall B",
    "status": "active",
    "created_at": "2026-02-17T14:00:00Z"
  }
}
```

---

#### `GET /api/v1/devices/{device_id}/properties`

Lists all auto-discovered telemetry properties for a device.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": "prop-001",
      "property_name": "temperature",
      "unit": "°C",
      "data_type": "float",
      "first_seen_at": "2026-01-01T00:00:00Z",
      "last_seen_at": "2026-02-17T14:59:00Z"
    },
    {
      "id": "prop-002",
      "property_name": "pressure",
      "unit": "bar",
      "data_type": "float",
      "first_seen_at": "2026-01-01T00:00:00Z",
      "last_seen_at": "2026-02-17T14:59:00Z"
    }
  ]
}
```

---

#### `GET /api/v1/devices/{device_id}/telemetry`

Fetches time-series telemetry data from InfluxDB for a device.

**Query Params:** `?property=temperature&start=2026-02-17T00:00:00Z&end=2026-02-17T14:00:00Z&aggregation=mean&window=5m`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "device_id": "dev-abc",
    "property": "temperature",
    "unit": "°C",
    "aggregation": "mean",
    "window": "5m",
    "points": [
      { "timestamp": "2026-02-17T00:00:00Z", "value": 72.4 },
      { "timestamp": "2026-02-17T00:05:00Z", "value": 73.1 }
    ]
  }
}
```

---

### 3.5 Rule Engine

#### `GET /api/v1/rules`

Lists rules for the factory.

**Query Params:** `?device_id=dev-abc&is_active=true&page=1&per_page=20`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "rule-001",
        "device_id": "dev-abc",
        "name": "High Temperature Alert",
        "is_active": true,
        "condition_operator": "AND",
        "conditions": [
          { "property": "temperature", "operator": "GT", "threshold": 85.0 }
        ],
        "cooldown_seconds": 300,
        "auto_resolve": true
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 1 }
  }
}
```

---

#### `POST /api/v1/rules`

Creates a new rule.

**Request:**
```json
{
  "device_id": "dev-abc",
  "name": "High Temperature Alert",
  "description": "Triggers when temperature exceeds 85°C",
  "conditions": [
    { "property": "temperature", "operator": "GT", "threshold": 85.0 }
  ],
  "condition_operator": "AND",
  "schedule_start": "06:00:00",
  "schedule_end": "22:00:00",
  "cooldown_seconds": 300,
  "auto_resolve": true
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "rule-001",
    "factory_id": "fct-001",
    "device_id": "dev-abc",
    "name": "High Temperature Alert",
    "is_active": true,
    "conditions": [
      { "property": "temperature", "operator": "GT", "threshold": 85.0 }
    ],
    "condition_operator": "AND",
    "schedule_start": "06:00:00",
    "schedule_end": "22:00:00",
    "cooldown_seconds": 300,
    "auto_resolve": true,
    "created_at": "2026-02-17T14:00:00Z"
  }
}
```

---

#### `PATCH /api/v1/rules/{rule_id}`

Updates a rule (e.g. toggle active state, change thresholds).

**Request:**
```json
{
  "is_active": false,
  "cooldown_seconds": 600
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "rule-001",
    "is_active": false,
    "cooldown_seconds": 600,
    "updated_at": "2026-02-17T15:00:00Z"
  }
}
```

---

#### `DELETE /api/v1/rules/{rule_id}`

Soft-deletes a rule (sets `is_active = false`, retains audit history).

**Response `200 OK`:**
```json
{ "success": true, "data": { "message": "Rule deactivated." } }
```

---

### 3.6 Alert Management

#### `GET /api/v1/alerts`

Fetches alerts for the factory.

**Query Params:** `?status=open&device_id=dev-abc&start=2026-02-17T00:00:00Z&page=1&per_page=20`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "alert-001",
        "rule_id": "rule-001",
        "device_id": "dev-abc",
        "status": "open",
        "triggered_at": "2026-02-17T10:00:00Z",
        "trigger_values": { "temperature": 88.2 },
        "acknowledged_at": null,
        "resolved_at": null
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 1 }
  }
}
```

---

#### `PATCH /api/v1/alerts/{alert_id}/acknowledge`

Marks an alert as acknowledged.

**Request:**
```json
{
  "notes": "Maintenance team dispatched."
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "alert-001",
    "status": "acknowledged",
    "acknowledged_at": "2026-02-17T10:15:00Z",
    "acknowledged_by": "usr-001"
  }
}
```

---

#### `PATCH /api/v1/alerts/{alert_id}/resolve`

Manually resolves an alert.

**Request:**
```json
{
  "notes": "Temperature returned to safe range after maintenance."
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "alert-001",
    "status": "resolved",
    "resolved_at": "2026-02-17T11:00:00Z"
  }
}
```

---

### 3.7 Analytics

#### `GET /api/v1/analytics/jobs`

Lists analytics jobs for the factory.

**Query Params:** `?status=completed&mode=ai_copilot&page=1&per_page=20`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "job-001",
        "name": "February Anomaly Detection",
        "mode": "ai_copilot",
        "analysis_type": "anomaly_detection",
        "status": "completed",
        "model_name": "IsolationForest",
        "model_version": "1.0",
        "metrics": { "precision": 0.94, "recall": 0.88 },
        "started_at": "2026-02-17T10:00:00Z",
        "completed_at": "2026-02-17T10:12:00Z"
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 1 }
  }
}
```

---

#### `POST /api/v1/analytics/jobs`

Submits a new analytics job.

**Request:**
```json
{
  "name": "February Anomaly Detection",
  "mode": "standard",
  "analysis_type": "anomaly_detection",
  "device_ids": ["dev-abc", "dev-def"],
  "properties": ["temperature", "pressure"],
  "period_start": "2026-02-01T00:00:00Z",
  "period_end": "2026-02-17T00:00:00Z",
  "model_name": "IsolationForest",
  "hyperparameters": {
    "n_estimators": 100,
    "contamination": 0.05
  }
}
```

**Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "id": "job-002",
    "status": "queued",
    "created_at": "2026-02-17T14:00:00Z"
  }
}
```

---

#### `GET /api/v1/analytics/jobs/{job_id}`

Gets full detail of a job including results.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "job-001",
    "name": "February Anomaly Detection",
    "status": "completed",
    "model_name": "IsolationForest",
    "model_version": "1.0",
    "dataset_s3_key": "factoryops/fct-001/datasets/job-001/dataset.parquet",
    "artifact_s3_prefix": "factoryops/fct-001/analytics/job-001/",
    "hyperparameters": { "n_estimators": 100, "contamination": 0.05 },
    "metrics": { "precision": 0.94, "recall": 0.88, "f1_score": 0.91 },
    "started_at": "2026-02-17T10:00:00Z",
    "completed_at": "2026-02-17T10:12:00Z"
  }
}
```

---

#### `GET /api/v1/analytics/models`

Lists reusable trained models in the factory.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": "model-001",
      "name": "IsolationForest",
      "version": "1.0",
      "analysis_type": "anomaly_detection",
      "source_job_id": "job-001",
      "is_active": true,
      "metrics": { "precision": 0.94 }
    }
  ]
}
```

---

### 3.8 Reporting

#### `POST /api/v1/reports`

Queues a new report for generation.

**Request:**
```json
{
  "name": "February Energy Summary",
  "type": "energy",
  "format": "pdf",
  "period_start": "2026-02-01T00:00:00Z",
  "period_end": "2026-02-28T23:59:59Z",
  "parameters": {
    "device_ids": ["dev-abc", "dev-def"],
    "include_alerts": true,
    "include_analytics": true
  }
}
```

**Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "id": "rpt-001",
    "status": "queued",
    "created_at": "2026-02-17T14:00:00Z"
  }
}
```

---

#### `GET /api/v1/reports/{report_id}`

Returns status and download info for a report.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "rpt-001",
    "name": "February Energy Summary",
    "status": "completed",
    "format": "pdf",
    "download_url": "https://minio.internal/factoryops/fct-001/reports/rpt-001/report.pdf",
    "download_expires_at": "2026-02-17T16:00:00Z",
    "generated_at": "2026-02-17T14:05:00Z"
  }
}
```

---

## 4. Service Logic & Internal Flows

### 4.1 Telemetry Ingestion Flow

This flow begins the moment a device publishes a message to EMQX and ends when the value is written to InfluxDB, the device is updated in MySQL, and rule evaluation is triggered.

```
Device
  │  PUBLISH factories/fct-001/devices/dev-abc/telemetry
  ▼
EMQX Broker (QoS 1)
  │  Delivers to subscriber
  ▼
Telemetry Service
  │
  ├─ 1. Parse topic → extract factory_id, device_id
  ├─ 2. Parse JSON payload
  │       { "temperature": 87.4, "pressure": 9.8, "rpm": 1450.0 }
  │
  ├─ 3. For each property in payload:
  │       a. Check device_properties cache (Redis or in-memory TTL)
  │       b. If unknown property → call Property Registry Service
  │             → INSERT into device_properties (ignore if exists)
  │             → broadcast property.registered event
  │       c. Write to InfluxDB (batch buffer, flush every 500ms or 100 points)
  │
  ├─ 4. UPDATE devices.last_seen_at = NOW() (async, debounced per device)
  │
  └─ 5. Publish internal event to Rule Engine queue:
         {
           "factory_id": "fct-001",
           "device_id": "dev-abc",
           "properties": { "temperature": 87.4, "pressure": 9.8, "rpm": 1450.0 },
           "timestamp": "2026-02-17T14:00:00Z"
         }
```

**Payload format (device publishes):**
```json
{
  "temperature": 87.4,
  "pressure": 9.8,
  "rpm": 1450.0
}
```

---

### 4.2 Rule Evaluation Flow

Triggered per telemetry event. No polling. No historical scans.

```
Rule Engine Worker (consumes from internal event queue)
  │
  ├─ 1. Load active rules for factory_id + device_id
  │       (cached with TTL 30s; invalidated on rule create/update)
  │
  ├─ 2. For each rule:
  │       a. Evaluate schedule window (schedule_start ≤ NOW ≤ schedule_end)
  │          → skip rule if outside window
  │
  │       b. Evaluate conditions against incoming property values:
  │          For each condition { property, operator, threshold }:
  │            - If property missing from payload → condition = FALSE
  │            - Evaluate: GT | LT | GTE | LTE | EQ | NEQ
  │          Apply condition_operator (AND / OR) across all results
  │
  │       c. If result = TRUE:
  │            - Check cooldown: is there an OPEN alert for this rule
  │              created within the last cooldown_seconds?
  │            - If in cooldown → skip
  │            - If not in cooldown:
  │                → INSERT new alert (status = 'open', trigger_values = payload snapshot)
  │                → Publish to Notification Queue:
  │                   { alert_id, rule, factory_id, trigger_values }
  │
  │       d. If result = FALSE and auto_resolve = TRUE:
  │            - Fetch most recent OPEN alert for this rule
  │            - If found → UPDATE status = 'resolved', resolved_at = NOW()
  │
  └─ Done (entire evaluation < 500ms target)
```

---

### 4.3 Notification Dispatch Flow

```
Notification Worker (consumes from Notification Queue)
  │
  ├─ 1. Fetch alert + rule + factory notification config
  │
  ├─ 2. For each configured notification channel (email / whatsapp):
  │       a. Build message body from template + trigger_values
  │       b. INSERT notification_log (status = 'pending')
  │       c. Dispatch:
  │            - Email → SMTP (smtplib or external relay)
  │            - WhatsApp → Twilio API
  │       d. On success:
  │            - UPDATE notification_log (status = 'sent', sent_at = NOW())
  │       e. On failure:
  │            - UPDATE notification_log (status = 'failed', error_message = ...)
  │            - Increment retry_count
  │            - If retry_count < 3 → re-enqueue with exponential backoff
  │            - If retry_count >= 3 → log to system health, no further retry
  │
  └─ Notification failure never blocks ingestion or rule evaluation
```

---

### 4.4 Analytics Job Lifecycle

```
User triggers POST /api/v1/analytics/jobs
  │
  ├─ API Service validates request + factory scope
  ├─ INSERT analytics_jobs (status = 'queued')
  ├─ Publish job_id to Analytics Queue
  │
Analytics Worker (picks up job)
  │
  ├─ 1. UPDATE status = 'running', started_at = NOW()
  │
  ├─ 2. Data Export Phase:
  │       - Query InfluxDB with factory_id + device_ids + properties + time range
  │       - Convert to Parquet format
  │       - Upload to MinIO: factoryops/{factory_id}/datasets/{job_id}/dataset.parquet
  │       - UPDATE analytics_jobs.dataset_s3_key
  │
  ├─ 3. Model Selection:
  │       - Standard mode: use model_name + hyperparameters from request
  │       - AI Co-Pilot mode:
  │           → Auto-detect analysis type from data characteristics
  │           → Grid search or Optuna for hyperparameter tuning
  │           → Select best model by cross-validation score
  │
  ├─ 4. Model Execution:
  │       - Load dataset from MinIO
  │       - Train / run inference
  │       - Produce results.json + model artifact
  │
  ├─ 5. Artifact Upload:
  │       - Upload model.pkl → factoryops/{factory_id}/analytics/{job_id}/model.pkl
  │       - Upload results.json → factoryops/{factory_id}/analytics/{job_id}/results.json
  │
  ├─ 6. Registry:
  │       - INSERT analytics_models (if new version)
  │
  ├─ 7. UPDATE analytics_jobs:
  │       status = 'completed'
  │       model_name, model_version, metrics, artifact_s3_prefix, completed_at
  │
  └─ On any exception:
       UPDATE analytics_jobs (status = 'failed', error_message = ...)
       Dataset is preserved for retry.
```

---

### 4.5 Report Generation Flow

```
User triggers POST /api/v1/reports
  │
  ├─ INSERT reports (status = 'queued')
  ├─ Publish report_id to Report Queue
  │
Report Worker (picks up job)
  │
  ├─ 1. UPDATE status = 'generating'
  │
  ├─ 2. Data Assembly:
  │       - Query InfluxDB aggregates for energy metrics
  │       - Query MySQL alerts (filtered by device + time range)
  │       - Query MySQL analytics_jobs results (if include_analytics = true)
  │
  ├─ 3. Render:
  │       - PDF  → WeasyPrint or ReportLab (HTML → PDF pipeline)
  │       - Excel → openpyxl
  │       - JSON → serialized data dump
  │
  ├─ 4. Upload to MinIO: factoryops/{factory_id}/reports/{report_id}/report.{ext}
  │
  ├─ 5. Generate pre-signed download URL (TTL: 2 hours)
  │
  └─ 6. UPDATE reports:
         status = 'completed', s3_key = ..., generated_at = NOW()
```

---

## 5. Security & Authentication Design

### 5.1 JWT Token Structure

Every token is signed with HS256 using a server-side secret (minimum 256-bit). Tokens expire after 24 hours.

**JWT Payload:**
```json
{
  "sub": "usr-001",
  "factory_id": "fct-001",
  "role": "admin",
  "can_write": true,
  "iat": 1708173600,
  "exp": 1708260000,
  "jti": "unique-token-id-for-deny-list"
}
```

**Token deny-list:** On logout or admin-forced revocation, the `jti` is stored in Redis with TTL matching remaining token lifetime. All authenticated middleware checks the deny-list before accepting a request.

---

### 5.2 Middleware Enforcement Chain

Every incoming API request passes through the following middleware layers in order:

```
Request
  │
  ├─ 1. TLS Termination (enforced at load balancer / nginx)
  │
  ├─ 2. JWT Validation Middleware
  │       - Verify signature
  │       - Check expiration
  │       - Check jti deny-list in Redis
  │       → 401 if any check fails
  │
  ├─ 3. Factory Context Middleware
  │       - Extract factory_id from JWT
  │       - Attach factory context to request object
  │       → All downstream DB queries use this factory_id
  │
  ├─ 4. Role & Permission Middleware
  │       - Route-level decorators define: required_role, requires_write
  │       - Platform Root: access to /platform/* only
  │       - Super Admin: full factory access
  │       - Admin: read always; write only if can_write = true
  │       → 403 if insufficient permissions
  │
  └─ 5. Request Handler
```

---

### 5.3 Password Security

- Passwords are hashed with **bcrypt**, cost factor **12**.
- Plaintext passwords are never logged or stored.
- Password reset requires a time-limited token (TTL: 1 hour) sent to the registered email.
- Minimum password requirements: 10 characters, at least one uppercase, one number, one special character.

---

### 5.4 Cross-Factory Isolation Enforcement

Factory isolation is enforced at every layer. There is no reliance on frontend-only filtering.

| Layer          | Mechanism                                                        |
|----------------|------------------------------------------------------------------|
| MQTT           | Topic path carries `factory_id`; EMQX ACL rules enforce it      |
| API Middleware | `factory_id` bound from JWT, never from request body            |
| MySQL Queries  | Every query includes `WHERE factory_id = :factory_id`           |
| InfluxDB       | Every query filtered by `factory_id` tag                        |
| MinIO          | Path prefix `factoryops/{factory_id}/` enforced by IAM policy   |
| Audit Logs     | Every write action records `factory_id` + `user_id`             |

---

### 5.5 TLS Configuration

- All external-facing services use TLS 1.2+ (TLS 1.3 preferred).
- Self-signed certificates for internal service-to-service communication in development.
- Production: certificates from a trusted CA, renewed automatically via Let's Encrypt or internal PKI.
- EMQX listeners use TLS for MQTT over TCP (port 8883) and MQTT over WebSocket (port 8084).

---

### 5.6 EMQX ACL Rules

EMQX enforces publish and subscribe permissions at the MQTT level. Rules are scoped by `factory_id` embedded in the topic.

```
# Allow devices to publish telemetry only to their own factory/device topic
allow publish: factories/{factory_id}/devices/{device_id}/telemetry
# Allow Telemetry Service to subscribe to all factory telemetry
allow subscribe: factories/+/devices/+/telemetry
# Deny all other patterns
deny all
```

Device credentials are provisioned per device with username = `device_id` and factory-scoped password.

---

## 6. MQTT & Telemetry Processing Detail

### 6.1 Topic Structure

```
factories/{factory_id}/devices/{device_id}/telemetry
```

Example:
```
factories/fct-001/devices/dev-abc/telemetry
```

### 6.2 Payload Schema (Device → Broker)

Devices publish a flat JSON object. All keys are firmware-defined property names. Values must be numeric (float/integer) or boolean.

```json
{
  "temperature": 87.4,
  "pressure": 9.8,
  "rpm": 1450,
  "vibration_x": 0.012,
  "fault_flag": false
}
```

Malformed payloads (non-JSON, invalid types) are rejected at parse time. The rejection is logged, and the device's error count is incremented. No partial writes occur.

### 6.3 InfluxDB Write Buffer

The Telemetry Service does not write one point per message. Instead:

- Points are accumulated in an in-memory buffer.
- Flush is triggered when: buffer reaches 100 points OR 500ms have elapsed (whichever comes first).
- On InfluxDB write failure, the buffer is persisted to a local file queue and retried with exponential backoff (1s → 2s → 4s → max 60s).
- System health alert is raised if write failures persist beyond 5 minutes.

---

## 7. Rule Engine Internals

### 7.1 Condition Operators

| Operator | Meaning                  |
|----------|--------------------------|
| `GT`     | Greater than             |
| `LT`     | Less than                |
| `GTE`    | Greater than or equal    |
| `LTE`    | Less than or equal       |
| `EQ`     | Equal (float tolerance ±0.001) |
| `NEQ`    | Not equal                |

### 7.2 Rule Cache Strategy

Rules are cached in-process (or Redis for multi-instance deployments) with a 30-second TTL keyed by `{factory_id}:{device_id}`. Cache is proactively invalidated whenever a rule is created, updated, or deleted via the API.

### 7.3 Cooldown Logic

For each rule that evaluates to TRUE:

1. Query `alerts` table: `WHERE rule_id = :rule_id AND status = 'open' AND triggered_at > NOW() - INTERVAL :cooldown_seconds SECOND`
2. If a recent alert exists → skip creating a new one.
3. If no recent alert → create a new alert.

This prevents alert storms on rapidly-fluctuating sensor readings.

---

## 8. Analytics Pipeline Detail

### 8.1 Supported Analysis Types

| Analysis Type        | Default Models                          | AI Co-Pilot Candidates                         |
|----------------------|-----------------------------------------|------------------------------------------------|
| `anomaly_detection`  | IsolationForest, LOF                   | IsolationForest, AutoEncoder, OneClassSVM       |
| `forecast`           | Prophet, ARIMA                          | Prophet, LSTM, XGBoost                         |
| `classification`     | RandomForest, LogisticRegression        | RandomForest, XGBoost, SVM                     |
| `clustering`         | KMeans, DBSCAN                          | KMeans, Hierarchical, DBSCAN                   |
| `energy_baseline`    | Linear Regression, Moving Average       | Polynomial Regression, LightGBM                |

### 8.2 AI Co-Pilot Auto-Selection Logic

```
1. Profile the dataset:
     - n_samples, n_features, missing_rate, stationarity test
2. If analysis_type = 'anomaly_detection':
     - If n_samples > 10,000 → IsolationForest
     - If n_samples ≤ 10,000 → LOF or OneClassSVM
3. Run Optuna with n_trials=30 to tune hyperparameters
4. Select model with best cross-validation score
5. Log selected model + hyperparameters to analytics_jobs
```

### 8.3 Dataset Immutability

Once a dataset Parquet file is written to MinIO, it is never modified. If a job fails and is retried, the existing dataset is reused (unless explicitly re-exported). This ensures reproducibility of analytics results.

---

## 9. Reporting Service Detail

### 9.1 Data Sources per Report Type

| Report Type  | InfluxDB Aggregates | MySQL Alerts | MySQL Analytics |
|--------------|---------------------|--------------|-----------------|
| `energy`     | ✅                   | Optional     | Optional        |
| `alerts`     | ❌                   | ✅            | ❌               |
| `analytics`  | Optional            | Optional     | ✅               |
| `custom`     | Optional            | Optional     | Optional        |

### 9.2 PDF Generation Pipeline

```
Data Assembly (Python dicts + DataFrames)
  │
  ▼
Jinja2 HTML Template Rendering
  │  (charts embedded as base64 PNG via matplotlib/Plotly)
  ▼
WeasyPrint → PDF bytes
  │
  ▼
MinIO Upload
```

### 9.3 Excel Generation Pipeline

```
Data Assembly
  │
  ▼
openpyxl Workbook
  │  - Sheet per data section
  │  - Auto-column widths
  │  - Conditional formatting on alert severity
  ▼
MinIO Upload
```

---

## 10. Failure Handling Internals

### 10.1 MQTT Reconnection Strategy

```python
# Pseudocode — Telemetry Service MQTT client
backoff = 1  # seconds
max_backoff = 60
while not connected:
    try:
        client.connect(EMQX_HOST, port=8883, tls=True)
        backoff = 1  # reset on success
    except ConnectionError:
        sleep(backoff)
        backoff = min(backoff * 2, max_backoff)
```

### 10.2 Service Health Endpoints

Every internal service exposes:

```
GET /health
→ 200 { "status": "healthy", "influx": "ok", "mysql": "ok", "redis": "ok" }
→ 503 { "status": "degraded", "influx": "error: connection timeout" }
```

Docker Compose health checks poll this endpoint every 10 seconds. Unhealthy services are restarted automatically.

### 10.3 Dead Letter Queue

Any message that fails processing after max retries is moved to a Dead Letter Queue (DLQ). DLQ entries are:

- Persisted to MySQL `dlq_messages` table.
- Visible in the Platform Root admin panel.
- Retryable manually by Platform Root users.

---

## 11. Infrastructure & Deployment

### 11.1 Docker Compose Service Map

| Service              | Image                  | Port(s)       | Depends On            |
|----------------------|------------------------|---------------|-----------------------|
| `emqx`               | emqx/emqx:5.x          | 1883, 8883, 8083, 18083 | —         |
| `influxdb`           | influxdb:2.x           | 8086          | —                     |
| `mysql`              | mysql:8.x              | 3306          | —                     |
| `minio`              | minio/minio:latest     | 9000, 9001    | —                     |
| `redis`              | redis:7.x              | 6379          | —                     |
| `api-service`        | factoryops/api:latest  | 8000          | mysql, redis          |
| `telemetry-service`  | factoryops/telemetry   | —             | emqx, influxdb, mysql |
| `rule-engine`        | factoryops/rules       | —             | mysql, redis          |
| `analytics-service`  | factoryops/analytics   | —             | influxdb, minio, mysql|
| `notification-service` | factoryops/notify    | —             | mysql                 |
| `report-service`     | factoryops/reports     | —             | influxdb, mysql, minio|
| `frontend`           | factoryops/frontend    | 3000          | api-service           |
| `nginx`              | nginx:alpine           | 80, 443       | api-service, frontend |

### 11.2 Environment Variable Convention

All service configuration is injected via environment variables. No secrets are hardcoded.

```env
# MySQL
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DB=factoryops
MYSQL_USER=app
MYSQL_PASSWORD=<secret>

# InfluxDB
INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=<secret>
INFLUX_ORG=factoryops
INFLUX_BUCKET=factoryops

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<secret>
MINIO_SECRET_KEY=<secret>
MINIO_BUCKET=factoryops

# JWT
JWT_SECRET=<minimum-256-bit-secret>
JWT_EXPIRY_SECONDS=86400

# EMQX
EMQX_HOST=emqx
EMQX_PORT=8883

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 11.3 Scalability Notes

The following services are stateless and can be horizontally scaled by adding replicas behind the nginx upstream:

- `api-service` — stateless, JWT-based auth
- `telemetry-service` — stateless MQTT consumer (EMQX shared subscription groups)
- `rule-engine` — stateless worker (queue-based, no shared memory)
- `analytics-service` — stateless worker (job-based, state in MySQL/MinIO)

Services with state (`mysql`, `influxdb`, `minio`, `redis`) are scaled vertically in the initial deployment. Kubernetes migration (planned) will introduce horizontal scaling for these via operator-managed clusters.

---

*End of FactoryOps AI Engineering Low-Level Design v1.0*
