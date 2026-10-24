# Contributing

This is a personal, single-user project, but small improvements are welcome.

1. Keep it dependency-free (Python standard library only) and single-purpose.
2. Keep every write path behind the `--owner-approved` gate, and add a
   `--dry-run` path for any new write command.
3. Add or update tests in `tests/` for any behaviour change, and run
   `python3 -m unittest discover -s tests` before submitting.
4. Never commit credentials, tokens, or real account data.
