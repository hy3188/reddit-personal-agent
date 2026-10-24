# Requested scopes — what each one is for

Least privilege is the goal: every scope below maps to a concrete endpoint
used in `docs/USE_CASE.md`. If a scope is not used by a workflow, it is not
requested.

| Scope | Endpoint(s) | Used for |
|---|---|---|
| `identity` | `GET /api/v1/me` | Confirm the authorized account (owner's own identity check before any read/write) |
| `read` | Listing endpoints (`/r/<subs>/new`, `/user/<name>/saved`) | Reading the owner's home feed and saved items |
| `history` | `GET /user/<name>/saved` history views | Reading the owner's history/saved views |
| `mysubreddits` | `GET /subreddits/mine/subscriber` | Listing the communities the owner follows, to build the digest |
| `submit` | `POST /api/submit` | Owner-approved text posts (guarded by `--owner-approved`) |
| `edit` | `POST /api/editusertext` (future) | Editing the owner's own posts/comments after approval |
| `vote` | `POST /api/vote` (future) | A vote only when the owner explicitly instructs one on content they viewed |
| `subscribe` | `POST /api/subscribe` | Subscribe/unsubscribe only on the owner's explicit instruction |
| `save` | `POST /api/save`, `POST /api/unsave` | Saving/unsaving the owner's own items on instruction |
| `privatemessages` | `GET /message/inbox` (future, read-only use) | Reading the owner's own inbox only if they ask; no automated messaging |
| `flair` | `POST /api/selectflair` (future) | Setting flair on the owner's own posts when they ask |
| `report` | `POST /api/report` (future) | Reporting content the owner flags |
| `wikiread` | `GET /r/<sub>/wiki/*` | Reading community wikis referenced in a discussion |

Scopes marked "future" are requested now so the authorization does not have
to be repeated for the documented workflows, but no code path calls those
endpoints until a workflow needs them — and every write still requires the
owner's explicit approval (see `reddit_client.py`).
