# Service Level Indicators (SLIs) and Service Level Objectives (SLOs)

## Project: SRE Microservices Platform
## Date: May 2026
## Author: Ilnur

---

## 1. Overview

This document defines the Service Level Indicators (SLIs) and Service Level Objectives (SLOs)
for the distributed microservices platform. These metrics establish measurable reliability
targets that guide operational decisions, incident response priorities, and capacity planning.

---

## 2. Service Level Indicators (SLIs)

### 2.1 Availability
- **Definition**: The proportion of time each service is operational and responding to requests.
- **Measurement**: `up` metric from Prometheus scrape targets.
- **Formula**: `(total_time - downtime) / total_time × 100%`
- **Data Source**: Prometheus `up == 1` metric per service.

### 2.2 Latency
- **Definition**: The time taken to process and respond to HTTP requests.
- **Measurement**: Request duration histogram from `prometheus-fastapi-instrumentator`.
- **Formula**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Data Source**: Prometheus `http_request_duration_seconds` histogram.

### 2.3 Error Rate
- **Definition**: The percentage of requests that result in server errors (5xx responses).
- **Measurement**: Ratio of 5xx responses to total responses.
- **Formula**: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) × 100%`
- **Data Source**: Prometheus `http_requests_total` counter with status labels.

### 2.4 Request Success Rate
- **Definition**: The percentage of requests that return a successful response (2xx/3xx).
- **Measurement**: Ratio of successful responses to total responses.
- **Formula**: `rate(http_requests_total{status=~"2..|3.."}[5m]) / rate(http_requests_total[5m]) × 100%`
- **Data Source**: Prometheus `http_requests_total` counter.

---

## 3. Service Level Objectives (SLOs)

| SLO Metric | Target | Error Budget (30 days) | Measurement Window |
|------------|--------|------------------------|-------------------|
| Availability | ≥ 99.0% | 7.2 hours downtime | Rolling 30-day |
| Latency (p95) | ≤ 200 ms | N/A | Rolling 5-minute |
| Error Rate | ≤ 1.0% | 1% of total requests | Rolling 5-minute |
| Request Success Rate | ≥ 99.0% | 1% of total requests | Rolling 5-minute |

### 3.1 Availability SLO: ≥ 99.0%
- **Target**: Each microservice must be available at least 99% of the time.
- **Error Budget**: 7.2 hours of allowed downtime per 30-day window.
- **Alerting Threshold**: Alert if availability drops below 99.5% over 5 minutes.
- **Prometheus Alert**:
  ```promql
  up == 0  # for > 30 seconds triggers ServiceDown alert
  ```

### 3.2 Latency SLO: ≤ 200 ms (p95)
- **Target**: 95th percentile response time must not exceed 200 ms.
- **Rationale**: Users expect sub-second responses; 200ms keeps perceived performance high.
- **Prometheus Query**:
  ```promql
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) <= 0.2
  ```

### 3.3 Error Rate SLO: ≤ 1.0%
- **Target**: No more than 1% of all requests should result in 5xx errors.
- **Prometheus Alert**:
  ```promql
  rate(http_requests_total{status=~"5.."}[5m]) > 0.05  # triggers HighErrorRate alert
  ```

### 3.4 Request Success Rate SLO: ≥ 99.0%
- **Target**: At least 99% of all requests should return a successful response.
- **Calculation**: Inverse of error rate, includes both client and server success paths.

---

## 4. SLO per Service

| Service | Availability | Latency (p95) | Error Rate |
|---------|-------------|---------------|------------|
| Auth Service | ≥ 99.0% | ≤ 150 ms | ≤ 1.0% |
| User Service | ≥ 99.0% | ≤ 150 ms | ≤ 1.0% |
| Product Service | ≥ 99.0% | ≤ 150 ms | ≤ 1.0% |
| Order Service | ≥ 99.5% | ≤ 200 ms | ≤ 0.5% |
| Chat Service | ≥ 99.0% | ≤ 150 ms | ≤ 1.0% |
| Payment Service | ≥ 99.5% | ≤ 200 ms | ≤ 0.5% |
| Notification Service | ≥ 99.0% | ≤ 200 ms | ≤ 1.0% |

> Order and Payment services have tighter SLOs due to their financial and transactional nature.

---

## 5. Monitoring Implementation

### 5.1 Prometheus Alert Rules (deployed)
- **ServiceDown**: Fires when `up == 0` for 30 seconds (critical).
- **HighCpuUsage**: Fires when CPU > 80% for 1 minute (warning).
- **HighErrorRate**: Fires when 5xx rate > 5% for 1 minute (critical).

### 5.2 Grafana Dashboards
- Real-time latency charts per service.
- Request rate and error rate panels.
- Service uptime indicators.
- Database connection status panel.

---

## 6. Error Budget Policy

When an error budget is exhausted (i.e., SLO is violated):
1. **Freeze non-critical deployments** until reliability is restored.
2. **Redirect engineering effort** to reliability improvements.
3. **Conduct a postmortem** to identify root cause and prevent recurrence.
4. **Increase monitoring** on the affected service for the next 7 days.
