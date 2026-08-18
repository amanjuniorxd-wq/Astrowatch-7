"""
Astrowatch Online -- minimal X (Twitter) API v2 client.
==========================================================
Implements OAuth 1.0a User Context request signing (the standard algorithm --
RFC 5849 / X's documented variant) using only the standard library, and a
single method to post a tweet (POST /2/tweets). No live network call is made
anywhere in this module unless post_tweet() is actually invoked by
publisher.py, which itself is gated by X_ENABLED.

Credentials (never hard-coded, read fresh from the environment on each call):
    X_API_KEY, X_API_SECRET                 -- app consumer key/secret
    X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET    -- user access token/secret
"""

import hashlib
import hmac
import json
import os
import random
import string
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

API_URL = "https://api.twitter.com/2/tweets"


class XClientError(Exception):
    """Raised for any X API/credential problem -- callers (publisher.py) catch
    this and record a clear failure, never silently drop or fabricate a
    post_id."""


class XCredentialsMissing(XClientError):
    pass


def _get_credentials() -> Dict[str, str]:
    keys = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    creds = {k: os.environ.get(k, "") for k in keys}
    missing = [k for k, v in creds.items() if not v]
    if missing:
        raise XCredentialsMissing(
            f"X publishing is enabled (X_ENABLED=true) but the following "
            f"required credentials are not set: {missing}. Set them in the "
            f"environment (.env.example lists all required X_* variables)."
        )
    return creds


def _nonce(length: int = 32) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def _percent_encode(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def _oauth1_signature(method: str, url: str, params: Dict[str, str],
                       consumer_secret: str, token_secret: str) -> str:
    sorted_params = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items())
    )
    base_string = "&".join([method.upper(), _percent_encode(url), _percent_encode(sorted_params)])
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"
    digest = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    import base64
    return base64.b64encode(digest).decode()


def _oauth1_header(method: str, url: str, creds: Dict[str, str]) -> str:
    oauth_params = {
        "oauth_consumer_key": creds["X_API_KEY"],
        "oauth_nonce": _nonce(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": creds["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    signature = _oauth1_signature(method, url, oauth_params,
                                   creds["X_API_SECRET"], creds["X_ACCESS_TOKEN_SECRET"])
    oauth_params["oauth_signature"] = signature
    header = "OAuth " + ", ".join(
        f'{_percent_encode(k)}="{_percent_encode(v)}"' for k, v in sorted(oauth_params.items())
    )
    return header


def post_tweet(text: str, timeout: int = 15) -> Dict[str, Any]:
    """Posts a single tweet via X API v2. Returns the parsed JSON response
    (contains data.id, the tweet id, on success). Raises XClientError on any
    failure -- never returns a fabricated post id."""
    creds = _get_credentials()
    auth_header = _oauth1_header("POST", API_URL, creds)
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace") if hasattr(e, "read") else str(e)
        raise XClientError(f"X API returned HTTP {e.code}: {detail}") from e
    except Exception as e:  # noqa: BLE001
        raise XClientError(f"X API request failed: {e}") from e
