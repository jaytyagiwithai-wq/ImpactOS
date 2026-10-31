# ImpactOS

ImpactOS is a change-impact investigation workspace for engineering teams. It
turns a proposed change into an inspectable report that connects the change to
the affected systems, APIs, policies, and supporting source evidence.

The repository currently contains a working product demo and a backend
foundation for document ingestion, retrieval, versioned source material, and
traceable investigations.

## Current status

- The frontend is a polished Next.js demo with synthetic investigation reports.
- The backend is a FastAPI modular monolith with PostgreSQL/pgvector-oriented
  data models, migrations, local document storage, and focused tests.
- Live authentication, production document ingestion, retrieval, and model
  analysis are still in development.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, Radix UI
- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL/pgvector
- Observability: OpenTelemetry Collector

## Run locally

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:4178`.

### Backend

```powershell
cd backend
uv sync
uv run --env-file .env opentelemetry-instrument python -m uvicorn app.main:app --reload --reload-dir app
```

Copy `backend/.env.example` to `backend/.env` and supply local configuration
before starting services that require it. Never commit `.env`.

## Verification

```powershell
cd frontend
npm run typecheck
npm run build

cd ..\backend
uv run python -m unittest discover -s tests -v
```

See the component READMEs for architecture, integration boundaries, and
infrastructure commands.
