# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Dependency management (uses uv)
uv sync                    # install production deps
uv sync --dev --frozen     # install all deps (locked)

# Run the API (inside container or with env loaded)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run the Celery worker alongside the API
celery -A app.tasks.celery_app worker

# Lint and format
ruff check .
ruff format .

# Tests (requires PostgreSQL with TEST_DB database running)
pytest tests/ -v
pytest tests/path/to/test.py::test_name -v   # single test

# Run tests in Docker (no local Postgres needed)
docker compose -f docker-compose.test.yml up

# Alembic migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Environment

Settings come from real environment variables; compose injects them by reading `/etc/deplocker/.env` on the host (`env_file:` in `docker-compose.yml`). `app/core/conf.py` also accepts a dotenv file at `$ENV_FILE`, defaulting to `.env` in the working directory — a fallback for running the app outside compose, since environment variables take precedence. Copy `.env.example` to `/etc/deplocker/.env`. Required variables: Postgres connection, `TEST_DB`, `ENVIRONMENT` (`dev`|`production`), frontend URLs, `SECRET_KEY`/`ALGORITHM`/`ACCESS_TOKEN_EXPIRES_MINUTES`, RabbitMQ credentials, Redis credentials, and SMTP email credentials.

## Architecture

### Request lifecycle

Routers (`app/routers/`) receive requests and inject dependencies via FastAPI's `Depends`. Simple CRUD is handled directly in routers. Complex domain logic is delegated to service classes (`app/services/`), which accept an `AsyncSession` and encapsulate the DB operations. All database access is async via SQLAlchemy + asyncpg.

### Authentication

Auth is **session-cookie based at the API level** — JWT is only used for email account confirmation links. On login, a UUID `session_id` is stored as a `Set-Cookie` (`httponly`, `samesite=strict`) and the session data is written to Redis with a 1-day TTL. Every protected route depends on `get_current_session` (`app/utils/auth.py`), which reads `session_id` from the cookie and looks up the session in Redis.

### Data layer

- `Base` (`app/core/database.py`) is the SQLAlchemy declarative base; all models inherit from it and get a `to_dict()` helper.
- Schemas (`app/schemas/`) are Pydantic models used for request validation and response serialization — they are separate from SQLAlchemy models.
- Slugs are auto-generated via `generate_slug()` (`app/utils/slug_generator.py`) when creating Projects, Applications, and Organizations.

### Domain model

`Project` → `Application` → `Deployment` → `DeploymentLogs` is the core ownership chain. Applications hold the Docker/Git config (git URL, branch, dockerfile path, port, env vars, domain). A `Deployment` tracks a single deploy lifecycle through states: `pending → cloning → building → pushing → deploying → health_checking → success/failed/cancelled`.

`User` → `Organization` is M2M via `OrganizationMembersModel`. On registration, a default organization is automatically created for the user with `OWNER` role.

### Celery / async tasks

`app/tasks/celery_app.py` configures Celery with RabbitMQ as the broker and Redis as the result backend. Currently the only task is `send_confirmation_email` in `app/tasks/account_confirmation.py`. After dispatching a task, the API returns a `task_id` which the frontend polls via `GET /tasks/{task_id}` until `SUCCESS` or `FAILURE`.

### Redis

`RedisManager` (`app/core/cache.py`) wraps `redis.asyncio` with a connection pool. It is used for session storage and also supports JSON operations (for future use). The `redis` singleton is imported from `app.core`.

### Startup and migrations

On startup (FastAPI lifespan), `Base.metadata.create_all` runs to ensure tables exist — this is a dev convenience, not a replacement for Alembic migrations. Alembic (`alembic/env.py`) imports all models explicitly and uses the same `DATABASE_URL` from `app.core.database`.

### Testing

Tests are async (`anyio` with asyncio backend). The `test_db_session` fixture connects to `TEST_DB`, wraps each test in a transaction that rolls back on teardown, and the `client` fixture overrides `get_db_session` with that session. Redis is expected to be available during test runs (use `fakeredis` for unit tests of cache-dependent code). The `docker-compose.test.yml` provides a self-contained CI environment.
