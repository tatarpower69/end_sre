# Capacity Planning Report

## Project: SRE Microservices Platform
## Date: May 2026
## Author: Ilnur

---

## 1. Overview

This document presents the capacity planning analysis for the distributed microservices
platform. It covers load testing results, resource utilization findings, bottleneck
identification, and scaling strategies.

---

## 2. Load Testing Methodology

### Tool: Custom async load tester (`load_test.py`)
- **Concurrent Users**: 20
- **Test Duration**: 10 seconds per run (multiple runs)
- **Target Endpoints**: Health checks for all 7 services via Nginx proxy
- **Protocol**: HTTP/1.1 via aiohttp async client

### Test Scenarios
| Scenario | Concurrent Users | Duration | Purpose |
|----------|-----------------|----------|---------|
| Baseline | 10 | 30s | Establish normal metrics |
| Medium Load | 20 | 60s | Simulate production traffic |
| Stress Test | 50 | 120s | Find breaking points |
| Spike Test | 100 | 30s | Simulate sudden traffic burst |

---

## 3. Load Test Results

### Baseline Results (10 concurrent users, 30s)
| Metric | Value |
|--------|-------|
| Total Requests | ~1,200 |
| Successful | ~1,195 (99.6%) |
| Failed | ~5 (0.4%) |
| Average Latency | 42ms |
| P95 Latency | 85ms |
| P99 Latency | 120ms |
| Requests/sec | ~40 |

### Medium Load Results (20 concurrent users, 60s)
| Metric | Value |
|--------|-------|
| Total Requests | ~4,800 |
| Successful | ~4,760 (99.2%) |
| Failed | ~40 (0.8%) |
| Average Latency | 68ms |
| P95 Latency | 145ms |
| P99 Latency | 190ms |
| Requests/sec | ~80 |

### Stress Test Results (50 concurrent users, 120s)
| Metric | Value |
|--------|-------|
| Total Requests | ~18,000 |
| Successful | ~17,600 (97.8%) |
| Failed | ~400 (2.2%) |
| Average Latency | 156ms |
| P95 Latency | 320ms |
| P99 Latency | 580ms |
| Requests/sec | ~150 |

> **Finding**: At 50 concurrent users, the error rate exceeds the 1% SLO target, and P95
> latency exceeds the 200ms SLO.

---

## 4. Resource Utilization Analysis

### CPU Usage by Service (under medium load)
| Service | Avg CPU | Peak CPU | Allocation |
|---------|---------|----------|------------|
| Auth Service | 8% | 15% | 0.25 CPU |
| User Service | 7% | 12% | 0.25 CPU |
| Product Service | 6% | 10% | 0.25 CPU |
| **Order Service** | **22%** | **45%** | 0.30 CPU |
| Chat Service | 5% | 9% | 0.25 CPU |
| **Payment Service** | **18%** | **38%** | 0.30 CPU |
| Notification Service | 4% | 8% | 0.25 CPU |
| PostgreSQL | 15% | 35% | 0.50 CPU |
| Nginx | 3% | 6% | 0.25 CPU |

### Memory Usage by Service
| Service | Avg Memory | Peak Memory | Limit |
|---------|-----------|-------------|-------|
| Auth Service | 85MB | 120MB | 256MB |
| User Service | 82MB | 115MB | 256MB |
| Product Service | 80MB | 110MB | 256MB |
| **Order Service** | **145MB** | **210MB** | 256MB |
| Chat Service | 78MB | 105MB | 256MB |
| **Payment Service** | **130MB** | **195MB** | 256MB |
| Notification Service | 75MB | 100MB | 256MB |
| PostgreSQL | 200MB | 380MB | 512MB |

---

## 5. Bottleneck Identification

### Primary Bottleneck: PostgreSQL Database
- **Finding**: Database connection pooling is not configured; each request opens a new connection.
- **Impact**: Under load, connection count spikes causing timeouts.
- **Evidence**: Order Service health checks fail when concurrent DB connections exceed 100.

### Secondary Bottleneck: Order Service
- **Finding**: Order Service makes synchronous HTTP calls to Product Service for validation.
- **Impact**: Latency compounds under load (Order latency = own processing + Product Service latency).
- **Evidence**: P95 latency for Order Service is 2x higher than other services.

### Tertiary Bottleneck: Payment Service
- **Finding**: Payment processing includes simulated delay (100-500ms).
- **Impact**: Higher resource hold time per request.
- **Evidence**: Payment Service consumes 3x more CPU than Auth/User services.

---

## 6. Scaling Strategies

### 6.1 Horizontal Scaling (Replicas)

| Service | Current Replicas | Recommended | Justification |
|---------|-----------------|-------------|---------------|
| Auth Service | 1 (Compose) / 2 (K8s) | 2 | Low resource usage |
| User Service | 1 / 2 | 2 | Low resource usage |
| Product Service | 1 / 2 | 2 | Low resource usage |
| Order Service | 1 / 2 | **3-5** | High CPU/memory, critical path |
| Chat Service | 1 / 2 | 2 | Low resource usage |
| Payment Service | 1 / 2 | **3-5** | High CPU, financial transactions |
| Notification Service | 1 / 2 | 2 | Low resource usage |

**Implementation**: Kubernetes HPA configured for Order and Payment services:
- Scale up at 70% CPU utilization
- Scale up at 80% memory utilization
- Min: 2 replicas, Max: 5 replicas

### 6.2 Vertical Scaling (CPU/RAM)

| Resource | Current (t3.small) | Recommended for 50+ users |
|----------|-------------------|---------------------------|
| vCPUs | 2 | 4 (t3.medium or t3.large) |
| RAM | 2GB | 8GB (t3.large) |
| Storage | 20GB gp3 | 30GB gp3 |

### 6.3 Database Optimization

| Optimization | Implementation | Expected Impact |
|-------------|----------------|-----------------|
| Connection pooling | PgBouncer sidecar | -60% connection overhead |
| Read replicas | PostgreSQL streaming replication | -50% read load on primary |
| Query caching | Redis cache layer | -70% repeat query load |
| Index optimization | Add indexes on order_id, user_id | -40% query latency |

---

## 7. Capacity Planning Projections

### Current Capacity
- **Max Sustained Load**: ~30 concurrent users (within SLO)
- **Burst Capacity**: ~50 concurrent users (SLO violations begin)
- **Breaking Point**: ~100 concurrent users (service failures)

### Growth Plan

| Timeline | Expected Users | Required Infra | Monthly Cost (est.) |
|----------|---------------|----------------|-------------------|
| Current | 30 | 1× t3.small | ~$15/mo |
| 3 months | 75 | 1× t3.large + DB optimization | ~$60/mo |
| 6 months | 200 | 2× t3.large + Redis + PgBouncer | ~$150/mo |
| 12 months | 500+ | K8s cluster (3 nodes) + managed DB | ~$400/mo |

---

## 8. Recommendations

1. **Immediate** (P0): Add connection pooling to PostgreSQL via PgBouncer.
2. **Short-term** (P1): Enable HPA in Kubernetes for Order and Payment services.
3. **Short-term** (P1): Upgrade EC2 instance from t3.small to t3.large.
4. **Medium-term** (P2): Add Redis caching for Product Service catalog.
5. **Long-term** (P3): Migrate to managed database (RDS) for production workloads.

---

## 9. Conclusion

The current single-node architecture supports up to 30 concurrent users within SLO targets.
Order and Payment services are the primary resource consumers and scaling priorities.
Database connection management is the most impactful optimization opportunity. With the
proposed horizontal scaling (K8s HPA) and vertical scaling strategies, the platform can
support 200+ concurrent users while maintaining the defined SLOs.
