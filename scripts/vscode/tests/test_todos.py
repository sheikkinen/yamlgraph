#!/usr/bin/env python3
"""FR-741: orphan intention triage — witnesses.

Unmarked per FR-737 F5 precedent. Run: pytest scripts/vscode/tests/ -q

Pins (judgement 2026-07-16 + addendum A1):
- AC-01 artifact cross-check: FR/NC-id orphans resolve against the
  filesystem → DELIVERED ELSEWHERE / NO ARTIFACT; no id → None.
- AC-03 content-keyed drops: (session_id, sha1(title)[:8]) — never
  positional (F3); dropped orphans excluded from listings.
- AC-02/A1 briefing: DIED OPEN ≤30d capped at 10; LIVE intent rows
  carry the `claims:` prefix (render_claims_as_claims); a live claim
  naming a delivered artifact is flagged STALE CLAIM (git overrules).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import todos  # noqa: E402  # CONF-392 idiom


def make_repo(tmp_path: Path, refs: list[str]) -> Path:
    fr = tmp_path / "feature-requests"
    fr.mkdir(parents=True, exist_ok=True)
    for ref in refs:
        (fr / f"{ref}-something.md").write_text("# x\n")
    return tmp_path


# ---------------------------------------------------------------- AC-01


def test_cross_check_delivered_elsewhere(tmp_path):
    repo = make_repo(tmp_path, ["NC-365"])
    assert todos.cross_check("Create NC-365 feature request", [repo]) == (
        "DELIVERED ELSEWHERE"
    )


def test_cross_check_no_artifact(tmp_path):
    repo = make_repo(tmp_path, ["NC-365"])
    assert todos.cross_check("Create NC-999 feature request", [repo]) == "NO ARTIFACT"


def test_cross_check_no_id_is_none(tmp_path):
    repo = make_repo(tmp_path, ["NC-365"])
    assert todos.cross_check("Write diary reflection", [repo]) is None


# ---------------------------------------------------------------- AC-03


def test_drop_key_is_content_based():
    k1 = todos.drop_key("sess-aaaa", "Fix the thing")
    k2 = todos.drop_key("sess-aaaa", "Fix the thing")
    k3 = todos.drop_key("sess-aaaa", "Fix another thing")
    assert k1 == k2 and k1 != k3
    assert len(k1.split(":")[1]) == 8  # sha8, printable/droppable


def test_drop_persists_and_excludes(tmp_path):
    sidecar = tmp_path / "orphan-dispositions.jsonl"
    todos.record_drop(sidecar, "sess-aaaa", "Fix the thing", reason="obsolete")
    dropped = todos.load_dispositions(sidecar)
    assert todos.drop_key("sess-aaaa", "Fix the thing") in dropped
    # second identical drop is a no-op (dedupe)
    todos.record_drop(sidecar, "sess-aaaa", "Fix the thing", reason="obsolete")
    assert len(sidecar.read_text().splitlines()) == 1


# ------------------------------------------------------------ AC-02 / A1


def _session(status_items, mtime_age_days, now=1_000_000.0):
    return {
        "todos": [{"title": t, "status": s} for t, s in status_items],
        "title": "T",
        "mtime": now - mtime_age_days * 86400,
    }


def test_briefing_age_cap_and_row_cap(tmp_path):
    now = 1_000_000.0
    sessions = {
        "old-dead": _session([("Ancient task", "not-started")], 93, now),
        "new-dead": _session([("Recent task", "in-progress")], 3, now),
    }
    lines = todos.briefing_lines(
        sessions, live=set(), roots=[], dispositions=set(), now=now
    )
    text = "\n".join(lines)
    assert "Recent task" in text
    assert "Ancient task" not in text  # >30d excluded (post-backlog-zero)


def test_briefing_live_claims_prefix_and_stale_flag(tmp_path):
    repo = make_repo(tmp_path, ["NC-365"])
    now = 1_000_000.0
    sessions = {
        "live-sess": _session(
            [
                ("Create NC-365 feature request", "not-started"),
                ("Investigate flux capacitor", "in-progress"),
            ],
            0.01,
            now,
        ),
    }
    lines = todos.briefing_lines(
        sessions, live={"live-sess"}, roots=[repo], dispositions=set(), now=now
    )
    text = "\n".join(lines)
    assert "claims:" in text  # testimony register, never fact register
    assert "STALE CLAIM" in text  # git overrules the todo
    assert "Investigate flux capacitor" in text


def test_briefing_excludes_dropped(tmp_path):
    now = 1_000_000.0
    sessions = {"dead": _session([("Fix the thing", "not-started")], 2, now)}
    dropped = {todos.drop_key("dead", "Fix the thing")}
    lines = todos.briefing_lines(
        sessions, live=set(), roots=[], dispositions=dropped, now=now
    )
    assert "Fix the thing" not in "\n".join(lines)
