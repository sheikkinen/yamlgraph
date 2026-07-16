#!/usr/bin/env python3
"""Tap reader: exact per-call usage from the Copilot OTel file tap.

FR-739 (judged 2026-07-16). Parses the JSONL written by the extension's
OTel file exporter (armed via otel-tap-on.sh). Unlike chatSessions —
which records only the LAST round of a turn — the tap logs EVERY
inference call, including side-model utility calls invisible elsewhere.

AC-00: `agent.turn` events carry NO session.id; attribution goes
through the measured join `session.start.traceId → session.id`, then
events keyed by `spanContext.traceId`. Read naively, the merged stream
manufactures phantom compactions (11 where per-session truth was 1).

AC-01: compactions (>50% context drop within one session) are recorded
to a calibration file; turns-to-ceiling estimates unlock at ≥3
witnesses — the ceiling is never hardcoded (n=1: 750,382; sessions
seen alive uncompacted at 692K).

AC-05: rotation is enforced on read past the cap (archive + truncate),
not warned.

Cost applies the two-anchor calibration (1 cr = $0.01; agent turns
≈98% cached; all-fresh printed as ceiling).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path.home() / "src/yamlgraph/tmp/copilot-otel.jsonl"
CALIB_PATH = Path(__file__).resolve().parent / "compactions.jsonl"
CAP_BYTES = 100 * 1024 * 1024
COMPACTION_DROP = 0.5  # >50% drop between consecutive turns = compaction
LIVE_WINDOW_S = 600

# calibrated pricing (credits per 1M tokens; 1 credit = $0.01)
PRICES = {
    "claude-fable-5": {"in": 1000, "out": 5000, "cache": 100},
    "claude-opus": {"in": 500, "out": 2500, "cache": 50},
    "gpt-4o-mini": {"in": 0, "out": 0, "cache": 0},  # utility calls: unbilled tier
}
DEFAULT_PRICE = {"in": 1000, "out": 5000, "cache": 100}
CACHE_RATIO = 0.98  # anchor-2 calibration

TURN_EVENT = "copilot_chat.agent.turn"
CALL_EVENT = "gen_ai.client.inference.operation.details"

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
TITLE_RE = re.compile(r'"customTitle":"([^"]{1,120})"')


def session_titles(sids) -> dict[str, str]:
    """Session names from chatSessions customTitle (file stem = session id)."""
    titles = {}
    for sid in sids:
        for p in WS_STORAGE.glob(f"*/chatSessions/{sid}.jsonl"):
            m = TITLE_RE.search(p.open(errors="replace").read(4000))
            if m:
                titles[sid] = m.group(1)
            break
    return titles


def price_for(model: str) -> dict[str, int]:
    for prefix, price in PRICES.items():
        if model.startswith(prefix):
            return price
    return DEFAULT_PRICE


def attrs_of(record: dict) -> dict:
    a = record.get("attributes") or {}
    if isinstance(a, list):  # tolerate OTel KeyValue form
        out = {}
        for kv in a:
            v = kv.get("value")
            out[kv.get("key")] = next(iter(v.values())) if isinstance(v, dict) else v
        return out
    return a


def load_events(path: Path) -> list[dict]:
    """Parsed records: {ts, trace, attrs}, in file order."""
    events = []
    for line in path.open(errors="replace"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        hr = rec.get("hrTime") or [0, 0]
        events.append(
            {
                "ts": hr[0] + hr[1] / 1e9,
                "trace": (rec.get("spanContext") or {}).get("traceId"),
                "attrs": attrs_of(rec),
            }
        )
    return events


def join_sessions(events: list[dict]) -> dict[str, dict]:
    """AC-00: attribute turn/call events to sessions via the traceId join."""
    trace_to_sid = {}
    for e in events:
        if e["attrs"].get("event.name") == "copilot_chat.session.start":
            sid = e["attrs"].get("session.id")
            if sid and e["trace"]:
                trace_to_sid[e["trace"]] = sid

    sessions: dict[str, dict] = {}
    for e in events:
        sid = trace_to_sid.get(e["trace"])
        if not sid:
            continue
        sess = sessions.setdefault(
            sid, {"turns": [], "calls": [], "last_ts": 0.0, "models": set()}
        )
        a = e["attrs"]
        event = a.get("event.name")
        sess["last_ts"] = max(sess["last_ts"], e["ts"])
        if event == TURN_EVENT and a.get("gen_ai.usage.input_tokens") is not None:
            sess["turns"].append((e["ts"], int(a["gen_ai.usage.input_tokens"])))
        elif event == CALL_EVENT and a.get("gen_ai.usage.input_tokens") is not None:
            model = a.get("gen_ai.response.model") or a.get("gen_ai.request.model")
            sess["models"].add(str(model))
            sess["calls"].append(
                (
                    e["ts"],
                    str(model),
                    int(a["gen_ai.usage.input_tokens"]),
                    int(a.get("gen_ai.usage.output_tokens") or 0),
                )
            )
    for sess in sessions.values():
        sess["turns"].sort()
        sess["calls"].sort()
    return sessions


def detect_compactions(turns: list[tuple[float, int]]) -> list[dict]:
    """>50% context drop between consecutive turns of ONE session.

    post=0 is a cancelled/dead turn, not a compaction — a real compaction
    leaves the summary as the new context floor (~56-61K witnessed).
    Field defect 2026-07-16: a 91,846→0 turn poisoned min(peaks).
    """
    comps = []
    for (_, prev), (ts, cur) in zip(turns, turns[1:], strict=False):
        if prev and cur and cur < prev * (1 - COMPACTION_DROP):
            comps.append({"peak": prev, "post": cur, "ts": ts})
    return comps


def load_calibration(calib_path: Path = CALIB_PATH) -> list[dict]:
    if not calib_path.is_file():
        return []
    return [json.loads(ln) for ln in calib_path.read_text().splitlines() if ln.strip()]


def record_compactions(calib_path: Path, sid: str, comps: list[dict]) -> int:
    """Append witnessed compactions, deduped on (session, ts). Returns new count."""
    seen = {(r["session"], r["ts"]) for r in load_calibration(calib_path)}
    new = [c for c in comps if (sid, c["ts"]) not in seen]
    with calib_path.open("a") as f:
        for c in new:
            f.write(json.dumps({"session": sid, **c}) + "\n")
    return len(new)


def altimeter_lines(
    sessions: dict[str, dict], calib_path: Path = CALIB_PATH
) -> list[str]:
    """AC-01: per-session level, slope, witnessed peak; ETA at ≥3 witnesses."""
    calib = load_calibration(calib_path)
    peaks = [r["peak"] for r in calib]
    peak_note = (
        f"peak_witnessed={min(peaks):,}–{max(peaks):,}"
        if peaks
        else "peak_witnessed=none"
    )
    lines = [f"altimeter ({len(calib)} compaction witnesses, {peak_note})"]
    for sid, sess in sorted(sessions.items()):
        turns = sess["turns"]
        if not turns:
            continue
        level = turns[-1][1]
        tail = turns[-4:]
        deltas = [b[1] - a[1] for a, b in zip(tail, tail[1:], strict=False)]
        slope = sum(deltas) / len(deltas) if deltas else 0.0
        line = f"  {sid[:8]}  level={level:,}  slope={slope:+,.0f}/turn"
        if len(calib) >= 3 and slope > 0:
            eta = (min(peaks) - level) / slope
            line += f"  ETA≈{max(eta, 0):.0f} turns to lowest witnessed peak"
        lines.append(line)
    return lines


def live_session_ids(
    sessions: dict[str, dict],
    within_s: float = LIVE_WINDOW_S,
    now: float | None = None,
) -> set[str]:
    """AC-03: liveness from event recency — ground truth, not mtimes."""
    now = time.time() if now is None else now
    return {sid for sid, s in sessions.items() if now - s["last_ts"] <= within_s}


def reconcile(est: dict[str, int], exact: dict[str, int]) -> list[dict]:
    """AC-04: per-session estimate-vs-exact, overlap only."""
    return [
        {
            "session": sid,
            "est": est[sid],
            "exact": exact[sid],
            "ratio": est[sid] / exact[sid],
        }
        for sid in sorted(set(est) & set(exact))
        if exact[sid]
    ]


def rotate_if_big(path: Path, cap_bytes: int = CAP_BYTES) -> Path | None:
    """AC-05: archive with date stamp and truncate. Returns archive path.

    Truncation (not rename) keeps the exporter's open append-mode fd valid.
    """
    if path.stat().st_size <= cap_bytes:
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = path.with_name(f"{path.stem}-{stamp}{path.suffix}")
    shutil.copy2(path, archive)
    path.open("w").close()
    return archive


def call_credits(model: str, ti: int, to: int) -> float:
    pr = price_for(model)
    return (
        ti / 1e6 * ((1 - CACHE_RATIO) * pr["in"] + CACHE_RATIO * pr["cache"])
        + to / 1e6 * pr["out"]
    )


def sessions_table(
    sessions: dict[str, dict], live: set[str], titles: dict[str, str] | None = None
) -> list[str]:
    """Per-session exact tokens + calibrated credits — the ongoing-session
    cost view (user ask 2026-07-16). Titles joined from chatSessions."""
    titles = titles or {}
    lines = [
        f"{'session':<10} {'state':<8} {'calls':>6} {'inputTok':>14}"
        f" {'outTok':>8} {'cr@98%':>8} {'USD':>7}  title"
    ]
    totals = [0, 0, 0.0]
    for sid, sess in sorted(
        sessions.items(), key=lambda kv: -sum(c[2] for c in kv[1]["calls"])
    ):
        ti = sum(c[2] for c in sess["calls"])
        to = sum(c[3] for c in sess["calls"])
        cr = sum(call_credits(c[1], c[2], c[3]) for c in sess["calls"])
        state = "LIVE" if sid in live else "idle"
        totals[0] += ti
        totals[1] += to
        totals[2] += cr
        lines.append(
            f"{sid[:8]:<10} {state:<8} {len(sess['calls']):>6} {ti:>14,}"
            f" {to:>8,} {cr:>8,.1f} {'$' + format(cr / 100, ',.2f'):>7}"
            f"  {titles.get(sid, '')[:48]}"
        )
    lines.append(
        f"{'TOTAL':<10} {'':<8} {'':>6} {totals[0]:>14,} {totals[1]:>8,}"
        f" {totals[2]:>8,.1f} {'$' + format(totals[2] / 100, ',.2f'):>7}"
    )
    return lines


def usage_table(sessions: dict[str, dict]) -> list[str]:
    by_model = defaultdict(lambda: [0, 0, 0])
    for sess in sessions.values():
        for _, model, ti, to in sess["calls"]:
            agg = by_model[model]
            agg[0] += ti
            agg[1] += to
            agg[2] += 1
    lines = [
        f"{'model':<28} {'calls':>6} {'inputTok':>13} {'outTok':>8}"
        f" {'cr@98%cache':>12} {'cr ceiling':>11}"
    ]
    total_cal = total_ceil = 0.0
    n_calls = 0
    for model, (ti, to, n) in sorted(by_model.items(), key=lambda kv: -kv[1][0]):
        pr = price_for(model)
        out_cr = to / 1e6 * pr["out"]
        cal = (
            ti / 1e6 * ((1 - CACHE_RATIO) * pr["in"] + CACHE_RATIO * pr["cache"])
            + out_cr
        )
        ceil = ti / 1e6 * pr["in"] + out_cr
        total_cal += cal
        total_ceil += ceil
        n_calls += n
        lines.append(
            f"{model:<28} {n:>6} {ti:>13,} {to:>8,} {cal:>12,.1f} {ceil:>11,.1f}"
        )
    lines.append(
        f"{'TOTAL':<28} {n_calls:>6} {'':>13} {'':>8} "
        f"{total_cal:>12,.1f} {total_ceil:>11,.1f}"
        f"   (${total_cal / 100:,.2f} … ${total_ceil / 100:,.2f})"
    )
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--altimeter", action="store_true", help="altimeter only")
    args = ap.parse_args()
    path = Path(
        args.path or os.environ.get("COPILOT_OTEL_FILE_EXPORTER_PATH", DEFAULT_PATH)
    )
    if not path.is_file():
        print(f"no tap file at {path} — arm with otel-tap-on.sh and restart VS Code")
        return

    archive = rotate_if_big(path)
    if archive:
        print(f"rotated: {archive.name} (reading archive this run)")
        path = archive

    sessions = join_sessions(load_events(path))
    for sid, sess in sessions.items():
        record_compactions(CALIB_PATH, sid, detect_compactions(sess["turns"]))

    live = live_session_ids(sessions)
    if not args.altimeter:
        size_mb = path.stat().st_size / 1e6
        print(
            f"tap: {path} ({size_mb:.1f} MB)"
            f"  sessions: {len(sessions)} ({len(live)} live)"
        )
        print("\n".join(usage_table(sessions)))
        print()
        print("\n".join(sessions_table(sessions, live, session_titles(sessions))))
        print()
    print("\n".join(altimeter_lines(sessions)))


if __name__ == "__main__":
    main()
