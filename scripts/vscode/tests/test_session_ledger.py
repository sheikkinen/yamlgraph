#!/usr/bin/env python3
"""FR-898: session accountability ledger — witnesses.

Unmarked per FR-737 F5 precedent. Run: pytest scripts/vscode/tests/ -q

Pins (judgement 2026-08-29, R-1..R-5 folded):
- AC-01 replay: kind 0 snapshot / kind 1 set / kind 2 insert / kind 2
  splice-delete, last-write-wins; intermediate credits never summed.
- AC-03 credits-absent: token-price estimate RANGE in unavailable_reason,
  never a fabricated point value.
- AC-04 malformed policy: explicit request -> hard error; scan -> skip
  with stderr report + unavailable_reason row; never silent omission.
- AC-08 read-only + R-4 privacy: --out refuses repo-internal paths
  without --allow-repo-output.
- Synthetic fixtures only (FR-884 pin) — never the operator's real stores.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import session_ledger  # noqa: E402  # CONF-428

MS = 1_000
CREATED_MS = 1_787_000_000_000  # fixture epoch, ms

CSV_COLUMNS = [
    "session_id",
    "session_title",
    "created",
    "workspace",
    "request",
    "request_time",
    "model",
    "credits",
    "prompt_tokens",
    "completion_tokens",
    "elapsed_ms",
    "prompt",
    "summary",
    "unavailable_reason",
]


def _request(prompt: str, model: str, ts: int) -> dict:
    return {
        "message": {"parts": [{"text": prompt}]},
        "modelId": model,
        "timestamp": ts,
        "response": [],
    }


def write_store(
    root: Path,
    session_id: str = "fixture-0001",
    *,
    credits: bool = True,
    ts: int = CREATED_MS,
) -> Path:
    """Synthetic patch log exercising all four record shapes."""
    ws = root / "hash0000"
    chat = ws / "chatSessions"
    chat.mkdir(parents=True, exist_ok=True)
    (ws / "workspace.json").write_text(
        json.dumps({"folder": "file:///fake/repo-under-test"})
    )
    recs = [
        {"kind": 0, "v": {"sessionId": session_id, "creationDate": ts, "requests": []}},
        # request 1 (model-a)
        {
            "kind": 2,
            "k": ["requests"],
            "v": _request("first prompt", "copilot/model-a", ts),
        },
        # intermediate credits patch — must NEVER be summed with the final
        # (inserted below only when credits=True; a credits-less turn has none)
        {"kind": 1, "k": ["requests", 0, "promptTokens"], "v": 1000},
        {"kind": 1, "k": ["requests", 0, "completionTokens"], "v": 200},
        # two response parts, then splice-delete the first
        {
            "kind": 2,
            "k": ["requests", 0, "response"],
            "i": 0,
            "v": {"kind": "x", "generatedTitle": "Doomed title"},
        },
        {
            "kind": 2,
            "k": ["requests", 0, "response"],
            "i": 1,
            "v": {"kind": "x", "generatedTitle": "Surviving title"},
        },
        {"kind": 2, "k": ["requests", 0, "response"], "i": 0},  # splice-delete
        # request 2 (model-b: mid-session switch), no generatedTitle at all —
        # markdown answer part (kind-less) provides the substitute summary line
        {
            "kind": 2,
            "k": ["requests"],
            "i": 1,
            "v": _request("second prompt", "copilot/model-b", ts + 60 * MS),
        },
        {
            "kind": 2,
            "k": ["requests", 1, "response"],
            "v": {"value": "Answer first line\nsecond line", "baseUri": "x"},
        },
        {"kind": 1, "k": ["requests", 1, "promptTokens"], "v": 500},
        {"kind": 1, "k": ["requests", 1, "completionTokens"], "v": 100},
        # late header patch — invisible to snapshot-only reads
        {"kind": 1, "k": ["customTitle"], "v": "Fixture Session Title"},
    ]
    if credits:
        recs.insert(2, {"kind": 1, "k": ["requests", 0, "copilotCredits"], "v": 10.0})
        recs.append({"kind": 1, "k": ["requests", 0, "copilotCredits"], "v": 42.5})
        recs.append({"kind": 1, "k": ["requests", 1, "copilotCredits"], "v": 7.5})
    path = chat / f"{session_id}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    return path


def csv_rows(argv: list[str], capsys) -> tuple[list[dict], str]:
    session_ledger.main(argv)
    captured = capsys.readouterr()
    return list(csv.DictReader(io.StringIO(captured.out))), captured.err


# --- AC-01: replay semantics ------------------------------------------------


def test_replay_last_write_wins_and_splice_delete(tmp_path):
    store = write_store(tmp_path)
    doc = session_ledger.replay(store)
    req0 = doc["requests"][0]
    assert req0["copilotCredits"] == 42.5  # final, not 10.0, not 52.5
    titles = [p.get("generatedTitle") for p in req0["response"]]
    assert titles == ["Surviving title"]  # splice-delete removed index 0
    assert doc["customTitle"] == "Fixture Session Title"  # late kind:1


# --- AC-02 / AC-06 / AC-07: join + CSV schema -------------------------------


def test_csv_join_fields(tmp_path, capsys):
    store = write_store(tmp_path)
    rows, _ = csv_rows(["--csv", str(store)], capsys)
    assert list(rows[0].keys()) == CSV_COLUMNS
    assert len(rows) == 2
    r1, r2 = rows
    assert r1["session_id"] == "fixture-0001"
    assert r1["session_title"] == "Fixture Session Title"
    assert r1["workspace"] == "/fake/repo-under-test"
    assert r1["prompt"] == "first prompt"
    assert r1["model"] == "model-a"
    assert r2["model"] == "model-b"  # mid-session switch labeled per request
    assert float(r1["credits"]) == 42.5
    assert r1["prompt_tokens"] == "1000"
    assert r1["summary"] == "Surviving title"
    assert "intent" not in rows[0]  # deferred per R-3


def test_summary_uses_answer_first_line_when_untitled(tmp_path, capsys):
    store = write_store(tmp_path)
    rows, _ = csv_rows(["--csv", str(store)], capsys)
    assert rows[1]["summary"] == "Answer first line"


def test_csv_single_header_multi_file(tmp_path, capsys):
    a = write_store(tmp_path / "a", "fixture-000a")
    b = write_store(tmp_path / "b", "fixture-000b")
    session_ledger.main(["--csv", str(a), str(b)])
    out = capsys.readouterr().out
    assert out.count("session_id,") == 1
    assert len(list(csv.DictReader(io.StringIO(out)))) == 4


# --- AC-03: credits-absent estimate range ------------------------------------


def test_credits_absent_estimate_range(tmp_path, capsys, monkeypatch):
    store = write_store(tmp_path, credits=False)
    monkeypatch.setattr(
        session_ledger,
        "load_prices",
        lambda: {
            "model-a": {"in": 1000, "out": 5000, "cache": 100},
            "model-b": {"in": 1000, "out": 5000, "cache": 100},
        },
    )
    rows, _ = csv_rows(["--csv", str(store)], capsys)
    assert rows[0]["credits"] == ""  # never fabricated
    reason = rows[0]["unavailable_reason"]
    assert "no copilotCredits" in reason
    assert "–" in reason or "-" in reason  # a RANGE, not a point


# --- AC-04: malformed-store policy -------------------------------------------


def test_malformed_explicit_hard_error(tmp_path):
    bad = tmp_path / "chatSessions"
    bad.mkdir(parents=True)
    store = bad / "broken.jsonl"
    store.write_text('{"kind": 0, "v": {}}\nnot json at all\n')
    with pytest.raises(SystemExit) as exc:
        session_ledger.main(["--csv", str(store)])
    assert exc.value.code != 0


def test_malformed_scan_skips_with_reason(tmp_path, capsys, monkeypatch):
    write_store(tmp_path, "fixture-good")
    bad = tmp_path / "hash0000" / "chatSessions" / "broken.jsonl"
    bad.write_text("not json\n")
    monkeypatch.setattr(session_ledger, "WS_STORAGE", tmp_path)
    rows, err = csv_rows(["--csv", "--all-workspaces"], capsys)
    good = [r for r in rows if r["session_id"] == "fixture-good"]
    broken = [r for r in rows if r["unavailable_reason"].startswith("replay failed")]
    assert len(good) == 2  # scan continued
    assert len(broken) == 1  # surfaced, not silently omitted
    assert "broken.jsonl" in err  # stderr report


# --- D-1: --window scoping ----------------------------------------------------


def test_window_excludes_stale_sessions(tmp_path, capsys, monkeypatch):
    write_store(tmp_path, "fixture-old", ts=CREATED_MS)  # far in the past
    monkeypatch.setattr(session_ledger, "WS_STORAGE", tmp_path)
    rows, _ = csv_rows(["--csv", "--all-workspaces", "--window", "1"], capsys)
    assert rows == []


# --- AC-08: read-only + R-4 privacy boundary ----------------------------------


def test_read_only_store_untouched(tmp_path, capsys):
    store = write_store(tmp_path)
    before = store.read_bytes()
    session_ledger.main(["--csv", str(store)])
    capsys.readouterr()
    assert store.read_bytes() == before


def test_out_refuses_repo_internal_paths(tmp_path, capsys):
    store = write_store(tmp_path)
    repo = tmp_path / "somerepo"
    (repo / ".git").mkdir(parents=True)
    target = repo / "report.csv"
    with pytest.raises(SystemExit):
        session_ledger.main(["--csv", str(store), "--out", str(target)])
    assert not target.exists()
    session_ledger.main(
        ["--csv", str(store), "--out", str(target), "--allow-repo-output"]
    )
    assert target.exists()
