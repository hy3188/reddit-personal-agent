# Use case: a personal reading and drafting assistant for one Reddit account

## The problem

A Reddit user who follows many communities cannot keep up with them in the
official feed alone: interesting posts are missed, saved items pile up
unorganized, and drafting a thoughtful reply takes longer than reading the
thread. This project solves that for **one account — the owner's own** — by
letting an assistant the owner already uses read their feed and draft text
for them.

## Who it serves

Exactly one person: the owner of the Reddit account that authorizes the app
(u/Small-Difficulty4306). There are no other users, no public deployment,
and nothing is offered to third parties. This is a personal tool, not a
product.

## Typical workflows

### 1. Morning digest (read-only)

```
owner asks for a digest
  -> GET /subreddits/mine/subscriber        (which communities do I follow?)
  -> GET /r/<a+b+c>/new                     (what is new there?)
  -> assistant summarizes, in chat only
```

Nothing is posted. The output is a private summary shown to the owner.

### 2. Organizing saved items (read-only)

```
owner asks what they saved
  -> GET /api/v1/me                         (who am I, for the path)
  -> GET /user/<name>/saved                 (saved posts/comments)
  -> assistant groups them by subreddit
```

### 3. Posting a reply (human-approved write)

```
owner dictates an idea
  -> assistant drafts the exact text
  -> owner reviews and approves the exact wording
  -> operator runs: submit/comment ... --owner-approved
  -> POST /api/comment                      (only now, once)
```

If `--owner-approved` is missing, the client **refuses to run** (exit code
non-zero, nothing sent). `--dry-run` prints the payload for review without
sending it. There is no scheduled, bulk, or unattended posting path anywhere
in the code.

## Why this genuinely needs the Data API

| Alternative | Why it does not work |
|---|---|
| **Devvit (Developer Platform)** | Devvit apps run hosted inside Reddit and are installed into subreddits (custom posts, moderator tools, games). Devvit has no way to build an external personal agent that runs in the user's own tooling, is invoked conversationally outside Reddit, or acts on behalf of one user's account across their personal feed, saved items, and history. |
| **RSS / public feeds** | Feeds are read-only, anonymous, and cannot represent the owner's subscriptions, saved items, history, or identity — and Reddit is retiring public RSS feeds. They cannot perform any of the owner-approved write workflows either. |
| **Scraping HTML** | Scraping is not an API, breaks constantly, and violates Reddit's terms. It is explicitly out of scope for this project. |
| **Third-party client apps** | Existing apps are built for many users and their own feature sets; none of them is the owner's own assistant, and routing the owner's OAuth credentials through an unrelated third party is a worse security posture than a small, auditable, single-purpose client. |

The Data API with OAuth2 is therefore the only supported route: it gives the
owner a scoped, revocable grant (`/api/v1/authorize` → `access_token` →
`oauth.reddit.com`), per-endpoint scope control, and rate limits the client
respects (see `docs/SCOPES.md` and `docs/COMPLIANCE.md`).

## What the app will never do

- Post, comment, vote, message, or subscribe without the owner's explicit
  instruction for that exact action.
- Post the same or similar content across subreddits.
- Manipulate votes or karma, brigade, or circumvent blocks or bans.
- Read or act on any account other than the owner's.
- Retain Reddit data beyond the task at hand, or share/sell/license it.
- Use Reddit data to train machine-learning or AI models.
