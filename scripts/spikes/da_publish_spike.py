#!/usr/bin/env python3
"""FR-822 DeviantArt publish spike — THROWAWAY (AC-08).

One real API publish to answer research-doc §4 questions.
Findings, not code, are the deliverable.
"""

import base64
import hashlib
import http.server
import json
import secrets
import stat
import sys
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

AUTH_URL = "https://www.deviantart.com/oauth2/authorize"
TOKEN_URL = "https://www.deviantart.com/oauth2/token"  # noqa: S105 - endpoint URL, not a secret (CONF-406)
API = "https://www.deviantart.com/api/v1/oauth2"
REDIRECT_URI = "http://localhost:8721/cb"
SCOPE = "basic stash publish"
TOKEN_FILE = Path.home() / ".deviantart" / "token.json"
UA = {"User-Agent": "yamlgraph-fr822-spike/0.1"}
TIMEOUT = 180  # upload of a 1.4 MB PNG on a slow link


def load_env() -> tuple[str, str]:
    env: dict[str, str] = {}
    for envfile in (Path(".env"), Path.home() / ".env"):
        if not envfile.exists():
            continue
        for line in envfile.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env.setdefault(k.strip(), v.strip().strip('"'))
    cid, csec = env.get("DA_CLIENT_ID"), env.get("DA_CLIENT_SECRET")
    if not cid or not csec:
        sys.exit("DA_CLIENT_ID / DA_CLIENT_SECRET missing from .env / ~/.env")
    return cid, csec


def save_token(tok: dict) -> None:
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(tok, indent=2))
    TOKEN_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def pkce_authorize(cid: str, csec: str) -> dict:
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = secrets.token_urlsafe(16)
    url = (
        AUTH_URL
        + "?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": cid,
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPE,
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
    )
    print(f"\nAuthorize in browser:\n{url}\n", flush=True)
    webbrowser.open(url)

    code_holder: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - stdlib contract (CONF-407)
            q = parse_qs(urlparse(self.path).query)
            code_holder.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Spike: code received, close this tab.")

        def log_message(self, *a):
            pass

    with http.server.HTTPServer(("localhost", 8721), Handler) as srv:
        srv.handle_request()
    if code_holder.get("state") != state:
        sys.exit(f"state mismatch or error: {code_holder}")
    r = requests.post(
        TOKEN_URL,
        headers=UA,
        timeout=TIMEOUT,
        data={
            "grant_type": "authorization_code",
            "client_id": cid,
            "client_secret": csec,
            "code": code_holder["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        },
    )
    print("token exchange:", r.status_code, r.text, flush=True)
    r.raise_for_status()
    return r.json()


def refresh(cid: str, csec: str, tok: dict) -> dict:
    r = requests.post(
        TOKEN_URL,
        headers=UA,
        timeout=TIMEOUT,
        data={
            "grant_type": "refresh_token",
            "client_id": cid,
            "client_secret": csec,
            "refresh_token": tok["refresh_token"],
        },
    )
    print("token refresh:", r.status_code, r.text, flush=True)
    r.raise_for_status()
    return r.json()


def main() -> None:
    cid, csec = load_env()
    if TOKEN_FILE.exists():
        tok = refresh(cid, csec, json.loads(TOKEN_FILE.read_text()))
    else:
        tok = pkce_authorize(cid, csec)
    save_token(tok)
    auth = {**UA, "Authorization": f"Bearer {tok['access_token']}"}

    r = requests.post(f"{API}/placebo", headers=auth, timeout=TIMEOUT)
    print("placebo:", r.status_code, r.text, flush=True)
    r.raise_for_status()

    comments = (
        "First paragraph of the spike description. Testing paragraph "
        "rendering for FR-822.\n\n"
        "Second paragraph after a blank line. If these merge, "
        "artist_comments is lossy for the style spec.\n\n"
        "Be Art. Be Unique."
    )
    tags = ["ai", "aiart", "digitalart", "inkpunk", "gothic"]
    data = [
        ("title", "API Spike: Veil and Vow"),
        ("artist_comments", comments),
        ("is_ai_generated", "true"),
        ("noai", "true"),
    ] + [(f"tags[{i}]", t) for i, t in enumerate(tags)]
    with open("tmp/da.png", "rb") as f:
        r = requests.post(
            f"{API}/stash/submit",
            headers=auth,
            data=data,
            timeout=TIMEOUT,
            files={"file": ("da.png", f, "image/png")},
        )
    print("submit:", r.status_code, r.text, flush=True)
    r.raise_for_status()
    itemid = r.json()["itemid"]

    r = requests.post(
        f"{API}/stash/publish",
        headers=auth,
        timeout=TIMEOUT,
        data={
            "itemid": itemid,
            "is_mature": "false",
            "is_ai_generated": "true",
            "noai": "true",
        },
    )
    print("publish:", r.status_code, r.text, flush=True)
    r.raise_for_status()
    print("\nDeviation URL:", r.json()["url"], flush=True)


if __name__ == "__main__":
    main()
