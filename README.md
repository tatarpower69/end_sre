# End-to-End Implementation of Site Reliability Engineering Practices
## Multi-Orchestrated Microservices Infrastructure Using Docker Swarm, Kubernetes, Terraform, and Ansible

---

## Table of Contents
1. [Abstract](#abstract)
2. [System Architecture](#system-architecture)
3. [Microservices (7 Services)](#microservices)
4. [Environment Setup (Assignment 1)](#assignment-1--environment-setup)
5. [SLI/SLO Design (Assignment 2)](#assignment-2--slislo-design)
6. [Monitoring & Alerting (Assignment 3)](#assignment-3--monitoring--alerting)
7. [Incident Response (Assignment 4)](#assignment-4--incident-response)
8. [Infrastructure as Code (Assignment 5)](#assignment-5--infrastructure-as-code)
9. [Automation & Capacity Planning (Assignment 6)](#assignment-6--automation--capacity-planning)
10. [Multi-Orchestration Architecture](#multi-orchestration-architecture)
11. [Quick Start Guide](#quick-start-guide)
12. [Project Structure](#project-structure)

---

## Abstract

This project presents a comprehensive implementation of Site Reliability Engineering (SRE)
principles applied to a distributed microservices-based system. The system integrates
containerization, multi-platform orchestration (Docker Swarm + Kubernetes), monitoring
(Prometheus + Grafana), infrastructure provisioning (Terraform), configuration management
(Ansible), incident response, and capacity planning.

The architecture consists of **7 independent microservices** deployed using both Docker Swarm
and Kubernetes to demonstrate comparative orchestration strategies.

---

## System Architecture

```
User
 |
Frontend (Nginx) — Reverse Proxy — Port 80
 |
API Gateway (Nginx routes)
 |
+------------------------------------------------------------+
|                     Microservices                           |
|------------------------------------------------------------|
| Auth | User | Product | Order | Chat | Payment | Notif.   |
+------------------------------------------------------------+
 |
PostgreSQL (Database) + Postgres Exporter
 |
Monitoring: Prometheus → Grafana
Infrastructure: Terraform → AWS EC2
Configuration: Ansible → Automated Setup
Orchestration: Docker Swarm + Kubernetes (K3s)
```

---

## Microservices

| # | Service | Description | Port | Key Endpoints |
|---|---------|-------------|------|---------------|
| 1 | **Auth Service** | User authentication & JWT | 8000 | `/login`, `/register`, `/info` |
| 2 | **User Service** | User profile management | 8000 | `/users`, `/profile/{id}` |
| 3 | **Product Service** | Product catalog management | 8000 | `/products` |
| 4 | **Order Service** | Order processing with DB | 8000 | `/orders` (GET/POST) |
| 5 | **Chat Service** | Real-time messaging | 8000 | `/messages` |
| 6 | **Payment Service** | Payment processing simulation | 8000 | `/payments`, `/payments/process` |
| 7 | **Notification Service** | Email/alert dispatch | 8000 | `/notifications`, `/notifications/send` |

### Supporting Components
- **Frontend**: Nginx-based SRE Control Plane dashboard
- **Database**: PostgreSQL 13 with Prometheus exporter
- **Monitoring**: Prometheus + Grafana with pre-configured dashboards
- **Reverse Proxy**: Nginx API Gateway (all services behind `/api/{service}/`)

---

## Assignment 1 — Environment Setup

### Docker Environment
- Each microservice has its own `Dockerfile` (Python 3.9 + FastAPI + Uvicorn)
- All services include `curl` for health check probes
- Prometheus instrumentation via `prometheus-fastapi-instrumentator`

### Docker Compose Orchestration
```bash
docker-compose up -d          # Start all services
docker-compose ps             # Check status
docker-compose logs -f        # View logs
```

### Configuration Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Development/production orchestration |
| `docker-stack.yml` | Docker Swarm deployment with replicas |
| `.env` | Environment variables (secrets, ports) |
| `validate_config.ps1` | Pre-deployment validation script |

---

## Assignment 2 — SLI/SLO Design

> Full document: [`docs/SLI_SLO.md`](docs/SLI_SLO.md)

### Service Level Indicators (SLIs)
| SLI | Measurement | Prometheus Metric |
|-----|-------------|-------------------|
| Availability | Service uptime percentage | `up` |
| Latency | Request response time (p95) | `http_request_duration_seconds` |
| Error Rate | 5xx response percentage | `http_requests_total{status=~"5.."}` |
| Success Rate | 2xx/3xx response percentage | `http_requests_total{status=~"2..\|3.."}` |

### Service Level Objectives (SLOs)
| Metric | Target |
|--------|--------|
| Availability | ≥ 99.0% |
| Latency (p95) | ≤ 200 ms |
| Error Rate | ≤ 1.0% |

---

## Assignment 3 — Monitoring & Alerting

### Prometheus
- Scrapes all 7 microservices + PostgreSQL exporter
- Evaluates alert rules every 15 seconds
- Configuration: `monitoring/prometheus.yml`

### Grafana
- Pre-provisioned datasource (Prometheus)
- Pre-provisioned dashboard (System Metrics Overview)
- Access: `http://localhost:3000` (admin / admin)

### Alert Rules (`monitoring/alert.rules.yml`)
| Alert | Condition | Severity |
|-------|-----------|----------|
| ServiceDown | `up == 0` for 30s | Critical |
| HighCpuUsage | CPU > 80% for 1m | Warning |
| HighErrorRate | 5xx rate > 5% for 1m | Critical |

---

## Assignment 4 — Incident Response

> Full document: [`docs/INCIDENT_REPORT.md`](docs/INCIDENT_REPORT.md)

### Simulated Incident: Order Service Database Failure

**Scenario**: Order Service fails due to incorrect `DB_HOST` configuration.

**Impact**: Order creation unavailable for 14 minutes.

**Detection**: Prometheus `ServiceDown` alert fired within 30 seconds.

**Resolution**:
```bash
# 1. Diagnose
docker logs order-service --tail 50

# 2. Fix configuration
# Correct DB_HOST in .env file

# 3. Restart
docker compose restart order-service

# 4. Verify
curl http://localhost/api/order/health
```

**Postmortem**: Root cause analysis, action items, and lessons learned documented.

---

## Assignment 5 — Infrastructure as Code

### Terraform (`terraform/`)
Provisions AWS infrastructure:
- **VPC** with public subnet and Internet Gateway
- **EC2 Instance** (Ubuntu 22.04, t3.small)
- **Security Groups** for SSH, HTTP, Grafana, Prometheus
- **Elastic IP** for persistent public access
- **Automated bootstrap**: Docker installation + project deployment via `user_data`

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Key Terraform Files
| File | Purpose |
|------|---------|
| `main.tf` | VPC, EC2, Security Groups, Key Pair |
| `variables.tf` | Configurable parameters |
| `outputs.tf` | Public IP, URLs, SSH command |
| `terraform.tfvars` | AWS credentials (gitignored) |

---

## Assignment 6 — Automation & Capacity Planning

### Automation
> Full document: [`docs/CAPACITY_PLANNING.md`](docs/CAPACITY_PLANNING.md)

| Feature | Implementation |
|---------|----------------|
| Automated Deployment | Docker Compose + Swarm stack |
| Health Checks | HTTP probes on `/health` for every service |
| Restart Policies | `unless-stopped` (Compose), `on-failure` (Swarm) |
| Config Validation | `validate_config.ps1` pre-deployment script |
| Monitoring Alerts | Prometheus alert rules → Grafana |

### Capacity Planning
- **Load Testing**: `load_test.py` — async stress tester (10-100 concurrent users)
- **Bottleneck**: PostgreSQL connections + Order/Payment service CPU
- **Scaling**: HPA in Kubernetes (2-5 replicas for Order/Payment)

---

## Multi-Orchestration Architecture

### Docker Swarm (`docker-stack.yml`)
```bash
docker swarm init
docker stack deploy -c docker-stack.yml sre-app
docker service ls
```
Features: Service replicas, rolling updates, restart policies, resource limits, overlay network.

### Kubernetes (`k8s/`)
```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/services.yml
kubectl apply -f k8s/monitoring.yml
kubectl apply -f k8s/ingress.yml
kubectl apply -f k8s/hpa.yml
```
Features: Deployments, Services, ConfigMaps, Secrets, Ingress, HPA (auto-scaling), liveness/readiness probes, resource requests/limits.

### Ansible (`ansible/`)
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
ansible-playbook -i ansible/inventory.ini ansible/monitoring.yml
ansible-playbook -i ansible/inventory.ini ansible/k8s-setup.yml
```
Automates: Docker installation, Swarm init, project deployment, K3s setup, monitoring configuration.

---

## Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for load testing)

### 1. Configure Environment
```powershell
# Validate configuration
./validate_config.ps1
```

### 2. Deploy System
```bash
docker-compose up -d --build
```

### 3. Access Services
| Component | URL |
|-----------|-----|
| Frontend Dashboard | http://localhost |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Auth API | http://localhost/api/auth/health |
| Order API | http://localhost/api/order/health |
| Payment API | http://localhost/api/payment/health |

### 4. Run Load Test
```bash
pip install aiohttp
python load_test.py
```

---

## Project Structure

```
my_project/
├── auth-service/           # Microservice 1: Authentication
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── user-service/           # Microservice 2: User Profiles
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── product-service/        # Microservice 3: Product Catalog
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── order-service/          # Microservice 4: Order Processing
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── chat-service/           # Microservice 5: Chat/Messaging
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── payment-service/        # Microservice 6: Payment Processing
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── notification-service/   # Microservice 7: Notifications
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/               # Nginx Frontend + Dashboard
│   ├── Dockerfile
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── nginx.conf
├── monitoring/             # Prometheus + Grafana
│   ├── prometheus.yml
│   ├── alert.rules.yml
│   └── grafana/provisioning/
├── terraform/              # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── k8s/                    # Kubernetes Manifests
│   ├── namespace.yml
│   ├── configmap.yml
│   ├── postgres.yml
│   ├── services.yml
│   ├── monitoring.yml
│   ├── ingress.yml
│   └── hpa.yml
├── ansible/                # Configuration Management
│   ├── inventory.ini
│   ├── playbook.yml
│   ├── monitoring.yml
│   └── k8s-setup.yml
├── docs/                   # Documentation
│   ├── SLI_SLO.md
│   ├── INCIDENT_REPORT.md
│   └── CAPACITY_PLANNING.md
├── docker-compose.yml      # Docker Compose (development)
├── docker-stack.yml        # Docker Swarm (production)
├── load_test.py            # Load testing script
├── validate_config.ps1     # Configuration validator
├── .env                    # Environment variables
└── README.md               # This file
```

---

## Author

**Ilnur** — Site Reliability Engineering Course, End Term Project, May 2026

## Repository

GitHub: [https://github.com/tatarpower69/Site-Reliability-Engineering-](https://github.com/tatarpower69/Site-Reliability-Engineering-)
