# Multi-Agent Sales & CRM Intelligence

An end-to-end agentic AI that simulates B2B sales intelligence workflow. The system researches target companies, scores their fit against a product catalog, generates personalized outreach sequences, and requires explicit human approval before any action is taken.

---

## 1. The Problem This Solves

Sales teams operating at scale face a problem: outreach needs to feel personal, but personalizing at volume is prohibitively slow when done manually resulting in:
1. generic mass emails with poor conversion rates
2. bottlenecked SDR process where reps spend more time on research and writing than on actual selling.

This system addresses that gap by automating the intelligence-gathering pipeline while keeping a human in the loop for final judgment. Here is what a sales team would do manually:

- Research a target company: industry, size, recent trends, hiring trends, tech stack, pain points
- Match that company against a product catalog to find the most relevant offerings
- Score how well the company fits the ideal customer profile (ICP Score)
- Generate a tailored outreach sequence: subject lines, email body, and follow-ups
- Validate the output for quality, tone, and completeness
- Present everything to a human for approval, rejection, or editing before anything is sent

Therefore the system automates a big part of the sales process the and cuts down time and effort greatly.

All company data is seeded synthetic data. No emails are sent. No scraping occurs. The goal is to build a MVP to demonstrate the architecture, agent collaboration, and observability patterns that a production system of this kind would require.

---

## 2. How It Works

### 2.1. Agent Pipeline

Tthe system is a four-agent pipeline orchestrated by LangGraph. Each agent is a node in a **directed acyclic graph (DAG)**. They share state through a typed schema and hand off **structured outputs** to the next node.

- **Agent A — Researcher**
Receives a company name. Looks it up in the PostgreSQL database where company profiles are seeded. If the company is not found, it calls the LLM to generate a plausible profile and passes output as structured JSON for the next model: industry, size, headquarters, tech stack, pain points, recent signals, hiring trends, and associated leads.

- **Agent B — Strategist**
Takes the research output and runs a semantic similarity search **RAG** against the product catalog stored in pgvector. Finds the most relevant products by **cosine distance**. Then calls the LLM with the company profile and retrieved products.

Outputs:
1. **ICP fit score** from 0 to 100
2. a recommended **pitch angle**
3. **matched pain points**, anticipated objections, and **key value propositions**.

- **Agent C — Writer**
Takes the strategy output and generates a full three-touch outreach sequence. The LLM is instructed to lead the outreach with the company's pain point, avoid buzzwords, and write in a conversational but professional tone.

Outputs:

1. two subject line variants for A/B testing, full email body
2. a day-3 follow-up
3. a day-7 breakup email.

- **Agent D — Validator**

A Validator is a very important step as it helps create **Responsible AI (Safety)**

Runs two layers of checks.

Layer 1:

checks subject line length, min and max email body length, ensures no placeholder text, presence of follow-ups, valid ICP score range.

Layer 2:

a review by the LLM that scores completeness and checks for safe appropriate tone, personalization, and a clear call to action.

- **The workflow pauses here and sets status to awaiting_hitl**
### 2.2. Human-in-the-Loop

After the Validator agent finishes, the workflow stops and does not proceed automatically. The frontend returns three options to select from: Approve, Edit and Approve, or Reject. A human is needed in this step to commence the process. The approval is simulated (logged to the database) — no emails are dispatched.

### 2.3. RAG

The product catalog is embedded at seed time using a **local sentence-transformers model** (all-MiniLM-L6-v2). Embeddings are stored as vector columns in PostgreSQL via the **pgvector extension**. At runtime, the Strategist agent (Agent B) constructs a query from the company's industry, description, and pain points, and retrieves the top matching products by cosine similarity. This retrieved context is injected directly into the LLM prompt.

### 2.4. Observability

Having an eye on the agent activity is important as it helps adhere to **Microsoft Responsible AI (Accountability/Transparency)**

Every agent step emits a structured trace log in the format:

    [Step N] AgentName: Action description

These logs are flushed to the agent_logs table immediately after each step, before the next agent runs. The **frontend polls the results** endpoint every 2.5 seconds and renders the timeline live, giving the appearance of a streaming activity feed **without WebSockets**.

### 2.5. Token and Cost Tracking

Every LLM call is wrapped in a function that captures prompt tokens, completion tokens, and estimated USD cost using configurable per-token rates. Totals accumulate in the shared graph state and are flushed to the analysis_runs table after each call. The frontend displays per-run and session-aggregate cost in a dedicated widget.

---

## 3. Tech Stack

### 3.1. Backend
- Python 3.11
- FastAPI — REST API framework
- SQLAlchemy 2.0 — ORM and query layer
- PostgreSQL 16 — primary relational database
- pgvector — vector similarity extension for PostgreSQL
- LangGraph — agent orchestration via compiled stateful DAG
- LangChain — LLM abstraction and prompt management
- OpenAI API (gpt-4o-mini) — LLM for all agent reasoning
- sentence-transformers / all-MiniLM-L6-v2 — local embedding model, no API cost
- RQ (Redis Queue) — lightweight background job queue
- Redis 7 — job broker and queue backend
- psycopg2 — PostgreSQL adapter
- pydantic-settings — environment-based configuration management
- Faker — synthetic data generation

### 3.2. Frontend
- React 18 with TypeScript
- Vite — build tool and dev server
- Tailwind CSS — utility-first styling
- Axios — HTTP client for API communication
- Lucide React — icon set

### 3.3. Infrastructure and Tooling
- Docker — containerization for all services
- Docker Compose — local multi-service orchestration
- Official Docker images: pgvector/pgvector:pg16, redis:7-alpine, node:20-slim, python:3.11-slim
- Makefile — single-command developer workflows
- PostCSS + Autoprefixer — CSS processing pipeline

---

## 4. Techniques and Concepts Demonstrated

- Multi-agent system design with specialized, single-responsibility agents
- Agent orchestration via LangGraph directed acyclic graph (DAG) with conditional edges
- RAG using pgvector cosine similarity search
- Local embedding inference with sentence-transformers (no external embedding API required)
- Human-in-the-loop (HITL) workflow with explicit approval gate before action
- Structured observability: every agent step emits a typed trace log flushed immediately to the database
- Per-call token accounting and USD cost estimation across the full pipeline
- Background job processing via RQ worker decoupled from the API process
- Frontend polling pattern for live trace streaming without WebSockets
- JSON LLM outputs for reliable structured data extraction
- Rule-based plus LLM-assisted output validation in a dedicated agent node
- pgvector as a unified store for both relational data and vector embeddings in a single database
- Seeded synthetic data with embedding at startup for a fully self-contained system
- Security guardrails via system prompt on every LLM call
- Environment-based configuration with pydantic-settings and .env files
- Docker-first local development with health checks and dependency ordering

---

## 5. Project Structure
| Path                          | Description                                                     |
| ----------------------------- | --------------------------------------------------------------- |
| **sales-crm-demo/**           | Root directory for the full-stack AI CRM system                 |
| ├── `docker-compose.yml`      | Defines services: Postgres, Redis, backend, worker, frontend    |
| ├── `.env.example`            | Template for environment variables with documentation           |
| ├── `Makefile`                | Developer commands (`make dev`, `make seed`, `make logs`, etc.) |
| ├── `README.md`               | Project documentation                                           |
|                               |                                                                 |
| ├── **backend/**              | Python FastAPI + LangGraph application                          |
| │ ├── `main.py`               | FastAPI entry point, startup hooks, router registration         |
| │ ├── `worker.py`             | RQ background worker process                                    |
| │ ├── `config.py`             | App settings via Pydantic + cost estimation helpers             |
| │ ├── `requirements.txt`      | Python dependencies                                             |
| │ ├── `Dockerfile`            | Backend container definition                                    |
| │ ├── **db/**                 | Data layer (PostgreSQL + pgvector)                              |
| │ │ ├── `connection.py`       | SQLAlchemy engine & session factory                             |
| │ │ ├── `models.py`           | ORM models (companies, leads, runs, logs, etc.)                 |
| │ │ ├── `migrations.py`       | Table creation logic (`create_all`)                             |
| │ │ ├── `vector_store.py`     | Embeddings + similarity search helpers                          |
| │ │ ├── `init.sql`            | Enables pgvector & extensions                                   |
| │ ├── **seed/**               | Synthetic data + seeding logic                                  |
| │ │ ├── `mock_companies.json` | Sample B2B companies                                            |
| │ │ ├── `mock_leads.json`      | Sample leads linked to companies                         |
| │ │ ├── `product_catalog.json` | Products with ICP + pain points                          |
| │ │ ├── `seed.py`              | Seeds database + generates embeddings                    |
| │ ├── **agents/**              | LangGraph multi-agent system                             |
| │ │ ├── `state.py`             | Shared `GraphState` TypedDict across nodes               |
| │ │ ├── `llm_wrapper.py`       | LLM wrapper with token tracking & tracing                |
| │ │ ├── `researcher.py`        | Agent A: company research & profiling                    |
| │ │ ├── `strategist.py`        | Agent B: RAG + strategy generation                       |
| │ │ ├── `writer.py`            | Agent C: outreach/email generation                       |
| │ │ ├── `validator.py`         | Agent D: validation + quality checks                     |
| │ │ ├── `graph.py`             | LangGraph DAG + workflow orchestration                   |
| │ ├── **api/**                 | FastAPI route layer                                      |
| │ │ ├── `routes.py`            | Endpoints: `/run-analysis`, `/results`, `/hitl`, `/runs` |
| │ │ ├── `schemas.py`           | Pydantic request/response models                         |
| │ ├── **jobs/**                | Background processing                                    |
| │ │ ├── `run_analysis.py`      | RQ job executing LangGraph workflow                      |
| ├── **frontend/**              | React + Vite + Tailwind UI                               |
| │ ├── `index.html`             | App HTML entry                                           |
| │ ├── `vite.config.ts`         | Dev server + API proxy config                            |
| │ ├── `tailwind.config.js`     | Tailwind theme (dark mode, tokens)                       |
| │ ├── `package.json`           | Frontend dependencies & scripts                          |
| │ ├── `Dockerfile`             | Frontend container definition                            |
| │ ├── **src/**                 | Frontend source code                                     |
| │ │ ├── `main.tsx`             | React entry point                                        |
| │ │ ├── `App.tsx`              | Root component (state, polling, layout)                  |
| │ │ ├── `index.css`            | Tailwind directives + global styles                      |
| │ │ ├── **api/**               | API integration layer                                    |
| │ │ │ ├── `client.ts`          | Axios wrapper for backend calls                          |
| │ │ ├── **components/**        | UI components                                            |
| │ │ │ ├── `RunForm.tsx`        | Input + trigger analysis run                             |
| │ │ │ ├── `AgentTimeline.tsx`  | Live agent trace visualization                           |
| │ │ │ ├── `OutputPanels.tsx`   | Research/Strategy/Email/Validation views                 |
| │ │ │ ├── `HITLControls.tsx`   | Approve/Edit/Reject (human-in-loop)                      |
| │ │ │ ├── `TokenWidget.tsx`    | Token usage + cost display                               |
| │ │ ├── **types/**             | TypeScript interfaces                                    |
| │ │ │ ├── `index.ts`           | Shared API response types                                |

---

## Getting Started

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Make (pre-installed on macOS and Linux, if on Windows use WSL or chocolatey to install Make)
- Git
- An OpenAI API key

### Setup

Run the below command (using git bash if on windows):

    make env

Open `.env` and set `OPENAI_API_KEY` or `GITHUB_OPENAI_KEY` to your key. All other defaults work out of the box.

Start all services, seed the database, and launch the application:

    make dev

The first run will pull Docker images and download the embedding model inside the backend container. This takes a few minutes once. Subsequent starts are fast.

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |

### Useful Commands (Docker)

    make logs            Tail output from all containers
    make logs-backend    Tail backend and worker logs only
    make seed            Re-run the seed script (safe to repeat)
    make stop            Stop all containers
    make clean           Stop containers and delete all volumes (full reset)

### Running Without Docker

If you have PostgreSQL 16 with pgvector and Redis running locally:

    make db              Start only Postgres and Redis via Docker
    make local-backend   Start FastAPI with uvicorn --reload
    make local-worker    Start the RQ worker
    make local-frontend  Start the Vite dev server

---

## Configuration Reference

Make sure to specify the api key **OPENAI_API_KEY** or **GITHUB_OPENAI_KEY** and your model name **OPENAI_MODEL**

All other values are already set in `.env`
| Variable                        | Default          | Description                              |
|---------------------------------|------------------|------------------------------------------|
| OPENAI_API_KEY                  | (required)       | Your OpenAI API key                      |
| GITHUB_OPENAI_KEY               | (required)       | Your GitHub PAT                      |
| OPENAI_MODEL                    | gpt-4o-mini      | Model used for all agent LLM calls       |
| DATABASE_URL                    | (auto-set)       | PostgreSQL connection string             |
| REDIS_URL                       | (auto-set)       | Redis connection string                  |
| COST_PER_1K_PROMPT_TOKENS       | 0.00015          | USD cost per 1K prompt tokens            |
| COST_PER_1K_COMPLETION_TOKENS   | 0.00060          | USD cost per 1K completion tokens        |
| EMBEDDING_MODEL                 | all-MiniLM-L6-v2 | Local sentence-transformers model        |
| EMBEDDING_DIMENSION             | 384              | Vector dimension matching the model      |

---

## Constraints and Scope

This is a demonstration system. The following limitations are intentional:

- No real company data is fetched. The Researcher agent reads from a seeded PostgreSQL table or generates a fictional profile via LLM.
- No real emails are sent. Approval triggers a log entry only.
- No real LinkedIn or web scraping occurs. All signals are pre-seeded or LLM-generated.
- The embedding model runs locally on CPU. Inference is fast enough for a demo but would need GPU or a hosted embedding API for high-throughput production use.
- The RQ worker is a single process. A production system would run multiple workers with job retry logic, dead-letter queues, and monitoring.
- Authentication and multi-tenancy are not implemented. This is a single-user local demo.

---

## Future Extensions

- Replace synthesized company lookup with a real web scraping pipeline (Playwright, Firecrawl) or a data provider API (Apollo, Clearbit)
- Add WebSocket support to replace the polling pattern with true push-based trace streaming
- Integrate a vector database (Qdrant, Weaviate) if the product catalog grows beyond what pgvector handles comfortably
- Add a feedback loop: store approved emails and use them to fine-tune prompts or rank future recommendations
- Add authentication, run ownership, and a team dashboard for multi-user scenarios
- Swap RQ for Celery or a managed queue (SQS, Cloud Tasks) for production-grade job handling
- Add evals: score agent output quality automatically using a separate judge LLM