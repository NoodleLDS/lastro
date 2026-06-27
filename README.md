# Lastro

App local de gestão financeira e de patrimônio pessoal. Single-user, roda na sua máquina — sem nuvem, sem servidor remoto, sem terceiros vendo seus dados financeiros.

Substitui uma planilha: os dados vivem num banco SQLite, cotações entram ao vivo (B3, cripto, CDI/Selic/IPCA), e uma camada de IA local (Ollama) categoriza lançamentos e responde como analista.

## Stack

- **Backend** — Python 3.12+, FastAPI, SQLModel, SQLite, Alembic (`uv` como gerenciador de pacotes)
- **Frontend** — React 19 + TypeScript, Vite, Tailwind, shadcn/ui (`pnpm`)
- **IA** — Ollama local (default) ou Claude API (opt-in, só para leitura de fatura por print)
- **Cotações** — brapi.dev (B3), CoinGecko (cripto), BCB-SGS (CDI/Selic/IPCA)
- **Deploy** — Docker Compose (`api` + `web` + `ollama`), tudo local

Detalhes de arquitetura, invariantes de domínio e roadmap de fases ficam em [`CLAUDE.md`](./CLAUDE.md).

## Como rodar

### Opção 1 — um clique (Windows)

1. Gere o executável uma vez: `just build-launcher`
2. Dê duplo-clique em `launcher/dist/Lastro.exe` (ou no atalho da área de trabalho)

Isso sobe os containers Docker, espera a API responder e abre o navegador direto no app. Se algo falhar, o erro fica em `launcher/lastro_launcher.log`.

> Pré-requisito: Docker Desktop instalado e aberto.

### Opção 2 — manual

```bash
just up          # docker compose up (api + web + ollama)
```

Depois abra `http://localhost:5173`.

Sem `just` instalado, equivalente: `docker compose up`.

### Desenvolvimento (sem Docker)

```bash
just dev-api     # uv run uvicorn lastro.main:app --reload (backend/)
just dev-web     # pnpm dev (frontend/)
```

> Não rode `dev-api` e o container `api` do Docker ao mesmo tempo — os dois competem pela porta 8000 e escrevem em bancos diferentes (um foi o motivo de uma perda de dados anterior neste projeto). Pare o container (`docker compose stop api`) antes de rodar localmente.

## Comandos úteis (`justfile`)

```
just up              # docker compose up (api + web + ollama)
just dev-api         # uvicorn local com reload
just dev-web         # vite dev server
just test            # pytest + vitest
just lint            # ruff check + biome check
just fmt             # ruff format + biome format
just migrate "<msg>" # alembic revision --autogenerate -m
just upgrade         # alembic upgrade head
just build-launcher  # gera launcher/dist/Lastro.exe
```

## Estrutura

```
lastro/
├── backend/        # FastAPI + SQLModel + Alembic
├── frontend/       # React + Vite + shadcn/ui
├── launcher/       # script + build do Lastro.exe
├── docker-compose.yml
├── justfile
└── CLAUDE.md       # arquitetura, invariantes, fases, protocolo de trabalho
```

## Dados e privacidade

Todo o banco fica num volume Docker local (`lastro-db`), nunca em disco compartilhado nem na nuvem. A camada de IA é opt-in para Claude API e só é usada para visão de fatura por print — por padrão tudo roda no Ollama local. Nenhum valor financeiro vindo de IA grava direto no banco: sempre passa por uma prévia editável pelo usuário.
