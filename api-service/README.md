# API Service - FactoryOps AI Engineering

This is the core API service for the FactoryOps AI Engineering platform. It serves as the primary gateway for frontend interactions, enforcing strict multi-tenant isolation, managing metadata, and orchestrating interactions with other microservices (Telemetry, Rules, Analytics, Reporting).

## Purpose
- Provide RESTful API endpoints for user, device, rule, alert, and analytics management.
- Enforce factory-level isolation using JWT-based tenant context.
- Manage structured metadata in MySQL.
- Proxy time-series data queries to InfluxDB.

## Architecture Alignment
- **Tenant Isolation**: Every request is authenticated via JWT, extracting `factory_id`. This ID is mandated in all MySQL queries and InfluxDB filters.
- **Tech Stack**: FastAPI (Python), SQLAlchemy (MySQL), Pydantic (data validation).
- **Security**: HS256 JWT, BCrypt password hashing.
- **Infrastructure**: Dockerized, Environment-based configuration.

## Environment Variables
See `.env.example` for a complete list. Key variables:
- `MYSQL_HOST`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD`
- `INFLUX_URL`, `INFLUX_ORG`, `INFLUX_BUCKET`
- `JWT_SECRET`, `JWT_ALGORITHM`
- `REDIS_URL`

## Setup Steps

1. **Prerequisites**: Python 3.11+, Docker, MySQL, InfluxDB, Redis.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env` and configure.
4. **Run Locally**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Docker Instructions

1. **Build**:
   ```bash
   docker build -t factoryops/api-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8000:8000 --env-file .env factoryops/api-service
   ```

## Testing Instructions

1. **Unit/Integration Tests**:
   ```bash
   pytest
   ```
   Tests cover authentication, tenant isolation, device management, and more.

## API Usage Examples

**Login:**
```http
POST /api/v1/auth/login
{
  "factory_slug": "plant-munich",
  "email": "admin@plant-munich.com",
  "password": "password"
}
```

**Get Devices:**
```http
GET /api/v1/devices
Authorization: Bearer <token>
```
