"""FR-1027 Jira REST v3 adapters (FR-892 slot contract) + smoke fixtures.

Credentials: JIRA_URL / JIRA_USERNAME / JIRA_API_TOKEN (the names the editor's
mcp-atlassian server already uses). Fixed URL templates, every path segment
and JQL part quoted/validated, per-call timeout, non-2xx → RuntimeError,
one 429 retry honouring Retry-After. Pagination aborts at the page cap
(OverflowError) before any LLM spend.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

JIRA_TIMEOUT = 60
PAGE_SIZE = 50
MAX_PROJECT_PAGES = 4
MAX_ISSUES = 30
MAX_DESC_CHARS = 300
MAX_PERSONS_PER_PROJECT = 10
MAX_BUNDLE_CHARS = 6000
AI_TERMS = ("AI", "LLM", "GPT", "Copilot", "tekoäly", "kielimalli")
ENV_VARS = ("JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN")
KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")
ISSUE_FIELDS = "summary,issuetype,status,assignee,reporter,description,updated"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "jira"

_sleep = time.sleep


def _env() -> tuple[str, str, str]:
    values = []
    for name in ENV_VARS:
        value = os.environ.get(name, "").strip()
        if not value:
            raise OSError(f"{name} is required for Jira access")
        values.append(value)
    url, user, token = values
    if not url.lower().startswith("https://"):
        raise OSError("JIRA_URL must be an https:// URL")
    return url.rstrip("/"), user, token


def _request(method: str, path: str, body: dict | None = None) -> Any:
    base, user, token = _env()
    url = f"{base}{path}"
    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method)  # noqa: S310 — https enforced in _env
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for attempt in (1, 2):
        try:
            with urlopen(req, timeout=JIRA_TIMEOUT) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 1:
                _sleep(float(exc.headers.get("Retry-After", "1") or 1))
                continue
            raise RuntimeError(f"jira: HTTP {exc.code} for {url}") from exc
    raise RuntimeError(f"jira: retry exhausted for {url}")  # pragma: no cover


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _window(raw: str) -> int:
    if not raw.isdigit() or int(raw) < 1:
        raise ValueError(f"jira: window_days must be a positive integer, got {raw!r}")
    return int(raw)


def _key(raw: str) -> str:
    if not KEY_RE.match(raw):
        raise ValueError(f"jira: invalid project key {raw!r}")
    return raw


def _jql_window(key: str, days: int, field: str = "updated") -> str:
    return f'project = "{key}" AND {field} >= -{days}d'


def _count(jql: str) -> int:
    payload = _request("POST", "/rest/api/3/search/approximate-count", {"jql": jql})
    return int(payload.get("count", 0)) if isinstance(payload, dict) else 0


# --- discover / coverage (AC-08) ----------------------------------------------


def _list_projects() -> tuple[list[str], bool]:
    keys: list[str] = []
    start = 0
    for page in range(MAX_PROJECT_PAGES + 1):
        if page == MAX_PROJECT_PAGES:
            raise OverflowError(
                f"jira: more than MAX_PROJECT_PAGES={MAX_PROJECT_PAGES} pages of projects"
            )
        query = urlencode({"startAt": start, "maxResults": PAGE_SIZE})
        payload = _request("GET", f"/rest/api/3/project/search?{query}")
        values = payload.get("values", []) if isinstance(payload, dict) else []
        for entry in values:
            keys.append(_key(str(entry.get("key", ""))))
        if payload.get("isLast", True) or not values:
            break
        start += PAGE_SIZE
    if len(set(keys)) != len(keys):
        raise ValueError("jira: duplicate project key in listing")
    return sorted(keys), False


def _activity(keys: list[str], days: int) -> tuple[list[str], list[str]]:
    active, dormant = [], []
    for key in keys:
        (active if _count(_jql_window(key, days)) > 0 else dormant).append(key)
    return active, dormant


def jira_active_discover(state: dict[str, Any]) -> list[str]:
    """Sorted project keys with ≥1 issue updated inside the window."""
    days = _window(_require(state, "source"))
    keys, _ = _list_projects()
    active, _ = _activity(keys, days)
    return active


def jira_coverage(state: dict[str, Any]) -> dict[str, Any]:
    """Visible / active / dormant accounting for the coverage record."""
    days = _window(_require(state, "source"))
    keys, cap_hit = _list_projects()
    active, dormant = _activity(keys, days)
    return {
        "visible": len(keys),
        "active": len(active),
        "dormant": len(dormant),
        "page_cap_hit": cap_hit,
        "active_keys": active,
        "dormant_keys": dormant,
    }


# --- extract (AC-09) ----------------------------------------------------------


def _adf_text(node: Any, parts: list[str]) -> None:
    if isinstance(node, dict):
        if node.get("type") == "text" and isinstance(node.get("text"), str):
            parts.append(node["text"])
        for child in node.get("content", []) or []:
            _adf_text(child, parts)
    elif isinstance(node, list):
        for child in node:
            _adf_text(child, parts)


def _flatten_description(desc: Any) -> str:
    if isinstance(desc, str):
        return desc[:MAX_DESC_CHARS]
    parts: list[str] = []
    _adf_text(desc, parts)
    return "".join(parts)[:MAX_DESC_CHARS]


def _person(raw: Any) -> tuple[str | None, str | None]:
    if not isinstance(raw, dict):
        return None, None
    return raw.get("accountId"), raw.get("displayName")


def _issue_row(issue: dict[str, Any]) -> tuple[dict[str, Any], tuple, tuple]:
    fields = issue.get("fields", {}) or {}
    a_id, a_name = _person(fields.get("assignee"))
    r_id, r_name = _person(fields.get("reporter"))
    row = {
        "key": issue.get("key"),
        "summary": fields.get("summary", ""),
        "issuetype": (fields.get("issuetype") or {}).get("name", ""),
        "status": (fields.get("status") or {}).get("name", ""),
        "assignee_id": a_id,
        "reporter_id": r_id,
        "description_head": _flatten_description(fields.get("description")),
    }
    return row, (a_id, a_name), (r_id, r_name)


def _top(counter: Counter, names: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {"account_id": acc, "display_name": names.get(acc, ""), "n": n}
        for acc, n in counter.most_common(MAX_PERSONS_PER_PROJECT)
    ]


def _trim(bundle: dict[str, Any]) -> str:
    blob = json.dumps(bundle, ensure_ascii=False)
    while len(blob) > MAX_BUNDLE_CHARS and bundle["issues"]:
        for issue in bundle["issues"]:
            issue["description_head"] = issue["description_head"][
                : len(issue["description_head"]) // 2
            ]
        if all(not i["description_head"] for i in bundle["issues"]):
            bundle["issues"].pop()
        blob = json.dumps(bundle, ensure_ascii=False)
    if len(blob) > MAX_BUNDLE_CHARS:
        raise ValueError("jira_project_extract: bundle cannot be trimmed under cap")
    return blob


def jira_project_extract(state: dict[str, Any]) -> str:
    """Typed, bounded evidence bundle for one project key."""
    key = _key(_require(state, "item"))
    days = _window(str(state.get("window_days", "")))
    meta = _request("GET", f"/rest/api/3/project/{quote(key)}")
    lead_id, lead_name = _person(meta.get("lead"))
    search = _request(
        "POST",
        "/rest/api/3/search/jql",
        {
            "jql": f"{_jql_window(key, days)} ORDER BY updated DESC",
            "fields": ISSUE_FIELDS.split(","),
            "maxResults": MAX_ISSUES,
        },
    )
    issues, assignees, reporters, names = [], Counter(), Counter(), {}
    for issue in (search.get("issues", []) or [])[:MAX_ISSUES]:
        row, (a_id, a_name), (r_id, r_name) = _issue_row(issue)
        issues.append(row)
        if a_id:
            assignees[a_id] += 1
            names[a_id] = a_name or ""
        if r_id:
            reporters[r_id] += 1
            names[r_id] = r_name or ""
    ai_clause = " OR ".join(f'text ~ "{term}"' for term in AI_TERMS)
    bundle = {
        "key": key,
        "name": meta.get("name", ""),
        "project_type": meta.get("projectTypeKey", ""),
        "lead": {"account_id": lead_id, "display_name": lead_name} if lead_id else None,
        "updated_in_window": _count(_jql_window(key, days)),
        "created_in_window": _count(_jql_window(key, days, "created")),
        "ai_term_count": _count(f"{_jql_window(key, days)} AND ({ai_clause})"),
        "issues": issues,
        "assignees": _top(assignees, names),
        "reporters": _top(reporters, names),
    }
    return _trim(bundle)


# --- smoke fixtures (public-safe, synthetic) -----------------------------------


def _fixture_bundles() -> list[dict[str, Any]]:
    files = sorted(FIXTURE_DIR.resolve().glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no Jira fixtures under {FIXTURE_DIR.resolve()}")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def jira_fixture_discover(state: dict[str, Any]) -> list[str]:
    _window(_require(state, "source"))
    return sorted(
        _key(b["key"]) for b in _fixture_bundles() if b.get("updated_in_window", 0) > 0
    )


def jira_fixture_coverage(state: dict[str, Any]) -> dict[str, Any]:
    _window(_require(state, "source"))
    bundles = _fixture_bundles()
    active = sorted(b["key"] for b in bundles if b.get("updated_in_window", 0) > 0)
    dormant = sorted(b["key"] for b in bundles if b.get("updated_in_window", 0) <= 0)
    return {
        "visible": len(bundles),
        "active": len(active),
        "dormant": len(dormant),
        "page_cap_hit": False,
        "active_keys": active,
        "dormant_keys": dormant,
    }


def jira_fixture_extract(state: dict[str, Any]) -> str:
    key = _key(_require(state, "item"))
    for bundle in _fixture_bundles():
        if bundle.get("key") == key:
            return _trim(bundle)
    raise ValueError(f"jira_fixture_extract: no fixture for {key}")
