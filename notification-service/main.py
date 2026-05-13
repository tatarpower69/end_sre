from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification-service")

app = FastAPI(title="Notification Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOTIFICATIONS_SENT = Counter('notifications_sent_total', 'Total notifications sent', ['channel'])

notification_log = []

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "Notification Service is running"}

@app.get("/notifications")
def get_notifications():
    return [
        {"id": 1, "type": "email", "to": "admin@example.com", "subject": "System Alert", "status": "sent", "timestamp": "2026-05-13T10:00:00Z"},
        {"id": 2, "type": "sms", "to": "+1234567890", "subject": "Order Confirmed", "status": "sent", "timestamp": "2026-05-13T10:05:00Z"},
        {"id": 3, "type": "webhook", "to": "https://hooks.slack.com/services/xxx", "subject": "Service Down", "status": "delivered", "timestamp": "2026-05-13T10:10:00Z"}
    ]

@app.post("/notifications/send")
def send_notification(channel: str = "email", to: str = "user@example.com", message: str = "Hello"):
    NOTIFICATIONS_SENT.labels(channel=channel).inc()

    notification = {
        "id": len(notification_log) + 1,
        "channel": channel,
        "to": to,
        "message": message,
        "status": "sent",
        "timestamp": datetime.utcnow().isoformat()
    }
    notification_log.append(notification)
    logger.info(f"Notification sent via {channel} to {to}")

    return notification

@app.post("/notifications/alert")
def send_alert(severity: str = "warning", service: str = "unknown", message: str = "Alert triggered"):
    NOTIFICATIONS_SENT.labels(channel="alert").inc()
    logger.warning(f"ALERT [{severity.upper()}] on {service}: {message}")
    return {
        "alert_id": len(notification_log) + 100,
        "severity": severity,
        "service": service,
        "message": message,
        "status": "dispatched",
        "timestamp": datetime.utcnow().isoformat()
    }

Instrumentator().instrument(app).expose(app)
