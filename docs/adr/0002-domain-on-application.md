# 2. Domain on Application, environments as separate Applications

Status: Accepted — 2026-08-15

## Context

Every deployed app is reachable at a domain, and the reverse proxy needs to know
which domain routes to which running container.

`deployments` holds one row per deploy attempt — `started_at`, `commit_hash`,
status and logs. Those rows are historical: a finished deployment never changes
again, while a domain is desired state that outlives any single deploy.

## Decision

`domain` is a column on `applications`, unique and indexed.

An environment — dev, staging, production — is a separate `applications` row with
its own domain, branch and environment variables.

## Consequences

- Routing is answered by reading a column rather than by searching deploy history
  for the most recent successful row.
- A deployment never owns a domain, so moving traffic from an old container to a
  new one is a proxy operation, not a schema concern.
- Environment rows repeat `git_url` and `dockerfile_path`, and nothing records
  that they belong to one logical app. Grouping is by naming convention.
- Domain uniqueness is global, which matches DNS.
- `name` and `slug` are unique globally as well, so environment rows have to be
  named uniquely across every project. A composite unique constraint on
  `(project_id, name)` is required before a second project reuses an app name.
