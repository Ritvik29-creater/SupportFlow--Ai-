# 🍔 SupportFlow AI — Agentic Food Delivery Support Platform

> **Full-Stack Agentic AI Platform** | Python · FastAPI · React/Vanilla JS · PostgreSQL · Redis · LangGraph · RAG · ChromaDB · Docker · LangSmith

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-blue)](https://www.trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)

---

## 📌 Project Overview

**SupportFlow AI** is a production-grade, full-stack **agentic customer support platform** engineered specifically for food delivery operations. It combines **deterministic multi-agent state machines (LangGraph)**, **policy-grounded RAG (ChromaDB)**, **PostgreSQL transactional records**, **Redis background task workers**, and a **modern web interface**.

Unlike basic chatbots, the system enforces **deterministic control**: LLMs generate responses, but **Python guards determine routing, hallucination blocking, prompt-injection defense, and human escalation**.

---

## 🎯 Key Resume Highlights & Architecture

### 1. Multi-Agent Orchestration (LangGraph)
- **Specialized Sub-Agents**: Dedicated agents for `Order Tracking`, `Payments & Billing`, `Refunds & Cancellations`, `Restaurant Inquiries`, and `General Policy RAG`.
- **Confidence-Aware Routing**: Evaluates response quality (0.0–1.0) with automated 3-way branching:
  - `High (> 0.65)`: Direct grounded response
  - `Medium (0.40 – 0.65)`: Policy context + Clarifying follow-up
  - `Low (< 0.40) / Force Escalate`: Creates support ticket and routes to human queue
- **Stateful Memory**: Maintains multi-turn conversation context across user queries.

### 2. Policy-Grounded RAG Pipeline (ChromaDB + HuggingFace)
- **Structured Knowledge Base**: Domain-specific markdown documentation covering refund guarantees, cancellation stages, delivery delays, and dietary guidelines.
- **Query Rewriting Fallback**: Dynamically rewrites under-specified queries incorporating conversation history before fallback retries.
- **Grounding Guardrails**: Pre-response verification detecting factual discrepancies or hallucinations before customer delivery.

### 3. PostgreSQL Database & REST API (FastAPI)
- **7 Relational Models**: `Customers`, `Restaurants`, `Orders`, `Order Items`, `Payments`, `Refunds`, `Support Tickets`.
- **JWT Authentication & RBAC**: Role-based access control with secure bcrypt password hashing.
- **REST Endpoints**: CRUD operations for active orders, real-time tracking, payment verification, and refund requests.

### 4. Redis Background Processing
- **Ticket Escalation Worker**: Asynchronous queue processing SLA targets, calculating ticket urgency based on sentiment/keywords.
- **Notification Worker**: Dispatches async alerts for order delays and ticket resolutions.

### 5. Dockerized Multi-Container Architecture
- One-click deployment with `docker-compose` running PostgreSQL, Redis, FastAPI Backend, and Background Worker.

---

## 🗺️ Multi-Agent Workflow Diagram

```
                              ┌───────────────────────────┐
                              │     Customer Request      │
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │  🛡️ Injection Guardrail    │
                              └─────────────┬─────────────┘
                                            │ Passed
                                            ▼
                              ┌───────────────────────────┐
                              │   🧠 Intent Classifier    │
                              └─────────────┬─────────────┘
                                            │
         ┌───────────────┬──────────────────┼───────────────┬───────────────┐
         ▼               ▼                  ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐      ┌───────────┐   ┌───────────┐   ┌───────────┐
   │🛵 Order   │   │💳 Payment │      │💰 Refund  │   │🍽️ Rest.   │   │📚 Policy  │
   │  Agent    │   │  Agent    │      │  Agent    │   │  Agent    │   │ RAG Agent │
   └─────┬─────┘   └─────┬─────┘      └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         └───────────────┴──────────────────┼───────────────┴───────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │  🛡️ Grounding Guardrail   │
                              │ (Hallucination Detection) │
                              └─────────────┬─────────────┘
                                            │ Grounded
                                            ▼
                              ┌───────────────────────────┐
                              │  🎯 Confidence Agent      │
                              │   (Score: 0.0 - 1.0)      │
                              └─────────────┬─────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │ > 0.65                │ 0.40 - 0.65           │ < 0.40
                    ▼                       ▼                       ▼
            ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
            │   ✅ Final    │       │ ❓ Clarifying │       │ 🎫 Auto-Create│
            │    Answer     │       │   Question    │       │ Support Ticket│
            └───────────────┘       └───────────────┘       └───────┬───────┘
                                                                    │
                                                                    ▼
                                                            ┌───────────────┐
                                                            │ ⚡ Redis Task │
                                                            │     Queue     │
                                                            └───────────────┘
```

---

## 📂 Project Directory Structure

```
Langgraph-Customer-Support-Multi-Agent/
│
├── api/                           # FastAPI REST API Backend
│   ├── app.py                     # Main FastAPI application & lifecycle
│   ├── auth/                      # JWT authentication & security dependencies
│   │   ├── jwt_handler.py
│   │   └── dependencies.py
│   ├── routers/                   # Modular API routers
│   │   ├── auth.py                # Login, registration, profile
│   │   ├── orders.py              # Order tracking & management
│   │   ├── payments.py            # Payment history & receipts
│   │   ├── refunds.py             # Refund request handling
│   │   ├── restaurants.py         # Restaurant info & menus
│   │   ├── support.py             # Ticket creation & status
│   │   └── chat.py                # Main LangGraph AI endpoint
│   └── schemas/                   # Pydantic validation schemas
│       └── schemas.py
│
├── agents/                        # Specialized LangGraph Agents & Guards
│   ├── intent_agent.py            # Food delivery intent classification
│   ├── order_agent.py             # Order tracking & delivery issues
│   ├── payment_agent.py           # Billing, invoices & duplicate charges
│   ├── refund_agent.py            # Policy-compliant refund assistance
│   ├── restaurant_agent.py        # Menus, hours & allergen queries
│   ├── rag_agent.py               # Document retrieval & context grounding
│   ├── confidence_agent.py        # Multi-factor score evaluation & routing
│   ├── clarification_agent.py     # Targeted intent-aware clarification
│   ├── escalation_agent.py        # Ticket creation & SLA metadata
│   ├── grounding_guard.py         # Factual hallucination check
│   └── injection_guard.py         # Prompt injection sanitizer
│
├── core/                          # State & Graph Construction
│   ├── state.py                   # TypedDict SupportState with memory
│   └── graph.py                   # LangGraph StateGraph orchestration
│
├── database/                      # PostgreSQL Database Layer
│   ├── models.py                  # SQLAlchemy ORM models (7 tables)
│   ├── connection.py              # DB engine & session dependency
│   └── seed.py                    # Demo database populator
│
├── data/docs/                     # RAG Knowledge Base (Markdown)
│   ├── order_tracking/
│   ├── payments/
│   ├── refunds/
│   ├── restaurants/
│   └── general_support/
│
├── rag/                           # Vector Store & Embedding Pipeline
│   ├── retriever.py               # ChromaDB retriever instance
│   └── ingestion.py               # Document parsing & chunk ingestion
│
├── workers/                       # Redis Background Workers
│   ├── ticket_worker.py           # SLA calculation & ticket processing
│   └── notification_worker.py     # Customer event notifications
│
├── evaluation/                    # Benchmarking & Testing Suite
│   ├── eval_dataset.json          # Labeled benchmark test cases
│   └── evaluate.py                # Intent, routing & injection benchmarks
│
├── frontend/                      # Web UI
│   ├── index.html                 # Modern dashboard layout
│   ├── style.css                  # Dark glassmorphism styling
│   └── app.js                     # Real-time chat & API client
│
├── Dockerfile                     # Container definition
├── docker-compose.yml             # PostgreSQL + Redis + FastAPI + Worker
├── requirements.txt               # Production dependencies
└── .env.example                   # Environment variable template
```

---

## 🚀 Quickstart & Setup Guide

### 1. Clone & Setup Virtual Environment
```bash
git clone <your-repo-url>
cd Langgraph-Customer-Support-Multi-Agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and enter your GROQ_API_KEY
```

### 3. Ingest Knowledge Base into ChromaDB
```bash
python rag/ingestion.py
```

### 4. Seed Demo PostgreSQL Database
```bash
python database/seed.py
```

### 5. Run the Application

#### Option A: Run via Docker Compose (Recommended)
```bash
docker-compose up --build
```

#### Option B: Run Locally
```bash
# Terminal 1: FastAPI API
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Redis Background Worker
python workers/ticket_worker.py
```

Open your browser at **`http://localhost:8000/docs`** for the Swagger UI and open `frontend/index.html` to access the chat dashboard!

---

## 🧪 Evaluation & Benchmarks

Run the automated evaluation suite against the multi-agent graph:
```bash
python evaluation/evaluate.py
```
**Evaluates:**
- `Intent Classification Accuracy`
- `Confidence Routing Accuracy`
- `Prompt Injection Defense Rate`
- `Groundedness vs Hallucination Rate`
