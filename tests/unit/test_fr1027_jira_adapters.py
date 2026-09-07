"""FR-1027 witnesses — Jira REST adapters (REQ-YG-670, AC-08, AC-09).

Fixed URL templates, quoted path/JQL parts, basic auth from the three env
names the editor MCP server already uses, bounded pagination with an
overflow abort before any LLM spend, typed bounded bundles.
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import jira_adapters as ja

pytestmark = pytest.mark.process

MOD = "examples.demos.corpus_census.adapters.jira_adapters"
ENV = {
    "JIRA_URL": "https://example.atlassian.net",
    "JIRA_USERNAME": "me@example.com",
    "JIRA_API_TOKEN": "tok",
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)


class _Resp:
    def __init__(self, body: dict | list, status: int = 200):
        self._body = json.dumps(body).encode()
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(url: str, code: int, headers: dict | None = None):
    return urllib.error.HTTPError(url, code, "err", headers or {}, None)  # type: ignore[arg-type]


def _project_pages(n_projects: int, page_size: int = 50):
    pages = []
    keys = [f"P{i:03d}" for i in range(n_projects)]
    for start in range(0, max(n_projects, 1), page_size):
        chunk = keys[start : start + page_size]
        pages.append(
            {
                "values": [{"key": k, "name": f"Project {k}"} for k in chunk],
                "isLast": start + page_size >= n_projects,
            }
        )
    return pages


def _router(pages, counts: dict[str, int] | None = None, extra: dict | None = None):
    """Route (method, url, body) → response; records every request."""
    calls: list[tuple[str, str, dict | None]] = []
    counts = counts or {}
    extra = extra or {}

    def opener(req, timeout=None):
        body = json.loads(req.data) if req.data else None
        url = req.full_url
        calls.append((req.get_method(), url, body))
        assert timeout == ja.JIRA_TIMEOUT
        assert req.get_header("Authorization", "").startswith("Basic ")
        for frag, resp in extra.items():
            if frag in url:
                if isinstance(resp, Exception):
                    raise resp
                return _Resp(resp) if not isinstance(resp, _Resp) else resp
        if "/project/search" in url:
            start = int(
                dict(p.split("=") for p in url.split("?")[1].split("&"))["startAt"]
            )
            return _Resp(pages[start // 50])
        if "/search/approximate-count" in url:
            jql = body["jql"]
            key = jql.split('"')[1]
            return _Resp({"count": counts.get(key, 0)})
        raise AssertionError(f"unrouted: {url}")

    return opener, calls


# --- AC-08: discover -------------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_discover_paginates_counts_and_returns_sorted_active_keys():
    opener, calls = _router(_project_pages(3), counts={"P000": 5, "P002": 1})
    with patch(f"{MOD}.urlopen", side_effect=opener):
        keys = ja.jira_active_discover({"source": "90"})
    assert keys == ["P000", "P002"]
    count_calls = [c for c in calls if "approximate-count" in c[1]]
    assert len(count_calls) == 3
    assert count_calls[0][2]["jql"] == 'project = "P000" AND updated >= -90d'
    assert calls[0][1].startswith(ENV["JIRA_URL"] + "/rest/api/3/project/search?")


@pytest.mark.req("REQ-YG-670")
def test_discover_page_cap_overflow_aborts():
    n = ja.MAX_PROJECT_PAGES * 50 + 1
    opener, _ = _router(_project_pages(n))
    with patch(f"{MOD}.urlopen", side_effect=opener), pytest.raises(OverflowError):
        ja.jira_active_discover({"source": "90"})


@pytest.mark.req("REQ-YG-670")
def test_discover_at_cap_succeeds():
    n = ja.MAX_PROJECT_PAGES * 50
    opener, _ = _router(_project_pages(n), counts={"P000": 1})
    with patch(f"{MOD}.urlopen", side_effect=opener):
        assert ja.jira_active_discover({"source": "90"}) == ["P000"]


@pytest.mark.req("REQ-YG-670")
def test_discover_rejects_bad_key_and_bad_window():
    pages = [{"values": [{"key": "bad-key", "name": "x"}], "isLast": True}]
    opener, _ = _router(pages)
    with (
        patch(f"{MOD}.urlopen", side_effect=opener),
        pytest.raises(ValueError, match="key"),
    ):
        ja.jira_active_discover({"source": "90"})
    for bad in ["", "x", "0", "-5"]:
        with pytest.raises(ValueError):
            ja.jira_active_discover({"source": bad})


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("missing", sorted(ENV))
def test_missing_env_raises_before_any_request(monkeypatch, missing):
    monkeypatch.delenv(missing)
    with patch(f"{MOD}.urlopen") as spy, pytest.raises(EnvironmentError, match=missing):
        ja.jira_active_discover({"source": "90"})
    spy.assert_not_called()


@pytest.mark.req("REQ-YG-670")
def test_coverage_listing_reports_visible_active_dormant():
    opener, _ = _router(_project_pages(4), counts={"P001": 2})
    with patch(f"{MOD}.urlopen", side_effect=opener):
        cov = ja.jira_coverage({"source": "90"})
    assert cov == {
        "visible": 4,
        "active": 1,
        "dormant": 3,
        "page_cap_hit": False,
        "active_keys": ["P001"],
        "dormant_keys": ["P000", "P002", "P003"],
    }


# --- AC-09: extract --------------------------------------------------------------

ADF = {
    "type": "doc",
    "content": [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Roll out "},
                {"type": "text", "text": "Copilot"},
            ],
        },
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "x" * 500}],
                        }
                    ],
                }
            ],
        },
    ],
}


def _issue(i: int, assignee: str | None = "a1", reporter: str | None = "r1"):
    return {
        "key": f"P000-{i}",
        "fields": {
            "summary": f"Issue {i}",
            "issuetype": {"name": "Task"},
            "status": {"name": "Done"},
            "assignee": {"accountId": assignee, "displayName": "Alice"}
            if assignee
            else None,
            "reporter": {"accountId": reporter, "displayName": "Rob"}
            if reporter
            else None,
            "description": ADF,
        },
    }


def _extract_extra(n_issues: int = 40, counts=(7, 3, 2)):
    updated, created, ai = counts

    def count_resp(req):
        jql = json.loads(req.data)["jql"]
        if "created >=" in jql:
            return {"count": created}
        if "text ~" in jql:
            return {"count": ai}
        return {"count": updated}

    return {
        "/project/P000": {
            "key": "P000",
            "name": "Proj",
            "projectTypeKey": "software",
            "lead": {"accountId": "l1", "displayName": "Lead"},
        },
        "/search/jql": {"issues": [_issue(i) for i in range(n_issues)]},
        "/search/approximate-count": count_resp,
    }


def _extract_opener(extra):
    calls = []

    def opener(req, timeout=None):
        url = req.full_url
        calls.append(
            (req.get_method(), url, json.loads(req.data) if req.data else None)
        )
        for frag, resp in extra.items():
            if frag in url:
                if isinstance(resp, Exception):
                    raise resp
                if callable(resp):
                    return _Resp(resp(req))
                return _Resp(resp)
        raise AssertionError(f"unrouted: {url}")

    return opener, calls


@pytest.mark.req("REQ-YG-670")
def test_extract_bundle_typed_bounded_and_adf_flattened():
    opener, calls = _extract_opener(_extract_extra())
    with patch(f"{MOD}.urlopen", side_effect=opener):
        blob = ja.jira_project_extract({"item": "P000", "window_days": "90"})
    assert len(blob) <= ja.MAX_BUNDLE_CHARS
    b = json.loads(blob)
    assert b["key"] == "P000" and b["lead"] == {
        "account_id": "l1",
        "display_name": "Lead",
    }
    assert (b["updated_in_window"], b["created_in_window"], b["ai_term_count"]) == (
        7,
        3,
        2,
    )
    assert len(b["issues"]) == ja.MAX_ISSUES
    first = b["issues"][0]
    assert first["assignee_id"] == "a1" and first["reporter_id"] == "r1"
    assert first["description_head"].startswith("Roll out Copilot")
    assert len(first["description_head"]) <= ja.MAX_DESC_CHARS
    assert b["assignees"] == [
        {"account_id": "a1", "display_name": "Alice", "n": ja.MAX_ISSUES}
    ]
    search = next(c for c in calls if "/search/jql" in c[1])
    assert search[2]["maxResults"] == ja.MAX_ISSUES
    assert (
        search[2]["jql"] == 'project = "P000" AND updated >= -90d ORDER BY updated DESC'
    )
    ai = next(c for c in calls if c[2] and "text ~" in c[2].get("jql", ""))
    assert ai[2]["jql"].startswith(
        'project = "P000" AND updated >= -90d AND (text ~ "AI" OR '
    )
    assert 'text ~ "tekoäly"' in ai[2]["jql"]


@pytest.mark.req("REQ-YG-670")
def test_extract_non_2xx_raises_and_429_retries_once(monkeypatch):
    sleeps = []
    monkeypatch.setattr(ja, "_sleep", sleeps.append)
    extra = _extract_extra()
    extra["/project/P000"] = _http_error("u", 500)
    opener, _ = _extract_opener(extra)
    with (
        patch(f"{MOD}.urlopen", side_effect=opener),
        pytest.raises(RuntimeError, match="500"),
    ):
        ja.jira_project_extract({"item": "P000", "window_days": "90"})

    attempts = {"n": 0}
    good = _extract_extra()["/project/P000"]

    def flaky(req):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise _http_error("u", 429, {"Retry-After": "2"})
        return good

    extra = _extract_extra()
    extra["/project/P000"] = flaky
    opener, _ = _extract_opener(extra)
    with patch(f"{MOD}.urlopen", side_effect=opener):
        ja.jira_project_extract({"item": "P000", "window_days": "90"})
    assert attempts["n"] == 2 and sleeps == [2.0]


@pytest.mark.req("REQ-YG-670")
def test_extract_timeout_surfaces():
    extra = _extract_extra()
    extra["/project/P000"] = TimeoutError("slow")
    opener, _ = _extract_opener(extra)
    with patch(f"{MOD}.urlopen", side_effect=opener), pytest.raises(TimeoutError):
        ja.jira_project_extract({"item": "P000", "window_days": "90"})


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("item", ["", "lower", "P000-1", "A B"])
def test_extract_rejects_bad_key(item):
    with pytest.raises(ValueError):
        ja.jira_project_extract({"item": item, "window_days": "90"})


# --- fixtures (smoke) --------------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_fixture_adapters_read_committed_public_safe_bundles():
    keys = ja.jira_fixture_discover({"source": "90"})
    assert keys and all(k.startswith("DEMO") for k in keys)
    blob = ja.jira_fixture_extract({"item": keys[0]})
    b = json.loads(blob)
    assert b["key"] == keys[0] and len(blob) <= ja.MAX_BUNDLE_CHARS
    assert ja.jira_fixture_coverage({"source": "90"})["visible"] >= len(keys)
