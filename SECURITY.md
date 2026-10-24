# Security

## Credential handling

- **No secrets in this repository.** Client IDs, client secrets, access
  tokens, and refresh tokens are never committed. `.gitignore` excludes
  `.env`, `*.token.json`, and the default token file.
- Credentials are read from environment variables (see `.env.example`) or a
  local token file created with mode `0600` by the client itself.
- The client never prints token values: `exchange` prints only a
  confirmation, and error messages are truncated and contain no credentials.
- OAuth uses the authorization-code flow with `duration=permanent` so a
  refresh token can renew the hourly access token. Token exchange and
  revocation authenticate with HTTP Basic (`client_secret_basic`).

## Reporting a vulnerability

Open an issue describing the problem without including any credentials or
tokens. If the issue involves credential handling, describe it in general
terms and we will follow up.
