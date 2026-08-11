# Deplocker

Self-hosted deployment platform for containerized applications.

Every check is a [Makefile](Makefile) target. Hooks and CI invoke the same
targets, so a local result and a pipeline result cannot disagree.

---

## Prerequisites

`docker` + `docker compose` v2, `uv`, `node`/`npm`, and GNU Make.

> [!WARNING]
> Make is required on every machine that runs this project, **including the
> self-hosted CI runner**. The hooks and all pipeline steps invoke it directly;
> without it each one fails with `make: command not found`.

Installation instructions for all platforms are on the GNU Make page:
<https://www.gnu.org/software/make/> — Linux via the distribution package
manager, macOS via the Xcode Command Line Tools, Windows via WSL.

```sh
make --version   # GNU Make 4.x expected
```

---

## Git hooks

Hooks live in [.githooks/](.githooks/) rather than `.git/hooks/`, so they are
version-controlled and reviewed like any other code. Git does not read that
directory by default; enable it once per clone:

```sh
git config core.hooksPath .githooks
```

| Hook | Rule | Reason |
| --- | --- | --- |
| `pre-commit` | `make lint-ci` must pass — ESLint, Prettier, `tsc`, ruff, mypy | A formatting violation fails in seconds locally instead of consuming a full CI run |
| `pre-push` | Pushes to `master` are rejected | Keeps the default branch reachable only through a pull request |

Hooks verify but never rewrite sources. Fix violations with
`make backend-reformat` or `make frontend-reformat`.

Both are bypassable with `--no-verify`, and are absent in a clone that skipped
the opt-in. They are a fast feedback loop, not a control — and, as noted under
[Branch protection](#branch-protection), currently the only thing guarding
`master`.

---

## CI/CD

[.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml), triggered on every
push to every branch. Both jobs run on `self-hosted`, and the runner is also the
production host.

### `ci` — "Build & Test"

One Make target per step, in order:

```
frontend-install-ci → frontend-lint-ci → frontend-test-ci
backend-lint-ci → backend-test-ci → backend-clean-ci
build-ci → publish-ci
```

`backend-clean-ci` is guarded with `if: always()`, because the runner workspace
is reused between runs: a failed test run must still tear down its compose stack
and volumes, or it corrupts the next one.

Images are published to GHCR under both the commit SHA and `latest`. The SHA tag
is what makes a deployed artifact traceable to its source commit.

### `cd` — "Deploy to production"

Gated on `needs: ci` and `refs/heads/master`. The `needs` clause is the gate —
without it the job would start in parallel with `ci` and could deploy a commit
whose tests never passed.

The job checks out and runs `make deploy-cd`. It handles no secrets: production
configuration lives at `/etc/deplocker/.env`, provisioned on the host by
hand and never written by CI. Compose reads that file host-side and injects the
values as environment variables — it is not mounted, and the infrastructure
images require it that way, since `postgres`, `redis-stack` and `rabbitmq` take
their credentials from the environment rather than parsing a file.

Every service in [docker-compose.yml](docker-compose.yml) names that path
literally, so the same file serves development and production. Each developer
provisions it on their own machine; compose aborts with a clear error if it is
missing, rather than starting the stack with an empty environment.

One-time setup, on the production host as the runner user and on each
development machine:

```sh
sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 0700 /etc/deplocker
install -m 0600 /dev/null /etc/deplocker/.env
$EDITOR /etc/deplocker/.env
```

`deploy-cd` reuses the images `ci` built on this same host, so no registry
round-trip occurs. It waits on the API healthcheck and fails the job if the stack
does not come up, which keeps a broken deploy from being reported as success.

### Required on GitHub

| Kind | Name | Purpose |
| --- | --- | --- |
| Variable | `PROD_API_URL` | Baked into the frontend bundle at build time by Vite |

No secrets are stored in GitHub. `GITHUB_TOKEN` is supplied automatically for the
GHCR login, and production configuration is provisioned on the host as above.

---

## Branch protection

Server-side protection is currently unavailable. GitHub gates both rulesets and
classic branch protection behind GitHub Pro for private repositories, and this
one is private on a Free personal account. Both REST endpoints return:

```
403  Upgrade to GitHub Pro or make this repository public to enable this feature.
```

`master` is therefore guarded only by the `pre-push` hook — a local convention,
not an enforced control. Merges to `master` rest on agreement, not on the
platform rejecting anything.

Making the repository public, or upgrading to Pro, lifts the restriction. Then
configure **Settings → Rules → Rulesets** against `master`: require a pull
request, require the `Build & Test` status check, block force pushes and
deletions. The check name is the job's `name:` field, matched literally, and it
appears in the picker only after the workflow has reported once — enabling it
sooner blocks every pull request indefinitely.
