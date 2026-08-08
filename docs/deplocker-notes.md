# Deplocker — Design Notes & Career Strategy

A working document covering the design of Deplocker (a self-hosted deployment
platform) and the platform-engineering career discussion around it.

---

## Part 1 — What Deplocker Is

A minimal self-hosted deployment platform for containerized applications,
similar in spirit to Dokploy/CapRover. Built from scratch (hand-written code,
not generated) as a portfolio + learning project.

**Week 1 scope:** Deploy a containerized app from Git, route to it, stream logs.
Single server. No scaling, no multi-server, no auth.

**Explicitly out of scope for Week 1:** multi-server, auto-scaling, zero-downtime
deploys, volume management, database provisioning, secret management, backups.

---

## Part 2 — Architecture (Week 1)

Everything runs on one server. Deplocker does **not** nest app containers inside
itself — it mounts the host Docker socket and creates containers as *siblings*.

```
Host Docker daemon
├── deplocker-api container   (FastAPI :8000)
├── postgres container        (:5432)
├── caddy container           (:80 / :443)  ← only public entry point
├── app-1 container           (deployed app)
├── app-2 container
└── app-3 container
```

- All containers share a Docker network (`deplocker-net`) so Caddy can reach
  app containers by name.
- App containers are **not** port-mapped to the host — Caddy is the single
  public ingress and routes internally.
- Docker socket is mounted into the API container:
  `/var/run/docker.sock:/var/run/docker.sock`

This is the same pattern Dokploy, CapRover, and Portainer use.

---

## Part 3 — Tech Stack

- **Backend:** FastAPI (async), SQLAlchemy 2.0, Alembic
- **Database:** PostgreSQL with UUID primary keys
- **Orchestration:** Docker SDK for Python
- **Reverse proxy:** Caddy (chosen over Traefik for simpler JSON admin API)
- **Background work:** FastAPI `BackgroundTasks` for Week 1; migrate to
  Celery + Redis in Week 3+ (one-line change at the call site)

---

## Part 4 — Data Model

Three core tables, all with UUID PKs (non-enumerable, distributed-ready,
professional appearance, good for Docker naming).

### Project → Application → Deployment

- **Project** (no dependencies)
- **Application** (belongs to a Project)
- **Deployment** (belongs to an Application)

### Application — the permanent "thing I want to deploy"

| Field | Notes |
|---|---|
| `id` | UUID PK |
| `project_id` | FK → projects (CASCADE) |
| `name`, `slug` | unique per project |
| `description` | optional |
| `git_url`, `branch`, `dockerfile_path` | source config |
| `port`, `env_vars`, `domain` | runtime config; `domain` unique globally |
| `status` | created / deploying / running / stopped / failed |
| `container_id`, `image_tag` | current state |
| `created_at`, `updated_at`, `last_deployed_at` | timestamps |

**Key decision:** `domain` lives on **Application**, not Deployment. The domain is
permanent identity (like a house address); deployments are events (like
renovations). It doesn't change between deploys. Per-deployment preview URLs, if
ever added, would be a *separate* `preview_url` field on Deployment.

### Deployment — one attempt to clone → build → run → route

| Field | Notes |
|---|---|
| `id` | UUID PK |
| `application_id` | FK → applications (CASCADE) |
| `status` | pending / cloning / building / deploying / success / failed |
| `image_tag` | set after build |
| `container_id` | set after container starts |
| `commit_hash` | String(40), set after clone |
| `build_logs` | Text (Week 1 simplification — see Part 8) |
| `error_message` | set on failure |
| `started_at`, `completed_at` | timestamps |

Computed properties: `duration_seconds`, `is_terminal`, `is_active`.

### Indexing decisions

- Foreign keys **must** be indexed (Postgres doesn't auto-index them).
- Composite index `(application_id, started_at)` covers per-app deployment
  history — the most common query.
- Separate index on `status` for status filtering.
- Do **not** add a redundant single-column `application_id` index (covered by
  composite). Don't index text fields or rarely-queried columns.

### Timestamp pattern

Use both `default=func.now()` and `server_default=func.now()`; `updated_at` adds
`onupdate=func.now()`. Never `default=datetime.now()` (evaluates once at import).

---

## Part 5 — Deployment State Machine

```
PENDING → CLONING → BUILDING → DEPLOYING → SUCCESS
                                         ↘ FAILED  (exit at any phase)
                                         ↘ CANCELLED
```

Terminal states: success, failed, cancelled. Validate transitions with a
`can_transition()` helper before any status write.

**Pipeline phases (DeploymentService.execute_deployment):**

1. **CLONING** — git clone (shallow, `depth=1`), extract `commit_hash`
2. **BUILDING** — docker build, stream logs, store `image_tag`
3. **DEPLOYING** — stop old container, start new one, wire Caddy route
4. **FINALIZE** — update deployment (status, completed_at, container_id,
   image_tag) and application (status, container_id, image_tag,
   last_deployed_at). On any exception → FAILED + error_message. Always clean up
   the temp build directory.

API returns **202 Accepted** immediately; the pipeline runs in the background.

---

## Part 6 — Service Layer

- **GitService** — `clone_repository(url, branch, destination, depth=1, token=None)`
  returns commit hash/message/author/date + resolved Dockerfile path. Token
  injected into HTTPS URL only for private repos; never log the authenticated URL.
- **DockerService** — build image (async generator yielding log lines),
  create/start/stop container, get status/logs/stats. Ensures `deplocker-net`
  exists on startup. App containers attached to the network, not host-port-mapped.
- **CaddyService** — add/remove/list routes via Caddy's JSON admin API.
- **DeploymentService** — orchestrates the above; owns the state machine.

**`depth=1` (shallow clone):** only fetch the latest commit, not full history.
Seconds instead of minutes, MBs instead of GBs. The only tradeoff (no git
history) is irrelevant — you just need the latest code + its commit hash.

**Git URLs:** Week 1 supports public HTTPS only. Week 3 adds token auth for
private repos. Week 5+ adds OAuth ("Connect GitHub"). HTTPS dominates; SSH is
rare for deployment platforms.

---

## Part 7 — BackgroundTasks vs Task Queues

| | BackgroundTasks | Celery + Redis |
|---|---|---|
| Process | Same as API | Separate worker |
| Persistence | Memory only | Redis/DB |
| Survives restart | No | Yes |
| Scalability | Limited | Horizontal |
| Retries | Manual | Built-in |
| Monitoring | None | Dashboard (Flower) |
| Week 1 | Good enough | Overkill |
| Production | Risky | Correct |

Start with BackgroundTasks. The service layer is identical either way, so the
later migration is a one-line change at the call site — no technical debt.

---

## Part 8 — Log Storage

Storing logs as a full Text column is **fine for Week 1** (<100 deploys, no real
traffic) but **wrong for production** (table bloat, every query drags MBs of log
data, inefficient retrieval).

- **Week 1:** Text column. Simple, demonstrates the core logic.
- **Week 3+:** Move to files on disk (`log_file_path` column), or a hybrid
  (last ~500 lines in DB for quick access, full logs in file).
- **Production-grade:** Loki / Elasticsearch / ClickHouse. Overkill for a
  portfolio piece. (Heroku→Logplex, Vercel→ClickHouse, Railway→Loki,
  Dokploy→Docker logs — none keep full logs in the primary DB.)

---

## Part 9 — Health Checks

Two different things that work *together*, not alternatives:

- **`/health` endpoint** — called by humans, uptime monitors, load balancers.
  Make it check dependencies (DB, Docker) and return `ok` / `degraded`.
- **Docker Compose `healthcheck`** — used by Docker for orchestration startup
  order (`depends_on: condition: service_healthy`). It *calls* your `/health`
  endpoint.

You want both. The compose healthcheck needs an endpoint to hit; `/health` is
that endpoint.

---

## Part 10 — Server Model (Week 3+, not Week 1)

Only needed when deploying to multiple servers. Skip entirely in Week 1
(everything is local via the Docker socket).

When added: identity (id, name, description), connection (host, port, ssh_user,
ssh_key_path), classification (environment, region, provider), status (is_active,
is_primary, health_status), capacity (max_applications, max_memory_mb, etc.),
usage (current_*), monitoring (last_health_check, health_check_failures),
metadata (tags), timestamps.

**Update strategy:**
- Config fields (host, limits, environment) → **on-demand** (user edits via API).
- Health + resource fields (health_status, current_cpu, etc.) → **polling**
  (background job every 30–60s).
- `current_applications` → **event-driven** (on deploy/delete) plus periodic
  polling to reconcile drift.

---

## Part 11 — CLI (Week 3–4, not Week 1)

A **separate module/package** that talks to the API over HTTP — it is just
another API client, like the web UI. All logic stays in the API (single source
of truth). Built with Click + requests (+ Rich for output). Distributed
independently (`pip install deplocker-cli`).

For Week 1, a simple bash wrapper around `curl` is plenty for demos.

---

## Part 12 — Scaling (Week 3+ reference)

Three-table model for horizontal scaling: Application (config + desired_replicas),
Deployment (build/deploy *event*), Replica (running *instance*, one per container).

- **Manual scaling** (Week 3): user sets `desired_replicas`; a reconciliation
  loop makes actual match desired.
- **Auto-scaling** (Week 5+): a monitor adjusts `desired_replicas` from metrics
  (CPU/memory/request rate); the same reconciliation loop enacts it.
- **Reconciliation loop** = the core pattern: every N seconds, compare desired vs
  actual, add/remove replicas to converge. This is also self-healing (crashed
  container → actual < desired → restart).

With replicas, application status becomes *computed* (count running replicas)
rather than a stored field.

---

## Part 13 — Implementation Strategy (10 phases)

1. **Foundation** — project structure, docker-compose, models, Alembic, `/health`
2. **CRUD API** — schemas + endpoints for projects/applications; auto-generate
   slug & domain
3. **GitService** — clone + commit extraction + Dockerfile resolution
4. **DockerService** — build images, manage containers, ensure network
5. **DeploymentService** — the pipeline + state machine; the `/deploy` endpoint
6. **Caddy integration** — dynamic routing; apps reachable by domain
7. **Real-time monitoring** — WebSocket log/stats streaming + HTTP snapshots
8. **Lifecycle** — stop / restart / redeploy / deployment history
9. **Testing** — integration tests per service, one full E2E test
10. **Deploy** — DigitalOcean droplet (or Railway/Render), polish README + demo

**Suggested pace:** ~1 day per pair of phases, 7 days total including polish.

**Rules:** models → services → API (never reverse). Test each service in
isolation before wiring together. Commit at each checkpoint. Small functions.
Explicit error handling. Never skip migrations. Each phase depends on the prior
one — don't skip ahead.

---

## Part 14 — Career Discussion: Is This Worth It for Platform Engineering?

The honest synthesis from the conversation:

### What platform-engineering roles actually screen for (2026)
- **Kubernetes** is the dominant gate (CKA is the highest-signal single cert).
- Plus IaC (Terraform), cloud, CI/CD, observability.
- And — repeated everywhere — **platform-as-product / developer experience /
  adoption**. The soft side (driving adoption, measuring impact) is treated as
  decisive, not optional.

### Where Deplocker aligns
- It *is* a self-service developer platform that abstracts infrastructure —
  exactly the platform-engineering thesis.
- It demonstrates platform APIs, deployment pipelines, monitoring — the right
  shape of work.

### Where it doesn't
- It builds *around raw Docker* instead of demonstrating Kubernetes — it routes
  around the actual hiring gate.
- As a solo project it has no users, so it can't show the adoption/impact muscle.

### The Dokploy point (and its limit)
- Dokploy is genuinely popular and genuinely platform-engineering — your
  attraction to it is a good signal about fit.
- But there's a barbell: small/mid companies *use* Dokploy precisely so they
  *don't* staff a platform team; large companies that *do* staff platform teams
  mostly run Kubernetes. So "companies use Dokploy" and "companies hire platform
  engineers to work on Dokploy-class tools" are different facts.
- Building Dokploy-class tools is real, marketable skill — it just tends to land
  under titles like DevOps / infra / "the person who set up our deploys" more
  than "Platform Engineer" at a company with a platform team. Same work,
  different door.

### As a *training* program — the strongest argument for finishing it
- Building the primitives by hand (reconciliation loop, routing/service
  discovery, container lifecycle, health) makes Kubernetes stop being magic.
  After this, a Deployment/ReplicaSet/Service/readiness probe each read as "the
  thing I hand-rolled, done properly."
- That understanding-from-below is rare and valuable (debug the control plane vs
  merely apply a manifest).
- **But** the training value is front-loaded — it peaks once the core pipeline +
  reconciliation loop are built; the rest is software grind, not new concepts.
- And it teaches the *concepts under* K8s, not the *operation of* K8s (networking,
  RBAC, operators, Helm, real failure modes). Complement, not replacement.

### The plan that came out of it
You already have hands-on Kubernetes experience and are early in studying it
deeper. Given that:

1. **Finish a deliberately minimal Deplocker** — the Week 1 scope above, nothing
   gold-plated. "Built and deployed a working platform" beats "designed one."
   You're only a few days from the payoff; don't spend the design effort without
   booking it.
2. **Then weight hard toward Kubernetes.** It's the gate for the larger half of
   the market and the title you're aiming for.
3. **Later, graft the Deplocker idea onto a real cluster** — a thin self-service
   "deploy my app" layer (small controller, or CLI+API provisioning K8s
   resources). This becomes the v2 that reuses everything (API shape, state
   machine, log streaming, health model).

**The arc:** Deplocker = "I understand what a developer platform should feel
like." K8s version = "and I can build it on the substrate the industry runs."
Together they cover both sides of the barbell with one coherent story —
that reads exactly like the role.
