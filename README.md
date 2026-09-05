# HPLC Chromatography Peak Resolver

> **Domain:** Computational Biology & AI Drug Discovery
> **Reference Guidelines & Standards:** `wwPDB, IUPAC & CLSI Computational Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

HPLC Chromatography Peak Resolver is an enterprise-grade analytical platform for chromatographic peak deconvolution, purity assessment, and anomaly detection. It combines deterministic calculation engines with multi-agent consensus workflows to evaluate analytical measurements against reference standards.

The system provides two parallel implementations:
- **agents/ (Enterprise v3.0.0):** wwPDB / IUPAC / OpenSMILES / ISAC Standards compliance
- **hplc_resolver/ (Frontier v2.0.0):** USP <621> Chromatography Standards compliance

---

## Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine:** Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification:** Multi-tier categorization (ROUTINE, ELEVATED_RISK, CRITICAL_STAT_PANIC) with automated clinical/operational action recommendations.
- **Validation & Guardrails:** Rigorous input bounds checking, NaN/Inf rejection, and anomaly detection.
- **Zero-PHI Outbound Guard:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
- **FastAPI REST API:** OpenAPI 3.1 endpoints with Prometheus-compatible metrics.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/hplc-chromatography-peak-resolver.git
cd hplc-chromatography-peak-resolver

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set the required audit secret key (must be at least 32 characters)
export AUDIT_SECRET_KEY="your-cryptographically-secure-random-key-here"
```

---

## CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. System Configuration Query
```bash
python cli.py chat "Explain specifications"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task/case identifier
- `--target`: Target identifier (e.g., specimen key)
- `--primary`: Primary domain measurement (float, must be finite)
- `--secondary`: Secondary kinetic/confidence score (float, must be finite)
- `--critical`: Emergency escalation flag
- `--status`: Status descriptor (e.g., NOMINAL, DISCORDANT, ANOMALY)

### Input Data Schema (CSV Batch)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target/specimen identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary metric value | Optional (default: 0.0) |
| `is_critical_flag` | Critical escalation flag | Optional (default: false) |
| `status_descriptor` | Status code descriptor | Optional (default: NOMINAL) |

---

## REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Operational metrics |
| POST | `/api/audit` | Submit task evaluation |
| POST | `/api/chat` | System configuration query |
| GET | `/api/audit/logs` | Retrieve audit trail |

---

## Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs. Requires `AUDIT_SECRET_KEY` environment variable (min 32 chars).
* **Path Traversal Protection:** All file operations are restricted to the working directory.
* **Input Validation:** Metric values are validated to reject NaN/Inf and enforce bounds.

---

## Testing & Verification

```bash
# Set test environment variable
export AUDIT_SECRET_KEY="test-secret-key-for-pytest-min-32-chars-long"

# Run the automated test suite
pytest -v

# Execute high-throughput batch simulation benchmarks
python simulator.py 1000
```

---

## Container Deployment

```bash
docker build -t hplc-chromatography-peak-resolver .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key-here-min-32-chars" hplc-chromatography-peak-resolver
```

---

## Project Structure

```
hplc-chromatography-peak-resolver/
├── agents/                  # Enterprise v3.0.0 implementation
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic v2 schemas
│   ├── supervisor.py       # Multi-agent orchestrator
│   ├── workers.py          # Specialized domain workers
│   ├── llm_factory.py      # LLM client factory
│   ├── metrics.py          # Prometheus metrics collector
│   ├── learning.py         # Bayesian calibration engine
│   └── streamer.py         # WebSocket telemetry broadcaster
├── hplc_resolver/          # Frontier v2.0.0 implementation
│   ├── agents.py           # Coordinator and sub-agents
│   ├── engine.py           # Domain calculation engine
│   ├── models.py           # Dataclass schemas
│   ├── cli.py              # CLI entry point
│   └── server.py           # FastAPI server factory
├── tests/                  # Pytest test suite
├── web/                    # Operations console (HTML/JS)
├── cli.py                  # Main CLI entry point
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Domain enrichment engines
├── sample.csv              # Sample batch input data
├── Dockerfile              # Container build config
└── pyproject.toml          # Project metadata
```
