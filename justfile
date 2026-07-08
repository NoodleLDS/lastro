up:
    docker compose up

dev-api:
    cd backend && uv run uvicorn lastro.main:app --reload

dev-web:
    cd frontend && pnpm dev

test:
    cd backend && uv run pytest
    cd frontend && pnpm test

lint:
    cd backend && uv run ruff check .
    cd frontend && pnpm lint

fmt:
    cd backend && uv run ruff format .
    cd frontend && pnpm fmt

migrate msg:
    cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

upgrade:
    cd backend && uv run alembic upgrade head

build-launcher:
    cd launcher && uv run pyinstaller --onefile --windowed --name Lastro --icon lastro.ico lastro_launcher.py

build-shell:
    cd frontend && pnpm shell:build
