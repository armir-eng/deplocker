
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
FRONTEND_MODULES   = $(FRONTEND)/node_modules

# Registry coordinates for the published images. IMAGE_OWNER and IMAGE_SHA are
# supplied by CI from the GitHub context.
REGISTRY          ?= ghcr.io
IMAGE_OWNER       ?=
IMAGE_SHA         ?=

API_IMAGE         ?= deplocker-api
UI_IMAGE          ?= deplocker-ui

# Vite bakes this into the bundle at build time, so a published ui image is
# pinned to one environment and CI must pass the production URL.
FRONTEND_API_URL  ?=

# GHCR rejects uppercase path segments, but the owner keeps the account casing.
REGISTRY_NS        = $(REGISTRY)/$(shell echo '$(IMAGE_OWNER)' | tr '[:upper:]' '[:lower:]')

# $(1) = local image name, tagged :latest by the corresponding *-build-ci target
define publish_image
	$(D) tag $(1):latest $(REGISTRY_NS)/$(1):$(IMAGE_SHA)
	$(D) tag $(1):latest $(REGISTRY_NS)/$(1):latest
	$(D) push $(REGISTRY_NS)/$(1):$(IMAGE_SHA)
	$(D) push $(REGISTRY_NS)/$(1):latest
	$(D) rmi $(REGISTRY_NS)/$(1):$(IMAGE_SHA) $(REGISTRY_NS)/$(1):latest
endef

define require_registry_vars
	@test -n "$(IMAGE_OWNER)" || { echo "IMAGE_OWNER is required"; exit 1; }
	@test -n "$(IMAGE_SHA)"   || { echo "IMAGE_SHA is required";   exit 1; }
endef


.PHONY: build-dev start-dev stop-dev


# #############################################################################
#
#   B A C K E N D
#
# #############################################################################

# --- Local development -------------------------------------------------------

.PHONY: backend-install-local backend-clean-local backend-reformat \
        backend-run-local backend-stop-local

## Install the locked Python dependencies into backend/.venv
backend-install-local:
	cd $(BACKEND) && \
	uv sync --frozen

## Remove the virtualenv and the resolved lockfile
backend-clean-local:
	cd $(BACKEND) && \
	rm -rf .venv uv.lock

## Rewrite sources in place: format, then autofix lint violations
backend-reformat:
	cd $(BACKEND) && \
	uv run ruff format . && \
	uv run ruff check --fix .

## Bring the backend stack up in the foreground (no ui: it is profile-gated)
backend-run-local:
	$(DC) -f $(COMPOSE_DEV_FILE) up

## Tear the backend stack down
backend-stop-local:
	$(DC) -f $(COMPOSE_DEV_FILE) down


# --- CI / CD -----------------------------------------------------------------

.PHONY: backend-lint-ci backend-test-ci backend-clean-ci backend-build-ci backend-publish-ci

## Verify formatting and static types without touching sources
backend-lint-ci:
	cd $(BACKEND) && \
	uv run ruff format --check . && \
	uv run mypy .

## Run the test suite in containers; exit with the api container's status
backend-test-ci:
	$(DC) -f $(COMPOSE_TEST_FILE) up \
		--build \
		--exit-code-from api \
		--abort-on-container-exit

## Tear the test stack down, volumes and stragglers included
backend-clean-ci:
	$(DC) -f $(COMPOSE_TEST_FILE) down -v --remove-orphans

## Build the shippable image from the production stage, which installs without
## dev dependencies and starts uvicorn directly (no --reload, no bind mount).
backend-build-ci:
	$(D) build --target production -t $(API_IMAGE):latest $(BACKEND)

## Tag and push the built image, then drop the registry tags so only the local
## `:latest` is left behind on the runner.
backend-publish-ci:
	$(require_registry_vars)
	$(call publish_image,$(API_IMAGE))


# #############################################################################
#
#   F R O N T E N D
#
# #############################################################################

# --- Local development -------------------------------------------------------

.PHONY: install-frontend-local clean-frontend-local frontend-reformat \

## Install npm dependencies into frontend/node_modules
install-frontend-local:
	cd $(FRONTEND) && \
	npm install

## Remove installed modules and the lockfile
clean-frontend-local:
	cd $(FRONTEND) && \
	rm -rf node_modules package-lock.json

## Rewrite sources in place with the project formatter
frontend-reformat:
	cd $(FRONTEND) && \
	npm run format


# --- CI / CD -----------------------------------------------------------------

.PHONY: frontend-install-ci frontend-lint-ci frontend-test-ci frontend-build-ci frontend-publish-ci

## Sentinel: reinstall only when the lockfile moves, so lint, typecheck and the
## suite can each be invoked as their own CI step without repeating `npm ci`.
$(FRONTEND_MODULES): $(FRONTEND)/package-lock.json
	cd $(FRONTEND) && \
	npm ci
	@touch $(FRONTEND_MODULES)

frontend-install-ci: $(FRONTEND_MODULES)

## Verify lint, formatting and types without touching sources
frontend-lint-ci: $(FRONTEND_MODULES)
	cd $(FRONTEND) && \
	npm run lint && \
	npm run format:check && \
	npx tsc -b

## Run the vitest suite once (jsdom, no server)
frontend-test-ci: $(FRONTEND_MODULES)
	cd $(FRONTEND) && \
	npm run test

## Build the shippable image. The dev stack bakes a localhost API_URL, so that
## image is never publishable; FRONTEND_API_URL has to be the production one.
frontend-build-ci:
	@test -n "$(FRONTEND_API_URL)" || { echo "FRONTEND_API_URL is required"; exit 1; }
	$(D) build --target runtime \
		--build-arg API_URL=$(FRONTEND_API_URL) \
		-t $(UI_IMAGE):latest $(FRONTEND)

## Tag and push the built image, then drop the registry tags
frontend-publish-ci:
	$(require_registry_vars)
	$(call publish_image,$(UI_IMAGE))


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
## without rebuilding the image.
start-dev: $(BUILD_DEV_STAMP)
	DEV_FRONTEND_URL='http://localhost:5173' $(DC) -f $(COMPOSE_DEV_FILE) up -d && \
	cd frontend && API_URL='http://localhost:8080' npm run dev

stop-dev:
	$(DC) -f $(COMPOSE_DEV_FILE) down

## Build if needed, then start api and ui detached
start-prod: $(BUILD_DEV_STAMP)
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend up -d

restart-dev: stop-dev start-dev

## Stop the full stack, ui included
stop-prod:
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend down


# --- CI / CD -----------------------------------------------------------------

.PHONY: lint-ci build-ci publish-ci deploy-cd

## Lint both frontend and backend
lint-ci: frontend-lint-ci backend-lint-ci

## Build both shippable images
build-ci: backend-build-ci frontend-build-ci

## Run tests for both frontend and backend
test-ci: backend-test-ci frontend-test-ci

## Publish both images under :$(IMAGE_SHA) and :latest
publish-ci: backend-publish-ci frontend-publish-ci

## Reconcile the running stack with the images this run just built.
##
## Deliberately not `start-prod`: that depends on $(BUILD_DEV_STAMP), which
## would rebuild `ui` with the dev stack's localhost API_URL and overwrite the
## image built with FRONTEND_API_URL. Both services are `pull_policy: never`,
## so this reuses the local :latest images and never reaches the registry.
##
## --wait blocks until api reports healthy and fails the job if it does not.
deploy-cd:
	$(DC) -f $(COMPOSE_DEV_FILE) --profile frontend up -d \
		--wait \
		--wait-timeout 180 \
		--remove-orphans