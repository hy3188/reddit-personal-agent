# reddit-personal-agent

A personal, **non-commercial** OAuth2 client for the official Reddit Data API.
It is operated **solely by and for one Reddit account** — the owner's own
account (u/Small-Difficulty4306) — as an assistant integration inside the
owner's private tooling.

> **Status:** Reddit Data API access has been requested under Reddit's
> [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
> and is pending approval. No API access takes place before explicit approval.

## What it does

1. **Read** — fetches the owner's home feed and subscribed subreddits to build
   a personal digest of new posts from communities the owner already follows.
2. **Organize** — reads the owner's history and saved items to group and
   summarize them (e.g. saved posts organized by subreddit).
3. **Write — human-approved only** — when the owner wants to post or reply, the
   assistant drafts the text, the owner reviews and explicitly approves the
   exact wording, and only then does the client call the API
   (`POST /api/submit`, `/api/comment`). The CLI enforces this with an explicit
   `--owner-approved` flag; there is no unattended posting path.
4. **Small actions on explicit instruction only** — save/unsave,
   subscribe/unsubscribe, and votes expressing the owner's own choice on
   content they personally viewed.

## Safeguards & policy compliance

- Single user, single account. No other accounts, no third-party users.
- No bulk, scheduled, or mass posting; no identical cross-posting.
- No vote manipulation or brigading.
- No private messages without the owner's explicit instruction.
- No selling, licensing, sharing, or commercializing Reddit data.
- **No use of Reddit data to train AI/ML models.**
- No retention of Reddit data beyond completing the requested task.
- Expected volume: a handful of human-initiated requests per day, far below
  the 100 QPM free-tier limit.
- Credentials are **never** stored in this repository. The client reads them
  from local environment variables / a git-ignored local token file only.

## OAuth configuration

| Item | Value |
|---|---|
| Flow | OAuth2 authorization code (`duration=permanent` for a refresh token) |
| Authorize endpoint | `https://www.reddit.com/api/v1/authorize` |
| Token endpoint | `https://www.reddit.com/api/v1/access_token` |
| Client authentication | HTTP Basic (`client_secret_basic`) |
| API host | `https://oauth.reddit.com` |
| App type (prefs/apps) | **web app**, name `bbcc` |
| User-Agent | `python:reddit-personal-agent:v0.1.0 (by /u/Small-Difficulty4306)` |

Requested scopes: `identity read history mysubreddits submit edit vote
subscribe save privatemessages flair report wikiread`

## Why not Devvit?

Devvit apps run hosted inside Reddit and are installed into subreddits
(custom posts, moderator tools, games). Devvit provides no way to build an
external personal agent that runs off-platform in the user's own tooling,
obtains OAuth authorization to act on behalf of one individual user's account
across their personal home feed, saved items and history, or is invoked
conversationally outside Reddit. This use case requires the classic Data API
OAuth2 authorization-code flow, which Devvit does not offer.

## Usage

```bash
cp .env.example .env   # fill in your own app credentials locally, never commit .env
python3 reddit_client.py auth-url          # print the authorization URL
python3 reddit_client.py exchange <code>   # exchange the returned code for tokens
python3 reddit_client.py me                # GET /api/v1/me — verify the connection
python3 reddit_client.py digest --limit 10 # newest posts from subscribed subreddits
python3 reddit_client.py saved --limit 10  # the owner's saved items
python3 reddit_client.py submit --subreddit test --title "..." --text "..." --owner-approved
```

Python 3.10+, standard library only — no third-party dependencies.

## License

MIT
