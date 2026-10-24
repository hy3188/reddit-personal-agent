"""Unit tests for reddit_client.py — no network access.

Every HTTP interaction is mocked, so `python3 -m unittest discover -s tests`
runs offline. Environment variables are set in setUp so no real credentials
are needed.
"""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import reddit_client as rc


class FakeResponse:
    """Minimal stand-in for urllib's HTTPResponse context manager."""

    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        os.environ["REDDIT_CLIENT_ID"] = "test-client-id"
        os.environ["REDDIT_CLIENT_SECRET"] = "test-client-secret"
        os.environ["REDDIT_REDIRECT_URI"] = "https://example.invalid/callback"
        rc.MIN_CALL_INTERVAL_SECONDS = 0  # tests must not sleep

    def test_auth_url_contains_required_parameters(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc.cmd_auth_url(mock.Mock())
        url = buf.getvalue().strip()
        self.assertTrue(url.startswith(rc.AUTHORIZE_URL + "?"))
        self.assertIn("response_type=code", url)
        self.assertIn("duration=permanent", url)
        self.assertIn("client_id=test-client-id", url)
        self.assertIn("scope=", url)

    def test_exchange_saves_tokens_without_printing_them(self):
        with mock.patch.object(rc, "save_tokens") as save, mock.patch(
            "urllib.request.urlopen",
            return_value=FakeResponse(
                {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
            ),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc.cmd_exchange(mock.Mock(code="one-time-code"))
            save.assert_called_once()
            self.assertNotIn("at", buf.getvalue())
            self.assertNotIn("rt", buf.getvalue())

    def test_submit_refuses_without_owner_approval(self):
        args = mock.Mock(
            subreddit="test", title="t", text="b",
            owner_approved=False, dry_run=False,
        )
        with self.assertRaises(SystemExit):
            rc.cmd_submit(args)

    def test_submit_dry_run_sends_no_request(self):
        args = mock.Mock(
            subreddit="test", title="Hello", text="Body",
            owner_approved=True, dry_run=True,
        )
        with mock.patch("urllib.request.urlopen") as urlopen:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc.cmd_submit(args)
            urlopen.assert_not_called()
            self.assertIn("/api/submit", buf.getvalue())
            self.assertIn("Hello", buf.getvalue())

    def test_me_parses_identity_response(self):
        with mock.patch.object(rc, "access_token", return_value="at"), mock.patch(
            "urllib.request.urlopen",
            return_value=FakeResponse({"name": "Small-Difficulty4306", "id": "abc"}),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc.cmd_me(mock.Mock())
            self.assertIn("Small-Difficulty4306", buf.getvalue())

    def test_api_request_refreshes_once_on_401(self):
        import urllib.error

        def fail_once_then_ok(request, timeout=30):
            if not hasattr(fail_once_then_ok, "called"):
                fail_once_then_ok.called = True
                raise urllib.error.HTTPError(
                    request.full_url, 401, "Unauthorized", {}, None
                )
            return FakeResponse({"name": "Small-Difficulty4306"})

        with mock.patch.object(rc, "load_tokens", return_value={"refresh_token": "rt"}), \
             mock.patch.object(rc, "refresh_tokens", return_value={"access_token": "new"}), \
             mock.patch("urllib.request.urlopen", side_effect=fail_once_then_ok):
            result = rc.api_request("GET", "/api/v1/me")
            self.assertEqual(result["name"], "Small-Difficulty4306")


if __name__ == "__main__":
    unittest.main()
