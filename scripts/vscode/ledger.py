#!/usr/bin/env python3
"""Metabolism: requests, tokens, models, and estimated cost over time.

Spike (scripts/vscode, 2026-07-16). Parses every chatSessions/*.jsonl
across ALL workspaces; attributes each request by its own timestamp
(not the session creation date); rolls up per period, per day, per model.

Credits: chatSessions DOES persist exact per-request `copilotCredits`
(discovered 2026-08-29, FR-898 — requires full patch replay; see
session_ledger.py for the per-session accountability view). This
script predates that discovery and still ESTIMATES from the
per-model price sheets in debug-logs models.json (credits per 1M
tokens; 1 credit = $0.01, calibrated 2026-07-16). Reported as a
best–worst range because promptTokens conflates cache reads with
fresh input; best assumes 98% cache reads (fresh tokens also pay one
cache write), worst assumes all-fresh. Anchor (FR-900, 2026-08-28):
August 2026 invoice $7,500 across two devices; this device's best
bound $3,927 ≈ 50% share — within ~5%. The relative attribution
(which day/model/repo/arc) is solid regardless.
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
UNKNOWN_MODEL_PRICE = {"in": 1000, "out": 5000, "cache": 100, "cache_w": 1250}
# 98% cache ratio: reconciles the corrected pricing with the August 2026
# invoice anchor (FR-900). The prior anchor-2 "pure-cache 814 vs 820.5"
# claim was computed under the cache_price=0 bug and is void.
CACHE_RATIO_BEST = 0.98


def parse_price_sheet(data) -> dict[str, dict[str, int]]:
    """Per-model-family prices from a models.json payload (FR-900).

    Schema keys: input_price, output_price, cache_read_price,
    cache_write_price (the old cache_price key never existed — reading it
    priced all cache reads at 0, a ~5× best-bound underestimate).
    """
    prices: dict[str, dict[str, int]] = {}
    items = data if isinstance(data, list) else data.get("data", data.get("models", []))
    for item in items:
        family = item.get("capabilities", {}).get("family")
        tp = item.get("billing", {}).get("token_prices", {}).get("default", {})
        if family and tp:
            prices[family] = {
                "in": tp.get("input_price", 0),
                "out": tp.get("output_price", 0),
                "cache": tp.get("cache_read_price", 0),
                "cache_w": tp.get("cache_write_price", 0),
            }
    return prices


def load_prices() -> dict[str, dict[str, int]]:
    """Prices from the newest models.json anywhere (empty if none readable)."""
    candidates = sorted(
        WS_STORAGE.glob("*/GitHub.copilot-chat/debug-logs/*/models.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        return {}
    try:
        data = json.loads(candidates[-1].read_text())
    except (OSError, ValueError):
        return {}
    return parse_price_sheet(data)


def credits(
    prices: dict[str, dict[str, int]], model: str, p: int, o: int
) -> tuple[float, float]:
    """(best, worst) in credits. Best: 98% of prompt tokens at cache-read
    price, the fresh 2% at input + one cache write. Worst: all-fresh,
    no write term (ceiling semantics)."""
    pr = prices.get(model, UNKNOWN_MODEL_PRICE)
    out = o / 1e6 * pr["out"]
    worst = p / 1e6 * pr["in"] + out
    fresh = 1 - CACHE_RATIO_BEST
    best = (
        p
        / 1e6
        * (fresh * (pr["in"] + pr.get("cache_w", 0)) + CACHE_RATIO_BEST * pr["cache"])
        + out
    )
    return best, worst


def workspace_name(ws_dir: Path) -> str:
    """Workspace folder basename from workspace.json; hash prefix when absent."""
    try:
        data = json.loads((ws_dir / "workspace.json").read_text())
    except (OSError, ValueError):
        return ws_dir.name[:8]
    uri = data.get("folder") or data.get("workspace") or data.get("configuration") or ""
    return Path(str(uri)).name or ws_dir.name[:8]


def iter_requests():
    if not WS_STORAGE.is_dir():  # machine without VS Code stores (e.g. CI)
        return
    for ws_dir in WS_STORAGE.iterdir():
        chats = sorted(ws_dir.glob("chatSessions/*.jsonl"))
        if not chats:
            continue
        repo = workspace_name(ws_dir)
        for chat in chats:
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
                    chat.stem,  # session id (FR-739 AC-04 seam reconciliation)
                    repo,  # workspace attribution (FR-900)
                )


def tap_seam_report() -> list[str]:
    """FR-739 AC-04: per-session estimate-vs-exact over the tap window.

    Pre-tap history stays rounds×-estimated; post-seam data has an exact
    witness in the tap. Reconciled per-session over sessions present in
    BOTH stores — per-total would be guaranteed noise (other machines,
    pre-restart turns absent from the tap by construction).
    """
    import os
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import tap

    path = Path(os.environ.get("COPILOT_OTEL_FILE_EXPORTER_PATH", tap.DEFAULT_PATH))
    if not path.is_file():
        return ["no tap file — seam unavailable (estimates only)"]
    events = tap.load_events(path)
    seam = datetime.fromtimestamp(min(e["ts"] for e in events if e["ts"]))
    sessions = tap.join_sessions(events)
    exact = {sid: sum(ti for _, _, ti, _ in s["calls"]) for sid, s in sessions.items()}
    est: dict[str, int] = {}
    for when, _, p, _, sid, _repo in iter_requests():
        if when >= seam and sid in exact:
            est[sid] = est.get(sid, 0) + p
    lines = [
        f"seam: {seam:%Y-%m-%d %H:%M} — pre-seam = rounds× estimate,"
        f" post-seam = tap exact",
        f"{'session':<10} {'est(rounds×)':>14} {'exact(tap)':>12} {'ratio':>6}  title",
    ]
    titles = tap.session_titles(exact)
    for row in tap.reconcile(est, exact):
        lines.append(
            f"{row['session'][:8]:<10} {row['est']:>14,} {row['exact']:>12,}"
            f" {row['ratio']:>6.2f}  {titles.get(row['session'], '')[:44]}"
        )
    return lines


def _print_by_model(prices: dict, by_model_period: dict) -> None:
    for name in ("today", "this month", "previous month"):
        models = by_model_period[name]
        if not models:
            continue
        print(f"\n== {name}, by model ==")
        for m, (p, o, r) in sorted(models.items(), key=lambda kv: -kv[1][0]):
            lo, hi = credits(prices, m, p, o)
            print(
                f"  {m:<28} {r:>5} req {p:>13,} in {o:>10,} out"
                f"  ≈{lo:,.0f}–{hi:,.0f} cr (${lo / 100:,.0f}–${hi / 100:,.0f})"
            )


def _print_by_repo(prices: dict, by_repo: dict, report_month: str) -> None:
    print(f"\n== {report_month}, by repo × model ==")
    rows = sorted(
        (
            (*credits(prices, model, p, o), repo, model, r, p, o)
            for (repo, model), (p, o, r) in by_repo.items()
        ),
        reverse=True,
    )
    repo_tot: dict[str, list] = defaultdict(lambda: [0, 0.0, 0.0])
    for lo, hi, repo, model, r, p, o in rows:
        print(
            f"  {repo[:30]:<31} {model[:26]:<27} {r:>5} req {p:>14,} in"
            f" {o:>10,} out  ≈{lo:,.0f}–{hi:,.0f} cr"
        )
        tot = repo_tot[repo]
        tot[0] += r
        tot[1] += lo
        tot[2] += hi
    print("\n  per-repo totals:")
    for repo, (r, lo, hi) in sorted(repo_tot.items(), key=lambda kv: -kv[1][1]):
        print(
            f"  {repo[:30]:<31} {r:>5} req  ≈{lo:,.0f}–{hi:,.0f} cr"
            f" (${lo / 100:,.0f}–${hi / 100:,.0f})"
        )
    tn = sum(t[0] for t in repo_tot.values())
    tb = sum(t[1] for t in repo_tot.values())
    tw = sum(t[2] for t in repo_tot.values())
    print(
        f"  TOTAL: {tn} req, ≈{tb:,.0f}–{tw:,.0f} cr"
        f" (${tb / 100:,.0f}–${tw / 100:,.0f})"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="also print N trailing days")
    ap.add_argument("--by-model", action="store_true")
    ap.add_argument("--by-repo", action="store_true", help="repo × model cost (FR-900)")
    ap.add_argument("--month", help="YYYY-MM scope for --by-repo (default: this month)")
    ap.add_argument("--tap", action="store_true", help="seam reconciliation (FR-739)")
    args = ap.parse_args()

    prices = load_prices()

    today = date.today()
    this_month = today.strftime("%Y-%m")
    prev_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    daily = defaultdict(lambda: [0, 0, 0])
    period_names = ("today", "this month", "previous month", "all-time")
    by_model_period: dict[str, dict[str, list]] = {
        k: defaultdict(lambda: [0, 0, 0]) for k in period_names
    }
    report_month = args.month or this_month
    by_repo: dict[tuple[str, str], list] = defaultdict(lambda: [0, 0, 0])
    for when, model, p, o, _sid, repo in iter_requests():
        d = when.date()
        if d.strftime("%Y-%m") == report_month:
            agg = by_repo[(repo, model)]
            agg[0] += p
            agg[1] += o
            agg[2] += 1
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
        "credits: 1 cr = $0.01; billed prompt = tool-call rounds × recorded context;\n"
        "range = 98%-cached incl. cache writes (FR-900 invoice anchor)"
        " .. all-fresh (ceiling)"
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
        lo = sum(credits(prices, m, v[0], v[1])[0] for m, v in models.items())
        hi = sum(credits(prices, m, v[0], v[1])[1] for m, v in models.items())
        print(
            f"{name:<16} {tr:>6} {tp:>14,} {to:>10,} {lo:>9,.0f}–{hi:<9,.0f}"
            f" ${lo / 100:>6,.0f}–${hi / 100:<6,.0f}"
        )

    if args.by_model:
        _print_by_model(prices, by_model_period)

    if args.by_repo:
        _print_by_repo(prices, by_repo, report_month)

    if args.days:
        print(f"\n{'day':<12} {'req':>5} {'promptTok':>13} {'outTok':>9}")
        for d in sorted(daily)[-args.days :]:
            p, o, r = daily[d]
            print(f"{d:<12} {r:>5} {p:>13,} {o:>9,}")

    if args.tap:
        print()
        print("\n".join(tap_seam_report()))


if __name__ == "__main__":
    main()
