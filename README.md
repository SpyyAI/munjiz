# منجز Branch AI — Munjiz Branch AI

A production-grade multi-agent AI dashboard for a Saudi bank branch.
Five AI agents (Orchestrator, Khalid, Nora, Fahad, Sara) communicate in Saudi Arabic
via an A2A protocol, analyze branch data through Qwen LLMs (free via OpenRouter),
and stream their decisions to a real-time RTL dashboard.

## Stack

- **Django 5** + **Channels** (WebSocket) + **DRF**
- **Celery** + **Redis** (async agent processing)
- **PostgreSQL 16**
- **Qwen** via **OpenRouter** (FREE) — OpenAI-compatible API
- **Tailwind CSS** + **Alpine.js** + **HTMX** + **Chart.js**
- **Docker Compose** (web, celery worker/beat, db, redis, nginx)

## Quick start

1. Clone & configure:

   ```sh
   cp .env.example .env
   # Edit .env and add your free OpenRouter key (https://openrouter.ai/keys)
   #   OPENROUTER_API_KEY=sk-or-v1-...
   # Without a key, the system runs in scripted-fallback mode (still fully functional).
   ```

2. Launch everything:

   ```sh
   docker compose up --build
   ```

   This will:
   - migrate the database
   - seed agents, branch, staff, customers, kiosks, scenarios
   - start Daphne (HTTP + WebSocket), Celery worker, Celery beat, Postgres, Redis, Nginx

3. Open the dashboard:

   ```
   http://localhost          (via Nginx)
   http://localhost:8000     (direct to Daphne)
   http://localhost:8000/admin/   (Django admin — create superuser if needed)
   ```

## Demo flow

1. Click any of the 7 scenario buttons in the left column.
2. Watch the 5 agents stream their analysis into the center feed (Saudi Arabic, RTL).
3. Watch the SVG agent network pulse as messages flow.
4. Open **محرر البيانات (للحكام)** in the right column — change the waiting count
   from 34 to 80, click **🚀 شغّل بالبيانات الجديدة**, and observe how Sara's
   analysis text changes meaningfully (proves the AI is real).

## Architecture

```
Browser (Alpine + WebSocket)
    │  /ws/dashboard/
    ▼
Daphne (ASGI)
    │
    ├─ HTTP → Django views + DRF API
    └─ WebSocket → DashboardConsumer → group "dashboard"
                                    └─ Celery task (run_scenario_task)
                                            ▼
                                    AgentEngine
                                            │
                                            ├─ OpenRouter (Qwen) ←→ each of 5 agents
                                            │     (or fallback to scripted playback)
                                            ▼
                                    AgentMessage saved + group_send → WebSocket → Browser
```

## Useful commands

```sh
# Reseed DB (wipe + re-insert)
docker compose exec web python manage.py seed_data --reset

# Smoke test
docker compose exec web python scripts/test_agents.py

# Tail Celery logs
docker compose logs -f celery_worker

# Open Django shell
docker compose exec web python manage.py shell
```

## API endpoints

| Method | Path                                  | Notes                                    |
|--------|---------------------------------------|------------------------------------------|
| GET    | `/api/agents/list/`                   | List all 5 agents                        |
| GET    | `/api/agents/scenarios/`              | List 7 scenarios                         |
| POST   | `/api/agents/scenarios/<id>/trigger/` | Trigger scenario via Celery              |
| GET    | `/api/agents/scenarios/<id>/messages/`| Past messages for scenario               |
| GET    | `/api/branch/overview/`               | Branch + staff + kiosks + screens combined |
| GET    | `/api/branch/staff/`                  | All staff                                |
| GET    | `/api/branch/kiosks/`                 | All kiosks                               |
| GET    | `/api/customers/list/`                | All customers                            |
| GET    | `/api/queue/snapshot/`                | Latest queue snapshot                    |
| GET    | `/api/queue/predictions/`             | Heuristic next-hour prediction           |
| GET    | `/api/analytics/today/`               | Live KPIs for the dashboard sidebar      |

## LLM provider switching

The engine uses an OpenAI-compatible interface, so you can swap providers via env vars:

```sh
# OpenRouter (default)
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_DEFAULT=qwen/qwen-2.5-72b-instruct:free

# Groq
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_DEFAULT=qwen-qwq-32b

# Ollama (local — uncomment Ollama service in docker-compose.yml)
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL_DEFAULT=qwen3:32b
```

## Disclaimer

سيناريو توضيحي — البيانات محاكاة واقعية. This is a demo project; data is simulated.
