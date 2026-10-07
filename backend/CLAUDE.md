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

### Helpers

Every helper function lives under `app/utils/` — never in a router, model or schema module, even when only one route calls it. Routers keep only path operation functions.

`app/utils/` is split into subdirectories named after the context a helper serves, so the tree reads as a map of the project: `app/utils/auth/` holds authentication helpers, one module per concern (`passkeys.py`, `google_oauth.py`, …) with `shared.py` for what several of them use. Put a new helper in the subdirectory of its context, creating the subdirectory (with an `__init__.py`) when none fits; do not add modules at the top level of `app/utils/`. A helper used across contexts goes in a subdirectory named for what it does (e.g. text formatting), not in a catch-all like `common/` or `misc/`.

### Authentication

Auth is **session-cookie based at the API level** — JWT is only used for email account confirmation links. On login, a UUID `session_id` is stored as a `Set-Cookie` (`httponly`, `samesite=strict`) and the session data is written to Redis with a 1-day TTL. Every protected route depends on `get_current_session` (`app/utils/auth/shared.py`), which reads `session_id` from the cookie and looks up the session in Redis.

Four ways in, all ending at `_login_response`: password, Google OAuth2, GitHub OAuth2, and passkeys (WebAuthn). Each has a router module under `app/routers/auth/` and a matching helper module under `app/utils/auth/`; the routers all register on the single `router` defined in `app/routers/auth/__init__.py`.

Passkeys use discoverable credentials, so `POST /auth/passkeys/login` identifies the account from the credential id alone. Both ceremonies are two calls — options, then verification — and the challenge issued by the first is held in Redis for 5 minutes and deleted on use, keyed by user id when registering (there is a session) and by a `passkey_challenge` cookie when logging in (there is not). `WEBAUTHN_RP_ID` scopes a credential to a domain and defaults to the frontend host; the expected origin is `settings.FRONTEND_URL`.

### Data layer

- `Base` (`app/core/database.py`) is the SQLAlchemy declarative base; all models inherit from it and get a `to_dict()` helper.
- Schemas (`app/schemas/`) are Pydantic models used for request validation and response serialization — they are separate from SQLAlchemy models.
- Slugs are auto-generated via `generate_slug()` (`app/utils/text/slug_generator.py`) when creating Projects, Applications, and Organizations.
- Names and slugs are unique within their parent: a project's per organization, an application's per project. An organization's name is a free display label and its slug a global handle (the default organization's gets a numeric suffix on collision).
- Routes that write a name commit through `commit_unless_name_taken` (`app/utils/naming/conflicts.py`), which turns a violation of one of those constraints into a 409 — the constraint decides, not a lookup beforehand, so concurrent requests can't race past it. A new name or slug constraint must be added to its `NAME_CONSTRAINTS`, or its violations surface as 500s.

### Domain model

`Project` → `Application` → `Deployment` → `DeploymentLogs` is the core ownership chain. Applications hold the Docker/Git config (git URL, branch, dockerfile path, port, env vars, domain). A `Deployment` tracks a single deploy lifecycle through states: `pending → cloning → building → pushing → deploying → health_checking → success/failed/cancelled`.

`User` → `Organization` is M2M via `OrganizationMembersModel`. On registration, a default organization is automatically created for the user with `OWNER` role.

### Celery / async tasks

`app/tasks/celery_app.py` configures Celery with RabbitMQ as the broker and Redis as the result backend. Currently the only task is `send_confirmation_email` in `app/tasks/account_confirmation.py`. After dispatching a task, the API returns a `task_id` which the frontend polls via `GET /tasks/{task_id}` until `SUCCESS` or `FAILURE`.

### Redis

`RedisManager` (`app/core/cache.py`) wraps `redis.asyncio` with a connection pool. It is used for session storage and also supports JSON operations (for future use). The `redis` singleton is imported from `app.core`.

### Startup and migrations

Alembic owns the schema. The container entrypoint (`scripts/entrypoint.sh`) runs `alembic upgrade head` before the app starts, and the FastAPI lifespan calls `ensure_schema_is_current` (`app/core/migrations.py`), which refuses to start unless the database is at the migration head — a stale schema fails loudly rather than being patched at runtime. Alembic (`alembic/env.py`) imports all models explicitly and uses the same `DATABASE_URL` from `app.core.database`.

Any model change needs a migration: CI runs `make backend-migrations-ci`, which applies the migrations to an empty database and fails if `alembic check` finds the models drifting from them. The test suite is the one place that still builds tables with `Base.metadata.create_all` (`tests/conftest.py`).

### Testing

Tests are async (`anyio` with asyncio backend). The `test_db_session` fixture connects to `TEST_DB`, wraps each test in a transaction that rolls back on teardown, and the `client` fixture overrides `get_db_session` with that session. Redis is expected to be available during test runs (use `fakeredis` for unit tests of cache-dependent code). The `docker-compose.test.yml` provides a self-contained CI environment.
