# ─────────────────────────────────────────────────────────────────────────────
# Multi-Agent Sales & CRM Intelligence — Makefile
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help env db seed backend worker frontend dev stop clean logs

# ── Default ───────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Multi-Agent Sales & CRM Intelligence — Commands"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make env        Copy .env.example → .env (first-time setup)"
	@echo "  make db         Start Postgres + Redis containers only"
	@echo "  make seed       Seed mock data + embed product catalog"
	@echo "  make backend    Start FastAPI backend (+ worker) via Docker"
	@echo "  make frontend   Start React dev server via Docker"
	@echo "  make dev        Start EVERYTHING (recommended)"
	@echo "  make stop       Stop all containers"
	@echo "  make clean      Stop + remove volumes (full reset)"
	@echo "  make logs       Tail logs from all containers"
	@echo ""

# ── First-time setup ──────────────────────────────────────────────────────────
env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅  .env created — open it and add your OPENAI_API_KEY"; \
	else \
		echo "ℹ️   .env already exists — skipping"; \
	fi

# ── Infrastructure only ───────────────────────────────────────────────────────
db:
	docker compose up -d postgres redis
	@echo "⏳  Waiting for Postgres to be healthy..."
	@until docker compose exec postgres pg_isready -U crm_user -d crm_db; do sleep 1; done
	@echo "✅  Postgres + Redis are ready"

# ── Seed database ─────────────────────────────────────────────────────────────
seed: db
	docker compose run --rm backend python seed/seed.py
	@echo "✅  Database seeded with mock data + embeddings"

# ── Start backend + worker ────────────────────────────────────────────────────
backend: db
	docker compose up -d backend worker
	@echo "✅  Backend running at http://localhost:8000"
	@echo "📄  API docs at    http://localhost:8000/docs"

# ── Start frontend ────────────────────────────────────────────────────────────
frontend:
	docker compose up -d frontend
	@echo "✅  Frontend running at http://localhost:5173"

# ── Start everything ──────────────────────────────────────────────────────────
dev: env db seed
	docker compose up -d
	@echo ""
	@echo "🚀  All services running:"
	@echo "    Frontend  → http://localhost:5173"
	@echo "    Backend   → http://localhost:8000"
	@echo "    API Docs  → http://localhost:8000/docs"
	@echo ""
	@echo "    Run 'make logs' to tail container output"
	@echo ""

# ── Tear down ─────────────────────────────────────────────────────────────────
stop:
	docker compose down
	@echo "🛑  All containers stopped"

clean:
	docker compose down -v --remove-orphans
	@echo "🧹  Containers + volumes removed (clean slate)"

# ── Logs ──────────────────────────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

# ── Local dev (without Docker, for fast iteration) ────────────────────────────
# Requires: postgres + redis already running via `make db`
local-backend:
	cd backend && uvicorn main:app --reload --port 8000

local-worker:
	cd backend && python worker.py

local-seed:
	cd backend && python seed/seed.py

local-frontend:
	cd frontend && npm run dev