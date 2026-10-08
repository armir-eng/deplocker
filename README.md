# Deplocker

Deplocker is a self-hosted platform for deploying containerized applications.
You describe an application once (its Git repository, branch, Dockerfile, port,
environment variables and domain), and Deplocker is meant to build it and run
it on your own server.

Today it covers everything around that step: accounts, organizations,
projects, application configuration and deployment records. The pipeline that
clones, builds and runs an application is not implemented yet.

- **Organizations** group users. Each member has a role: *owner*, *admin* or
  *member*.
- **Projects** belong to an organization and group its applications.
- **Applications** hold the configuration needed to build and run one service.
- **Deployments** record each attempt to ship an application.

Users sign in with email and password, Google, GitHub, or a passkey.

---

## Architecture

The whole stack runs with Docker Compose, defined in
[docker-compose.yml](docker-compose.yml).

| Service | What it does | Host port |
| --- | --- | --- |
| `api` | REST API ([FastAPI](https://fastapi.tiangolo.com/)) and a [Celery](https://docs.celeryq.dev/) worker for background jobs such as confirmation emails | `127.0.0.1:8080` |
| `ui` | Web app (React, Vite, Tailwind), served by nginx | `8082` |
| `postgres` | Main database | `5435` |
| `redis-stack` | Login sessions and background job results | `6380` |
| `rabbitmq` | Queue that hands background jobs to the worker | `5672`, admin UI `15672` |

Backend details are in [backend/CLAUDE.md](backend/CLAUDE.md), and the database
schema in [backend/docs/models.md](backend/docs/models.md).

---

## Getting started

### 1. Install the tools

Docker with Compose v2, GNU Make, [uv](https://docs.astral.sh/uv/) (Python
package manager) and Node.js with npm.

On Linux, the [dev container](.devcontainer/devcontainer.json) provides all of
them except Docker, which it uses from the host.

### 2. Create the configuration file

Every service reads its settings from `/etc/deplocker/.env`, on development
machines and on the production server alike. Compose refuses to start if the
file is missing. Create it from the template and fill in the values:

```sh
sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 0700 /etc/deplocker
install -m 0600 backend/.env.example /etc/deplocker/.env
$EDITOR /etc/deplocker/.env
```

### 3. Install dependencies and enable the Git hooks

```sh
make backend-install-local frontend-install-ci
git config core.hooksPath .githooks
```

The hooks are described under [Checks](#checks).

### 4. Start the stack

```sh
make start-dev
```

This builds the images when needed, starts the backend containers in the
background, and runs the Vite dev server in the foreground, which reloads the
page as you edit.

- Web app: <http://localhost:5173>
- API: <http://localhost:8080>, interactive docs at <http://localhost:8080/docs>

Stop Vite with <kbd>Ctrl</kbd>+<kbd>C</kbd> and the containers with
`make stop-dev`.

### Everyday commands

All commands are [Makefile](Makefile) targets.

| Command | What it does |
| --- | --- |
| `make start-dev` / `make stop-dev` | Start or stop the development stack |
| `make start-dev-https` | Same, over HTTPS, for testing passkeys (see below) |
| `make start-prod` / `make stop-prod` | Run the full stack in containers, web app included, at <http://localhost:8082> |
| `make backend-reformat` | Format the Python code and fix lint errors |
| `make frontend-reformat` | Format the frontend code |
| `make backend-test-ci` | Run the backend tests in a separate, throwaway stack; remove it afterwards with `make backend-clean-ci` |
| `make frontend-test-ci` | Run the frontend tests |
| `make clean-dev` | Remove the containers and images, so the next start rebuilds them |

### Testing passkeys over HTTPS

`make start-dev-https` serves the web app at <https://lvh.me:5173> and forwards
API calls through Vite at `/api`, so passkeys are registered against a real
domain over HTTPS, as in production. `lvh.me` is a public domain that resolves
to `127.0.0.1`.

The certificate comes from [mkcert](https://github.com/FiloSottile/mkcert).
Install mkcert, then once per machine:

```sh
mkcert -install                  # create a local certificate authority and trust it
cd frontend && mkcert lvh.me     # write lvh.me.pem and lvh.me-key.pem
```

Restart the browser afterwards so it picks up the new authority. On Linux,
Firefox and Chrome trust it only if `certutil` (package `libnss3-tools`) was
installed before `mkcert -install`. The `.pem` files are ignored by Git.

---

## Checks

Every check is a Make target, and the Git hooks and CI run the same targets, so
a check gives the same result on your machine as in CI.

| Hook | What it does |
| --- | --- |
| `pre-commit` | Runs `make lint-ci` for the parts with staged changes. Frontend: ESLint, Prettier and the TypeScript compiler. Backend: Ruff's format check and mypy. |
| `pre-push` | Rejects pushes to `master`, so changes reach it only through a pull request |

The hooks only report problems; fix formatting with `make backend-reformat` or
`make frontend-reformat`. Git skips them with `--no-verify`, and they do nothing
in a clone that has not enabled them.

---

## CI/CD

The workflow in [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) runs
on every push to any branch. Both of its jobs run on a self-hosted runner,
which is also the production server.

**Build & Test** (`ci` job):

1. Checks each part the push changed. Frontend: lint, type check, tests.
   Backend: lint, type check, a check that the migrations match the models,
   and tests. A new branch or a force push checks both.
2. Removes the backend test stack, even when a check failed, because the next
   run reuses the runner's workspace.
3. Builds the `api` and `ui` images and publishes them to the GitHub Container
   Registry, tagged with the commit SHA and `latest`.

**Deploy to production** (`cd` job) runs only on `master`, after `ci`
succeeds. It restarts the stack with the images `ci` just built on the same
machine, then waits up to three minutes for the API to report healthy, failing
the job otherwise.

The workflow handles no secrets: the server's configuration lives in
`/etc/deplocker/.env`, written by hand. GitHub needs a single repository
variable:

| Variable | Purpose |
| --- | --- |
| `PROD_API_URL` | The production API URL, built into the web app's bundle |

---

## License

[Apache License 2.0](LICENSE). Attribution requirements are in [NOTICE](NOTICE).
