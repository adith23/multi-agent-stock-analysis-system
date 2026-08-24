# Multi-Agent Stock Analysis System

[![Architecture](https://img.shields.io/badge/Architecture-Service--Layer%20DDD%20%2B%20LangGraph-blue.svg)](#system-architecture)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](#prerequisites)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20.svg?logo=django&logoColor=white)](#technology-stack)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4%2B-FF4F00.svg)](#multi-agent-research-workflow)
[![Next.js](https://img.shields.io/badge/Next.js-15%20(React%2019)-black.svg?logo=next.js&logoColor=white)](#frontend-application)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791.svg?logo=postgresql&logoColor=white)](#prerequisites)
[![Celery](https://img.shields.io/badge/Celery-5.4%2B-37814A.svg?logo=celery&logoColor=white)](#technology-stack)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Research-lightgrey.svg)](#)

An institutional-grade, AI-assisted equity research and portfolio decision-support platform. The system mirrors institutional research desk workflows by ingesting multi-modal financial data, computing deterministic valuation, forensic accounting, and risk metrics, running parallel specialist reasoning agents, stress-testing hypotheses through cyclic adversarial bull-vs-bear debate, enforcing binding risk/compliance gates, and generating actionable buy/sell signals under durable Human-in-the-Loop (HITL) Portfolio Manager review.

---

## Table of Contents

- [System Architecture & Core Principles](#system-architecture--core-principles)
- [Multi-Agent Research Workflow](#multi-agent-research-workflow)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Environment Configuration (`.env`)](#environment-configuration-env)
- [Quick Start — Docker Compose](#quick-start--docker-compose)
- [Local Setup — Without Docker](#local-setup--without-docker)
- [Frontend Dashboard](#frontend-dashboard)
- [End-to-End Workflow Walkthrough](#end-to-end-workflow-walkthrough)
- [API Reference & Interactive Docs](#api-reference--interactive-docs)
- [Testing & Quality Verification](#testing--quality-verification)
- [Governance, Security & Auditability](#governance-security--auditability)

---

## System Architecture & Core Principles

The platform strictly enforces the **Separation of Responsibilities** mandated by institutional AI engineering standards (SRS §1.5):

| Role | Component | Key Implementations |
| :--- | :--- | :--- |
| **Reasoning & Synthesis** | **LangGraph Agents** | Macro, Fundamental, Technical, Sentiment, Bull vs. Bear Adversarial, Risk, Portfolio Manager, Supervisor. |
| **Deterministic Calculations** | **Engines** | DCF Valuation, Multiples, DDM, Beneish M-Score, Altman Z-Score, Sloan Accruals, VaR, Kelly/Risk-Parity Sizing, MVO/HRP Optimization. |
| **Classification & Extraction** | **ML Models** | Lazy-loaded FinBERT (Sentiment), Gaussian HMM (Regime Detection), Attention/Crowding Z-Score Detector. |
| **Enforcement & Hard Gates** | **Rule Engines** | Binding Risk Budget Limits, Restricted Lists, Regulatory Compliance, Signal Conviction Taxonomy, Time Horizon Framework. |
| **State & Persistence** | **Django + PostgreSQL** | 11 Bounded Context apps, `PostgresSaver` durable LangGraph checkpointing, immutable audit trails. |
| **Asynchronous Scheduling** | **Celery + Redis** | Outer pipeline orchestration, parallel specialist chords, 5-min exit monitoring, hourly catalyst checks, daily performance attribution. |

---

## Multi-Agent Research Workflow

```
                               ┌─── [1] Macro Agent ────────┐
                               ├─── [2] Fundamental Agent ──┤
START ──▶ Parallel Fan-Out ───┼─── [3] Technical Agent ────┼──▶ Join & Aggregate
                               └─── [4] Sentiment Agent ────┘
                                             │
                                             ▼
                               ┌─── Bull Advocate ◄───┐
                               ▼                      │ (Cyclic debate loop, max 3 rounds)
                               Bear Advocate ─────────┤
                               │                      │
                               ▼                      │
                               Moderator (Verdict) ───┘
                                             │ [conclude]
                                             ▼
                               Adversarial Decision Memo
                                             │
                                             ▼
                               Risk Manager & Compliance Gates
                               (Binding check: if blocked ➔ zero sizing & terminate)
                                             │ [passed / warnings]
                                             ▼
                               Position Sizing & Portfolio Optimization
                                             │
                                             ▼
                               [PORTFOLIO MANAGER HITL CHECKPOINT]
                               (State machine pauses at interrupt_before node)
                                             │
                                             ▼ (Human PM approves/rejects via API/UI)
                               Actionable Buy/Sell Recommendation & Exit Strategy
```

---

## Technology Stack

### Backend
* **Language & Framework**: Python 3.12, Django 5.1+, Django REST Framework (DRF).
* **Agent Framework**: LangGraph 0.4+, LangChain Core, `langgraph-checkpoint-postgres`.
* **LLM Provider**: Google Gemini (`gemini-2.5-flash`, `gemini-3.1-flash-lite`) via `langchain-google-genai`.
* **Asynchronous Tasks & Scheduling**: Celery 5.4+, `django-celery-beat`, Redis 7+.
* **Database & Storage**: PostgreSQL 16+ with binary psycopg3 driver.
* **Financial Data & Analysis**: `pandas`, `numpy`, `scipy`, `pandas-ta`, `PyPortfolioOpt`, `yfinance`, `finnhub-python`, `fredapi`, `edgartools`.
* **Machine Learning**: `torch`, `transformers` (ProsusAI/FinBERT), `hmmlearn`, `scikit-learn`.
* **API Documentation & Utilities**: `drf-spectacular` (OpenAPI 3.0), `django-structlog`, `tenacity`.

### Frontend
* **Framework**: Next.js 15 (App Router), React 19, TypeScript.
* **Styling**: TailwindCSS, CSS Modules, Lucide React Icons.
* **Package Manager**: `pnpm` / `npm`.

---

## Repository Structure

```text
multi-agent-stock-analysis-system/
├── backend/                               # Django Project Root
│   ├── agents/                            # Standalone LangGraph Agent StateGraphs
│   │   ├── base/                          # Shared agent infrastructure, state & checkpointer
│   │   ├── macro/                         # Macroeconomic / Regime Agent (FR-008→FR-013)
│   │   ├── fundamental/                   # Fundamental Research Agent (FR-014→FR-020)
│   │   ├── technical/                     # Technical Analyst Agent (FR-021→FR-026)
│   │   ├── sentiment/                     # Sentiment & News Agent (FR-027→FR-033)
│   │   ├── adversarial/                   # Cyclic Bull vs. Bear Debate Agent (FR-034→FR-039)
│   │   ├── risk/                          # Risk Manager Agent (FR-040→FR-046)
│   │   ├── pm/                            # Portfolio Manager HITL Agent (FR-047→FR-052)
│   │   └── supervisor/                    # Multi-Agent Parallel Supervisor Graph
│   ├── apps/                              # 11 Domain-Driven Django Bounded Contexts
│   │   ├── core/                          # Shared kernel, base models, value objects, circuit breakers
│   │   ├── data_ingestion/                # External connectors (Finnhub, FRED, SEC, News, YFinance)
│   │   ├── market_data/                   # Securities, OHLCV bars, financial statements, peer groups
│   │   ├── research/                      # Specialist reports, theses, catalysts, decision memos
│   │   ├── signals/                       # Conviction scores, signal agreement matrix, regime states
│   │   ├── risk_compliance/               # Risk limits, portfolio state, compliance policies
│   │   ├── portfolio/                     # PM recommendations, sizing, exit strategies, attribution
│   │   ├── orchestrator/                  # AnalysisRun state machine, Celery tasks, pipeline services
│   │   ├── audit/                         # Immutable audit trails & request tracing
│   │   ├── users/                         # Authentication & Role-Based Access Control (RBAC)
│   │   └── api/                           # Aggregated versioned REST API (v1), views, serializers
│   ├── engines/                           # Standalone Deterministic Calculation Modules
│   │   ├── valuation/                     # DCF, Multiples, DDM valuation engines
│   │   ├── earnings_quality/              # Beneish M-Score, Altman Z-Score, Sloan Accruals
│   │   ├── technical/                     # Technical indicator, trend, and S/R engines
│   │   ├── risk/                          # VaR, Expected Shortfall, Stress-Testing engines
│   │   ├── position_sizing/               # Kelly, Vol-Targeting, Risk-Parity, Fixed-Fractional
│   │   ├── exit_strategy/                 # Stop-Loss, Profit-Target, Trailing-Stop engines
│   │   └── portfolio_optimization/        # Mean-Variance Optimization & Hierarchical Risk Parity
│   ├── ml/                                # Machine Learning Wrappers & Registries
│   │   ├── finbert/                       # FinBERT sentiment analysis model
│   │   ├── regime/                        # Gaussian HMM market regime classifier
│   │   └── attention/                     # News burst & narrative crowding detector
│   ├── rules/                             # Deterministic Rule Engines & Hard Controls
│   │   ├── conviction/                    # Inter-agent agreement & conviction scoring rules
│   │   ├── time_horizon/                  # Tactical / Medium-term / Strategic classifiers
│   │   ├── compliance/                    # Restricted lists & regulatory compliance checks
│   │   └── risk_limits/                   # Hard risk budget enforcement rules
│   ├── config/                            # Django project settings, ASGI/WSGI, Celery app
│   ├── docs/                              # Detailed phase documentation & non-Docker runbooks
│   ├── requirements/                      # Base, dev, test, and prod dependency files
│   ├── tests/                             # Unit, integration, contracts, e2e, and load tests
│   └── manage.py                          # Management script
├── frontend/                              # Next.js 15 Institutional Dashboard
│   ├── src/app/                           # App router pages, layouts, and style tokens
│   ├── public/                            # Static assets
│   └── package.json                       # Frontend dependencies & build scripts
├── docker/                                # Containerization manifests
│   ├── Dockerfile.backend                 # Backend production container
│   ├── Dockerfile.frontend                # Frontend Next.js container
│   └── docker-compose.yml                 # Full stack (PostgreSQL, Redis, Django, Celery, Frontend)
└── SOFTWARE_REQUIREMENTS_SPECIFICATION.md # Formal SRS v2.0 specification
```

---

## Prerequisites

Ensure the following tools are installed on your host machine:

* **Python**: `3.12.x` ([python.org](https://www.python.org/))
* **Node.js**: `20.x` or newer & `pnpm` (or `npm`) ([nodejs.org](https://nodejs.org/))
* **PostgreSQL**: `16.x` or newer ([postgresql.org](https://www.postgresql.org/))
* **Redis**: `7.x` or newer (Native, WSL2 Ubuntu, or Memurai on Windows)
* **Git**: `2.x+`
* *(Optional)* **Docker & Docker Compose**: If running via containerized stack.

---

## Environment Configuration (`.env`)

Copy the example environment file to `.env` in the repository root:

```bash
cp .env.example .env
```

Configure the following essential environment variables:

```dotenv
# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=generate_a_secure_random_key_here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Databases
DATABASE_URL=postgresql://stockanalysis:your_password@127.0.0.1:5432/stockanalysis
LANGGRAPH_DATABASE_URL=postgresql://stockanalysis:your_password@127.0.0.1:5432/stockanalysis

# Redis & Celery
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2

# LLM Providers (Required for Agent Reasoning)
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
LLM_DEFAULT_MODEL=gemini-2.5-flash
LLM_FALLBACK_MODEL=gemini-3.1-flash-lite

# Financial Data Providers (Optional / Fallbacks available)
FINNHUB_API_KEY=your_finnhub_api_key
FRED_API_KEY=your_fred_api_key
TAVILY_API_KEY=your_tavily_search_api_key
SEC_EDGAR_USER_AGENT=YourName yourname@example.com
```

> [!NOTE]
> To generate a secure `DJANGO_SECRET_KEY`, run:
> `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

---

## Quick Start — Docker Compose

To launch the complete application stack (PostgreSQL, Redis, Django API, Celery Worker, Celery Beat, and Next.js Frontend) using Docker:

```bash
# 1. Build and start all services in detached mode
docker compose -f docker/docker-compose.yml up --build -d

# 2. Apply database migrations and bootstrap LangGraph tables
docker compose -f docker/docker-compose.yml exec backend python manage.py bootstrap_infrastructure

# 3. Seed default data source connector policies
docker compose -f docker/docker-compose.yml exec backend python manage.py bootstrap_data_sources

# 4. Create an administrative user
docker compose -f docker/docker-compose.yml exec backend python manage.py createsuperuser
```

Once running, access:
* **Frontend Dashboard**: `http://localhost:3000/`
* **Backend REST API**: `http://localhost:8000/api/v1/`
* **Swagger API Documentation**: `http://localhost:8000/api/docs/`
* **Django Admin**: `http://localhost:8000/admin/`

---

## Local Setup — Without Docker

For native development on **Windows (PowerShell)**, macOS, or Linux without Docker, follow these steps:

### 1. Database Setup (PostgreSQL)

Open your PostgreSQL terminal (`psql -U postgres -h 127.0.0.1`) and create the application role and database:

```sql
CREATE ROLE stockanalysis WITH LOGIN PASSWORD 'your_password';
CREATE DATABASE stockanalysis OWNER stockanalysis;
\q
```

### 2. Python Virtual Environment Setup

From the repository root:

```powershell
# Windows PowerShell

# 1. Create virtual environment
python -m venv backend\venv

# 2. Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# 3. Upgrade pip and install development dependencies
pip install --upgrade pip
pip install -r backend\requirements\dev.txt
```

*(Alternatively on Windows Command Prompt: `backend\venv\Scripts\activate.bat`)*

```bash
# macOS / Linux

# 1. Create virtual environment
python -m venv backend/venv

# 2. Activate virtual environment
source backend/venv/bin/activate

# 3. Upgrade pip and install development dependencies
pip install --upgrade pip
pip install -r backend/requirements/dev.txt
```

### 3. Bootstrap Database & LangGraph Infrastructure

```bash
# Windows PowerShell
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py bootstrap_infrastructure
.\venv\Scripts\python.exe manage.py bootstrap_data_sources
.\venv\Scripts\python.exe manage.py createsuperuser

# macOS / Linux
cd backend
python manage.py check
python manage.py bootstrap_infrastructure
python manage.py bootstrap_data_sources
python manage.py createsuperuser
```

### 4. Running the Backend (4 Terminals)

Open four separate terminal windows from the repository root:

#### **Terminal 1: Redis Server**
```bash
# Windows (WSL2 Ubuntu)
wsl -d Ubuntu -- sudo service redis-server start
wsl -d Ubuntu -- redis-cli ping

# macOS / Linux
redis-server
```

#### **Terminal 2: Celery Worker**
```bash
# Windows (Use --pool=solo on Windows)
cd backend
.\venv\Scripts\celery.exe -A config worker --loglevel=INFO --pool=solo

# macOS / Linux
cd backend
celery -A config worker --loglevel=INFO --concurrency=4
```

#### **Terminal 3: Celery Beat (Scheduler)**
```bash
# Windows PowerShell
cd backend
.\venv\Scripts\celery.exe -A config beat --loglevel=INFO --scheduler=django_celery_beat.schedulers:DatabaseScheduler

# macOS / Linux
cd backend
celery -A config beat --loglevel=INFO --scheduler=django_celery_beat.schedulers:DatabaseScheduler
```

#### **Terminal 4: Django REST API Server**
```bash
# Windows PowerShell
cd backend
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# macOS / Linux
cd backend
python manage.py runserver 127.0.0.1:8000
```

Verify backend health by visiting:
* Readiness Check: `http://127.0.0.1:8000/api/v1/health/ready/` (Verifies DB, Cache, and Celery Broker).
* Interactive Swagger Docs: `http://127.0.0.1:8000/api/docs/`

---

## Frontend Dashboard

To run the Next.js institutional research interface:

```bash
cd frontend

# Install dependencies
pnpm install
# or: npm install

# Start local development server
pnpm dev
# or: npm run dev
```

Open `http://localhost:3000` to view the interactive dashboard featuring:
* Interactive price charts and real-time execution log streams.
* Specialist Agent breakdown cards (Macro Threat, Fundamental Scores, Technical Cues, Sentiment Gauges).
* Bull vs. Bear Debate arena, pre-mortem failure mode cards, and catalyst timeline.
* Risk & Compliance validation matrix.
* Portfolio Manager decision card with conviction sliders, sizing recommendations, and interactive Human-in-the-Loop **Approve / Reject** controls.

---

## End-to-End Workflow Walkthrough

### Step 1: Ingest Sample Market Data

Enable the fallback Yahoo Finance connector and ingest 2 years of daily price bars for Apple (`AAPL`):

```bash
# 1. Enable keyless yfinance connector
python manage.py shell -c "from apps.data_ingestion.models import DataSourceConfiguration; DataSourceConfiguration.objects.filter(source_type='yfinance').update(is_enabled=True)"

# 2. Ingest OHLCV data synchronously
python manage.py ingest_data --source yfinance --category ohlcv --params "{\"symbol\":\"AAPL\",\"period\":\"2y\",\"interval\":\"1d\"}" --synchronous
```

### Step 2: Trigger End-to-End Stock Analysis

#### Via Management Command:
```bash
python manage.py run_analysis AAPL --exchange US --username YOUR_SUPERUSER
```

#### Via Authenticated REST API:
```bash
# 1. Obtain JWT token
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "YOUR_USER", "password": "YOUR_PASSWORD"}'

# 2. Dispatch analysis run (with required Idempotency-Key)
curl -X POST http://127.0.0.1:8000/api/v1/analysis/ \
     -H "Authorization: Bearer <ACCESS_TOKEN>" \
     -H "Idempotency-Key: 7b36f1c4-9842-4f9e-b91c-29b53f6db123" \
     -H "Content-Type: application/json" \
     -d '{"symbol": "AAPL", "exchange": "US", "scope": "single", "config": {"portfolio_value": 100000}}'
```

### Step 3: Inspect Progress & Specialist Reports

Poll the run status:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/analysis/<RUN_ID>/ \
     -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Inspect specialist outputs:
* **Specialist Reports**: `GET /api/v1/analysis/<RUN_ID>/specialists/`
* **Bull vs. Bear Memo**: `GET /api/v1/analysis/<RUN_ID>/bull-bear/`
* **Conviction Matrix**: `GET /api/v1/analysis/<RUN_ID>/conviction/`
* **Risk & Compliance**: `GET /api/v1/analysis/<RUN_ID>/risk/`
* **Draft Recommendation**: `GET /api/v1/analysis/<RUN_ID>/recommendation/`

### Step 4: Human-in-the-Loop (HITL) PM Approval

When the analysis reaches `awaiting_pm_approval`, an authorized Portfolio Manager can approve, reject, or defer the recommendation, resuming the LangGraph execution without re-running LLMs:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analysis/<RUN_ID>/approve/ \
     -H "Authorization: Bearer <ACCESS_TOKEN>" \
     -H "Idempotency-Key: c9d78901-4567-4890-abcd-1234567890ab" \
     -H "Content-Type: application/json" \
     -d '{"rationale": "Approved based on strong free cash flow durability and manageable tail risk.", "expected_version": 1}'
```

---

## API Reference & Interactive Docs

The system generates OpenAPI 3.0 schemas through `drf-spectacular`:

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/live/` | Process liveness probe | Public |
| `GET` | `/api/v1/health/ready/` | Dependency readiness probe (DB, Redis, Celery) | Public |
| `POST` | `/api/v1/auth/token/` | Obtain JWT access and refresh token pair | Public |
| `POST` | `/api/v1/analysis/` | Dispatch a new multi-agent analysis run | Analyst, PM, Admin |
| `GET` | `/api/v1/analysis/{id}/` | Get analysis state and pipeline step history | Authenticated |
| `GET` | `/api/v1/analysis/{id}/specialists/` | View Macro, Fundamental, Technical, Sentiment outputs | Authenticated |
| `GET` | `/api/v1/analysis/{id}/bull-bear/` | View Adversarial debate memo and pre-mortem | Authenticated |
| `GET` | `/api/v1/analysis/{id}/conviction/` | View conviction scores and inter-agent matrix | Authenticated |
| `GET` | `/api/v1/analysis/{id}/risk/` | View risk limits, VaR, and compliance checks | Sensitive Data Role |
| `GET` | `/api/v1/analysis/{id}/recommendation/` | View draft or finalized PM recommendation | Sensitive Data Role |
| `POST` | `/api/v1/analysis/{id}/approve/` | Submit PM approval decision (HITL resume) | Portfolio Manager |
| `POST` | `/api/v1/analysis/{id}/reject/` | Submit PM rejection decision (HITL resume) | Portfolio Manager |
| `GET` | `/api/v1/portfolio/` | View current portfolio holdings and weights | Sensitive Data Role |
| `POST` | `/api/v1/scenarios/` | Run custom what-if macroeconomic stress test | Authenticated |
| `GET` | `/api/v1/catalysts/` | List upcoming catalysts and thesis linkages | Authenticated |
| `GET` | `/api/v1/alerts/` | List active regime shifts and exit trigger alerts | Authenticated |

---

## Testing & Quality Verification

The test suite is structured across unit, integration, contract, end-to-end, and load testing layers:

```bash
cd backend

# 1. Run Python style and formatting checks
.\venv\Scripts\ruff.exe check .
.\venv\Scripts\black.exe --check .

# 2. Validate Django migrations & OpenAPI schema
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py spectacular --file openapi.yaml --validate

# 3. Execute Pytest suite with code coverage
.\venv\Scripts\pytest.exe --cov --cov-report=term-missing

# 4. Run concurrent load test profile (Locust)
locust -f tests/load/locustfile.py --host http://127.0.0.1:8000
```

---

## Governance, Security & Auditability

* **Data Isolation**: Ingestion components only communicate with public data APIs; internal portfolio holdings, private risk limits, and compliance lists are isolated behind RBAC permissions (NFR-015–NFR-017).
* **Point-in-Time Integrity**: All analysis runs record immutable cutoff timestamps (`available_at <= cutoff`) and configuration hashes, preventing future data leakage during backtests and historical evaluations.
* **Deterministic Risk Gates**: Hard risk and compliance limits cannot be overridden by LLM reasoning. Violations immediately block trade execution and set allocations to zero.
* **Immutable Audit Trail**: Every data transformation, prompt version, agent output, and reviewer action is logged with correlation IDs for post-trade attribution and audit compliance.

---

## Contributing & License

* **License**: Internal Research / Proprietary
* **Specification Traceability**: All features map directly to requirements in [SOFTWARE_REQUIREMENTS_SPECIFICATION.md](SOFTWARE_REQUIREMENTS_SPECIFICATION.md).
