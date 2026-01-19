# MT5-Docker Monitoring Stack

A lightweight, resource-efficient observability stack for MT5-Docker based on VictoriaMetrics.

## Stack Components

| Component | Purpose | URL |
|-----------|---------|-----|
| **VictoriaMetrics** | Time-series database for metrics | http://localhost:8428/vmui |
| **VictoriaLogs** | Log storage and querying | http://localhost:9428/select/vmui |
| **Grafana** | Dashboards and visualization | http://localhost:3000 |
| **vmagent** | Metrics collection agent | http://localhost:8429 |
| **cAdvisor** | Container metrics | http://localhost:8080 |
| **node_exporter** | Host system metrics | http://localhost:9100 |
| **Vector** | Log collection agent | - |

## Resource Usage

Total monitoring overhead: **~500MB RAM**, **~1 CPU core**

| Service | Memory Limit | CPU Limit |
|---------|--------------|-----------|
| VictoriaMetrics | 128MB | 0.5 |
| VictoriaLogs | 128MB | 0.5 |
| Grafana | 256MB | 0.5 |
| vmagent | 64MB | 0.25 |
| cAdvisor | 64MB | 0.25 |
| node_exporter | 32MB | 0.1 |
| Vector | 64MB | 0.25 |

## Quick Links

### By Task

| I want to... | Go to |
|--------------|-------|
| Check container CPU/memory | [Grafana](http://localhost:3000) → cAdvisor dashboard |
| Search logs | [VictoriaLogs UI](http://localhost:9428/select/vmui) |
| Query metrics | [VictoriaMetrics UI](http://localhost:8428/vmui) |
| See all running services | `docker compose ps` |

### By Audience

| You are... | Start here |
|------------|------------|
| Returning user needing quick commands | [QUICKSTART.md](./QUICKSTART.md) |
| Maintainer understanding the system | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| New user learning the stack | [tutorials/01_GETTING_STARTED.md](./tutorials/01_GETTING_STARTED.md) |

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin |

Configure via environment variables in `.env`:
```bash
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_secure_password
```

## Data Retention

| Data Type | Retention | Location |
|-----------|-----------|----------|
| Metrics | 30 days | `vmdata` volume |
| Logs | 7 days | `vldata` volume |
| Dashboards | Persistent | `grafana-data` volume |
