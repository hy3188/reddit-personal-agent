# Changelog

## v0.2.0 — 2026-10-24

- Client hardening: minimum gap between calls, `Retry-After` backoff on 429,
  single token refresh-and-retry on 401, typed `RedditAPIError`.
- `revoke` command: revokes the stored token and removes the local token file.
- `--dry-run` for `submit` and `comment`: print the payload without sending.
- Tests: 6 offline unit tests (auth URL, token exchange, approval gate,
  dry-run, identity parsing, 401 refresh) using only the standard library.
- Docs: use case, per-scope rationale, compliance statement, security policy.
- CI: GitHub Actions runs compile + tests on every push and pull request.

## v0.1.0 — 2026-10-24

- Initial client: OAuth2 authorization-code flow, `me`, `digest`, `saved`,
  `subscriptions`, and owner-approved `submit`/`comment`.
- README with purpose, safeguards, and setup instructions.
