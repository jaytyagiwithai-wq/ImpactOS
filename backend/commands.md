# ImpactOS development command reference

Use Git Bash. Copy commands from this file; the learning goal is understanding what they do and checking their results.

**Start in the backend directory**

```bash
cd ~/Desktop/ImpactOS/backend
```

**Optional short names for this terminal session**

```bash
alias dc='docker compose -f infra/docker/compose.yaml'
alias api='uv run --env-file .env opentelemetry-instrument python -m uvicorn app.main:app --reload --reload-dir app'
```

These aliases last for the current Git Bash session. Define them again in a new terminal. Run them from the backend directory.

**Validate the Compose file**

```bash
dc config --quiet
```

This checks the Compose model. It does not prove that the Collector configuration is valid or that telemetry reaches storage.

**Start the configured infrastructure**

```bash
dc up -d --wait
dc ps
```

Services with health checks must pass them. A service without a health check is only checked for running state by this command.

**Run the API**

```bash
api
```

Expected `.env` settings for our current telemetry setup:

```dotenv
OTEL_SERVICE_NAME=impactos-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_TRACES_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_METRICS_EXPORTER=console
OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION=true
```

Keep the API terminal open. Ctrl+C stops that API process. Python changes under `app/` reload automatically; restart after changing environment settings or installed dependencies.

**Seed the local organization**

```bash
uv run python -m app.cli.seed
```

**Run focused backend checks**

```bash
uv run python -m unittest discover -s tests -v
```

These checks use an in-memory SQLite database and temporary uploads, not the development PostgreSQL database or uploaded files.

**Make a request from another terminal**

```bash
curl -i http://127.0.0.1:8000/health
```

HTTP 200 confirms that the endpoint responded. Separately verify telemetry storage in Grafana or ClickHouse after allowing for batching.

**Inspect service logs**

```bash
dc logs --tail=50 otel-collector
dc logs --tail=50 grafana
```

**Stop infrastructure while retaining its containers and volumes**

```bash
dc stop
```

**Open the tools**

- API documentation: http://127.0.0.1:8000/docs
- Grafana: http://localhost:3111

**Inspect a log and its active span in Grafana Explore**

Choose the ClickHouse data source, SQL editor, and Table output. Run:

```sql
SELECT
    l.Timestamp,
    l.Body,
    t.SpanName,
    l.TraceId,
    l.SpanId,
    round(t.Duration / 1000000, 2) AS span_duration_ms,
    l.LogAttributes
FROM otel.otel_logs AS l
INNER JOIN otel.otel_traces AS t
    ON l.TraceId = t.TraceId AND l.SpanId = t.SpanId
WHERE l.ServiceName = 'impactos-api'
    AND l.Body = 'health.checked'
    AND l.Timestamp > now() - INTERVAL 1 HOUR
ORDER BY l.Timestamp DESC
LIMIT 20;
```

Trace ID groups the request journey. Span ID identifies the active operation. Duration is the enclosing span's duration, converted from nanoseconds to milliseconds.

**PostgreSQL and migrations**

Inspect the existing PostgreSQL service:

```bash
dc config --quiet
dc up -d --wait postgres
dc ps
```

Inspect migration state, or apply new revisions when one is introduced:

```bash
uv run alembic current
uv run alembic upgrade head
```

The module refactor does not change tables and needs no new migration. Model discovery is in `app/model_registry.py`; Alembic imports that registry. The pgvector image supplies extension files; enabling the extension in the database still requires a migration before vector columns are introduced.



- Compose describes runtime services, networking, mounts, and health checks.
- Collector configuration describes receivers, processors, exporters, and active pipelines.
- Application traces and logs currently travel over OTLP/HTTP to the Collector, then to ClickHouse. Metrics currently go to the API console.
- Grafana queries ClickHouse to display telemetry. PostgreSQL stores organization, document, and version records; chunks and embeddings come next.
- The current Collector export queue is in memory and has bounded retries. It does not guarantee lossless delivery across crashes or prolonged outages.
