# Lastro

Local personal finance and net worth management app. Single-user, runs on your own machine — no cloud, no remote server, no third party seeing your financial data.

Replaces a spreadsheet: data lives in a SQLite database, quotes come in live (B3, crypto, CDI/Selic/IPCA, Tesouro Direto), and a local AI layer (Ollama) categorizes transactions, reads bill screenshots, and answers as a financial analyst with memory of past conversations.

## Stack

- **Backend** — Python 3.12+, FastAPI, SQLModel, SQLite, Alembic (`uv` as package manager)
- **Frontend** — React 19 + TypeScript, Vite, Tailwind, shadcn/ui (`pnpm`)
- **AI** — local Ollama (default, including a vision model for reading bill screenshots) or Claude API (opt-in)
- **Auth** — single admin user, JWT-based login (bootstrapped from `.env`, no external identity provider)
- **Quotes** — brapi.dev (B3), CoinGecko (crypto), BCB-SGS (CDI/Selic/IPCA), Tesouro Transparente (Tesouro Direto)
- **Deploy** — Docker Compose (`api` + `web` + `ollama`), everything local

Architecture details, domain invariants, and the phase roadmap live in [`CLAUDE.md`](./CLAUDE.md).

## Quick demo (try it right now)

```bash
git clone https://github.com/NoodleLDS/lastro.git
cd lastro

# 1. Configure environment
cp backend/.env.example backend/.env   # edit LASTRO_BRAPI_TOKEN (free at brapi.dev)
cp frontend/.env.example frontend/.env

# 2. Start services (Docker required)
docker compose up -d

# 3. Run migrations and seed demo data
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run python scripts/seed_demo.py

# 4. Open in browser
open http://localhost:5173   # or just navigate there
```

**Login:** `admin` / `demo1234`

The seed creates fictitious transactions (3 months), portfolio positions, income, and emergency reserve — enough to exercise the full UI without any personal data.

> **Personalizing the AI analyst:** after logging in, go to _Analista → Memória / Instruções_ and edit the analyst profile (Section 12 of the master prompt) with your real income, positions, and goals. That text is loaded into every chat context, so the analyst answers based on your actual situation.

## Running it

### Option 1 — one click (Windows)

1. Build the executable once: `just build-launcher`
2. Double-click `launcher/dist/Lastro.exe` (or the desktop shortcut)

This brings up the Docker containers, waits for the API to respond, and opens the browser straight into the app. If something fails, the error is logged to `launcher/lastro_launcher.log`.

> Prerequisite: Docker Desktop installed and running.

### Option 2 — manual

```bash
just up          # docker compose up (api + web + ollama)
```

Then open `http://localhost:5173`.

Without `just` installed, the equivalent is: `docker compose up`.

### Development (without Docker)

```bash
just dev-api     # uv run uvicorn lastro.main:app --reload (backend/)
just dev-web     # pnpm dev (frontend/)
```

> Don't run `dev-api` and the Docker `api` container at the same time — they compete for port 8000 and write to different databases (this caused a previous data loss in this project). Stop the container (`docker compose stop api`) before running locally.

First run creates the admin user automatically from `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `backend/.env`.

## Useful commands (`justfile`)

```
just up              # docker compose up (api + web + ollama)
just dev-api         # local uvicorn with reload
just dev-web         # vite dev server
just test            # pytest + vitest
just lint            # ruff check + biome check
just fmt             # ruff format + biome format
just migrate "<msg>" # alembic revision --autogenerate -m
just upgrade         # alembic upgrade head
just build-launcher  # builds launcher/dist/Lastro.exe
```

## Structure

```
lastro/
├── backend/        # FastAPI + SQLModel + Alembic
├── frontend/       # React + Vite + shadcn/ui
├── launcher/       # Lastro.exe script + build
├── docker-compose.yml
├── justfile
└── CLAUDE.md       # architecture, invariants, phases, work protocol
```

## AI analyst: memory and instructions

The analyst chat (tab "Analista") keeps separate, named conversations — each one persists its own message history, which is replayed to the model on every new question in that conversation. A context panel (brain icon) shows:

- **Memória** (read-only) — the actual master prompt and live portfolio data sent to the model on every question, for auditing.
- **Instruções** (editable) — free-text instructions that complement the master prompt (e.g. "always answer in 3 sentences"). They never replace the fixed financial profile/rules.

## Data and privacy

The whole database lives in a local Docker volume (`lastro-db`), never on shared disk or in the cloud. By default everything — categorization, bill screenshot reading, the analyst chat — runs on local Ollama; Claude API is opt-in and never required. No financial value coming from AI writes directly to the database: it always goes through a preview the user can edit.
