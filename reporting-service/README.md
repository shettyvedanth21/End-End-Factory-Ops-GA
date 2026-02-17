# Reporting Service - FactoryOps AI Engineering

The Reporting Service generates structured operational reports in various formats (PDF, Excel, JSON). It aggregates data from InfluxDB and MySQL, renders it using templates or data libraries, and uploads the artifacts to MinIO.

## Purpose
- Aggregate multi-source data (Telemetry + Alerts).
- Render professional reports (PDF/Excel).
- Upload to secure object storage (MinIO).
- Asynchronous processing via Redis queue.

## Architecture Alignment
- **Asynchronous**: Worker-based processing via `reports_queue`.
- **Data Aggregation**: Queries InfluxDB (Aggregates) and MySQL (Transactional) within a single job.
- **Factory Isolation**: All paths and queries scoped by `factory_id`.
- **Output**: PDF generation using WeasyPrint; Excel using OpenPyXL.

## Environment Variables
See `.env.example`. Key variables:
- `INFLUX_URL`, `INFLUX_BUCKET`
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- `MYSQL_HOST`, `MYSQL_DB`
- `REDIS_URL`

## Setup Steps

1. **Prerequisites**: Python 3.11+, MySQL, Redis, InfluxDB, MinIO.
   *System Dependencies**: `libpango-1.0-0`, `libpangoft2-1.0-0`, `libjpeg-dev`, `libopenjp2-7-dev` (for WeasyPrint).
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env`.
4. **Run Locally**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8004
   ```

## Docker Instructions

1. **Build** (includes necessary system libraries):
   ```bash
   docker build -t factoryops/reporting-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8004:8004 --env-file .env factoryops/reporting-service
   ```

## Testing Instructions

1. **Unit Tests**:
   ```bash
   pytest
   ```
   Tests cover the report generation lifecycle with mocked renderers and external services.

## API Usage
This service is primarily a background worker but exposes a health endpoint:
```http
GET /api/v1/health
```
