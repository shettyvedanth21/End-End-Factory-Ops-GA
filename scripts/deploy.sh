#!/bin/bash
set -e

echo "=================================="
echo "   FactoryOps Production Deploy   "
echo "=================================="
echo "Date: $(date)"
echo "----------------------------------"

# 1. Environment Check
if [ ! -f .env ]; then
    echo "[WARN] .env file not found. Creating from .env.example..."
    # Usually we want a consolidated .env, but each service has its own.
    # The docker-compose uses its own env vars or env_file if specified.
    # Assuming root .env or service .envs are managed.
    cp .env.example .env 2>/dev/null || echo "No .env.example found at root. Proceeding..."
fi

# 2. Build Docker Images
echo "[INFO] Building Docker images..."
docker-compose build --parallel

# 3. Start Database & Infrastructure first
echo "[INFO] Starting Infrastructure (MySQL, InfluxDB, Redis, MinIO, EMQX)..."
docker-compose up -d mysql influxdb redis minio emqx

# 4. Wait for MySQL (Simple check loop)
echo "[INFO] Waiting for MySQL to be ready..."
until docker-compose exec -T mysql mysqladmin ping -h "localhost" --silent; do
    echo "Waiting for MySQL..."
    sleep 2
done

# 5. Start Application Services
echo "[INFO] Starting Application Services..."
docker-compose up -d api-service telemetry-service rule-engine-service analytics-service reporting-service notification-service frontend nginx

# 6. Verify Health
echo "[INFO] Verifying Service Health..."
sleep 10
docker-compose ps

echo "=================================="
echo "   Deployment Complete!           "
echo "=================================="
echo "Frontend: http://localhost:80"
echo "API:      http://localhost:80/api/v1/"
echo "MinIO:    http://localhost:9090"
echo "Grafana:  http://localhost:3000"
