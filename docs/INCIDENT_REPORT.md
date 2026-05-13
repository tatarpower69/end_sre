# Incident Report & Postmortem

## Project: SRE Microservices Platform
## Date: May 2026
## Author: Ilnur

---

## Incident Summary

| Field | Details |
|-------|---------|
| **Incident ID** | INC-2026-001 |
| **Date** | May 12, 2026 |
| **Duration** | 14 minutes (10:23 – 10:37 UTC) |
| **Severity** | SEV-2 (Partial Service Outage) |
| **Affected Service** | Order Service |
| **Impact** | Order creation unavailable; Payment service degraded |
| **Detected By** | Prometheus `ServiceDown` alert |
| **Resolved By** | Configuration fix and service restart |

---

## 1. Incident Description

The Order Service became unavailable due to an incorrect database host configuration
introduced during a routine environment variable update. The service failed to connect
to PostgreSQL, causing all `/health` checks to return HTTP 503 and triggering the
`ServiceDown` Prometheus alert within 30 seconds.

---

## 2. Timeline

| Time (UTC) | Event |
|------------|-------|
| 10:20 | Environment variable update deployed to `.env` file |
| 10:21 | Docker Compose services restarted with `docker compose up -d` |
| 10:23 | Order Service health check fails — returns HTTP 503 |
| 10:23 | Prometheus `ServiceDown` alert fires for `order-service` |
| 10:24 | Grafana dashboard shows Order Service as DOWN (red indicator) |
| 10:25 | On-call engineer begins investigation |
| 10:26 | `docker logs order-service` reveals: `DATABASE_CONNECTION_FAILURE: Unable to connect to db-wrong:5432` |
| 10:28 | Root cause identified: `DB_HOST` was changed from `db` to `db-wrong` in `.env` |
| 10:30 | Payment Service starts returning increased errors (dependency on Order) |
| 10:32 | `.env` corrected: `DB_HOST=db` |
| 10:33 | `docker compose restart order-service` executed |
| 10:35 | Order Service health check returns HTTP 200 |
| 10:36 | Prometheus `ServiceDown` alert resolves |
| 10:37 | All metrics normalized, Grafana confirms full recovery |

---

## 3. Root Cause Analysis

**Primary Cause**: Human error during environment configuration update.

The `DB_HOST` variable in the `.env` file was accidentally changed from `db` (the correct
Docker Compose service name for PostgreSQL) to `db-wrong`. This caused the Order Service
to fail at startup because `psycopg2.connect()` could not resolve the hostname.

**Contributing Factors**:
1. No validation of environment variables before deployment.
2. No staging environment — changes went directly to production.
3. Order Service lacked graceful degradation (no retry/fallback for DB connection).

---

## 4. Impact Assessment

| Metric | Normal | During Incident | SLO Target |
|--------|--------|-----------------|------------|
| Availability | 100% | 0% (Order Service) | ≥ 99.5% |
| Error Rate | < 0.1% | 100% (Order endpoints) | ≤ 0.5% |
| Latency (p95) | ~45ms | N/A (503 responses) | ≤ 200ms |
| Orders Created | ~50/min | 0/min | N/A |

**User Impact**: Users could not create orders for 14 minutes. Product browsing, authentication,
user profiles, and chat remained fully operational.

**Error Budget Consumed**: 14 minutes out of 7.2 hours monthly budget = 3.2% of error budget.

---

## 5. Detection

The incident was detected automatically through the monitoring stack:

1. **Prometheus** scrape to `order-service:8000/metrics` returned connection error.
2. **Alert rule** `ServiceDown (up == 0 for 30s)` fired at 10:23.
3. **Grafana dashboard** turned the Order Service card from green to red.
4. On-call engineer received alert notification within 2 minutes.

---

## 6. Resolution

### Immediate Actions
1. Checked `docker ps` — confirmed Order Service container was running but unhealthy.
2. Ran `docker logs order-service` — found `DATABASE_CONNECTION_FAILURE` error messages.
3. Identified misconfigured `DB_HOST=db-wrong` in `.env` file.
4. Corrected to `DB_HOST=db` and restarted the service.

### Commands Executed
```bash
# Diagnosis
docker logs order-service --tail 50
docker exec order-service cat /proc/1/environ | tr '\0' '\n' | grep DB_HOST

# Fix
sed -i 's/DB_HOST=db-wrong/DB_HOST=db/' .env
docker compose restart order-service

# Verification
curl http://localhost/api/order/health
docker logs order-service --tail 10
```

---

## 7. Lessons Learned

### What went well
- Prometheus alert fired within 30 seconds of the failure.
- Grafana dashboard provided clear visual confirmation of the outage.
- Root cause was identified within 3 minutes through structured log analysis.
- Total MTTR (Mean Time To Recovery) was 14 minutes.

### What went wrong
- No environment variable validation before deployment.
- Manual `.env` editing is error-prone.
- No configuration change review process.

### Where we got lucky
- Only one service was directly affected (Order Service).
- Other services (Auth, User, Product, Chat) had no dependency on Order Service.
- The incident occurred during low-traffic hours.

---

## 8. Action Items

| # | Action | Priority | Owner | Status |
|---|--------|----------|-------|--------|
| 1 | Add `validate_config.ps1` script to verify `.env` before deployment | P0 | Ilnur | ✅ Done |
| 2 | Implement DB connection retry logic in Order Service (3 retries, 5s delay) | P1 | Ilnur | Planned |
| 3 | Add environment variable validation at service startup | P1 | Ilnur | Planned |
| 4 | Create staging environment for pre-production testing | P2 | Ilnur | Planned |
| 5 | Add Slack/email notification channel for Prometheus alerts | P2 | Ilnur | Planned |

---

## 9. Incident Simulation for Demonstration

To reproduce this incident for demonstration purposes:

### Step 1: Break the Configuration
```bash
# Change DB_HOST to an invalid value
sed -i 's/DB_HOST=db/DB_HOST=db-wrong/' .env
docker compose restart order-service
```

### Step 2: Observe in Monitoring
- Open Grafana: `http://localhost:3000`
- Open Prometheus: `http://localhost:9090`
- Query: `up{job="order-service"}` — should show `0`

### Step 3: Fix and Recover
```bash
sed -i 's/DB_HOST=db-wrong/DB_HOST=db/' .env
docker compose restart order-service
```

### Step 4: Verify Recovery
```bash
curl http://localhost/api/order/health
# Expected: {"status": "healthy", "database": "connected"}
```
