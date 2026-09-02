#!/usr/bin/env python3
"""Session accountability ledger over VS Code Copilot chat session stores (FR-898).

Usage:
    python3 scripts/vscode/session_ledger.py <session.jsonl> [more.jsonl ...]
    python3 scripts/vscode/session_ledger.py --csv --all-workspaces > all.csv
    python3 scripts/vscode/session_ledger.py --csv --session <id>
    python3 scripts/vscode/session_ledger.py --csv --all-workspaces --window 24

Modes:
    default  human-readable markdown, one section per request
    --csv    one row per request, session details repeated on every row
             (pivot-ready; concatenate sessions by passing multiple files
             or --all-workspaces)

The store is an event-sourced patch log; correct reads REQUIRE full replay
(kind 0 = snapshot, kind 1 = set at key-path, kind 2 with "v" = array
insert, kind 2 without "v" = splice-delete at index). Partial scans return
stale intermediate values — a broken scan under-reported total credits
3.2x (560 vs 1800).

Privacy (judged, R-4): rows carry verbatim prompts. Output goes to stdout
or --out only; --out refuses repo-internal paths unless
--allow-repo-output. Reports are never committed.

Malformed stores (judged, R-2): explicitly requested paths fail hard;
scans (--all-workspaces) skip the store, report it on stderr, and emit a
row whose unavailable_reason records the failure — never silent omission.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ledger import (  # noqa: E402  # CONF-429
    CACHE_RATIO_BEST,
    UNKNOWN_MODEL_PRICE,
    WS_STORAGE,
    load_prices,
)

BOILERPLATE_TITLES = {"Run in Terminal"}

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

__all__ = ["WS_STORAGE", "load_prices", "replay", "main"]


def apply_patch(doc, rec):
    kind = rec["kind"]
    if kind == 0:
        return rec["v"]
    keys = rec["k"]
    node = doc
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = keys[-1]
    if kind == 1:  # set at key-path
        if isinstance(node, list):
            node[int(last)] = rec["v"]
        else:
            node[last] = rec["v"]
    elif kind == 2:  # array splice at index i: insert v, or delete when v absent
        tgt = node[int(last)] if isinstance(node, list) else node[last]
        idx = rec.get("i", len(tgt))
        if "v" in rec:
            val = rec["v"]
            tgt[idx:idx] = val if isinstance(val, list) else [val]
        else:
            del tgt[idx]
    return doc


def replay(path: Path):
    doc = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            doc = apply_patch(doc, json.loads(line))
    if doc is None:
        raise ValueError(f"empty store: {path}")
    return doc


REPLAY_ERRORS = (ValueError, KeyError, IndexError, TypeError, OSError)


def collect_titles(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "generatedTitle" and isinstance(v, str):
                acc.append(v)
            collect_titles(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            collect_titles(v, acc)


def workspace_folder(session_path: Path) -> str | None:
    ws = session_path.parent.parent / "workspace.json"
    if ws.exists():
        try:
            return json.loads(ws.read_text(encoding="utf-8")).get("folder")
        except (json.JSONDecodeError, OSError):
            return None
    return None


def answer_first_line(req) -> str | None:
    """First line of the assistant's markdown answer (kind-less response parts)."""
    for part in req.get("response") or []:
        if (
            isinstance(part, dict)
            and "kind" not in part
            and isinstance(part.get("value"), str)
        ):
            for line in part["value"].splitlines():
                line = line.strip()
                if line:
                    return line if len(line) <= 120 else line[:117] + "..."
    return None


def summarize(req) -> list[str]:
    """Per-turn summary: real titles, else raw titles, else answer line."""
    raw: list[str] = []
    collect_titles(req, raw)
    seen: set[str] = set()
    titles = [
        t for t in raw if not (t in seen or t in BOILERPLATE_TITLES or seen.add(t))
    ]
    if titles:
        return titles
    if raw:  # boilerplate-only turn: keep the deduped raw titles
        return sorted(set(raw))
    line = answer_first_line(req)
    if line:
        return [line]
    return ["(no summary)"]


def fmt_ts(ms) -> str:
    return f"{datetime.fromtimestamp(ms / 1000):%Y-%m-%d %H:%M:%S}" if ms else ""


def session_header(doc, path: Path) -> dict:
    session_id = doc.get("sessionId", path.stem)
    return {
        "session_id": session_id,
        "session_title": doc.get("customTitle") or f"Session {session_id[:8]}",
        "created": fmt_ts(doc.get("creationDate")),
        "workspace": (workspace_folder(path) or "").removeprefix("file://"),
    }


def estimate_reason(row, prices) -> str:
    """Reason string for a credits-less request: a RANGE, never a point value."""
    p_tok, c_tok = row["prompt_tokens"], row["completion_tokens"]
    if p_tok is None or c_tok is None:
        return "no copilotCredits (cancelled or summarized turn)"
    pr = prices.get(row["model"], UNKNOWN_MODEL_PRICE)
    # prices are milli-credits per 1M tokens -> credits = tokens * price / 1e9
    worst = (p_tok * pr["in"] + c_tok * pr["out"]) / 1e9
    best = (
        p_tok * ((1 - CACHE_RATIO_BEST) * pr["in"] + CACHE_RATIO_BEST * pr["cache"])
        + c_tok * pr["out"]
    ) / 1e9
    return f"no copilotCredits; est {best:.3g}–{worst:.3g} cr"


def request_rows(doc, header: dict):
    for i, req in enumerate(doc.get("requests") or [], 1):
        msg = req.get("message") or {}
        prompt = "".join(
            p.get("text", "") for p in (msg.get("parts") or []) if isinstance(p, dict)
        ).strip()
        yield {
            **header,
            "request": i,
            "request_time": fmt_ts(req.get("timestamp")),
            "model": (req.get("modelId") or "unknown").removeprefix("copilot/"),
            "credits": req.get("copilotCredits"),
            "prompt_tokens": req.get("promptTokens"),
            "completion_tokens": req.get("completionTokens"),
            "elapsed_ms": req.get("elapsedMs"),
            "prompt": prompt,
            "titles": summarize(req),
        }


def within_window(doc, cutoff_ms: float) -> bool:
    stamps = [req.get("timestamp") for req in doc.get("requests") or []]
    stamps.append(doc.get("creationDate"))
    return any(ts is not None and ts >= cutoff_ms for ts in stamps)


def load_sessions(paths: list[Path], *, scan: bool, cutoff_ms: float | None):
    """Yield (path, doc, error) triples honouring the judged malformed policy."""
    for path in paths:
        try:
            doc = replay(path)
        except REPLAY_ERRORS as exc:
            if not scan:
                sys.exit(f"replay failed: {path}: {exc}")
            print(f"skip {path}: replay failed: {exc}", file=sys.stderr)
            yield path, None, f"replay failed: {exc}"
            continue
        if cutoff_ms is not None and not within_window(doc, cutoff_ms):
            continue
        yield path, doc, None


def render_markdown(sessions) -> str:
    out = []
    for path, doc, error in sessions:
        if doc is None:
            out.append(f"# {path.stem}\n\n**Unavailable:** {error}\n")
            continue
        header = session_header(doc, path)
        out.append(f"# {header['session_title']}\n")
        if header["created"]:
            out.append(f"**Created:** {header['created']}  ")
        out.append(f"**Session:** {header['session_id']}  ")
        if header["workspace"]:
            out.append(f"**Workspace:** {header['workspace']}  ")
        out.append("")
        total, count = 0.0, 0
        for row in request_rows(doc, header):
            count += 1
            out.append(f"## Request {row['request']}")
            out.append(f"**User:**  \n{row['prompt']}\n")
            out.append(f"**{row['model']}:**")
            out.extend(f"- {t}" for t in row["titles"])
            credits = row["credits"]
            if credits is not None:
                total += credits
                cost = f"{credits:.1f} credits"
            else:
                cost = estimate_reason(row, load_prices())
            out.append(f"\n**Cost:** {cost}\n")
        out.append(
            f"---\n**Session total: {total:.1f} credits over {count} requests**\n"
        )
    return "\n".join(out)


def render_csv(sessions, stream) -> None:
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    rows: list[dict] = []
    for path, doc, error in sessions:
        if doc is None:
            rows.append(
                {
                    **dict.fromkeys(CSV_COLUMNS, ""),
                    "session_id": path.stem,
                    "unavailable_reason": error,
                }
            )
            continue
        for row in request_rows(doc, session_header(doc, path)):
            row["summary"] = "; ".join(row.pop("titles"))
            row["prompt"] = " ".join(row["prompt"].split())  # single physical line
            rows.append(row)
    needs_estimate = any("credits" in r and r["credits"] is None for r in rows)
    prices = load_prices() if needs_estimate else {}
    for row in rows:
        if row.get("credits") is None:
            row["unavailable_reason"] = estimate_reason(row, prices)
            row["credits"] = ""
        elif "unavailable_reason" not in row:
            row["unavailable_reason"] = ""
        if isinstance(row["credits"], float):
            row["credits"] = round(row["credits"], 2)
        writer.writerow(row)


def check_out_path(target: Path, allow_repo_output: bool) -> None:
    """R-4 privacy boundary: refuse repo-internal report paths by default."""
    if allow_repo_output:
        return
    for parent in target.resolve().parents:
        if (parent / ".git").exists():
            sys.exit(
                f"refusing to write a prompt-bearing report inside a git repo: "
                f"{target} (pass --allow-repo-output to override)"
            )


def resolve_paths(args) -> tuple[list[Path], bool]:
    """Return (paths, scan) — scan=True means malformed stores skip, not fail."""
    if args.paths:
        paths = [p.expanduser() for p in args.paths]
        missing = [p for p in paths if not p.exists()]
        if missing:
            sys.exit(f"not found: {', '.join(map(str, missing))}")
        return paths, False
    if args.session:
        paths = sorted(WS_STORAGE.glob(f"*/chatSessions/{args.session}.jsonl"))
        if not paths:
            sys.exit(f"session not found under {WS_STORAGE}: {args.session}")
        return paths, False
    if args.all_workspaces:
        return sorted(WS_STORAGE.glob("*/chatSessions/*.jsonl")), True
    sys.exit("provide session paths, --session <id>, or --all-workspaces")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--csv", action="store_true", help="one row per request, pivot-ready"
    )
    parser.add_argument(
        "--session", help="session id to locate under the workspace storage"
    )
    parser.add_argument(
        "--all-workspaces", action="store_true", help="scan every chatSessions store"
    )
    parser.add_argument(
        "--window", type=float, help="only sessions active in the last N hours"
    )
    parser.add_argument(
        "--out", type=Path, help="write report to file instead of stdout"
    )
    parser.add_argument(
        "--allow-repo-output",
        action="store_true",
        help="permit --out targets inside a git repository (R-4 override)",
    )
    args = parser.parse_args(argv)
    paths, scan = resolve_paths(args)
    cutoff_ms = None
    if args.window is not None:
        cutoff_ms = (datetime.now() - timedelta(hours=args.window)).timestamp() * 1000
    sessions = load_sessions(paths, scan=scan, cutoff_ms=cutoff_ms)
    if args.out:
        check_out_path(args.out, args.allow_repo_output)
        with open(args.out, "w", encoding="utf-8") as stream:
            if args.csv:
                render_csv(sessions, stream)
            else:
                stream.write(render_markdown(sessions) + "\n")
        return
    if args.csv:
        render_csv(sessions, sys.stdout)
    else:
        print(render_markdown(sessions))


if __name__ == "__main__":
    main()
