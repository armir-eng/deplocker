
# =============================================================================
#
#   D E P L O C K E R
#
#   Task runner for local development and CI.
#   Targets are namespaced <component>-<action>-<environment>.
#
# =============================================================================


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

D                  = docker
DC                 = docker compose

BACKEND            = ./backend
FRONTEND           = ./frontend

UV                := $(shell which uv)

# Both compose stacks live at the project root. The dev stack keeps `ui` behind
# a profile; the test stack is self-contained and uses its own project name.
COMPOSE_DEV_FILE   = docker-compose.yml
COMPOSE_TEST_FILE  = docker-compose.test.yml

BUILD_DEV_STAMP    = .build-dev.stamp


.PHONY: build-dev start-dev stop-dev


# #############################################################################
#
#   B A C K E N D
#
# #############################################################################

# --- Local development -------------------------------------------------------

.PHONY: backend-install-local backend-clean-local backend-reformat-local \
        backend-ci-local backend-run-local backend-stop-local

## Resolve and install Python dependencies into backend/.venv
backend-install-local:
	cd $(BACKEND) && \
	uv sync

## Remove the virtualenv and the resolved lockfile
backend-clean-local:
	cd $(BACKEND) && \
	rm -rf .venv uv.lock

## Rewrite sources in place: format, then autofix lint violations
backend-reformat-local:
	cd $(BACKEND) && \
	uv run ruff format $(BACKEND)
	uv run ruff check --fix $(BACKEND)

## Verify formatting and static types without touching sources
backend-ci-local:
	cd $(BACKEND) && \
	uv run ruff format --check . && \
	uv run mypy .

## Bring the backend stack up in the foreground (no ui: it is profile-gated)
backend-run-local:
	$(DC) -f $(COMPOSE_DEV_FILE) up

## Tear the backend stack down
backend-stop-local:
	$(DC) -f $(COMPOSE_DEV_FILE) down


# --- CI / CD -----------------------------------------------------------------

.PHONY: backend-test-ci

## Run the test suite in containers; exit with the api container's status
backend-test-ci:
	$(DC) -f $(COMPOSE_TEST_FILE) up \
		--build \
		--exit-code-from api \
		--abort-on-container-exit


# #############################################################################
#
#   F R O N T E N D
#
# #############################################################################

# --- Local development -------------------------------------------------------

.PHONY: install-frontend-local clean-frontend-local frontend-reformat-local \
        frontend-run-local

## Install npm dependencies into frontend/node_modules
install-frontend-local:
	cd $(FRONTEND) && \
	npm install

## Remove installed modules and the lockfile
clean-frontend-local:
	cd $(FRONTEND) && \
	rm -rf node_modules package-lock.json

## Rewrite sources in place with the project formatter
frontend-reformat-local:
	cd $(FRONTEND) && \
	npm run format


# #############################################################################
#
#   F U L L   S T A C K
#
# #############################################################################

# --- Development environment -------------------------------------------------

.PHONY: build-dev clean-dev start-dev stop-dev restart-dev

## Sentinel: images are rebuilt only when a Dockerfile or the stack definition
## changes. The `frontend` profile is named so that `ui` is built alongside api.
$(BUILD_DEV_STAMP): $(COMPOSE_DEV_FILE) $(BACKEND)/Dockerfile $(BACKEND)/.dockerignore $(FRONTEND)/Dockerfile
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend build
	@touch $(BUILD_DEV_STAMP)

## Remove the build stamp and tear down the stack, including the ui service.
## The next `make build-dev` will rebuild everything.
clean-dev:
	@rm -f $(BUILD_DEV_STAMP)
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend down --rmi all
	@touch $(BUILD_DEV_STAMP)

build-dev:
	$(MAKE) $(BUILD_DEV_STAMP)

## Start only backend as containers in the foreground.
## The `DEV_FRONTEND_URL` environment variable is passed to the api container
## This way, it can redirect to the frontend dev server.
## In this , the frontend will have the hot reloading capability, enabling real-time testing of changes,
##  without rebuilding the image.
start-dev: $(BUILD_DEV_STAMP)
	DEV_FRONTEND_URL='http://localhost:5173' $(DC) -f $(COMPOSE_DEV_FILE) up -d && \
	cd frontend && API_URL='http://localhost:8080' npm run dev

stop-dev:
	$(DC) -f $(COMPOSE_DEV_FILE) down && \
	cd frontend && npm run stop

## Build if needed, then start api and ui detached
start-prod: $(BUILD_DEV_STAMP)
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend up -d

restart-dev: stop-dev start-dev

## Stop the full stack, ui included
stop-prod:
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend down