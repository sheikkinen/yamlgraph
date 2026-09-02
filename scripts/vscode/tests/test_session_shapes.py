#!/usr/bin/env python3
"""FR-884: session task-shape mining — witnesses.

Unmarked per FR-737 F5 precedent. Run: pytest scripts/vscode/tests/ -q

Pins (judgement 2026-08-25):
- AC-03 inventory joins chatSessions + price sheets + audit traces by
  session id; missing optional sources reported as unavailable, never
  silently substituted.
- AC-04 synthetic fixtures only — never the operator's real stores.
- Cost figures are best/worst ranges (cache-read conflation).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import session_shapes  # noqa: E402  # CONF-392 idiom

WINDOW = ("2026-06-26", "2026-08-25")

# 2026-07-15 12:00:00 UTC in ms — inside the frozen window
TS_IN = 1784548800000
# 2026-05-01 — outside the window
TS_OUT = 1778022000000


def make_chat_session(
    tmp_path: Path,
    ws_hash: str,
    session_id: str,
    requests: list[tuple[int, str, int, int]],
    title: str = "synthetic session",
) -> Path:
    """Write a minimal chatSessions jsonl mimicking the real shape."""
    ws = tmp_path / ws_hash / "chatSessions"
    ws.mkdir(parents=True, exist_ok=True)
    head = {
        "version": 3,
        "sessionId": session_id,
        "customTitle": title,
        "creationDate": requests[0][0],
    }
    lines = [json.dumps(head)]
    for ts, model, ptok, otok in requests:
        lines.append(
            json.dumps(
                {
                    "requestId": f"req-{ts}",
                    "timestamp": ts,
                    "modelId": model,
                    "result": {"timings": {}, "metadata": {}},
                    "promptTokens": ptok,
                    "outputTokens": otok,
                }
            )
        )
    path = ws / f"{session_id}.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def make_audit(tmp_path: Path, entries: list[tuple[str, str]]) -> Path:
    """Synthetic hooks audit.jsonl: (session_id, tool) rows."""
    path = tmp_path / "audit.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                {
                    "ts": "2026-07-15T12:00:00+00:00",
                    "hook": "h",
                    "tool": tool,
                    "decision": "pass",
                    "session_id": sid,
                }
            )
            for sid, tool in entries
        )
    , encoding="utf-8")
    return path


def test_parse_session_extracts_requests(tmp_path: Path) -> None:
    p = make_chat_session(
        tmp_path,
        "ws1",
        "aaaa-bbbb",
        [(TS_IN, "claude-fable-5", 1000, 200), (TS_IN + 60000, "gpt-5.5", 500, 100)],
    )
    sess = session_shapes.parse_session(p)
    assert sess["session_id"] == "aaaa-bbbb"
    assert sess["title"] == "synthetic session"
    assert len(sess["requests"]) == 2
    ts, model, ptok, otok = sess["requests"][0]
    assert (model, ptok, otok) == ("claude-fable-5", 1000, 200)
    assert ts == TS_IN


def test_inventory_filters_by_window(tmp_path: Path) -> None:
    make_chat_session(
        tmp_path, "ws1", "in-window", [(TS_IN, "claude-fable-5", 1000, 200)]
    )
    make_chat_session(
        tmp_path, "ws1", "out-window", [(TS_OUT, "claude-fable-5", 1000, 200)]
    )
    rows = session_shapes.inventory(ws_storage=tmp_path, window=WINDOW)
    ids = {r["session_id"] for r in rows}
    assert ids == {"in-window"}


def test_inventory_aggregates_tokens_and_models(tmp_path: Path) -> None:
    make_chat_session(
        tmp_path,
        "ws1",
        "s1",
        [
            (TS_IN, "claude-fable-5", 1000, 200),
            (TS_IN + 1000, "claude-fable-5", 3000, 400),
            (TS_IN + 2000, "gpt-5.5", 500, 50),
        ],
    )
    (row,) = session_shapes.inventory(ws_storage=tmp_path, window=WINDOW)
    assert row["prompt_tokens"] == 4500
    assert row["output_tokens"] == 650
    assert row["requests"] == 3
    assert row["models"] == {"claude-fable-5": 2, "gpt-5.5": 1}
    assert row["workspace"] == "ws1"


def test_cost_range_best_below_worst(tmp_path: Path) -> None:
    prices = {"claude-fable-5": {"in": 1000, "out": 5000, "cache": 100}}
    make_chat_session(
        tmp_path, "ws1", "s1", [(TS_IN, "claude-fable-5", 1_000_000, 100_000)]
    )
    (row,) = session_shapes.inventory(ws_storage=tmp_path, window=WINDOW, prices=prices)
    best, worst = row["cost_range"]
    assert 0 < best < worst


def test_audit_join_counts_tools(tmp_path: Path) -> None:
    make_chat_session(tmp_path, "ws1", "s1", [(TS_IN, "claude-fable-5", 100, 10)])
    audit = make_audit(
        tmp_path,
        [
            ("s1", "run_in_terminal"),
            ("s1", "run_in_terminal"),
            ("s1", "create_file"),
            ("other", "read_file"),
        ],
    )
    rows = session_shapes.inventory(
        ws_storage=tmp_path, window=WINDOW, audit_path=audit
    )
    (row,) = rows
    assert row["tool_calls"] == {"run_in_terminal": 2, "create_file": 1}


def test_missing_audit_reported_unavailable(tmp_path: Path) -> None:
    make_chat_session(tmp_path, "ws1", "s1", [(TS_IN, "claude-fable-5", 100, 10)])
    rows = session_shapes.inventory(
        ws_storage=tmp_path, window=WINDOW, audit_path=tmp_path / "absent.jsonl"
    )
    (row,) = rows
    assert row["tool_calls"] is None  # unavailable, not empty-dict substitution


def test_select_strata_top_and_random(tmp_path: Path) -> None:
    for i in range(12):
        make_chat_session(
            tmp_path,
            "ws1",
            f"s{i:02d}",
            [(TS_IN + i, "claude-fable-5", (i + 1) * 1000, 100)],
        )
    rows = session_shapes.inventory(ws_storage=tmp_path, window=WINDOW)
    top, rand = session_shapes.select_strata(rows, top_n=5, random_n=5, seed=884)
    top_ids = [r["session_id"] for r in top]
    assert top_ids == ["s11", "s10", "s09", "s08", "s07"]  # by prompt+output desc
    assert len(rand) == 5
    assert not {r["session_id"] for r in rand} & set(top_ids)  # disjoint strata


def test_extract_transcript_text(tmp_path: Path) -> None:
    ws = tmp_path / "ws1" / "chatSessions"
    ws.mkdir(parents=True)
    path = ws / "s1.jsonl"
    path.write_text(
        json.dumps({"sessionId": "s1", "creationDate": TS_IN})
        + "\n"
        + json.dumps(
            {
                "requestId": "r1",
                "timestamp": TS_IN,
                "modelId": "m",
                "message": {"text": "user asks a thing"},
                "response": [{"value": "agent answers a thing"}],
            }
        )
    , encoding="utf-8")
    text = session_shapes.extract_transcript(path)
    assert "user asks a thing" in text
    assert "agent answers a thing" in text


def make_oplog(tmp_path: Path, session_id: str = "s-op") -> Path:
    """Synthetic op-log session file (kind 0 snapshot / 1 set / 2 extend)."""
    snapshot = {
        "sessionId": session_id,
        "customTitle": "op-log synthetic",
        "requests": [
            {
                "message": {"text": "first user message"},
                "response": [{"value": "first agent reply"}],
                "promptTokens": 100,
            }
        ],
    }
    ops = [
        {"kind": 0, "v": snapshot},
        {"kind": 1, "k": ["requests", 0, "promptTokens"], "v": 111},
        {
            "kind": 2,
            "k": ["requests"],
            "v": [{"message": {"text": "second user message"}, "response": []}],
        },
        {
            "kind": 2,
            "k": ["requests", 1, "response"],
            "v": [{"value": "second "}, {"value": "agent reply"}],
        },
        {"kind": 1, "k": ["requests", 1, "promptTokens"], "v": 222},
    ]
    path = tmp_path / f"{session_id}.jsonl"
    path.write_text("\n".join(json.dumps(op) for op in ops), encoding="utf-8")
    return path


def test_replay_oplog_applies_set_and_extend(tmp_path: Path) -> None:
    state = session_shapes.replay(make_oplog(tmp_path))
    assert state is not None
    reqs = state["requests"]
    assert len(reqs) == 2
    assert reqs[0]["promptTokens"] == 111  # kind-1 set over snapshot value
    assert reqs[1]["promptTokens"] == 222  # kind-1 set on extended entry
    assert [p["value"] for p in reqs[1]["response"]] == ["second ", "agent reply"]


def test_replay_non_oplog_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "plain.jsonl"
    path.write_text(json.dumps({"sessionId": "x", "requests": []}), encoding="utf-8")
    assert session_shapes.replay(path) is None


def test_turn_skeleton_user_text_and_agent_head(tmp_path: Path) -> None:
    state = session_shapes.replay(make_oplog(tmp_path))
    turns = session_shapes.turn_skeleton(state, cap=10)
    assert [t["index"] for t in turns] == [0, 1]
    assert turns[0]["user"] == "first user message"
    assert turns[0]["prompt_tokens"] == 111
    assert turns[1]["agent"] == "second agi"[:10] or len(turns[1]["agent"]) <= 10
    assert turns[1]["agent"].startswith("second")  # concatenated response parts
