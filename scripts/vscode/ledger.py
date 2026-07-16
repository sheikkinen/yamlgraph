#!/usr/bin/env python3
"""Metabolism: requests, tokens, models, and estimated cost over time.

Spike (scripts/vscode, 2026-07-16). Parses every chatSessions/*.jsonl
across ALL workspaces; attributes each request by its own timestamp
(not the session creation date); rolls up per day and per model.

Cost model (price sheet from debug-logs models.json, per 1M tokens):
input 1000 / output 5000 / cache-read 100 units. promptTokens
conflates cache reads with fresh input, so cost is reported as a RANGE:
worst case (all fresh input) to best case (all-but-first-turn cached).
The truth lives between; calibrate with --anchor if you know one real
spend figure.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"

REQ_SPLIT = re.compile(r'"requestId":"')
TS_RE = re.compile(r'"timestamp":(\d{13})')
MODEL_RE = re.compile(r'"modelId":"([^"]+)"')
TOK_RE = re.compile(r'"promptTokens":(\d+),"outputTokens":(\d+)')

# units per 1M tokens (models.json billing.token_prices, Fable default)
PRICE_IN, PRICE_OUT, PRICE_CACHE = 1000, 5000, 100


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
            yield (
                datetime.fromtimestamp(int(ts.group(1)) / 1000),
                (model.group(1).removeprefix("copilot/") if model else "?"),
                int(tok.group(1)),
                int(tok.group(2)),
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="trailing days to print")
    ap.add_argument("--by-model", action="store_true")
    args = ap.parse_args()

    daily = defaultdict(lambda: [0, 0, 0])
    by_model = defaultdict(lambda: [0, 0, 0])
    for when, model, p, o in iter_requests():
        d = when.date().isoformat()
        for agg in (daily[d], by_model[model]):
            agg[0] += p
            agg[1] += o
            agg[2] += 1

    def cost_range(p: int, o: int, r: int) -> tuple[float, float]:
        out = o / 1e6 * PRICE_OUT
        worst = p / 1e6 * PRICE_IN + out
        # best case: only the per-request NEW tokens are fresh; approximate
        # new-per-request by the mean turn delta (crude: 10% fresh).
        best = p / 1e6 * (0.1 * PRICE_IN + 0.9 * PRICE_CACHE) + out
        return best, worst

    print(
        f"{'day':<12} {'req':>5} {'promptTok':>13} {'outTok':>9} {'units(best–worst)':>22}"
    )
    for d in sorted(daily)[-args.days :]:
        p, o, r = daily[d]
        lo, hi = cost_range(p, o, r)
        print(f"{d:<12} {r:>5} {p:>13,} {o:>9,} {lo:>10,.0f}–{hi:<10,.0f}")

    tp = sum(v[0] for v in daily.values())
    to = sum(v[1] for v in daily.values())
    tr = sum(v[2] for v in daily.values())
    lo, hi = cost_range(tp, to, tr)
    print(f"{'ALL-TIME':<12} {tr:>5} {tp:>13,} {to:>9,} {lo:>10,.0f}–{hi:<10,.0f}")

    if args.by_model:
        print(f"\n{'model':<32} {'req':>6} {'promptTok':>14} {'outTok':>10}")
        for m, (p, o, r) in sorted(by_model.items(), key=lambda kv: -kv[1][0]):
            print(f"{m:<32} {r:>6} {p:>14,} {o:>10,}")


if __name__ == "__main__":
    main()
