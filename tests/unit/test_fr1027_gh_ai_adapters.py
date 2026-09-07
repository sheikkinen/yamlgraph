"""FR-1027 witnesses — GitHub AI-signal adapters (REQ-YG-670, AC-05..AC-07).

Slot contract (FR-892): state-dict in; discover → sorted unique ids,
extract → bounded JSON bundle, search → keyword→repos map with cap flags.
Every `gh` call is fixed argv, no shell. Ceilings are frozen in the FR
(§ Ceilings): N passes, N+1 aborts before any LLM spend.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import gh_ai_adapters as gh

pytestmark = pytest.mark.process

MOD = "examples.demos.corpus_census.adapters.gh_ai_adapters"
NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def _completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout)


def _iso(days_ago: int) -> str:
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo(name: str, days_ago: int = 1, archived: bool = False, vis: str = "PRIVATE"):
    return {
        "name": name,
        "pushedAt": _iso(days_ago),
        "isArchived": archived,
        "visibility": vis,
    }


@pytest.fixture(autouse=True)
def _frozen_now(monkeypatch):
    monkeypatch.setattr(gh, "_now", lambda: NOW)


# --- AC-05: discover -----------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_discover_filters_and_sorts_unique():
    listing = json.dumps(
        [
            _repo("zeta"),
            _repo("alpha", days_ago=10),
            _repo("old", days_ago=91),
            _repo("arch", archived=True),
            _repo("pub", vis="PUBLIC"),
        ]
    )
    with patch(f"{MOD}.subprocess.run", return_value=_completed(listing)) as run:
        items = gh.gh_org_active_discover(
            {"source": "acme:90", "visibility": "private,internal"}
        )
    argv = run.call_args[0][0]
    assert argv[:4] == ["gh", "repo", "list", "acme"]
    assert argv[argv.index("--limit") + 1] == str(gh.MAX_REPOS + 1)
    assert run.call_args.kwargs.get("shell") in (None, False)
    assert items == ["acme/alpha", "acme/zeta"]


@pytest.mark.req("REQ-YG-670")
def test_discover_visibility_rejection_is_counted_not_fatal():
    listing = json.dumps([_repo("a"), _repo("p", vis="PUBLIC")])
    with patch(f"{MOD}.subprocess.run", return_value=_completed(listing)):
        items = gh.gh_org_active_discover(
            {"source": "acme:90", "visibility": "private"}
        )
    assert items == ["acme/a"]


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("source", ["", "acme", "acme:x", "acme:0", ":90"])
def test_discover_malformed_source_raises(source):
    with pytest.raises(ValueError):
        gh.gh_org_active_discover({"source": source, "visibility": "private"})


@pytest.mark.req("REQ-YG-670")
def test_discover_requires_visibility_policy():
    with pytest.raises(ValueError, match="visibility"):
        gh.gh_org_active_discover({"source": "acme:90"})


@pytest.mark.req("REQ-YG-670")
def test_discover_malformed_timestamp_raises():
    bad = [
        {
            "name": "a",
            "pushedAt": "yesterday",
            "isArchived": False,
            "visibility": "PRIVATE",
        }
    ]
    with (
        patch(f"{MOD}.subprocess.run", return_value=_completed(json.dumps(bad))),
        pytest.raises(ValueError, match="pushedAt"),
    ):
        gh.gh_org_active_discover({"source": "acme:90", "visibility": "private"})


@pytest.mark.req("REQ-YG-670")
def test_discover_duplicate_raises():
    listing = json.dumps([_repo("a"), _repo("a")])
    with (
        patch(f"{MOD}.subprocess.run", return_value=_completed(listing)),
        pytest.raises(ValueError, match="duplicate"),
    ):
        gh.gh_org_active_discover({"source": "acme:90", "visibility": "private"})


@pytest.mark.req("REQ-YG-670")
def test_discover_overflow_aborts_at_ceiling_plus_one():
    at_cap = json.dumps([_repo(f"r{i:04d}") for i in range(gh.MAX_REPOS)])
    with patch(f"{MOD}.subprocess.run", return_value=_completed(at_cap)):
        assert (
            len(
                gh.gh_org_active_discover(
                    {"source": "acme:90", "visibility": "private"}
                )
            )
            == gh.MAX_REPOS
        )
    over = json.dumps([_repo(f"r{i:04d}") for i in range(gh.MAX_REPOS + 1)])
    with (
        patch(f"{MOD}.subprocess.run", return_value=_completed(over)),
        pytest.raises(OverflowError),
    ):
        gh.gh_org_active_discover({"source": "acme:90", "visibility": "private"})


# --- AC-06: extract ------------------------------------------------------------

TREE = {
    "truncated": False,
    "tree": [
        {"path": "package.json"},
        {"path": ".github/copilot-instructions.md"},
        {"path": ".github/workflows/ci.yml"},
        {"path": "src/index.ts"},
        {"path": "CLAUDE.md"},
    ],
}


def _b64(text: str) -> str:
    import base64

    return base64.b64encode(text.encode()).decode()


def _gh_router(overrides: dict | None = None):
    """Route fixed argv → canned stdout by URL fragment."""
    table = {
        "repos/acme/r": json.dumps(
            {
                "description": "demo",
                "pushed_at": _iso(1),
                "archived": False,
                "visibility": "private",
                "language": "TypeScript",
            }
        ),
        "/readme": json.dumps({"content": _b64("# R\nhello " * 800)}),
        "/contributors": json.dumps([{"login": f"u{i}"} for i in range(15)]),
        "/git/trees/HEAD": json.dumps(TREE),
        "/contents/package.json": json.dumps(
            {"content": _b64('{"dependencies": {"openai": "^4", "left-pad": "1"}}')}
        ),
        "/contents/.github/workflows/ci.yml": json.dumps(
            {"content": _b64("uses: github/copilot-action@v1\n")}
        ),
        "/pulls": json.dumps(
            [
                {"user": {"login": "alice"}, "updated_at": _iso(2)},
                {"user": {"login": "alice"}, "updated_at": _iso(3)},
                {"user": {"login": "dependabot[bot]"}, "updated_at": _iso(1)},
                {"user": {"login": "old"}, "updated_at": _iso(200)},
            ]
        ),
    }
    table.update(overrides or {})

    def run(argv, **kwargs):
        assert argv[0] == "gh" and kwargs.get("shell") in (None, False)
        url = argv[2]
        for frag, out in table.items():
            if frag in url and not (frag == "repos/acme/r" and url != "repos/acme/r"):
                if isinstance(out, Exception):
                    raise out
                return _completed(out)
        raise AssertionError(f"unrouted gh call: {url}")

    return run


@pytest.mark.req("REQ-YG-670")
def test_extract_bundle_is_typed_and_bounded():
    with patch(f"{MOD}.subprocess.run", side_effect=_gh_router()):
        blob = gh.gh_repo_ai_extract({"item": "acme/r", "window_days": "90"})
    assert len(blob) <= gh.MAX_BUNDLE_CHARS
    b = json.loads(blob)
    assert b["id"] == "acme/r"
    assert b["visibility"] == "private"
    assert b["tree_truncated"] is False
    assert set(b["instruction_files"]) == {
        ".github/copilot-instructions.md",
        "CLAUDE.md",
    }
    assert [h["path"] for h in b["manifest_hits"]] == ["package.json"]
    assert "openai" in b["manifest_hits"][0]["line"]
    assert b["workflow_hits"][0]["path"] == ".github/workflows/ci.yml"
    assert len(b["contributors"]) == gh.MAX_CONTRIBUTORS
    authors = {a["login"]: a for a in b["pr_authors"]}
    assert authors["alice"]["n"] == 2 and authors["alice"]["bot"] is False
    assert authors["dependabot[bot]"]["bot"] is True
    assert "old" not in authors, "out-of-window PR author must be excluded"
    assert b["absent"] == []


@pytest.mark.req("REQ-YG-670")
def test_extract_404_on_optional_call_yields_absent_marker():
    err = subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 404")
    with patch(f"{MOD}.subprocess.run", side_effect=_gh_router({"/readme": err})):
        b = json.loads(gh.gh_repo_ai_extract({"item": "acme/r", "window_days": "90"}))
    assert b["readme_head"] == ""
    assert "readme" in b["absent"]


@pytest.mark.req("REQ-YG-670")
def test_extract_metadata_failure_raises():
    err = subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 401")
    with (
        patch(f"{MOD}.subprocess.run", side_effect=_gh_router({"repos/acme/r": err})),
        pytest.raises(subprocess.CalledProcessError),
    ):
        gh.gh_repo_ai_extract({"item": "acme/r", "window_days": "90"})


@pytest.mark.req("REQ-YG-670")
def test_extract_tree_truncation_and_caps():
    big_tree = {
        "truncated": True,
        "tree": [{"path": f"pkg{i}/package.json"} for i in range(20)]
        + [{"path": f".github/workflows/w{i}.yml"} for i in range(9)],
    }
    over = {
        "/git/trees/HEAD": json.dumps(big_tree),
        "/contents/": json.dumps({"content": _b64("openai\n")}),
    }
    with patch(f"{MOD}.subprocess.run", side_effect=_gh_router(over)) as run:
        b = json.loads(gh.gh_repo_ai_extract({"item": "acme/r", "window_days": "90"}))
    assert b["tree_truncated"] is True
    fetched = [c[0][0][2] for c in run.call_args_list if "/contents/" in c[0][0][2]]
    assert len([f for f in fetched if "package.json" in f]) == gh.MAX_MANIFESTS
    assert len([f for f in fetched if "workflows" in f]) == gh.MAX_WORKFLOWS


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("item", ["", "norepo", "a/b/c"])
def test_extract_malformed_ref_raises(item):
    with pytest.raises(ValueError):
        gh.gh_repo_ai_extract({"item": item, "window_days": "90"})


@pytest.mark.req("REQ-YG-670")
def test_extract_malformed_json_raises():
    with (
        patch(
            f"{MOD}.subprocess.run",
            side_effect=_gh_router({"repos/acme/r": "not json"}),
        ),
        pytest.raises(ValueError),
    ):
        gh.gh_repo_ai_extract({"item": "acme/r", "window_days": "90"})


# --- AC-07: org code search ------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_search_budgets_calls_and_flags_caps(monkeypatch):
    clock = {"t": 0.0}
    sleeps: list[float] = []
    monkeypatch.setattr(gh, "_monotonic", lambda: clock["t"])

    def fake_sleep(s):
        sleeps.append(s)
        clock["t"] += s

    monkeypatch.setattr(gh, "_sleep", fake_sleep)
    capped = json.dumps(
        [
            {"repository": {"nameWithOwner": f"acme/r{i}", "isPrivate": True}}
            for i in range(gh.MAX_SEARCH_RESULTS)
        ]
    )
    small = json.dumps(
        [{"repository": {"nameWithOwner": "acme/x", "isPrivate": True}}] * 3
        + [{"repository": {"nameWithOwner": "acme/pub", "isPrivate": False}}]
    )

    def run(argv, **kwargs):
        assert argv[:3] == ["gh", "search", "code"]
        assert argv[argv.index("--limit") + 1] == str(gh.MAX_SEARCH_RESULTS)
        return _completed(capped if argv[3] == "openai" else small)

    with patch(f"{MOD}.subprocess.run", side_effect=run) as spy:
        hits = gh.gh_org_code_search({"org": "acme", "visibility": "private,internal"})[
            "search_hits"
        ]
    assert spy.call_count == len(gh.SEARCH_TERMS) <= gh.MAX_SEARCH_TERMS
    assert (
        hits["openai"]["capped"] is True
        and len(hits["openai"]["repos"]) == gh.MAX_SEARCH_RESULTS
    )
    assert hits["anthropic"] == {
        "repos": ["acme/x"],
        "capped": False,
    }, "public hit excluded"
    assert "tekoäly" in hits
    # ≤10 calls per minute → at least 6 s spacing enforced by sleeping
    assert len(sleeps) == len(gh.SEARCH_TERMS) - 1
    assert all(s >= gh.SEARCH_MIN_INTERVAL_S - 1e-9 for s in sleeps)


@pytest.mark.req("REQ-YG-670")
def test_search_requires_org():
    with pytest.raises(ValueError, match="org"):
        gh.gh_org_code_search({"visibility": "public"})


@pytest.mark.req("REQ-YG-670")
def test_search_public_policy_drops_private_hits(monkeypatch):
    monkeypatch.setattr(gh, "_sleep", lambda s: None)
    body = json.dumps(
        [
            {"repository": {"nameWithOwner": "acme/secret", "isPrivate": True}},
            {"repository": {"nameWithOwner": "acme/open", "isPrivate": False}},
        ]
    )
    with patch(f"{MOD}.subprocess.run", return_value=_completed(body)):
        hits = gh.gh_org_code_search({"org": "acme", "visibility": "public"})[
            "search_hits"
        ]
    assert all(h["repos"] == ["acme/open"] for h in hits.values())
    assert "acme/secret" not in json.dumps(hits)


@pytest.mark.req("REQ-YG-670")
def test_discover_accepts_org_and_window_days_when_source_template_unresolved():
    listing = json.dumps([_repo("a")])
    with patch(f"{MOD}.subprocess.run", return_value=_completed(listing)):
        items = gh.gh_org_active_discover(
            {
                "source": None,
                "org": "acme",
                "window_days": "90",
                "visibility": "private",
            }
        )
    assert items == ["acme/a"]
