#!/usr/bin/env python3
"""FR-739: VS Code introspection suite — tap attribution, altimeter, rotation.

Unmarked per FR-737 F5 precedent (process infrastructure follows its
target's convention). Run: pytest scripts/vscode/tests/ -q

Pins witnessed:
- AC-00 traceId join: agent.turn events (no session.id) attributed via
  session.start traceId; the merged-stream phantom (11 collapses vs 1
  real, measured 2026-07-16) must not survive the join.
- AC-01 altimeter: compaction = >50% drop between consecutive turns of
  ONE session; witnessed compactions recorded (deduped) to a
  calibration file; turns-to-ceiling estimate only at ≥3 witnesses.
- AC-03 liveness: ground truth from event recency, not file mtimes.
- AC-04 seam: per-session reconciliation of estimate vs exact.
- AC-05 rotation: archive-and-truncate past the cap, not a warning.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tap  # noqa: E402


def rec(event: str, trace: str, ts: float, **attrs) -> dict:
    """One record in the real exporter shape (attributes = plain dict)."""
    return {
        "hrTime": [int(ts), int((ts % 1) * 1e9)],
        "spanContext": {"traceId": trace, "spanId": "s", "traceFlags": 1},
        "attributes": {"event.name": event, **attrs},
        "_body": event,
    }


def write_tap(path: Path, records: list[dict]) -> Path:
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    return path


def two_session_interleave(t0: float) -> list[dict]:
    """Session A high context, session B low — interleaved so a merged
    reading manufactures phantom collapses (the measured trap)."""
    rows = []
    for i, (trace, sid) in enumerate([("tA", "sess-aaaa"), ("tB", "sess-bbbb")]):
        rows.append(
            rec(
                "copilot_chat.session.start",
                trace,
                t0 + i,
                **{"session.id": sid, "gen_ai.request.model": "claude-fable-5"},
            )
        )
    for j, (trace, tokens) in enumerate(
        [("tA", 700_000), ("tB", 100_000), ("tA", 710_000), ("tB", 110_000)]
    ):
        rows.append(
            rec(
                "copilot_chat.agent.turn",
                trace,
                t0 + 10 + j,
                **{"gen_ai.usage.input_tokens": tokens, "turn.index": j // 2},
            )
        )
    return rows


# ---------------------------------------------------------------- AC-00


def test_turns_attributed_by_trace_join(tmp_path):
    path = write_tap(tmp_path / "tap.jsonl", two_session_interleave(1000.0))
    sessions = tap.join_sessions(tap.load_events(path))
    assert set(sessions) == {"sess-aaaa", "sess-bbbb"}
    assert [tok for _, tok in sessions["sess-aaaa"]["turns"]] == [700_000, 710_000]
    assert [tok for _, tok in sessions["sess-bbbb"]["turns"]] == [100_000, 110_000]


def test_phantom_collapses_do_not_survive_the_join(tmp_path):
    path = write_tap(tmp_path / "tap.jsonl", two_session_interleave(1000.0))
    events = tap.load_events(path)
    merged = [
        (e["ts"], e["attrs"]["gen_ai.usage.input_tokens"])
        for e in events
        if e["attrs"].get("event.name") == "copilot_chat.agent.turn"
    ]
    assert tap.detect_compactions(merged), "fixture must reproduce the trap"
    for sess in tap.join_sessions(events).values():
        assert tap.detect_compactions(sess["turns"]) == []


# ---------------------------------------------------------------- AC-01


def test_detect_compaction_witnessed_shape():
    turns = [(1.0, 700_000), (2.0, 748_000), (3.0, 61_000), (4.0, 75_000)]
    comps = tap.detect_compactions(turns)
    assert len(comps) == 1
    assert comps[0]["peak"] == 748_000
    assert comps[0]["post"] == 61_000


def test_zero_post_turn_is_not_a_compaction():
    """Field defect 2026-07-16: a cancelled/zero-token turn (91,846 → 0)
    was recorded as a witness and poisoned min(peaks) → ETA≈0 for all.
    A real compaction leaves a summary (~56-61K witnessed); post=0 is a
    dead turn, not a guillotine."""
    turns = [(1.0, 91_846), (2.0, 0)]
    assert tap.detect_compactions(turns) == []


def test_calibration_records_appended_and_deduped(tmp_path):
    calib = tmp_path / "compactions.jsonl"
    comps = [{"peak": 748_000, "post": 61_000, "ts": 3.0}]
    assert tap.record_compactions(calib, "sess-aaaa", comps) == 1
    assert tap.record_compactions(calib, "sess-aaaa", comps) == 0
    rows = [json.loads(ln) for ln in calib.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["session"] == "sess-aaaa"
    assert rows[0]["peak"] == 748_000


def test_no_eta_below_three_witnesses(tmp_path):
    calib = tmp_path / "compactions.jsonl"
    tap.record_compactions(calib, "s1", [{"peak": 750_000, "post": 61_000, "ts": 1}])
    sessions = {
        "sess-aaaa": {"turns": [(1.0, 700_000), (2.0, 703_000)], "models": set()}
    }
    text = "\n".join(tap.altimeter_lines(sessions, calib))
    assert "700" in text.replace(",", "") or "703" in text.replace(",", "")
    assert "peak" in text.lower()
    assert "eta" not in text.lower()


def test_eta_at_three_witnesses(tmp_path):
    calib = tmp_path / "compactions.jsonl"
    for i in range(3):
        tap.record_compactions(
            calib, f"s{i}", [{"peak": 740_000 + i * 5_000, "post": 60_000, "ts": i}]
        )
    sessions = {
        "sess-aaaa": {"turns": [(1.0, 700_000), (2.0, 703_000)], "models": set()}
    }
    text = "\n".join(tap.altimeter_lines(sessions, calib))
    assert "eta" in text.lower()


# ---------------------------------------------------------------- AC-03


def test_liveness_from_event_recency(tmp_path):
    now = time.time()
    rows = two_session_interleave(now - 3600)  # session B's last turn ~1h ago
    rows.append(
        rec(
            "copilot_chat.agent.turn",
            "tA",
            now - 60,
            **{"gen_ai.usage.input_tokens": 712_000, "turn.index": 2},
        )
    )
    path = write_tap(tmp_path / "tap.jsonl", rows)
    sessions = tap.join_sessions(tap.load_events(path))
    live = tap.live_session_ids(sessions, within_s=600, now=now)
    assert live == {"sess-aaaa"}


# ---------------------------------------------------------------- AC-04


def test_reconcile_per_session_only_overlap():
    est = {"sess-aaaa": 5_000_000, "sess-bbbb": 900_000, "sess-old": 4_000_000}
    exact = {"sess-aaaa": 5_200_000, "sess-bbbb": 850_000, "sess-other-machine": 1}
    rows = tap.reconcile(est, exact)
    assert {r["session"] for r in rows} == {"sess-aaaa", "sess-bbbb"}
    a = next(r for r in rows if r["session"] == "sess-aaaa")
    assert a["est"] == 5_000_000 and a["exact"] == 5_200_000
    assert abs(a["ratio"] - 5_000_000 / 5_200_000) < 1e-9


# ---------------------------------------------------------------- AC-05


def test_rotation_archives_and_truncates(tmp_path):
    path = tmp_path / "tap.jsonl"
    path.write_text("x" * 2048)
    archive = tap.rotate_if_big(path, cap_bytes=1024)
    assert archive is not None and archive.exists()
    assert archive.read_text() == "x" * 2048
    assert path.stat().st_size == 0


def test_no_rotation_below_cap(tmp_path):
    path = tmp_path / "tap.jsonl"
    path.write_text("x" * 10)
    assert tap.rotate_if_big(path, cap_bytes=1024) is None
    assert path.read_text() == "x" * 10
