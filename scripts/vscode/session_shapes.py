#!/usr/bin/env python3
"""FR-884: session task-shape inventory — the ungoverned-surface census.

Spike (scripts/vscode, 2026-08-25). Read-only, stdlib-only. Joins, per
session id, within a frozen window:

- chatSessions/*.jsonl  — per-request timestamp, modelId, tokens, title;
- debug-logs models.json price sheets (via ledger.load_prices);
- .github/hooks/logs/audit.jsonl — tool-call profile per session.

Missing optional sources are reported as unavailable (None), never
silently substituted (AC-03). Cost figures are best/worst ranges —
promptTokens conflates cache reads with fresh input (ledger anchor:
agent turns run ~98% cached).

Usage:
    python3 scripts/vscode/session_shapes.py                 # table
    python3 scripts/vscode/session_shapes.py --json          # rows
    python3 scripts/vscode/session_shapes.py --strata        # 5 top + 5 random
    python3 scripts/vscode/session_shapes.py --transcript ID # raw text dump
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
AUDIT_DEFAULT = Path(__file__).resolve().parents[2] / ".github/hooks/logs/audit.jsonl"
FROZEN_WINDOW = ("2026-06-26", "2026-08-25")  # FR-884 R-2, Europe/Helsinki local

REQ_SPLIT = re.compile(r'"requestId":\s*"')
TS_RE = re.compile(r'"timestamp":\s*(\d{13})')
MODEL_RE = re.compile(r'"modelId":\s*"([^"]+)"')
TOK_RE = re.compile(r'"promptTokens":\s*(\d+),\s*"outputTokens":\s*(\d+)')
TITLE_RE = re.compile(r'"customTitle":\s*"([^"]{1,200})"')

# ledger.py assumption: milli-credits per 1M tokens, fable = ceiling
UNKNOWN_MODEL_PRICE = {"in": 1000, "out": 5000, "cache": 100}
CACHE_RATIO_BEST = 0.98


def parse_session(path: Path) -> dict:
    """Extract requests (ts, model, ptok, otok) from one chatSessions file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"session_id": path.stem, "title": None, "requests": []}
    title = TITLE_RE.search(text[:4000])
    requests: list[tuple[int, str, int, int]] = []
    for chunk in REQ_SPLIT.split(text)[1:]:
        ts = TS_RE.search(chunk)
        model = MODEL_RE.search(chunk)
        tok = TOK_RE.search(chunk)
        if not (ts and model):
            continue
        ptok, otok = (int(tok.group(1)), int(tok.group(2))) if tok else (0, 0)
        requests.append((int(ts.group(1)), model.group(1), ptok, otok))
    return {
        "session_id": path.stem,
        "title": title.group(1) if title else None,
        "requests": requests,
    }


def _window_ms(window: tuple[str, str]) -> tuple[int, int]:
    start = datetime.fromisoformat(window[0])
    end = datetime.fromisoformat(window[1]) + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _cost_range(
    models: Counter, ptok_by_model: Counter, otok_by_model: Counter, prices: dict
) -> tuple[float, float]:
    best = worst = 0.0
    for model in models:
        price = prices.get(model)
        if price is None:  # prefix match: modelId vs price-sheet family keys
            price = next(
                (
                    p
                    for fam, p in prices.items()
                    if model.startswith(fam) or fam.startswith(model)
                ),
                UNKNOWN_MODEL_PRICE,
            )
        pt, ot = ptok_by_model[model], otok_by_model[model]
        fresh = pt * price["in"] + ot * price["out"]
        cached = (
            pt
            * (CACHE_RATIO_BEST * price["cache"] + (1 - CACHE_RATIO_BEST) * price["in"])
            + ot * price["out"]
        )
        best += cached / 1e9  # milli-credits/1M tokens → credits
        worst += fresh / 1e9
    return best, worst


def _audit_counts(audit_path: Path | None) -> dict[str, Counter] | None:
    """Tool-call counts per session id; None when the source is unavailable."""
    if audit_path is None or not audit_path.is_file():
        return None
    counts: dict[str, Counter] = {}
    with audit_path.open(errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            sid, tool = entry.get("session_id"), entry.get("tool")
            if sid and tool:
                counts.setdefault(sid, Counter())[tool] += 1
    return counts


def inventory(
    ws_storage: Path = WS_STORAGE,
    window: tuple[str, str] = FROZEN_WINDOW,
    prices: dict | None = None,
    audit_path: Path | None = AUDIT_DEFAULT,
) -> list[dict]:
    """One row per session with in-window requests, joined by session id."""
    lo, hi = _window_ms(window)
    audit = _audit_counts(audit_path)
    rows = []
    for chat in sorted(ws_storage.glob("*/chatSessions/*.jsonl")):
        sess = parse_session(chat)
        in_window = [r for r in sess["requests"] if lo <= r[0] < hi]
        if not in_window:
            continue
        models: Counter = Counter()
        ptok_by: Counter = Counter()
        otok_by: Counter = Counter()
        for _ts, model, ptok, otok in in_window:
            models[model] += 1
            ptok_by[model] += ptok
            otok_by[model] += otok
        row = {
            "session_id": sess["session_id"],
            "workspace": chat.parts[-3],
            "title": sess["title"],
            "requests": len(in_window),
            "first_ts": min(r[0] for r in in_window),
            "last_ts": max(r[0] for r in in_window),
            "prompt_tokens": sum(ptok_by.values()),
            "output_tokens": sum(otok_by.values()),
            "models": dict(models),
            "tool_calls": (
                dict(audit.get(sess["session_id"], Counter()))
                if audit is not None
                else None
            ),
            "path": str(chat),
        }
        if prices is not None:
            row["cost_range"] = _cost_range(models, ptok_by, otok_by, prices)
        rows.append(row)
    return rows


def select_strata(
    rows: list[dict], top_n: int = 5, random_n: int = 5, seed: int = 884
) -> tuple[list[dict], list[dict]]:
    """AC-02 sampling: top-N by token volume + N random from the remainder."""
    ranked = sorted(
        rows, key=lambda r: r["prompt_tokens"] + r["output_tokens"], reverse=True
    )
    top = ranked[:top_n]
    pool = ranked[top_n:]
    rand = random.Random(seed).sample(pool, min(random_n, len(pool)))  # noqa: S311  # CONF-416
    return top, rand


def _collect_text(node: object, out: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("text", "value") and isinstance(value, str) and value.strip():
                out.append(value)
            else:
                _collect_text(value, out)
    elif isinstance(node, list):
        for item in node:
            _collect_text(item, out)


def _descend(state: dict, keys: list) -> object:
    """Walk to the parent of the last key, creating intermediates."""
    node: object = state
    for key in keys[:-1]:
        if isinstance(node, dict):
            node = node.setdefault(key, {})
        elif isinstance(node, list):
            while len(node) <= key:
                node.append({})
            node = node[key]
    return node


def replay(path: Path) -> dict | None:
    """Reconstruct session state from a chatSessions op-log.

    Line format: kind 0 = snapshot (v), kind 1 = set at path k,
    kind 2 = extend list at path k. Returns None when no kind-0
    snapshot is present (not an op-log).
    """
    state: dict | None = None
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return None
    with fh:
        for line in fh:
            try:
                op = json.loads(line)
            except ValueError:
                continue
            kind = op.get("kind") if isinstance(op, dict) else None
            if kind == 0:
                state = op["v"]
                continue
            if state is None or kind not in (1, 2):
                continue
            keys = op.get("k") or []
            if not keys or "v" not in op:
                continue
            node = _descend(state, keys)
            last = keys[-1]
            if kind == 1:
                if isinstance(node, list):
                    while len(node) <= last:
                        node.append(None)
                    node[last] = op["v"]
                elif isinstance(node, dict):
                    node[last] = op["v"]
            else:  # kind == 2: extend
                target = node.get(last) if isinstance(node, dict) else node[last]
                if not isinstance(target, list):
                    target = []
                    if isinstance(node, dict):
                        node[last] = target
                    else:
                        node[last] = target
                value = op["v"]
                target.extend(value if isinstance(value, list) else [value])
    return state


def turn_skeleton(state: dict | None, cap: int = 300) -> list[dict]:
    """Per-turn rows (index, user, agent head, prompt_tokens) from replayed state."""
    turns = []
    for i, req in enumerate((state or {}).get("requests") or []):
        if not isinstance(req, dict):
            continue
        parts: list[str] = []
        total = 0
        for part in req.get("response") or []:
            if isinstance(part, dict):
                value = part.get("value")
                if isinstance(value, dict):
                    value = value.get("value")
                if isinstance(value, str) and value.strip():
                    parts.append(value)
                    total += len(value)
                    if total > cap:
                        break
        turns.append(
            {
                "index": i,
                "user": ((req.get("message") or {}).get("text") or "")[:500],
                "agent": "".join(parts)[:cap],
                "prompt_tokens": req.get("promptTokens"),
            }
        )
    return turns


def extract_transcript(path: Path) -> str:
    """Human-visible narrative (message text + response values) of a session."""
    out: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    try:
        _collect_text(json.loads(text), out)
    except ValueError:
        for line in text.splitlines():
            try:
                _collect_text(json.loads(line), out)
            except ValueError:
                continue
    return "\n".join(out)


def _fmt_row(row: dict) -> str:
    models = ",".join(sorted(row["models"], key=row["models"].get, reverse=True)[:2])
    day = datetime.fromtimestamp(row["first_ts"] / 1000).strftime("%m-%d")
    cost = ""
    if "cost_range" in row:
        best, worst = row["cost_range"]
        cost = f"  {best:7.1f}-{worst:<7.1f}cr"
    tools = sum(row["tool_calls"].values()) if row["tool_calls"] else 0
    return (
        f"  {day}  {row['session_id'][:8]}  req={row['requests']:<4} "
        f"ptok={row['prompt_tokens'] / 1e6:7.1f}M otok={row['output_tokens'] / 1e3:6.0f}K "
        f"tools={tools:<4}{cost}  {models}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--window", nargs=2, metavar=("START", "END"), default=list(FROZEN_WINDOW)
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strata", action="store_true", help="print AC-02 sample (5 top + 5 random)"
    )
    parser.add_argument("--seed", type=int, default=884)
    parser.add_argument(
        "--transcript", metavar="SESSION_ID", help="dump transcript text to stdout"
    )
    args = parser.parse_args()

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from ledger import load_prices  # noqa: PLC0415  # sibling-spike reuse, CLI only

        prices = load_prices()
    except Exception:
        prices = {}

    window = (args.window[0], args.window[1])
    rows = inventory(window=window, prices=prices or None)

    if args.transcript:
        for row in rows:
            if row["session_id"].startswith(args.transcript):
                print(extract_transcript(Path(row["path"])))
                return
        sys.exit(f"no session in window matching {args.transcript!r}")

    if args.json:
        print(json.dumps(rows, indent=1))
        return

    rows.sort(key=lambda r: r["prompt_tokens"] + r["output_tokens"], reverse=True)
    total_pt = sum(r["prompt_tokens"] for r in rows)
    print(
        f"== sessions in window {window[0]}..{window[1]}: {len(rows)}, prompt tokens {total_pt / 1e6:.0f}M =="
    )
    if args.strata:
        top, rand = select_strata(rows, seed=args.seed)
        print("-- stratum: top-5 by token volume --")
        for row in top:
            print(_fmt_row(row))
        print(f"-- stratum: random-5 (seed {args.seed}) --")
        for row in rand:
            print(_fmt_row(row))
    else:
        for row in rows[:40]:
            print(_fmt_row(row))
        audit_state = (
            "joined" if rows and rows[0]["tool_calls"] is not None else "UNAVAILABLE"
        )
        print(f"(audit trail: {audit_state}; cost unit: estimated credits, best-worst)")


if __name__ == "__main__":
    main()
