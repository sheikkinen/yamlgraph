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


# ------------------------------------------------------- FR-742: diary debt


def test_diary_class_matches_real_debts():
    for title in (
        "Document findings and diary entry",
        "Write diary reflection",
        "Diary reflection",
        "Distill the arc",
    ):
        assert todos.is_diary_class(title), title
    assert not todos.is_diary_class("Fix the thing")


def test_diary_debt_exempt_from_age_cap(tmp_path):
    """FR-742 AC-01: doctrine debt does not expire — 93d diary orphan
    stays visible while a 93d ordinary orphan is capped out."""
    now = 1_000_000.0
    sessions = {
        "old-dead": _session([("Write diary reflection", "in-progress")], 93, now),
    }
    lines = todos.briefing_lines(
        sessions, live=set(), roots=[], dispositions=set(), now=now
    )
    text = "\n".join(lines)
    assert "Write diary reflection" in text
    assert "DIARY DEBT" in text


def test_diary_class_applies_to_died_open_only(tmp_path):
    """FR-742 F4: LIVE sessions own their futures."""
    now = 1_000_000.0
    sessions = {
        "live-s": _session([("Write diary reflection", "not-started")], 0.01, now),
    }
    lines = todos.briefing_lines(
        sessions, live={"live-s"}, roots=[], dispositions=set(), now=now
    )
    text = "\n".join(lines)
    assert "claims:" in text
    assert "DIARY DEBT" not in text


def test_diary_debt_verdict_window(tmp_path):
    """FR-742 AC-02/F2: window = [last_active − 7d, last_active + 1d];
    a successor's LATER posthumous entry must not count as delivery."""
    diary = tmp_path / "docs/diary"
    diary.mkdir(parents=True)
    day = 86400.0
    last_active = 1_000_000_000.0  # 2001-09-09
    (diary / "diary-2001-09-06-in-window.md").write_text("x")
    assert todos.diary_debt_verdict(last_active, [diary]) == "LIKELY DELIVERED"
    (diary / "diary-2001-09-06-in-window.md").unlink()
    (diary / "diary-2001-09-20-too-late.md").write_text("x")
    assert todos.diary_debt_verdict(last_active, [diary]) == "UNWRITTEN"
    (diary / "diary-2001-08-25-too-early.md").write_text("x")
    assert todos.diary_debt_verdict(last_active, [diary]) == "UNWRITTEN"
    assert last_active + day  # window upper bound documented


def test_material_priority_transcript_else_chatsessions(tmp_path, monkeypatch):
    """FR-742 F1: transcripts do not survive for old debts; chatSessions
    is the second-priority material source."""
    ws = tmp_path / "ws1"
    (ws / "GitHub.copilot-chat/transcripts").mkdir(parents=True)
    (ws / "chatSessions").mkdir(parents=True)
    monkeypatch.setattr(todos, "WS_STORAGE", tmp_path)
    (ws / "chatSessions/sess-old.jsonl").write_text("{}")
    assert "chatSessions" in str(todos.material_for("sess-old"))
    (ws / "GitHub.copilot-chat/transcripts/sess-old.jsonl").write_text("{}")
    assert "transcripts" in str(todos.material_for("sess-old"))
    assert todos.material_for("sess-none") is None
