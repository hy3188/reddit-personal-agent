#!/usr/bin/env python3
"""reddit-personal-agent — a single-user OAuth2 client for the Reddit Data API.

Personal, non-commercial use only, operated solely by and for the account
owner. Design rules enforced in code:

* Credentials come from environment variables or a local, git-ignored token
  file. They are never printed, logged, or committed.
* Every write operation (submit / comment) requires the explicit
  ``--owner-approved`` flag, which the operator sets only after the owner has
  reviewed and approved the exact text. ``--dry-run`` prints the payload
  instead of sending it, for review and for tests. There is no unattended
  posting path.
* Requests carry a descriptive User-Agent and stay far below Reddit's
  100 QPM free-tier limit: a minimum gap between calls, plus exponential
  backoff honouring ``Retry-After`` on 429, plus a single automatic token
  refresh-and-retry on 401.

Usage:
    python3 reddit_client.py auth-url
    python3 reddit_client.py exchange <code>
    python3 reddit_client.py revoke
    python3 reddit_client.py me
    python3 reddit_client.py digest [--limit N]
    python3 reddit_client.py saved [--limit N]
    python3 reddit_client.py subscriptions
    python3 reddit_client.py submit --subreddit NAME --title T --text BODY --owner-approved
    python3 reddit_client.py comment --parent t3_xxx --text BODY --owner-approved
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AUTHORIZE_URL = "https://www.reddit.com/api/v1/authorize"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REVOKE_URL = "https://www.reddit.com/api/v1/revoke_token"
API_BASE = "https://oauth.reddit.com"

SCOPES = (
    "identity read history mysubreddits submit edit vote subscribe save "
    "privatemessages flair report wikiread"
)

DEFAULT_USER_AGENT = (
    "python:reddit-personal-agent:v0.1.0 (by /u/Small-Difficulty4306)"
)

TOKEN_FILE = os.environ.get(
    "REDDIT_TOKEN_FILE",
    os.path.join(os.path.expanduser("~"), ".reddit-personal-agent-token.json"),
)

# Stay far below the 100 queries/minute free-tier limit.
MIN_CALL_INTERVAL_SECONDS = 0.6
MAX_429_RETRIES = 3
_LAST_CALL_AT = 0.0


class RedditAPIError(Exception):
    """An error response from Reddit's API (status + short body, no secrets)."""

    def __init__(self, status: int, body: str = "") -> None:
        super().__init__(f"Reddit API error {status}: {body[:200]}")
        self.status = status
        self.body = body


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"error: required environment variable {name} is not set")
    return value


def user_agent() -> str:
    return os.environ.get("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)


def _throttle() -> None:
    """Enforce a minimum gap between API calls."""
    global _LAST_CALL_AT
    now = time.monotonic()
    wait = MIN_CALL_INTERVAL_SECONDS - (now - _LAST_CALL_AT)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL_AT = time.monotonic()


def _urlopen_with_backoff(request: urllib.request.Request):
    """Open a request, honouring 429 Retry-After with bounded retries."""
    for attempt in range(MAX_429_RETRIES + 1):
        _throttle()
        try:
            return urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_429_RETRIES:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = float(retry_after) if retry_after else 2.0
                except ValueError:
                    delay = 2.0
                time.sleep(min(delay, 60.0))
                continue
            raise
    raise AssertionError("unreachable")


def basic_auth_header() -> str:
    pair = f"{env('REDDIT_CLIENT_ID')}:{env('REDDIT_CLIENT_SECRET')}"
    return "Basic " + base64.b64encode(pair.encode()).decode()


def post_token(data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Authorization": basic_auth_header(),
            "User-Agent": user_agent(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with _urlopen_with_backoff(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise RedditAPIError(exc.code, exc.read().decode(errors="replace")) from exc


def save_tokens(tokens: dict) -> None:
    with open(TOKEN_FILE, "w", encoding="utf-8") as fh:
        json.dump(tokens, fh)
    os.chmod(TOKEN_FILE, 0o600)


def load_tokens() -> dict:
    if not os.path.exists(TOKEN_FILE):
        sys.exit("error: no token file; run `auth-url` then `exchange <code>` first")
    with open(TOKEN_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def refresh_tokens() -> dict:
    tokens = load_tokens()
    if not tokens.get("refresh_token"):
        sys.exit("error: token file holds no refresh_token; re-run the auth flow")
    fresh = post_token(
        {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
    )
    tokens.update(fresh)
    save_tokens(tokens)
    return tokens


def access_token() -> str:
    tokens = load_tokens()
    if tokens.get("access_token"):
        return tokens["access_token"]
    return refresh_tokens()["access_token"]


def _do_api_request(method: str, path: str, params: dict | None, token: str) -> dict:
    url = API_BASE + path
    data = None
    if params:
        if method == "GET":
            url += "?" + urllib.parse.urlencode(params)
        else:
            data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": user_agent(),
        },
        method=method,
    )
    try:
        with _urlopen_with_backoff(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise RedditAPIError(exc.code, exc.read().decode(errors="replace")) from exc


def api_request(method: str, path: str, params: dict | None = None) -> dict:
    """Call oauth.reddit.com, refreshing the token once on a 401."""
    try:
        return _do_api_request(method, path, params, access_token())
    except RedditAPIError as exc:
        if exc.status != 401 or not load_tokens().get("refresh_token"):
            raise
        token = refresh_tokens()["access_token"]
        return _do_api_request(method, path, params, token)


def cmd_auth_url(_: argparse.Namespace) -> None:
    query = urllib.parse.urlencode(
        {
            "client_id": env("REDDIT_CLIENT_ID"),
            "response_type": "code",
            "state": secrets.token_urlsafe(16),
            "redirect_uri": env("REDDIT_REDIRECT_URI"),
            "duration": "permanent",
            "scope": SCOPES,
        }
    )
    print(f"{AUTHORIZE_URL}?{query}")


def cmd_exchange(args: argparse.Namespace) -> None:
    tokens = post_token(
        {
            "grant_type": "authorization_code",
            "code": args.code,
            "redirect_uri": env("REDDIT_REDIRECT_URI"),
        }
    )
    save_tokens(tokens)
    print("tokens saved to token file (values not shown)")


def cmd_revoke(_: argparse.Namespace) -> None:
    tokens = load_tokens()
    token = tokens.get("refresh_token") or tokens.get("access_token")
    if not token:
        sys.exit("error: token file holds no token to revoke")
    body = urllib.parse.urlencode(
        {
            "token": token,
            "token_type_hint": "refresh_token"
            if tokens.get("refresh_token")
            else "access_token",
        }
    ).encode()
    req = urllib.request.Request(
        REVOKE_URL,
        data=body,
        headers={
            "Authorization": basic_auth_header(),
            "User-Agent": user_agent(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with _urlopen_with_backoff(req):
            pass
    except urllib.error.HTTPError as exc:
        raise RedditAPIError(exc.code, exc.read().decode(errors="replace")) from exc
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    print("token revoked and local token file removed")


def cmd_me(_: argparse.Namespace) -> None:
    me = api_request("GET", "/api/v1/me")
    print(json.dumps({"name": me.get("name"), "id": me.get("id")}, indent=2))


def cmd_digest(args: argparse.Namespace) -> None:
    subs = api_request("GET", "/subreddits/mine/subscriber", {"limit": 100})
    names = [
        child["data"]["display_name"]
        for child in subs.get("data", {}).get("children", [])
    ]
    if not names:
        print("no subscriptions found")
        return
    listing = api_request("GET", f"/r/{'+'.join(names)}/new", {"limit": args.limit})
    for child in listing.get("data", {}).get("children", []):
        d = child["data"]
        print(f"r/{d['subreddit']} · {d['title']} · {d['permalink']}")


def cmd_saved(args: argparse.Namespace) -> None:
    me = api_request("GET", "/api/v1/me")
    listing = api_request("GET", f"/user/{me['name']}/saved", {"limit": args.limit})
    for child in listing.get("data", {}).get("children", []):
        d = child["data"]
        title = d.get("title") or (d.get("body") or "")[:80]
        print(f"{child['kind']} · r/{d.get('subreddit')} · {title}")


def cmd_subscriptions(_: argparse.Namespace) -> None:
    subs = api_request("GET", "/subreddits/mine/subscriber", {"limit": 100})
    for child in subs.get("data", {}).get("children", []):
        print(child["data"]["display_name"])


def require_owner_approved(args: argparse.Namespace) -> None:
    if not args.owner_approved:
        sys.exit(
            "refused: writes require --owner-approved, set only after the "
            "account owner has reviewed and approved the exact text"
        )


def cmd_submit(args: argparse.Namespace) -> None:
    require_owner_approved(args)
    payload = {
        "sr": args.subreddit,
        "title": args.title,
        "text": args.text,
        "kind": "self",
        "resubmit": "false",
        "send_replies": "true",
    }
    if args.dry_run:
        print(json.dumps({"endpoint": "/api/submit", "payload": payload}, indent=2))
        return
    result = api_request("POST", "/api/submit", payload)
    print(json.dumps(result.get("json", {}).get("data", {}), indent=2))


def cmd_comment(args: argparse.Namespace) -> None:
    require_owner_approved(args)
    payload = {"thing_id": args.parent, "text": args.text}
    if args.dry_run:
        print(json.dumps({"endpoint": "/api/comment", "payload": payload}, indent=2))
        return
    result = api_request("POST", "/api/comment", payload)
    print(json.dumps(result.get("json", {}).get("data", {}), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth-url").set_defaults(func=cmd_auth_url)

    p_exchange = sub.add_parser("exchange")
    p_exchange.add_argument("code")
    p_exchange.set_defaults(func=cmd_exchange)

    sub.add_parser("revoke").set_defaults(func=cmd_revoke)

    sub.add_parser("me").set_defaults(func=cmd_me)

    p_digest = sub.add_parser("digest")
    p_digest.add_argument("--limit", type=int, default=10)
    p_digest.set_defaults(func=cmd_digest)

    p_saved = sub.add_parser("saved")
    p_saved.add_argument("--limit", type=int, default=10)
    p_saved.set_defaults(func=cmd_saved)

    sub.add_parser("subscriptions").set_defaults(func=cmd_subscriptions)

    p_submit = sub.add_parser("submit")
    p_submit.add_argument("--subreddit", required=True)
    p_submit.add_argument("--title", required=True)
    p_submit.add_argument("--text", required=True)
    p_submit.add_argument("--owner-approved", action="store_true")
    p_submit.add_argument("--dry-run", action="store_true")
    p_submit.set_defaults(func=cmd_submit)

    p_comment = sub.add_parser("comment")
    p_comment.add_argument("--parent", required=True, help="fullname, e.g. t3_xxxxxx")
    p_comment.add_argument("--text", required=True)
    p_comment.add_argument("--owner-approved", action="store_true")
    p_comment.add_argument("--dry-run", action="store_true")
    p_comment.set_defaults(func=cmd_comment)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
