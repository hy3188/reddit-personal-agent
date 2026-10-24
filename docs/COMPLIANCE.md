# Compliance with Reddit's policies

This project is built to comply with Reddit's
[Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy),
[Developer Terms](https://www.redditinc.com/policies/developer-terms), and
[Data API Terms](https://www.redditinc.com/policies/data-api-terms).

## Approval

Per the Responsible Builder Policy, **explicit approval is required before
accessing any Reddit data through the API**. A Data Access Request was
submitted for this app (see README status); no data is fetched through the
API before approval is granted. App registration alone is not treated as
approval.

## Rules the client enforces

- **Single user, single account.** Only the authorizing owner's account is
  ever accessed. No other accounts, no multi-user deployment.
- **Human-approved writes.** Every submit/comment requires `--owner-approved`,
  set only after the owner reviewed the exact text. No bulk, scheduled, or
  unattended posting. No identical cross-posting.
- **No manipulation.** No vote manipulation, brigading, karma farming, or
  circumvention of blocks, bans, or other safety mechanisms.
- **No spam.** No automated posts, comments, or direct messages beyond the
  owner's own, individually approved actions.
- **No commercialization.** Non-commercial, personal use only. Reddit data
  is never sold, licensed, shared, or used for advertising.
- **No AI training.** Reddit data is never used to train machine-learning or
  AI models.
- **No sensitive inference.** Data is never processed to derive or infer
  sensitive characteristics about users, and never used to re-identify or
  de-anonymize anyone.
- **Minimal retention.** Reddit data is used only to complete the requested
  task and is not retained beyond it.
- **Rate limits respected.** The client enforces a minimum gap between calls
  (well below the 100 queries/minute free-tier limit), honours `Retry-After`
  on 429 responses with bounded backoff, and never circumvents limits.

## Transparency

- The app's purpose, scope, and source code are public in this repository.
- The User-Agent identifies the app and the owner account:
  `python:reddit-personal-agent:v0.1.0 (by /u/Small-Difficulty4306)`.
- Tokens are revocable at any time: `python3 reddit_client.py revoke`, or
  from the Reddit account's authorized-apps page.

## If approval is denied or revoked

The client stops being used for Data API access. The `revoke` command
removes the stored tokens locally, and the app can also be deauthorized from
the Reddit account settings.
