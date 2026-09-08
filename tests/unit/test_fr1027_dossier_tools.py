"""FR-1027 witnesses — org AI dossier local tools (REQ-YG-670).

Covers preflight (AC-03, AC-16, AC-18), reducer reconciliation, evidence
boundary and canaries (AC-10, AC-11), ceilings (AC-12), persons (AC-15),
summary boundary (AC-16), renderers and denominators (AC-13, AC-14), atomic
artifact boundary (AC-18).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.demos.org_ai_dossier import models as m
from examples.demos.org_ai_dossier import preflight as pf
from examples.demos.org_ai_dossier import render as render_mod
from examples.demos.org_ai_dossier import tools as t

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
AZURE = {
    "AZURE_AI_ENDPOINT": "https://x",
    "AZURE_AI_API_KEY": "k",
    "AZURE_MODEL": "dep",
}
JIRA = {
    "JIRA_URL": "https://x.atlassian.net",
    "JIRA_USERNAME": "u",
    "JIRA_API_TOKEN": "t",
}


@pytest.fixture
def env(monkeypatch):
    for k, v in {**AZURE, **JIRA}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(pf, "_gh_auth_ok", lambda: None)
    monkeypatch.setattr(pf, "_git_ignored", lambda p: True)


def _live_state(tmp_path: Path, **over) -> dict:
    state = {
        "org": "acme",
        "visibility": "private,internal",
        "window_days": "90",
        "top_persons": "30",
        "persons_llm": "false",
        "persons_llm_ack": "",
        "out_dir": str(REPO_ROOT / "research" / "org-ai-dossier" / "test-run"),
    }
    state.update(over)
    return state


# --- preflight (AC-03, AC-16, AC-18) ------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_preflight_ok_live(env, tmp_path):
    assert t.preflight(_live_state(tmp_path)) == {"preflight_ok": True}


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("missing", sorted({**AZURE, **JIRA}))
def test_preflight_missing_env_fails_before_any_call(
    env, monkeypatch, tmp_path, missing
):
    monkeypatch.delenv(missing)
    with pytest.raises((ValueError, OSError), match=missing):
        t.preflight(_live_state(tmp_path))


@pytest.mark.req("REQ-YG-670")
def test_preflight_gh_auth_failure(env, monkeypatch, tmp_path):
    def boom():
        raise RuntimeError("gh auth status: not logged in")

    monkeypatch.setattr(pf, "_gh_auth_ok", boom)
    with pytest.raises(RuntimeError, match="gh auth"):
        t.preflight(_live_state(tmp_path))


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize(
    "over,msg",
    [
        ({"visibility": ""}, "visibility"),
        ({"visibility": "secret"}, "visibility"),
        ({"window_days": "0"}, "window_days"),
        ({"top_persons": str(m.MAX_TOP_PERSONS + 1)}, "top_persons"),
        ({"persons_llm": ""}, "persons_llm"),
        ({"persons_llm": "yes"}, "persons_llm"),
        ({"persons_llm": "true", "persons_llm_ack": ""}, "persons_llm_ack"),
    ],
)
def test_preflight_input_policy(env, tmp_path, over, msg):
    with pytest.raises(ValueError, match=msg):
        t.preflight(_live_state(tmp_path, **over))


@pytest.mark.req("REQ-YG-670")
def test_preflight_persons_llm_true_with_ack_passes(env, tmp_path):
    assert t.preflight(
        _live_state(tmp_path, persons_llm="true", persons_llm_ack="I am the controller")
    )


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize(
    "out_dir",
    [
        "feature-requests/leak",
        "research/org-ai-dossier/../../docs/leak",
        "tmp/org-ai-dossier-smoke/x",
        "research/other/x",
    ],
)
def test_preflight_out_dir_must_be_under_research_root(env, tmp_path, out_dir):
    with pytest.raises(ValueError, match="out_dir"):
        t.preflight(_live_state(tmp_path, out_dir=str(REPO_ROOT / out_dir)))


@pytest.mark.req("REQ-YG-670")
def test_preflight_out_dir_symlink_escape_rejected(env, tmp_path):
    root = REPO_ROOT / "research" / "org-ai-dossier"
    root.mkdir(parents=True, exist_ok=True)
    link = root / "escape-link-test"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(tmp_path)
    try:
        with pytest.raises(ValueError, match="out_dir"):
            t.preflight(_live_state(tmp_path, out_dir=str(link / "run")))
    finally:
        link.unlink()


@pytest.mark.req("REQ-YG-670")
def test_preflight_out_dir_must_not_exist_and_root_must_be_ignored(
    env, monkeypatch, tmp_path
):
    existing = REPO_ROOT / "research" / "org-ai-dossier" / "existing-test-dir"
    existing.mkdir(parents=True, exist_ok=True)
    try:
        with pytest.raises(ValueError, match="exists"):
            t.preflight(_live_state(tmp_path, out_dir=str(existing)))
    finally:
        existing.rmdir()
    monkeypatch.setattr(pf, "_git_ignored", lambda p: False)
    with pytest.raises(ValueError, match="gitignore"):
        t.preflight(_live_state(tmp_path))


@pytest.mark.req("REQ-YG-670")
def test_preflight_smoke_skips_jira_env_but_forces_public_and_tmp_root(
    env, monkeypatch, tmp_path
):
    for k in JIRA:
        monkeypatch.delenv(k)
    smoke = _live_state(
        tmp_path,
        visibility="public",
        out_dir=str(REPO_ROOT / "tmp" / "org-ai-dossier-smoke" / "run"),
    )
    assert t.preflight_smoke(smoke) == {"preflight_ok": True}
    with pytest.raises(ValueError, match="visibility"):
        t.preflight_smoke({**smoke, "visibility": "private"})
    with pytest.raises(ValueError, match="persons_llm"):
        t.preflight_smoke({**smoke, "persons_llm": "true", "persons_llm_ack": "x"})
    with pytest.raises(ValueError, match="out_dir"):
        t.preflight_smoke(
            {**smoke, "out_dir": str(REPO_ROOT / "research" / "org-ai-dossier" / "x")}
        )


# --- fixtures for reduce -----------------------------------------------------------------


def _gh_bundle(rid: str, **over) -> dict:
    b = {
        "id": rid,
        "description": "d",
        "pushed_at": "2026-09-01T00:00:00Z",
        "archived": False,
        "visibility": "private",
        "language": "TypeScript",
        "readme_head": "hello",
        "contributors": ["alice", "bob"],
        "tree_truncated": False,
        "instruction_files": [".github/copilot-instructions.md"],
        "manifest_hits": [{"path": "package.json", "line": '"openai": "^4"'}],
        "workflow_hits": [],
        "pr_authors": [
            {"login": "alice", "bot": False, "n": 3},
            {"login": "dependabot[bot]", "bot": True, "n": 9},
        ],
        "absent": [],
    }
    b.update(over)
    return b


def _jira_bundle(key: str, **over) -> dict:
    b = {
        "key": key,
        "name": key,
        "project_type": "software",
        "lead": None,
        "updated_in_window": 4,
        "created_in_window": 1,
        "ai_term_count": 2,
        "issues": [
            {
                "key": f"{key}-1",
                "summary": "Copilot rollout",
                "issuetype": "Task",
                "status": "Done",
                "assignee_id": "acc1",
                "reporter_id": "acc2",
                "description_head": "",
            }
        ],
        "assignees": [{"account_id": "acc1", "display_name": "Alice J", "n": 1}],
        "reporters": [{"account_id": "acc2", "display_name": "Rob", "n": 1}],
    }
    b.update(over)
    return b


def _entries(bundles: list[dict], start: int = 0) -> list[dict]:
    return [
        {"value": json.dumps(b), "_map_index": start + i} for i, b in enumerate(bundles)
    ]


def _repo_finding(i: int, **over) -> dict:
    f = {
        "_map_index": i,
        "purpose": "demo",
        "ai_usage": "both",
        "ai_tools": [
            {"name": "openai", "kind": "provider", "evidence_path": "package.json"},
            {
                "name": "copilot",
                "kind": "coding_agent",
                "evidence_path": ".github/copilot-instructions.md",
            },
        ],
        "rationale": "r",
    }
    f.update(over)
    return f


def _jira_finding(i: int, **over) -> dict:
    f = {
        "_map_index": i,
        "purpose": "demo project",
        "ai_usage": "dev_tooling",
        "ai_tools": [
            {"name": "copilot", "kind": "coding_agent", "evidence_issue": "P1-1"}
        ],
        "rationale": "r",
    }
    f.update(over)
    return f


def _canary_findings(kind: str, start: int) -> list[dict]:
    """Correct answers for the committed canary families, indexed after the real items."""
    return t.canary_expected_findings(kind, start)


def _reduce_state(**over) -> dict:
    repo_ids = ["acme/a", "acme/b"]
    jira_keys = ["P1"]
    repo_bundles = _entries(
        [
            _gh_bundle("acme/a"),
            _gh_bundle("acme/b", manifest_hits=[], instruction_files=[]),
        ]
    )
    repo_bundles += t.inject_repo_canaries({"repo_bundles": repo_bundles})[
        "repo_bundles"
    ]
    jira_bundles = _entries([_jira_bundle("P1")])
    jira_bundles += t.inject_jira_canaries({"jira_bundles": jira_bundles})[
        "jira_bundles"
    ]
    state = {
        "org": "acme",
        "window_days": "90",
        "top_persons": "30",
        "repo_items": repo_ids,
        "repo_bundles": repo_bundles,
        "search_hits": {
            "openai": {"repos": ["acme/a", "acme/zzz"], "capped": False},
            "anthropic": {"repos": [], "capped": True},
        },
        "repo_findings": [
            _repo_finding(0),
            _repo_finding(1, ai_usage="none", ai_tools=[]),
        ]
        + _canary_findings("repo", 2),
        "coverage_gh": {
            "api_total": 10,
            "listed": 8,
            "archived": 1,
            "out_of_window": 4,
            "visibility_rejected": 1,
            "active": 2,
        },
        "jira_items": jira_keys,
        "jira_bundles": jira_bundles,
        "jira_findings": [_jira_finding(0)] + _canary_findings("jira", 1),
        "coverage_jira": {
            "visible": 3,
            "active": 1,
            "dormant": 2,
            "page_cap_hit": False,
            "active_keys": ["P1"],
            "dormant_keys": ["P2", "P3"],
        },
    }
    state.update(over)
    return state


# --- reduce: reconciliation (AC-10) ------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_reduce_happy_path_rows_persons_tools_coverage():
    out = t.reduce(_reduce_state())["reduced"]
    repos = {r["id"]: r for r in out["repos"]}
    assert set(repos) == {"acme/a", "acme/b"} and all(
        r["status"] == "classified" for r in repos.values()
    )
    assert repos["acme/a"]["search_keywords"] == ["openai"]
    assert (
        out["jira"][0]["key"] == "P1"
        and out["jira"][0]["ai_tools"][0]["evidence_issue"] == "P1-1"
    )
    tools = {row["name"]: row for row in out["ai_tools"]}
    assert tools["openai"]["n_repos"] == 1 and tools["copilot"]["n_projects"] == 1
    cov = out["coverage"]
    assert cov["github"]["classified"] == 2 and cov["github"]["unclear"] == 0
    assert any(
        "openai" in c and "1 hit(s) outside" in c
        for c in cov["github"]["search_caveats"]
    )
    assert "acme/zzz" not in json.dumps(
        out
    ), "out-of-set repos are counted, never named"
    assert any(
        "anthropic" in c and "capped" in c for c in cov["github"]["search_caveats"]
    )
    assert cov["jira"] == {
        "visible": 3,
        "active": 1,
        "dormant": 2,
        "extracted": 1,
        "classified": 1,
        "unclear": 0,
        "map_failed": 0,
        "page_cap_hit": False,
    }
    assert out["canaries"] == {"repo": "pass", "jira": "pass"}
    assert out["llm_calls_actual"] == 3 + m.N_CANARIES


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize(
    "mutate,msg",
    [
        (lambda s: s["repo_items"].append("acme/missing"), "acme/missing"),
        (
            lambda s: s["repo_bundles"].append(
                _entries([_gh_bundle("acme/extra")], 99)[0]
            ),
            "acme/extra",
        ),
        (
            lambda s: s["repo_bundles"].append(
                dict(s["repo_bundles"][0], _map_index=98)
            ),
            "duplicate",
        ),
        (lambda s: s["repo_bundles"][0].__setitem__("value", "{not json"), "bundle"),
        (
            lambda s: s["repo_bundles"][0].__setitem__(
                "value", json.dumps({"id": "acme/a"})
            ),
            "bundle",
        ),
        (lambda s: s["jira_items"].append("P9"), "P9"),
    ],
)
def test_reduce_structural_failures_raise(mutate, msg):
    state = _reduce_state()
    mutate(state)
    with pytest.raises(ValueError, match=msg):
        t.reduce(state)


@pytest.mark.req("REQ-YG-670")
def test_reduce_model_enum_drift_is_contained_not_fatal():
    """Live-run witness 2026-09-07: a Jira finding carried kind='feature'."""
    state = _reduce_state()
    # bad tool entry only → entry dropped, finding kept
    state["jira_findings"][0]["ai_tools"].append(
        {"name": "triage bot", "kind": "feature", "evidence_issue": "P1-1"}
    )
    out = t.reduce(state)["reduced"]
    assert [x["name"] for x in out["jira"][0]["ai_tools"]] == ["copilot"]
    assert out["jira"][0]["status"] == "classified"
    # finding-level drift → typed map_failed row, counted, no abort
    state = _reduce_state()
    state["repo_findings"][0]["ai_usage"] = "maybe"
    out = t.reduce(state)["reduced"]
    row = next(r for r in out["repos"] if r["id"] == "acme/a")
    assert (
        row["status"] == "map_failed" and out["coverage"]["github"]["map_failed"] == 1
    )


@pytest.mark.req("REQ-YG-670")
def test_reduce_error_finding_from_on_error_skip_is_contained():
    state = _reduce_state()
    state["repo_findings"][1] = {
        "_map_index": 1,
        "_error": "[PipelineError(type=llm_error, message='429 rate limit')]",
    }
    out = t.reduce(state)["reduced"]
    row = next(r for r in out["repos"] if r["id"] == "acme/b")
    assert row["status"] == "map_failed" and row["ai_usage"] == "unclear"
    assert out["coverage"]["github"]["map_failed"] == 1


@pytest.mark.req("REQ-YG-670")
def test_reduce_missing_finding_becomes_typed_map_failed_row_within_cap():
    state = _reduce_state()
    state["repo_findings"] = [f for f in state["repo_findings"] if f["_map_index"] != 1]
    out = t.reduce(state)["reduced"]
    row = next(r for r in out["repos"] if r["id"] == "acme/b")
    assert (
        row["status"] == "map_failed"
        and row["ai_usage"] == "unclear"
        and row["ai_tools"] == []
    )
    assert (
        out["coverage"]["github"]["map_failed"] == 1
        and out["coverage"]["github"]["classified"] == 1
    )


@pytest.mark.req("REQ-YG-670")
def test_reduce_map_failed_over_cap_raises():
    ids = [f"acme/r{i}" for i in range(m.MAX_MAP_FAILED + 1)]
    bundles = _entries([_gh_bundle(i) for i in ids])
    bundles += t.inject_repo_canaries({"repo_bundles": bundles})["repo_bundles"]
    state = _reduce_state(
        repo_items=ids,
        repo_bundles=bundles,
        repo_findings=_canary_findings("repo", len(ids)),
        coverage_gh={
            "api_total": None,
            "listed": 6,
            "archived": 0,
            "out_of_window": 0,
            "visibility_rejected": 0,
            "active": len(ids),
        },
    )
    with pytest.raises(ValueError, match="map_failed"):
        t.reduce(state)


# --- evidence boundary + canaries (AC-11) ---------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_reduce_drops_unsupported_tools_and_demotes_to_unclear():
    state = _reduce_state()
    state["repo_findings"][1] = _repo_finding(
        1,
        ai_usage="product",
        ai_tools=[
            {"name": "openai", "kind": "provider", "evidence_path": "src/llm.ts"}
        ],
    )
    out = t.reduce(state)["reduced"]
    row = next(r for r in out["repos"] if r["id"] == "acme/b")
    assert row["ai_tools"] == [] and row["ai_usage"] == "unclear"
    assert out["coverage"]["github"]["unclear"] == 1


@pytest.mark.req("REQ-YG-670")
def test_reduce_keeps_supported_tools_and_drops_only_the_unsupported():
    state = _reduce_state()
    state["repo_findings"][0]["ai_tools"].append(
        {"name": "ghost", "kind": "model", "evidence_path": "nowhere"}
    )
    out = t.reduce(state)["reduced"]
    row = next(r for r in out["repos"] if r["id"] == "acme/a")
    assert [x["name"] for x in row["ai_tools"]] == ["openai", "copilot"] and row[
        "ai_usage"
    ] == "both"


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize("kind", ["repo", "jira"])
def test_reduce_canary_miss_aborts(kind):
    state = _reduce_state()
    key = "repo_findings" if kind == "repo" else "jira_findings"
    n_real = 2 if kind == "repo" else 1
    for f in state[key]:
        if f["_map_index"] >= n_real:
            f["ai_usage"] = "none" if f["ai_usage"] != "none" else "product"
            break
    with pytest.raises(ValueError, match="canary"):
        t.reduce(state)


@pytest.mark.req("REQ-YG-670")
def test_canary_ids_are_stripped_from_ledgers_and_prefixed():
    out = t.reduce(_reduce_state())["reduced"]
    assert not any(r["id"].startswith(m.CANARY_PREFIX) for r in out["repos"])
    assert not any(r["key"].startswith("CANARY") for r in out["jira"])
    canaries = t.inject_repo_canaries({"repo_bundles": []})["repo_bundles"]
    assert len(canaries) == 3 and all(
        json.loads(c["value"])["id"].startswith(m.CANARY_PREFIX) for c in canaries
    )
    assert len(t.inject_jira_canaries({"jira_bundles": []})["jira_bundles"]) == 2


# --- persons (AC-15) ----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_persons_source_qualified_two_rankings_no_join():
    out = t.reduce(_reduce_state())["reduced"]
    gh = out["persons_github"]
    # 3 PRs on each of two repos + contributor credit (1) on each = 8 (frozen formula)
    assert (
        gh[0]["id"] == "github:alice"
        and gh[0]["score"] == 3 + 3 + 1 + 1
        and gh[0]["rank"] == 1
    )
    assert gh[0]["repos"] == ["acme/a", "acme/b"] and gh[0]["projects"] == []
    assert all(not p["id"].endswith("[bot]") for p in gh), "bots excluded"
    ji = out["persons_jira"]
    assert (
        ji[0]["id"] == "jira:acc1"
        and ji[0]["label"] == "Alice J"
        and ji[0]["projects"] == ["P1"]
    )
    assert "same_person" not in gh[0] and "same_person" not in m.PersonRow.model_fields
    assert "persons" not in out, "no combined ranking key"


@pytest.mark.req("REQ-YG-670")
def test_persons_cut_at_top_persons():
    out = t.reduce(_reduce_state(top_persons="1"))["reduced"]
    assert len(out["persons_github"]) == 1 and len(out["persons_jira"]) == 1


# --- prepare_person_input / summary boundary (AC-16) -----------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_prepare_person_input_routes_on_policy():
    reduced = t.reduce(_reduce_state())["reduced"]
    off = t.prepare_person_input({"reduced": reduced, "persons_llm": "false"})
    assert off["persons_llm_active"] is False and off["person_input"] == []
    on = t.prepare_person_input({"reduced": reduced, "persons_llm": "true"})
    assert on["persons_llm_active"] is True
    first = on["person_input"][0]
    assert first["id"] == "github:alice" and {"id", "purpose"} <= set(
        first["footprint"][0]
    )
    assert all(x["source"] in ("github", "jira") for x in on["person_input"])


@pytest.mark.req("REQ-YG-670")
@pytest.mark.parametrize(
    "summary,ok",
    [
        ("Contributes to acme/a and acme/b, both demo services.", True),
        ("Contributes to acme/a and acme/secret.", False),
        ("Works alongside github:bob on acme/a.", False),
        ("A senior engineer who is clearly overworked on acme/a.", False),
        ("Probably intends to migrate acme/a soon.", False),
    ],
)
def test_summary_boundary(summary, ok):
    reduced = t.reduce(_reduce_state())["reduced"]
    person_input = t.prepare_person_input({"reduced": reduced, "persons_llm": "true"})[
        "person_input"
    ]
    summaries = [{"_map_index": 0, "summary": summary}] + [
        {
            "_map_index": i,
            "summary": "Contributes to "
            + ", ".join(u["id"] for u in p["footprint"])
            + ".",
        }
        for i, p in enumerate(person_input)
        if i > 0
    ]
    state = {
        "reduced": reduced,
        "person_input": person_input,
        "person_summaries": summaries,
        "persons_llm_active": True,
    }
    if ok:
        out = t.prepare_findings_input(state)
        assert out["reduced"]["persons_github"][0]["summary"] == summary
    else:
        with pytest.raises(ValueError, match="summary"):
            t.prepare_findings_input(state)


@pytest.mark.req("REQ-YG-670")
def test_findings_input_has_citable_ids_and_no_summaries_when_off():
    reduced = t.reduce(_reduce_state())["reduced"]
    out = t.prepare_findings_input(
        {
            "reduced": reduced,
            "person_input": [],
            "person_summaries": [],
            "persons_llm_active": False,
        }
    )
    ids = {r["item_ref"] for r in out["findings_input"]["rows"]}
    assert {"repo:acme/a", "jira:P1", "tool:openai", "person:github:alice"} <= ids
    assert all(p["summary"] is None for p in out["reduced"]["persons_github"])


# --- render (AC-13, AC-14, AC-18) ------------------------------------------------------------


def _claims(ids: list[str], n: int) -> dict:
    return {
        "claims": [
            {
                "claim_id": f"c{i}",
                "text": f"Finding {i} about {ids[i % len(ids)]}.",
                "citations": [f"row:{ids[i % len(ids)]}"],
                "confidence": 0.9,
            }
            for i in range(n)
        ]
    }


def _render_state(tmp_path: Path, monkeypatch, **over) -> dict:
    monkeypatch.setattr(render_mod, "_head_sha", lambda: "a" * 40)
    monkeypatch.setenv("AZURE_MODEL", "dep")
    reduced = t.reduce(_reduce_state())["reduced"]
    prep = t.prepare_findings_input(
        {
            "reduced": reduced,
            "person_input": [],
            "person_summaries": [],
            "persons_llm_active": False,
        }
    )
    ids = [r["item_ref"] for r in prep["findings_input"]["rows"]]
    state = {
        "org": "acme",
        "visibility": "private,internal",
        "window_days": "90",
        "top_persons": "30",
        "persons_llm": "false",
        "persons_llm_ack": "",
        "out_dir": str(tmp_path / "out"),
        "coverage_gh": _reduce_state()["coverage_gh"],
        "reduced": prep["reduced"],
        "findings_input": prep["findings_input"],
        "findings_claims": _claims(ids, 4),
        "onepager_claims": _claims(ids, m.ONEPAGER_FINDINGS),
        "run_started": "2026-09-07T10:00:00+00:00",
    }
    state.update(over)
    return state


@pytest.mark.req("REQ-YG-670")
def test_render_writes_all_artifacts_atomically_with_denominators(
    tmp_path, monkeypatch
):
    state = _render_state(tmp_path, monkeypatch)
    out = t.render_artifacts(state)["artifacts"]
    out_dir = Path(state["out_dir"])
    names = {
        "onepager.md",
        "dossier.md",
        "repos.md",
        "jira.md",
        "run.json",
        "ledgers/repos.jsonl",
        "ledgers/jira.jsonl",
        "ledgers/persons.jsonl",
        "ledgers/ai_tools.csv",
    }
    assert names <= {str(Path(p).relative_to(out_dir)) for p in out.values()}
    assert not list(tmp_path.glob("*.tmp*")), "temp dir must be renamed away"
    onepager = (out_dir / "onepager.md").read_text(encoding="utf-8")
    assert len(onepager.split()) <= m.MAX_ONEPAGER_WORDS
    assert onepager.count("Finding ") == m.ONEPAGER_FINDINGS
    for doc in ("onepager.md", "dossier.md", "repos.md", "jira.md"):
        text = (out_dir / doc).read_text(encoding="utf-8")
        assert "of active=2" in text, doc
        assert "unclear" in text and "map_failed" in text, doc
    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    m.RunRecord.model_validate(run)
    assert (
        run["persons_llm"] is False
        and run["head_sha"] == "a" * 40
        and len(run["graph_sha256"]) == 64
    )
    assert run["canaries"] == {
        "repo": "pass",
        "jira": "pass",
    } and "token" not in json.dumps(run)
    assert set(run["artifact_sha256"]) >= {"onepager.md", "dossier.md"}
    persons = [
        json.loads(line)
        for line in (out_dir / "ledgers/persons.jsonl").read_text().splitlines()
    ]
    assert {p["source"] for p in persons} == {"github", "jira"}


@pytest.mark.req("REQ-YG-670")
def test_render_api_total_unavailable_prints_unavailable_not_percentage(
    tmp_path, monkeypatch
):
    state = _render_state(tmp_path, monkeypatch)
    state["coverage_gh"] = dict(state["coverage_gh"], api_total=None)
    state["reduced"]["coverage"]["github"]["api_total"] = None
    t.render_artifacts(state)
    text = (Path(state["out_dir"]) / "onepager.md").read_text(encoding="utf-8")
    assert "org API total: unavailable" in text
    assert "of api_total" not in text


@pytest.mark.req("REQ-YG-670")
def test_render_rejects_bad_citations_and_leaves_no_artifact(tmp_path, monkeypatch):
    state = _render_state(tmp_path, monkeypatch)
    state["onepager_claims"]["claims"][0]["citations"] = ["row:repo:acme/nope"]
    with pytest.raises(ValueError, match="citation"):
        t.render_artifacts(state)
    assert not Path(state["out_dir"]).exists()
    state = _render_state(tmp_path, monkeypatch)
    state["onepager_claims"] = _claims(
        [r["item_ref"] for r in state["findings_input"]["rows"]], 2
    )
    with pytest.raises(ValueError, match="three"):
        t.render_artifacts(state)
    assert not Path(state["out_dir"]).exists()


@pytest.mark.req("REQ-YG-670")
def test_render_word_bound_enforced(tmp_path, monkeypatch):
    state = _render_state(tmp_path, monkeypatch)
    for c in state["onepager_claims"]["claims"]:
        c["text"] = "word " * 400
    with pytest.raises(ValueError, match="800"):
        t.render_artifacts(state)
    assert not Path(state["out_dir"]).exists()


# --- ceilings (AC-12) --------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-670")
def test_llm_call_estimate_and_ceiling():
    assert t.estimate_llm_calls(400, 150, 60) == m.MAX_LLM_CALLS
    with pytest.raises(ValueError, match="MAX_LLM_CALLS"):
        t.estimate_llm_calls(401, 150, 60)


@pytest.mark.req("REQ-YG-670")
def test_preflight_ceiling_mirrors_match_models():
    for name in (
        "MAX_REPOS",
        "MAX_PROJECTS",
        "MAX_TOP_PERSONS",
        "MAX_SYNTHESIS_CALLS",
        "N_CANARIES",
        "MAX_LLM_CALLS",
    ):
        assert getattr(pf, name) == getattr(m, name), name
