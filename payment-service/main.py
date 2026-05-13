from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
import time
import random
import redis
import os
import json

app = FastAPI(title="Payment Service")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=2)
    r.ping()
    redis_connected = True
except:
    redis_connected = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAYMENT_COUNTER = Counter('payments_processed_total', 'Total payments processed', ['status'])
PAYMENT_LATENCY = Histogram('payment_processing_seconds', 'Payment processing time')

@app.get("/health")
def health():
    status = {"status": "healthy"}
    if redis_connected:
        try:
            r.ping()
            status["redis"] = "connected"
        except:
            status["redis"] = "disconnected"
    return status

@app.get("/")
def read_root():
    return {"message": "Payment Service is running"}

@app.get("/payments")
def get_payments():
    # Try to get from cache first
    if redis_connected:
        try:
            cached = r.get("latest_payments")
            if cached:
                return json.loads(cached)
        except:
            pass

    payments = [
        {"id": "PAY-001", "order_id": 5001, "amount": 1200.00, "status": "completed", "method": "credit_card"},
        {"id": "PAY-002", "order_id": 5002, "amount": 499.99, "status": "pending", "method": "paypal"},
        {"id": "PAY-003", "order_id": 5003, "amount": 89.50, "status": "completed", "method": "bank_transfer"}
    ]

    # Store in cache
    if redis_connected:
        try:
            r.setex("latest_payments", 60, json.dumps(payments))
        except:
            pass

    return payments

@app.post("/payments/process")
def process_payment(order_id: int, amount: float, method: str = "credit_card"):
    start_time = time.time()
    processing_delay = random.uniform(0.1, 0.5)
    time.sleep(processing_delay)

    success = random.random() > 0.05
    status = "completed" if success else "failed"

    PAYMENT_COUNTER.labels(status=status).inc()
    PAYMENT_LATENCY.observe(time.time() - start_time)

    if not success:
        raise HTTPException(status_code=402, detail="Payment processing failed")

    return {
        "payment_id": f"PAY-{random.randint(1000, 9999)}",
        "order_id": order_id,
        "amount": amount,
        "method": method,
        "status": status,
        "processing_time_ms": round((time.time() - start_time) * 1000, 2)
    }

@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):
    return {
        "payment_id": payment_id,
        "order_id": 5001,
        "amount": 1200.00,
        "status": "completed",
        "method": "credit_card"
    }

Instrumentator().instrument(app).expose(app)
