# ImpactOS backend

A modular monolith: one application, one database, and feature-owned code.
The worker will reuse these modules when asynchronous ingestion is introduced.

```text
backend/
  app/
    main.py                  # Application assembly and lifespan
    model_registry.py        # Explicit ORM registration for startup and Alembic
    core/
      config.py              # Settings and stable backend-relative paths
    modules/
      organizations/
        models.py            # Organization table
        dependencies.py      # Local-only tenant fixture
      documents/
        api.py               # HTTP contracts, dependencies, error mapping
        schemas.py           # Request and response validation
        service.py           # Use cases, transactions, business spans and logs
        models.py            # Document and document-version tables
        errors.py            # Errors shared by the service and HTTP adapter
      ingestion/
        parsing.py           # Text extraction; chunking/indexing follow here
      health/
        api.py               # Liveness and database readiness
    shared/
      db/
        base.py              # One SQLAlchemy Base
        session.py           # Engine, pool policy, request sessions
      storage/
        base.py              # Storage protocol, result, validation errors
        local.py             # Current local filesystem implementation
        dependencies.py      # Storage implementation selection
    cli/
      seed.py                # Local organization seed
  migrations/                # One migration history for the shared database
  infra/                     # Compose and OpenTelemetry Collector configuration
  tests/                     # Focused behavior and module integration checks
```

## Boundaries

- `main.py` assembles routers and lifecycle behavior. Business logic belongs in
  a feature module.
- HTTP adapters validate HTTP input and map application errors to status codes.
  The document service has no FastAPI dependency and can be called by a worker.
- The service owns transaction boundaries and emits a completion event after
  the commit outcome is known. Each request owns its SQLAlchemy Session.
- Feature models use the same `Base`. Modules own their tables; the registry
  makes them discoverable to Alembic without importing the HTTP application.
- Documents use the storage protocol. The local implementation owns file I/O;
  a future S3 implementation can satisfy the same contract. Existing files do
  not move automatically when storage providers change.
- Shared infrastructure must not import feature modules. Cross-module use cases
  should call an explicit service or contract instead of importing another
  module's router or reaching through its internals. The composition root and
  local seed deliberately assemble multiple modules.
- Keep direct SQLAlchemy queries in the owning service while the data access
  is small. Add a module-owned repository when shared query behavior warrants it.
- Future retrieval, impact analysis, and evaluation modules should be added as
  their first real behavior is implemented. No empty placeholder modules are
  needed now.

## Run locally

From this backend directory in Git Bash:

```bash
uv run --env-file .env opentelemetry-instrument \
  python -m uvicorn app.main:app --reload --reload-dir app
```

The API entry point remains `app.main:app`. The local seed command is now:

```bash
uv run python -m app.cli.seed
```

Run focused checks:

```bash
uv run python -m unittest discover -s tests -v
```

The service checks use a disposable in-memory SQLite database and temporary
upload directory. They check request contracts, persistence, tenant scoping,
file validation, commit-failure telemetry, and business-span relationships.
They do not prove PostgreSQL row-lock concurrency or Collector delivery.

See `commands.md` for infrastructure, migration, and telemetry commands.

## Data and migrations

This refactor changes Python imports, not SQL table definitions. It does not
require a database migration. Existing applied revisions remain unchanged.
Alembic and application startup both call `app.model_registry.load_metadata()`.
Register a new module's model import there before generating its migration.

Settings still load `backend/.env`. Local files remain under
`backend/.data/uploads` with their existing tenant/document/version keys.

## Current implementation limits

The tenant dependency is a local/test fixture, not authentication. Parsing
supports text and Markdown; registering another source type does not add a
parser for it. Indexing, retrieval, model calls, and durable ingestion jobs
have not been implemented.

A file retained after a failed database write is flagged for reconciliation.
No durable reconciliation worker exists yet. The local storage helper attempts
cleanup after ordinary write failures; crash recovery remains a separate task.
Metrics currently go to the console; traces and logs use the Collector pipeline.
