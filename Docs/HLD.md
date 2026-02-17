# FACTORYOPS AI ENGINEERING

## Enterprise High-Level Design (HLD)

Version: 1.0 Generated on: 2026-02-17 14:02:56 UTC

------------------------------------------------------------------------

# 1. Executive Overview

FactoryOps AI Engineering is a multi-tenant, factory-isolated,
firmware-adaptive industrial energy intelligence platform. It is
designed to ingest real-time telemetry from industrial machines,
dynamically adapt to evolving firmware metrics, enforce real-time rule
evaluation, execute advanced analytics workflows, and generate
structured operational reports --- all while maintaining strict
factory-level isolation.

This document defines the complete high-level architecture, system
boundaries, operational philosophy, analytics lifecycle, scalability
model, and failure-handling strategy.

------------------------------------------------------------------------

# 2. Core Architectural Philosophy

The system is built on five non-negotiable principles:

1.  Factory-First Isolation
2.  Firmware-Adaptive Telemetry
3.  Event-Driven Processing
4.  Asynchronous Analytics
5.  Open-Source Infrastructure

Each factory is treated as an isolated digital universe. No
cross-factory access is permitted at any layer.

------------------------------------------------------------------------

# 3. Factory-Scoped Access Model

## 3.1 Entry Flow

1.  User opens portal.
2.  User selects factory from dropdown.
3.  Factory-scoped login screen appears.
4.  User logs in as:
    -   Super Admin
    -   Admin

The session token includes: - user_id - factory_id - role - permission
flags

Every backend request is filtered by factory_id.

## 3.2 Role Model

Platform Root: - Create factories - Assign initial Super Admin

Factory Super Admin: - Full read/write - Manage users - Manage rules -
Run analytics - Generate reports

Factory Admin: - Read access - Write access only if permission granted -
Cannot manage users

------------------------------------------------------------------------

# 4. Multi-Tenant Isolation Model

Isolation is enforced at three levels:

## 4.1 MQTT Namespace Isolation

Single EMQX cluster.

Topic structure:

factories/{factory_id}/devices/{device_id}/telemetry

Telemetry Service subscribes to: factories/+/devices/+/telemetry

Factory context is derived from topic path.

## 4.2 API-Level Isolation

JWT contains factory_id. All services enforce filtering by factory_id.

## 4.3 Storage-Level Isolation

InfluxDB: - factory_id stored as tag

MySQL: - factory_id column in all tenant tables

S3 (MinIO): s3://factoryops/{factory_id}/analytics/

------------------------------------------------------------------------

# 5. Telemetry Architecture

## 5.1 Device Metadata (MySQL)

Stores: - device_id - name - type - location - factory_id - status -
last_seen

Constant attributes only.

## 5.2 Dynamic Telemetry (InfluxDB)

Measurement: device_metrics

Tags: - factory_id - device_id - property_name

Field: - value

Timestamp: - ingestion time

No hardcoded schema. Firmware defines metric vocabulary.

## 5.3 Property Auto-Discovery

When new metric appears: - System registers property automatically -
Property becomes immediately usable in UI and rule engine - Properties
cannot be deleted (historical integrity preserved)

------------------------------------------------------------------------

# 6. Rule Engine Architecture

Rules are event-driven.

Trigger: Every telemetry event.

Evaluation Flow: 1. Fetch active rules for device. 2. Validate schedule.
3. Evaluate multi-condition logic. 4. If TRUE: - Check cooldown - Create
alert - Trigger notification 5. If FALSE and auto-resolve enabled: -
Resolve alert

No historical scanning. No polling.

------------------------------------------------------------------------

# 7. Alert & Notification Architecture

Alert Service: - Stores alert state - Tracks lifecycle (open,
acknowledged, resolved)

Notification Service: - Email (SMTP) - WhatsApp (Twilio)

Notifications are asynchronous. Failure does not block ingestion.

------------------------------------------------------------------------

# 8. Analytics Architecture

Analytics is asynchronous and decoupled from ingestion.

## 8.1 Modes

Standard Mode: - User selects analysis type and model - Models can be
reused - Results versioned per run

AI Co-Pilot Mode: - System auto-selects best model - Auto feature
selection - Auto hyperparameter tuning

## 8.2 Dataset Lifecycle

1.  Data Export Service extracts telemetry from Influx.
2.  Dataset stored in S3 (MinIO).
3.  Analytics Service reads dataset.
4.  Model executed.
5.  Results stored in MySQL.
6.  Artifacts stored in S3.

Datasets are immutable snapshots.

## 8.3 Model Versioning

Each analytics run produces: - model_name - model_version -
dataset_reference - hyperparameters - metrics - timestamp

Models can be reused for later runs.

------------------------------------------------------------------------

# 9. Reporting Architecture

Reporting pulls from: - Influx aggregates - MySQL alerts - MySQL
analytics results

Generates: - PDF - Excel - JSON

Report generation is asynchronous.

------------------------------------------------------------------------

# 10. Failure Handling & Reliability Model

## 10.1 MQTT Disconnection

-   Telemetry Service reconnect with exponential backoff.
-   Messages use QoS 1.
-   No data loss under temporary failure.

## 10.2 Influx Write Failure

-   Retry with backoff.
-   Persist to temporary buffer queue.
-   Alert system health if failure persists.

## 10.3 Property Registration Failure

-   Reject message.
-   Log error.
-   Notify system admin.

## 10.4 Analytics Job Failure

-   Mark job status as failed.
-   Preserve dataset.
-   Allow retry.

## 10.5 MinIO Unavailability

-   Block analytics execution.
-   Return system-level warning.
-   No impact on telemetry or rules.

------------------------------------------------------------------------

# 11. Scalability Assumptions

-   Telemetry ingestion: \< 2 sec latency
-   Rule evaluation: \< 500 ms
-   Support 10,000+ devices per factory
-   Time-series retention policy configurable
-   Downsampling strategy required for long-term storage

Architecture supports horizontal scaling of: - Telemetry Service - Rule
Engine - Analytics Service

------------------------------------------------------------------------

# 12. Security Model

-   Password hashing (bcrypt)
-   JWT-based authentication
-   TLS communication
-   Backend-enforced tenant filtering
-   No cross-factory queries permitted

------------------------------------------------------------------------

# 13. Open Source Stack

-   EMQX
-   InfluxDB
-   MySQL
-   MinIO
-   Python backend services
-   React frontend
-   Docker Compose

------------------------------------------------------------------------

# 14. Future Expansion Readiness

-   Kubernetes migration
-   AWS deployment
-   Real-time model inference
-   Advanced energy optimization
-   Device grouping and benchmarking
-   AI recommendation engine

------------------------------------------------------------------------

# Conclusion

This High-Level Design defines a production-grade, firmware-adaptive,
multi-tenant industrial energy intelligence platform.

The architecture ensures: - Strict isolation - Dynamic telemetry
adaptability - Real-time rule enforcement - Scalable analytics
lifecycle - Enterprise-grade reliability - Open-source independence

This document serves as the authoritative reference for Low-Level Design
(LLD) implementation.
