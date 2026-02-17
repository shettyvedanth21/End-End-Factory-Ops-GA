# Telemetry Service - FactoryOps AI Engineering

The Telemetry Service is the ingestion engine of the FactoryOps platform. It subscribes to MQTT topics, processes real-time telemetry, handles property auto-discovery, writes time-series data to InfluxDB, and publishes events to the Rule Engine.

## Purpose
- Ingest high-volume telemetry via MQTT.
- Enforce factory isolation via topic structure (`factories/{factory_id}/...`).
- Auto-discover new device properties and register them in MySQL.
- Buffer and write data to InfluxDB.
- Forward clean events to the Rule Engine via Redis.

## Architecture Alignment
- **Event-Driven**: Subscribes to MQTT topics; publishes to Redis queue.
- **Factory Isolation**: Topic parsing ensures data is tagged with correct `factory_id`.
- **InfluxDB Usage**: Writes formatted points with tags for factory, device, and property.
- **Auto-Discovery**: Dynamically updates metadata in MySQL without schema migrations.

## Environment Variables
See `.env.example`. Key variables:
- `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`
- `INFLUX_URL`, `INFLUX_BUCKET`
- `MYSQL_HOST`, `MYSQL_DB`
- `REDIS_URL`

## Setup Steps

1. **Prerequisites**: Python 3.11+, MQTT Broker (EMQX), InfluxDB, MySQL, Redis.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env`.
4. **Run Locally**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001
   ```

## Docker Instructions

1. **Build**:
   ```bash
   docker build -t factoryops/telemetry-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8001:8001 --env-file .env factoryops/telemetry-service
   ```

## Testing Instructions

1. **Unit Tests**:
   ```bash
   pytest
   ```
   Tests cover message processing logic, auto-discovery, and invalid payload handling.

## API Usage
This service is primarily a background worker but exposes a health endpoint:
```http
GET /health
```
