# 1. Session cookies in Redis for API authentication

Status: Accepted — 2026-08-15

## Context

The API is consumed by a browser SPA served from its own origin. Authentication
state has to be invalidable server-side, and role or account changes have to take
effect without waiting for a credential to expire.

## Decision

`POST /auth/login` generates a uuid4 session id, stores the `SessionData` record
as JSON under `session:{id}` in Redis with a one-day TTL, and returns the id in a
`session_id` cookie — `httponly`, `samesite=strict`, and `secure` outside the dev
environment.

`get_current_session` reads that cookie and loads the record from Redis. A missing
cookie or an absent key is a 401.

JWT remains in use for email confirmation and password-reset links: single-use,
delivered out of band, and carrying no state worth looking up.

## Consequences

- Session contents live on the server, so a role change applies on the next
  request rather than at credential expiry. Revoking a session is one key delete.
- Redis sits on the critical path of every authenticated request. Losing it signs
  every user out.
- Session lifetime is the Redis TTL; the cookie `expires` attribute duplicates the
  same one-day value and the two have to be changed together.
- `samesite=strict` requires the SPA to be served from the same registrable domain
  as the API in production.
- No `Authorization` header is read anywhere in the application.
