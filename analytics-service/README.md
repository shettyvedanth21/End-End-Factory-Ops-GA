# Analytics Service - FactoryOps AI Engineering

The Analytics Service handles the execution of machine learning workflows, including data extraction, model training, and artifact management. It operates asynchronously, processing jobs from a Redis queue.

## Purpose
- Execute long-running analytics jobs (Training/Inference).
- Export telemetry data from InfluxDB to Parquet/MinIO.
- Train Scikit-Learn models (Random Forest, Linear Regression, etc.).
- manage model registry and versioning.

## Architecture Alignment
- **Asynchronous**: Worker-based processing via Redis queue (`analytics_queue`).
- **Data Lifecycle**: InfluxDB (Source) -> Parquet (Intermediate) -> MinIO (Storage).
- **Factory Isolation**: All data queries and storage paths are scoped by `factory_id`.
- **Model Registry**: Metadata stored in MySQL (`analytics_models`).

## Environment Variables
See `.env.example`. Key variables:
- `INFLUX_URL`, `INFLUX_BUCKET`
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- `MYSQL_HOST`, `MYSQL_DB`
- `REDIS_URL`

## Setup Steps

1. **Prerequisites**: Python 3.11+, MySQL, Redis, InfluxDB, MinIO.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env`.
4. **Run Locally**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8003
   ```

## Docker Instructions

1. **Build**:
   ```bash
   docker build -t factoryops/analytics-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8003:8003 --env-file .env factoryops/analytics-service
   ```

## Testing Instructions

1. **Unit Tests**:
   ```bash
   pytest
   ```
   Tests cover the worker processing logic with mocked external services (Influx, MinIO).

## API Usage
This service is primarily a background worker but exposes a health endpoint:
```http
GET /api/v1/health
```
