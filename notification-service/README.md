# Notification Service - FactoryOps AI Engineering

The Notification Service handles the dispatch of alerts to users via multiple channels (Email, WhatsApp). It ensures that critical factory events are communicated reliably.

## Purpose
- Dispatch alerts via Email (SMTP) and WhatsApp (Twilio).
- Maintain logs of all sent notifications.
- Handle retries for failed deliveries.
- Asynchronous processing via Redis queue.

## Architecture Alignment
- **Asynchronous**: Worker-based processing via `notifications_queue`.
- **Channels**: Modular senders for Email and WhatsApp.
- **Factory Isolation**: Queries `User` table by `factory_id` to resolve admins.

## Environment Variables
See `.env.example`. Key variables:
- `MYSQL_HOST`, `MYSQL_DB`
- `REDIS_URL`
- `SMTP_SERVER`, `SMTP_FROM_EMAIL`
- `TWILIO_ACCOUNT_SID`, `TWILIO_FROM_NUMBER`

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
   uvicorn app.main:app --host 0.0.0.0 --port 8005
   ```

## Docker Instructions

1. **Build**:
   ```bash
   docker build -t factoryops/notification-service .
   ```
2. **Run**:
   ```bash
   docker run -p 8005:8005 --env-file .env factoryops/notification-service
   ```

## Testing Instructions

1. **Unit Tests**:
   ```bash
   pytest
   ```
   Tests cover the dispatch logic with mocked SMTP and Twilio clients.

## API Usage
This service is primarily a background worker but exposes a health endpoint:
```http
GET /api/v1/health
```
