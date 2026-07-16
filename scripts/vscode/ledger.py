#!/usr/bin/env python3
"""Metabolism: requests, tokens, models, and estimated cost over time.

Spike (scripts/vscode, 2026-07-16). Parses every chatSessions/*.jsonl
across ALL workspaces; attributes each request by its own timestamp
(not the session creation date); rolls up per period, per day, per model.

Credits: no balance/usage history is persisted locally (verified — the
UI's number is fetched live), so credits are ESTIMATED from the
per-model price sheets in debug-logs models.json. UNIT ASSUMPTION:
prices are milli-credits per 1M tokens (fable input 1000 → 1.0
credit/1M). Reported as a best–worst range because promptTokens
conflates cache reads (~10× cheaper) with fresh input; best assumes
90% cache, worst assumes all-fresh. Calibrate against a known spend
figure before trusting absolute numbers; the relative attribution
(which day/model/arc) is solid regardless.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"

REQ_SPLIT = re.compile(r'"requestId":"')
TS_RE = re.compile(r'"timestamp":(\d{13})')
MODEL_RE = re.compile(r'"modelId":"([^"]+)"')
TOK_RE = re.compile(r'"promptTokens":(\d+),"outputTokens":(\d+)')

# price assumption for models absent from the sheet: fable rates — the
# HIGHEST tier, so unknown models overestimate (conservative for a ceiling)
UNKNOWN_MODEL_PRICE = {"in": 1000, "out": 5000, "cache": 100}
# ANCHOR-2 (820.5 cr turn, 11 rounds × 695K): pure-cache pricing of the
# full turn hit 814 cr vs 820.5 actual → agent turns run ≈98% cached.
CACHE_RATIO_BEST = 0.98  # calibrated; worst bound keeps all-fresh


def load_prices() -> dict[str, dict[str, int]]:
    """Per-model-family prices from the newest models.json anywhere."""
    candidates = sorted(
        WS_STORAGE.glob("*/GitHub.copilot-chat/debug-logs/*/models.json"),
        key=lambda p: p.stat().st_mtime,
    )
    prices: dict[str, dict[str, int]] = {}
    if not candidates:
        return prices
    try:
        data = json.loads(candidates[-1].read_text())
    except (OSError, ValueError):
        return prices
    items = data if isinstance(data, list) else data.get("data", data.get("models", []))
    for item in items:
        family = item.get("capabilities", {}).get("family")
        tp = item.get("billing", {}).get("token_prices", {}).get("default", {})
        if family and tp:
            prices[family] = {
                "in": tp.get("input_price", 0),
                "out": tp.get("output_price", 0),
                "cache": tp.get("cache_price", 0),
            }
    return prices


def iter_requests():
    for chat in WS_STORAGE.glob("*/chatSessions/*.jsonl"):
        try:
            text = chat.read_text(errors="replace")
        except OSError:
            continue
        for chunk in REQ_SPLIT.split(text)[1:]:
            head = chunk[:400_000]
            ts = TS_RE.search(head)
            tok = TOK_RE.search(head)
            if not (ts and tok):
                continue
            model = MODEL_RE.search(head)
            # ANCHOR-2 finding (2026-07-16, 820.5 cr turn): promptTokens
            # records the LAST round's context only; every tool-call round
            # re-bills the full context. Billed prompt ≈ rounds × recorded.
            rounds = max(1, len(re.findall(r'"toolCalls":\[', chunk)))
            yield (
                datetime.fromtimestamp(int(ts.group(1)) / 1000),
                (model.group(1).removeprefix("copilot/") if model else "?"),
                int(tok.group(1)) * rounds,
                int(tok.group(2)) * rounds,
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="also print N trailing days")
    ap.add_argument("--by-model", action="store_true")
    args = ap.parse_args()

    prices = load_prices()

    def credits(model: str, p: int, o: int) -> tuple[float, float]:
        """(best, worst) in credits. CALIBRATED 2026-07-16: a single session
        showing 2702.9 credits billed $27.09 → 1 credit = $0.01, and the
        models.json prices ARE credits per 1M tokens (fable: $10/M in,
        $50/M out, $1/M cache-read — frontier-consistent, corroborating)."""
        pr = prices.get(model, UNKNOWN_MODEL_PRICE)
        out = o / 1e6 * pr["out"]
        worst = p / 1e6 * pr["in"] + out
        best = (
            p
            / 1e6
            * ((1 - CACHE_RATIO_BEST) * pr["in"] + CACHE_RATIO_BEST * pr["cache"])
            + out
        )
        return best, worst

    today = date.today()
    this_month = today.strftime("%Y-%m")
    prev_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    daily = defaultdict(lambda: [0, 0, 0])
    period_names = ("today", "this month", "previous month", "all-time")
    by_model_period: dict[str, dict[str, list]] = {
        k: defaultdict(lambda: [0, 0, 0]) for k in period_names
    }
    for when, model, p, o in iter_requests():
        d = when.date()
        buckets = ["all-time"]
        if d == today:
            buckets.append("today")
        if d.strftime("%Y-%m") == this_month:
            buckets.append("this month")
        elif d.strftime("%Y-%m") == prev_month:
            buckets.append("previous month")
        for b in buckets:
            agg = by_model_period[b][model]
            agg[0] += p
            agg[1] += o
            agg[2] += 1
        agg = daily[d.isoformat()]
        agg[0] += p
        agg[1] += o
        agg[2] += 1

    print(
        "credits: 1 cr = $0.01; billed prompt = tool-call rounds × recorded context "
        "(anchor-2: 11×695K turn = 820.5 cr, pure-cache model hit 814);\n"
        "range = 98%-cached (calibrated) .. all-fresh (ceiling)"
    )
    print("tokens  = exact from chatSessions request records\n")
    print(
        f"{'period':<16} {'req':>6} {'promptTok':>14} {'outTok':>10}"
        f" {'est. credits':>19} {'est. USD':>15}"
    )
    for name in period_names:
        models = by_model_period[name]
        tp = sum(v[0] for v in models.values())
        to = sum(v[1] for v in models.values())
        tr = sum(v[2] for v in models.values())
        lo = sum(credits(m, v[0], v[1])[0] for m, v in models.items())
        hi = sum(credits(m, v[0], v[1])[1] for m, v in models.items())
        print(
            f"{name:<16} {tr:>6} {tp:>14,} {to:>10,} {lo:>9,.0f}–{hi:<9,.0f}"
            f" ${lo / 100:>6,.0f}–${hi / 100:<6,.0f}"
        )

    if args.by_model:
        for name in ("today", "this month", "previous month"):
            models = by_model_period[name]
            if not models:
                continue
            print(f"\n== {name}, by model ==")
            for m, (p, o, r) in sorted(models.items(), key=lambda kv: -kv[1][0]):
                lo, hi = credits(m, p, o)
                print(
                    f"  {m:<28} {r:>5} req {p:>13,} in {o:>10,} out"
                    f"  ≈{lo:,.0f}–{hi:,.0f} cr (${lo / 100:,.0f}–${hi / 100:,.0f})"
                )

    if args.days:
        print(f"\n{'day':<12} {'req':>5} {'promptTok':>13} {'outTok':>9}")
        for d in sorted(daily)[-args.days :]:
            p, o, r = daily[d]
            print(f"{d:<12} {r:>5} {p:>13,} {o:>9,}")


if __name__ == "__main__":
    main()
