#!/usr/bin/env python3
"""Tap reader: exact per-call usage from the Copilot OTel file tap.

Spike (scripts/vscode, 2026-07-16). Parses the JSONL written by the
extension's OTel file exporter (armed via otel-tap-on.sh). Unlike
chatSessions — which records only the LAST round of a turn — the tap
logs EVERY inference call (`gen_ai.client.inference.operation.details`),
including side-model utility calls (gpt-4o-mini titling) invisible
elsewhere. Volume is exact; cost applies the two-anchor calibration
(1 cr = $0.01; agent turns ≈98% cached; all-fresh printed as ceiling).

Verified 2026-07-16: four fable turns at ~740K input each, per-round,
matching the anchor-2 billing model at source.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path.home() / "src/yamlgraph/tmp/copilot-otel.jsonl"

# calibrated pricing (credits per 1M tokens; 1 credit = $0.01)
PRICES = {
    "claude-fable-5": {"in": 1000, "out": 5000, "cache": 100},
    "claude-opus": {"in": 500, "out": 2500, "cache": 50},
    "gpt-4o-mini": {"in": 0, "out": 0, "cache": 0},  # utility calls: unbilled tier
}
DEFAULT_PRICE = {"in": 1000, "out": 5000, "cache": 100}
CACHE_RATIO = 0.98  # anchor-2 calibration


def price_for(model: str) -> dict[str, int]:
    for prefix, price in PRICES.items():
        if model.startswith(prefix):
            return price
    return DEFAULT_PRICE


def attrs_of(record: dict) -> dict:
    a = record.get("attributes") or record.get("attrs") or {}
    if isinstance(a, list):  # OTel KeyValue form
        out = {}
        for kv in a:
            v = kv.get("value")
            out[kv.get("key")] = next(iter(v.values())) if isinstance(v, dict) else v
        return out
    return a


def when(record: dict) -> datetime | None:
    hr = record.get("hrTime")
    if isinstance(hr, list) and len(hr) == 2:
        return datetime.fromtimestamp(hr[0] + hr[1] / 1e9)
    return None


def main() -> None:
    path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("COPILOT_OTEL_FILE_EXPORTER_PATH", DEFAULT_PATH)
    )
    if not path.is_file():
        print(f"no tap file at {path} — arm with otel-tap-on.sh and restart VS Code")
        return

    calls = []  # (time, model, in, out)
    turns = tools = 0
    for line in path.open(errors="replace"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        a = attrs_of(rec)
        event = a.get("event.name", "")
        if event == "copilot_chat.agent.turn":
            turns += 1
        elif event == "copilot_chat.tool.call":
            tools += 1
        elif event == "gen_ai.client.inference.operation.details":
            ti = a.get("gen_ai.usage.input_tokens")
            to = a.get("gen_ai.usage.output_tokens")
            model = (
                a.get("gen_ai.response.model") or a.get("gen_ai.request.model") or "?"
            )
            if isinstance(ti, int | float):
                calls.append((when(rec), str(model), int(ti), int(to or 0)))

    by_model = defaultdict(lambda: [0, 0, 0])
    for _, model, ti, to in calls:
        agg = by_model[model]
        agg[0] += ti
        agg[1] += to
        agg[2] += 1

    size_mb = path.stat().st_size / 1e6
    times = [t for t, *_ in calls if t]
    span = (
        f"{min(times).strftime('%m-%d %H:%M')} → {max(times).strftime('%H:%M')}"
        if times
        else "?"
    )
    print(f"tap: {path} ({size_mb:.1f} MB)  window: {span}")
    print(f"inference calls: {len(calls)}  agent turns: {turns}  tool calls: {tools}\n")

    print(
        f"{'model':<28} {'calls':>6} {'inputTok':>13} {'outTok':>8} {'cr@98%cache':>12} {'cr ceiling':>11}"
    )
    total_cal = total_ceil = 0.0
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
        print(f"{model:<28} {n:>6} {ti:>13,} {to:>8,} {cal:>12,.1f} {ceil:>11,.1f}")
    print(
        f"{'TOTAL':<28} {len(calls):>6} {'':>13} {'':>8} "
        f"{total_cal:>12,.1f} {total_ceil:>11,.1f}"
        f"   (${total_cal / 100:,.2f} … ${total_ceil / 100:,.2f})"
    )
    if size_mb > 100:
        print(f"\n⚠ tap file is {size_mb:.0f} MB — rotate or disarm (otel-tap-off.sh)")


if __name__ == "__main__":
    main()
