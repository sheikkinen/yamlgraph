"""curl_probe — URL probe tool for API discovery (FR-783).

Python wrapper because curl ``-w`` format braces conflict with the
shell runtime's ``str.format()`` substitution. Uses subprocess
with argument lists (no shell=True) for security.

Contract: ``curl_probe(url, user_agent, timeout) -> dict``
  All parameters required (FR-768 shell manifests have no defaults).
  Returns ``{"status": int, "redirect": str, "content_type": str,
             "body_head": str}`` where ``body_head`` ≤ 2048 chars.
"""

from __future__ import annotations

import json
import subprocess

BODY_HEAD_LIMIT = 2048


def curl_probe(url: str, user_agent: str, timeout: str) -> dict:
    """Probe a URL with curl, return structured metadata + body preview."""
    write_out = (
        '{"status":%{http_code},'
        '"redirect":"%{redirect_url}",'
        '"content_type":"%{content_type}"}'
    )

    # Pass 1: metadata via -w (no shell — args list is injection-safe)
    meta_result = subprocess.run(
        [
            "curl",
            "-s",
            "--max-time",
            str(timeout),
            "-A",
            user_agent,
            "-o",
            "/dev/null",
            "-w",
            write_out,
            url,
        ],
        capture_output=True,
        text=True,
        timeout=int(timeout) + 5,
    )

    try:
        meta = json.loads(meta_result.stdout)
    except (json.JSONDecodeError, ValueError):
        meta = {"status": 0, "redirect": "", "content_type": ""}

    # Pass 2: body head (capped)
    body_result = subprocess.run(
        [
            "curl",
            "-s",
            "--max-time",
            str(timeout),
            "-A",
            user_agent,
            url,
        ],
        capture_output=True,
        text=True,
        timeout=int(timeout) + 5,
    )
    body_head = body_result.stdout[:BODY_HEAD_LIMIT]

    return {
        "status": int(meta.get("status", 0)),
        "redirect": meta.get("redirect", ""),
        "content_type": meta.get("content_type", ""),
        "body_head": body_head,
    }
