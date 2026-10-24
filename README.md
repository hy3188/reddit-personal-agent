# reddit-personal-agent

[![CI](https://github.com/hy3188/reddit-personal-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/hy3188/reddit-personal-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](reddit_client.py)

A personal, **non-commercial** OAuth2 client for the official Reddit Data
API. It is operated **solely by and for one Reddit account** — the owner's
own account (u/Small-Difficulty4306) — as an assistant integration inside
the owner's private tooling. It is not a product, has no other users, and is
not deployed publicly.

## Status

- **API access request:** submitted to Reddit on 2026-10-24 under the
  [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy),
  currently pending approval.
- **No data is fetched through the API before approval is granted.**
- **Timing note:** Reddit announced (30 September 2026) that it will stop
  accepting new public API access requests on **31 October 2026**, with the
  public Data API winding down afterwards — which is why this request was
  filed now, with a complete, reviewable implementation attached.

## What it does

| Workflow | How | Writes? |
|---|---|---|
| Morning digest of subscribed subreddits | `GET /subreddits/mine/subscriber`, then `GET /r/<subs>/new` | No |
| Organize saved items and history | `GET /api/v1/me`, `GET /user/<name>/saved` | No |
| Post or reply, after the owner approves the exact text | `POST /api/submit`, `POST /api/comment` | Yes — guarded (below) |
| Save, subscribe, vote, flair, report | Corresponding endpoints | Only on the owner's explicit instruction |

Full workflows, examples, and the "why this needs the Data API" argument
(including why Devvit, RSS, and scraping do not work) are in
[`docs/USE_CASE.md`](docs/USE_CASE.md). Per-scope rationale is in
[`docs/SCOPES.md`](docs/SCOPES.md); the policy statement is in
[`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).

## How it works

```
Owner (chat) ──► Assistant ──► reddit_client.py ──► oauth.reddit.com
                    │                │
                    │                ├── OAuth2 authorization-code flow
                    │                │   (www.reddit.com/api/v1/authorize,
                    │                │    /api/v1/access_token, client_secret_basic)
                    │                └── min. gap between calls, Retry-After
                    │                    backoff on 429, refresh-on-401
                    └── owner reviews and approves exact text
                        before any --owner-approved write
```

## Safety rules enforced in code

- **Human-approved writes only.** `submit` and `comment` refuse to run
  without `--owner-approved`, set only after the owner reviewed the exact
  text. `--dry-run` prints the payload without sending it. There is no
  scheduled, bulk, or unattended posting path.
- **Single user, single account.** No other accounts are ever accessed.
- **Rate limits respected.** Minimum gap between calls, bounded backoff on
  429 honouring `Retry-After`, far below the 100 queries/minute free tier.
- **No secrets in the repo.** Credentials live in environment variables or a
  `0600` local token file (see `.env.example`); `.gitignore` excludes them.
  The client never prints token values, and `revoke` deletes them locally.
- **No AI training, no redistribution, no retention** beyond the task at
  hand. See [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).

## Quick start

```bash
cp .env.example .env   # fill in your own app credentials locally, never commit .env
python3 reddit_client.py auth-url          # print the authorization URL
python3 reddit_client.py exchange <code>   # exchange the returned code for tokens
python3 reddit_client.py me                # GET /api/v1/me — verify the connection
python3 reddit_client.py digest --limit 10 # newest posts from subscribed subreddits
python3 reddit_client.py saved --limit 10  # the owner's saved items
python3 reddit_client.py revoke            # revoke tokens and remove the local file
```

Create the Reddit app at <https://www.reddit.com/prefs/apps> (type: **web
app**, name `bbcc`); the redirect URI must match `REDDIT_REDIRECT_URI`
exactly.

## Development

Python 3.10+, standard library only — no third-party dependencies.

```bash
python3 -m py_compile reddit_client.py tests/test_reddit_client.py
python3 -m unittest discover -s tests -v   # offline, all HTTP mocked
```

The same two commands are wired for CI in `.github/workflows/ci.yml`
(add it via the web UI — GitHub blocks workflow files from API pushes —
and the badge above will light up on the first run).
Contributions: see [`CONTRIBUTING.md`](CONTRIBUTING.md). Security policy:
see [`SECURITY.md`](SECURITY.md). Changes: see
[`CHANGELOG.md`](CHANGELOG.md).

## License

MIT — see [`LICENSE`](LICENSE).
