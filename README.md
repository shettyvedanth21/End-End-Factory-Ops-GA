# FactoryOps AI Engineering Platform

**FactoryOps** is a production-grade, multi-tenant industrial IoT platform designed for real-time telemetry ingestion, rule-based monitoring, advanced analytics, and automated reporting. It adheres to strict factory-level isolation and supports firmware-adaptive metrics.

---

## 🏗️ Architecture Overview

The system is composed of decoupled microservices communicating asynchronously via **Redis** (Task Queues) and **EMQX** (MQTT Telemetry).

| Service | Technology | Responsibility | Port |
| :--- | :--- | :--- | :--- |
| **Frontend** | React (Vite) | User Interface (Dashboard, Rules, Alerts) | 80 |
| **API Gateway** | Nginx | Reverse Proxy & Routing | 80 |
| **API Service** | FastAPI | REST API for Users, Devices, Metadata | 8000 |
| **Telemetry** | Python | High-Throughput Ingestion (MQTT -> InfluxDB) | 8001 |
| **Rule Engine** | Python | Real-time Alert Evaluation | 8002 |
| **Analytics** | Python (Scikit) | ML Training & Interference Jobs | 8003 |
| **Reporting** | Python (WeasyPrint) | PDF/Excel Generation | 8004 |
| **Notification** | Python (Twilio) | Alert Dispatch (Email/WhatsApp) | 8005 |

**Infrastructure:**
- **MySQL 8.0**: Relational Metadata (Users, Devices, Rules)
- **InfluxDB 2.7**: Time-Series Telemetry
- **Redis 7.0**: Message Broker & Caching
- **MinIO**: S3-Compatible Object Storage
- **EMQX 5.0**: MQTT Broker

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose**
- **Python 3.11+** (for local development)
- **Make** (optional)

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-org/factoryops.git
   cd factoryops
   ```

2. **Environment Configuration:**
   Each service has its own `.env.example`. The root `docker-compose.yml` orchestrates them.
   ```bash
   # Copy example envs (script provided for convenience)
   cp .env.example .env
   ```

3. **Build & Run (Production Mode):**
   Use the provided deployment script to build images and start the stack.
   ```bash
   ./scripts/deploy.sh
   ```
   *Alternatively:*
   ```bash
   docker-compose up --build -d
   ```

4. **Verify Deployment:**
   - **Frontend Dashboard**: [http://localhost](http://localhost)
   - **API Docs**: [http://localhost/api/v1/docs](http://localhost/api/v1/docs)
   - **MinIO Console**: [http://localhost:9090](http://localhost:9090) (User/Pass: `minio_access_key` / `minio_secret_key`)

---

## 🧪 Testing

### Running Unit Tests
Each service has a `tests/` directory with `pytest` suites.
```bash
# Example: Run API Service tests
cd api-service
pip install -r requirements.txt
pytest
```

### Running End-to-End (E2E) Tests
Wait for the full stack to be healthy, then run the integration suite:
```bash
# Requires requests, paho-mqtt, pytest
pip install pytest requests paho-mqtt
pytest tests/e2e/test_system_flow.py
```

---

## 🔧 Operational Guides

### Database Migrations
Database schemas are automatically applied on startup via `docker/mysql/init.sql`.
To reset the database:
```bash
docker-compose down -v
docker-compose up -d mysql
```

### Adding a New Service
1. Create directory `new-service/`
2. Add `Dockerfile` & `app/` code.
3. Register in `docker-compose.yml`.
4. Add Nginx routing in `docker/nginx/nginx.conf`.

---

## 📜 License
Private & Confidential - FactoryOps Engineering Team
