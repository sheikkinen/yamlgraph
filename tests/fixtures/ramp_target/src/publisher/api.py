"""External gallery API client (fixture)."""

import os
import urllib.request

API_URL = "https://gallery.example.com/api/v1/posts"
MAX_TITLE = 50


def post_card(title: str, body: str) -> int:
    """Upload a card; returns HTTP status."""
    token = os.environ["GALLERY_TOKEN"]
    if len(title) > MAX_TITLE:
        raise ValueError("title exceeds gallery cap")
    req = urllib.request.Request(
        API_URL,
        data=body.encode(),
        headers={"Authorization": f"Bearer {token}", "X-Title": title},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status
