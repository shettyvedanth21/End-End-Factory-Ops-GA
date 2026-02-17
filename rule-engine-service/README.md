# Rule Engine Service - FactoryOps AI Engineering

The Rule Engine Service is the real-time event processing brain of the FactoryOps platform. It consumes property updates from the Telemetry Service, evaluates user-defined rules, and manages the lifecycle of alerts (open, acknowledged, resolved).

## Purpose
- Real-time rule evaluation (< 500ms).
- Manage Alert lifecycle (Open, Acknowledge, Resolve).
- Enforce rule scheduling and cool-down periods.
- Dispatch notification triggers.

## Architecture Alignment
- **Event-Driven**: Consumes from Redis Queue (`events_queue`).
- **Factory Isolation**: Rules and Alerts are strictly scoped by `factory_id`.
- **State Management**: Uses MySQL for persistent state (rules, alerts).
- **Asynchronous**: Processing happens in background workers, decoupled from ingestion latency.

## Environment Variables
See `.env.example`. Key variables:
- `MYSQL_HOST`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD`
- `REDIS_URL`

## Setup Steps

1. **Prerequisites**: Python 3.11+, MySQL, Redis.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env`.
4. **Run Locally**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8002
   ```

## Docker Instructions

1. **Build**:
   ```bash
   docker build -t factoryops/rule-engine-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8002:8002 --env-file .env factoryops/rule-engine-service
   ```

## Testing Instructions

1. **Unit Tests**:
   ```bash
   pytest
   ```
   Tests cover condition evaluation logic, schedule checking, cooldown enforcement, and auto-resolution.

## API Usage
This service is a background worker but exposes a health endpoint:
```http
GET /api/v1/health
```
