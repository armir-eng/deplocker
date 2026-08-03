#!/bin/bash
uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload --reload-exclude 'app/logs/*' &
uv run --no-sync celery -A app.tasks.celery_app worker