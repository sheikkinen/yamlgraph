"""FR-1065 investigation probes on minimal LangGraph fixtures.

Each probe returns a plain dict of measurements. Run all of them with
``python tests/fixtures/fr1065/probes.py report`` to reproduce the numbers
in docs/investigations/fr1065-resumable-map.md.
"""

from __future__ import annotations

import argparse
import json
import operator
import os
import signal
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.cache.memory import InMemoryCache
from langgraph.cache.sqlite import SqliteCache
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy, Send

HERE = Path(__file__).resolve()
NS = ("fr1065",)


class MapState(TypedDict, total=False):
    items: list[int]
    results: Annotated[list[dict], operator.add]
    count: Annotated[int, operator.add]
    cursor: int
    selected: list[dict]


def _fan_out(state: MapState) -> list[Send]:
    return [Send("work", {"item": i}) for i in state["items"]]


def _build_map(work, *, join=None) -> StateGraph:
    g = StateGraph(MapState)
    g.add_node("start", lambda s: {})
    g.add_node("work", work)
    g.add_node("join", join or (lambda s: {}))
    g.add_edge(START, "start")
    g.add_conditional_edges("start", _fan_out, ["work"])
    g.add_edge("work", "join")
    g.add_edge("join", END)
    return g


# --- AC-01: store concurrency and persistence -------------------------------


def probe_cache_in_process(path: str, n: int = 500, workers: int = 16) -> dict:
    """Branches of one map call SqliteCache.set/get directly, as a wrapper would."""
    cache = SqliteCache(path=path)
    latencies: list[float] = []
    errors: list[str] = []

    def work(payload: dict) -> dict:
        key = (NS, f"item-{payload['item']}")
        t0 = time.perf_counter()
        try:
            cache.set({key: ({"i": payload["item"]}, None)})
            got = cache.get([key])
            if got.get(key) != {"i": payload["item"]}:
                errors.append(f"mismatch {key}")
        except sqlite3.Error as exc:
            errors.append(repr(exc))
        latencies.append(time.perf_counter() - t0)
        return {"count": 1}

    app = _build_map(work).compile()
    app.invoke({"items": list(range(n))}, {"max_concurrency": workers})
    stored = cache.get([(NS, f"item-{i}") for i in range(n)])
    return {
        "branches": n,
        "errors": len(errors),
        "stored": len(stored),
        "p50_ms": round(statistics.median(latencies) * 1000, 3),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[18] * 1000, 3),
    }


def _cache_writer(path: str, offset: int, n: int, start_at: float) -> None:
    cache = SqliteCache(path=path)
    while time.time() < start_at:
        pass
    errors = 0
    for i in range(offset, offset + n):
        try:
            cache.set({(NS, f"item-{i}"): ({"i": i, "pid": os.getpid()}, None)})
        except sqlite3.Error:
            errors += 1
    print(json.dumps({"errors": errors}))


def _run_worker(*args: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(HERE), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def probe_cache_two_process(path: str, n: int = 500, precreate: bool = False) -> dict:
    """Two processes write disjoint keys concurrently; a third process reads."""
    if precreate:
        SqliteCache(path=path)
    start_at = time.time() + 1.0
    procs = [
        _run_worker("cache-writer", path, str(off), str(n), str(start_at))
        for off in (0, n)
    ]
    outs = [p.communicate(timeout=120) for p in procs]
    crashes = [
        err.strip().splitlines()[-1]
        for p, (_, err) in zip(procs, outs, strict=True)
        if p.returncode
    ]
    errors = sum(
        json.loads(o.strip().splitlines()[-1])["errors"]
        for p, (o, _) in zip(procs, outs, strict=True)
        if not p.returncode
    )
    reader = subprocess.run(
        [sys.executable, str(HERE), "cache-reader", path, str(2 * n)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return {
        "writers": 2,
        "keys_per_writer": n,
        "write_errors": errors,
        "writer_crashes": crashes,
        **json.loads(reader.stdout),
    }


def _cache_reader(path: str, n: int) -> None:
    got = SqliteCache(path=path).get([(NS, f"item-{i}") for i in range(n)])
    print(
        json.dumps(
            {"read_back": len(got), "pids": len({v["pid"] for v in got.values()})}
        )
    )


LEASE_DDL = (
    "CREATE TABLE IF NOT EXISTS lease (store TEXT PRIMARY KEY, token TEXT NOT NULL)"
)


def _lease_claimant(kind: str, path: str, token: str, start_at: float) -> None:
    if kind == "cache":
        cache = SqliteCache(path=path)
        while time.time() < start_at:
            pass
        cache.set({(NS, "lease"): (token, None)})
        won = True
    else:
        conn = sqlite3.connect(path, timeout=10, isolation_level=None)
        conn.execute(LEASE_DDL)
        while time.time() < start_at:
            pass
        try:
            conn.execute("INSERT INTO lease (store, token) VALUES ('s', ?)", (token,))
            won = True
        except sqlite3.IntegrityError:
            won = False
    print(json.dumps({"won": won}))


def probe_lease(kind: str, rounds: int = 10, precreate: bool = False) -> dict:
    """Two processes race to acquire one lease; count rounds with >1 winner."""
    double_wins = 0
    crashes: list[str] = []
    for r in range(rounds):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "lease.db")
            if kind == "sqlite":
                sqlite3.connect(path).execute(LEASE_DDL)
            elif precreate:
                SqliteCache(path=path)
            start_at = time.time() + 0.8
            procs = [
                _run_worker("lease", kind, path, f"tok-{r}-{k}", str(start_at))
                for k in range(2)
            ]
            wins = 0
            for proc in procs:
                out, err = proc.communicate(timeout=60)
                if proc.returncode:
                    crashes.append(err.strip().splitlines()[-1])
                else:
                    wins += json.loads(out)["won"]
            double_wins += wins > 1
    return {
        "kind": kind,
        "rounds": rounds,
        "rounds_with_two_winners": double_wins,
        "claimant_crashes": crashes,
    }


# --- AC-02: checkpoint size --------------------------------------------------


def _checkpoint_bytes(saver: SqliteSaver, config: dict) -> int:
    tup = saver.get_tuple(config)
    return len(saver.serde.dumps_typed(tup.checkpoint)[1])


def _writes_bytes(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COALESCE(SUM(LENGTH(value)), 0) FROM writes"
    ).fetchone()[0]


def probe_checkpoint_size(
    tmp: str, n: int = 10_000, payload: int = 400, select: int = 50
) -> dict:
    """Final checkpoint bytes: results in state vs results in a side store."""
    out: dict[str, Any] = {"items": n, "payload_bytes": payload, "selected": select}
    text = "x" * payload

    def collect_work(p: dict) -> dict:
        return {"results": [{"key": p["item"], "text": text}]}

    store_path = str(Path(tmp) / "side-store.db")
    store = sqlite3.connect(store_path, check_same_thread=False, isolation_level=None)
    store.execute("CREATE TABLE r (key INTEGER PRIMARY KEY, text TEXT)")
    lock = threading.Lock()

    def store_work(p: dict) -> dict:
        with lock:
            store.execute("INSERT INTO r VALUES (?, ?)", (p["item"], text))
        return {"count": 1}

    def store_join(s: MapState) -> dict:
        rows = store.execute(
            "SELECT key, text FROM r ORDER BY key LIMIT ?", (select,)
        ).fetchall()
        return {"selected": [{"key": k, "text": t} for k, t in rows]}

    for name, work, join in (
        ("collect", collect_work, None),
        ("store", store_work, store_join),
    ):
        db = str(Path(tmp) / f"{name}.db")
        conn = sqlite3.connect(db, check_same_thread=False)
        saver = SqliteSaver(conn)
        cfg = {"configurable": {"thread_id": name}}
        t0 = time.perf_counter()
        _build_map(work, join=join).compile(checkpointer=saver).invoke(
            {"items": list(range(n))}, cfg
        )
        out[name] = {
            "final_checkpoint_bytes": _checkpoint_bytes(saver, cfg),
            "pending_writes_bytes": _writes_bytes(conn),
            "db_file_bytes": os.path.getsize(db),
            "seconds": round(time.perf_counter() - t0, 2),
        }
        conn.close()
    out["side_store_file_bytes"] = os.path.getsize(store_path)
    return out


# --- AC-03: bounded batches --------------------------------------------------


def _dispatch_batch(batch: int):
    def route(state: MapState) -> list[Send] | str:
        lo = state.get("cursor", 0)
        chunk = state["items"][lo : lo + batch]
        return [Send("work", {"item": i}) for i in chunk] if chunk else END

    return route


def _build_batched(work, batch: int) -> StateGraph:
    g = StateGraph(MapState)
    g.add_node("dispatch", lambda s: {})
    g.add_node("work", work)
    g.add_node("join", lambda s: {"cursor": s.get("cursor", 0) + batch})
    g.add_edge(START, "dispatch")
    g.add_conditional_edges("dispatch", _dispatch_batch(batch), ["work", END])
    g.add_edge("work", "join")
    g.add_edge("join", "dispatch")
    return g


def probe_batches(n: int = 10_000, batch: int = 500) -> dict:
    """Peak Python memory for one-step fan-out vs a bounded batch loop."""

    def work(p: dict) -> dict:
        return {"count": 1}

    def measure(build) -> tuple[int, int, float]:
        tracemalloc.start()
        t0 = time.perf_counter()
        app, cfg = build()
        final = app.invoke({"items": list(range(n)), "cursor": 0}, cfg)
        secs = time.perf_counter() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        return peak, final["count"], secs

    def one_step():
        return _build_map(work).compile(), {}

    def batched():
        return _build_batched(work, batch).compile(), {}

    p1, c1, s1 = measure(one_step)
    p2, c2, s2 = measure(batched)
    return {
        "items": n,
        "batch": batch,
        "one_step": {"peak_bytes": p1, "count": c1, "seconds": round(s1, 2)},
        "batched": {"peak_bytes": p2, "count": c2, "seconds": round(s2, 2)},
    }


# --- AC-04: killed-process resume --------------------------------------------


def _log(calls: str, line: str) -> None:
    with open(calls, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _resume_worker(
    mode: str, db: str, calls: str, n: int, thread: str, durability: str, batch: int
) -> None:
    def work(p: dict) -> dict:
        _log(calls, f"start {p['item']}")
        time.sleep(0.05)
        _log(calls, f"done {p['item']}")
        return {"results": [{"key": p["item"]}]}

    conn = sqlite3.connect(db, check_same_thread=False)
    graph = _build_batched(work, batch) if batch else _build_map(work)
    app = graph.compile(checkpointer=SqliteSaver(conn))
    cfg = {"configurable": {"thread_id": thread}, "max_concurrency": 2}
    state = None if mode == "resume" else {"items": list(range(n)), "cursor": 0}
    final = app.invoke(
        state, cfg, durability=None if durability == "default" else durability
    )
    print(json.dumps({"results": sorted(r["key"] for r in final["results"])}))


def _events(path: str, kind: str) -> list[int]:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    return [int(v) for k, v in (ln.split() for ln in lines) if k == kind]


def probe_resume(
    tmp: str,
    sig: int,
    durability: str = "default",
    n: int = 20,
    kill_after: int = 6,
    batch: int = 0,
) -> dict:
    """Interrupt a map mid-superstep with ``sig``, resume the same thread.

    ``batch`` 0 is one-step fan-out; otherwise a bounded batch loop.
    """
    tag = f"{signal.Signals(sig).name}-{durability}-b{batch}"
    db = str(Path(tmp) / f"ckpt-{tag}.db")
    first = str(Path(tmp) / f"calls-first-{tag}.txt")
    second = str(Path(tmp) / f"calls-resume-{tag}.txt")
    proc = _run_worker("resume", "run", db, first, str(n), "t1", durability, str(batch))
    deadline = time.time() + 60
    while len(_events(first, "done")) < kill_after and time.time() < deadline:
        time.sleep(0.005)
    proc.send_signal(sig)
    proc.communicate(timeout=60)
    done_before = _events(first, "done")
    conn = sqlite3.connect(db)
    writes_rows = conn.execute("SELECT COUNT(DISTINCT task_id) FROM writes").fetchone()[
        0
    ]
    conn.close()
    resumed = subprocess.run(
        [
            sys.executable,
            str(HERE),
            "resume",
            "resume",
            db,
            second,
            str(n),
            "t1",
            durability,
            str(batch),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    resume_calls = _events(second, "start")
    results = json.loads(resumed.stdout.strip().splitlines()[-1])["results"]
    return {
        "signal": signal.Signals(sig).name,
        "durability": durability,
        "batch": batch,
        "items": n,
        "completed_before_interrupt": len(done_before),
        "tasks_with_persisted_writes": writes_rows,
        "calls_on_resume": len(resume_calls),
        "completed_items_rerun": len(set(done_before) & set(resume_calls)),
        "results_equal_uninterrupted": results == list(range(n)),
    }


def probe_cross_run(tmp: str, n: int = 20) -> dict:
    """A new thread over the same items: the checkpointer reuses nothing."""
    db = str(Path(tmp) / "cross.db")
    calls = str(Path(tmp) / "calls-cross.txt")
    for thread in ("run-1", "run-2"):
        subprocess.run(
            [
                sys.executable,
                str(HERE),
                "resume",
                "run",
                db,
                calls,
                str(n),
                thread,
                "default",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
    return {"items": n, "runs": 2, "total_calls": len(_events(calls, "start"))}


# --- AC-06: FR-032 cache policy is inert without compile(cache=) -------------


def probe_cache_policy() -> dict:
    calls = {"n": 0}

    def node(s: MapState) -> dict:
        calls["n"] += 1
        return {"count": 1}

    def runs(cache) -> int:
        calls["n"] = 0
        g = StateGraph(MapState)
        g.add_node("n", node, cache_policy=CachePolicy(ttl=60))
        g.add_edge(START, "n")
        g.add_edge("n", END)
        app = g.compile(cache=cache)
        for _ in range(2):
            app.invoke({"items": [1]})
        return calls["n"]

    return {
        "calls_without_cache": runs(None),
        "calls_with_in_memory_cache": runs(InMemoryCache()),
    }


def report() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        return {
            "cache_in_process": probe_cache_in_process(str(Path(tmp) / "c1.db")),
            "cache_two_process_fresh_file": probe_cache_two_process(
                str(Path(tmp) / "c2.db")
            ),
            "cache_two_process_precreated": probe_cache_two_process(
                str(Path(tmp) / "c3.db"), precreate=True
            ),
            "lease_sqlite_cache_fresh_file": probe_lease("cache"),
            "lease_sqlite_cache_precreated": probe_lease("cache", precreate=True),
            "lease_sqlite_unique": probe_lease("sqlite"),
            "checkpoint_size": probe_checkpoint_size(tmp),
            "batches": probe_batches(),
            "resume": [
                probe_resume(tmp, sig, durability)
                for sig in (signal.SIGKILL, signal.SIGINT)
                for durability in ("default", "sync")
            ]
            + [
                probe_resume(tmp, signal.SIGKILL, durability, batch=4)
                for durability in ("default", "sync")
            ],
            "cross_run": probe_cross_run(tmp),
            "cache_policy": probe_cache_policy(),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd")
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args()
    a = ns.args
    if ns.cmd == "report":
        print(json.dumps(report(), indent=2))
    elif ns.cmd == "cache-writer":
        _cache_writer(a[0], int(a[1]), int(a[2]), float(a[3]))
    elif ns.cmd == "cache-reader":
        _cache_reader(a[0], int(a[1]))
    elif ns.cmd == "lease":
        _lease_claimant(a[0], a[1], a[2], float(a[3]))
    elif ns.cmd == "resume":
        _resume_worker(a[0], a[1], a[2], int(a[3]), a[4], a[5], int(a[6]))
    else:
        raise SystemExit(f"unknown command {ns.cmd}")


if __name__ == "__main__":
    main()
