# Lastro

Local personal finance and net worth management app. Single-user, runs on your own machine — no cloud, no remote server, no third party seeing your financial data.

Replaces a spreadsheet: data lives in a SQLite database, quotes come in live (B3, crypto, CDI/Selic/IPCA), and a local AI layer (Ollama) categorizes transactions and answers as a financial analyst.

## Stack

- **Backend** — Python 3.12+, FastAPI, SQLModel, SQLite, Alembic (`uv` as package manager)
- **Frontend** — React 19 + TypeScript, Vite, Tailwind, shadcn/ui (`pnpm`)
- **AI** — local Ollama (default) or Claude API (opt-in, only for reading a bill from a screenshot)
- **Quotes** — brapi.dev (B3), CoinGecko (crypto), BCB-SGS (CDI/Selic/IPCA)
- **Deploy** — Docker Compose (`api` + `web` + `ollama`), everything local

Architecture details, domain invariants, and the phase roadmap live in [`CLAUDE.md`](./CLAUDE.md).

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

## Data and privacy

The whole database lives in a local Docker volume (`lastro-db`), never on shared disk or in the cloud. The AI layer is opt-in for Claude API and only used for reading a bill from a screenshot — by default everything runs on local Ollama. No financial value coming from AI writes directly to the database: it always goes through a preview the user can edit.
