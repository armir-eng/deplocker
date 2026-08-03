FROM python:3.14.5-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# curl is used by the api healthcheck; python:*-slim does not ship it
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS test
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "pytest", "tests/", "-v"]


FROM base AS production
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
