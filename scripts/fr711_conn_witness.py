"""FR-711 connection-reuse latency witness (local instrument, AC-01/AC-02).

Measures what one LLM call costs when the client OBJECT is warm (the
existing `_llm_cache`) but the event LOOP is fresh — the production topology
of every race-node turn (`_run_coro_sync_safe` runs asyncio.run in a fresh
daemon thread per call).

Arm A: one loop, warm-up + N sequential calls  -> reuse floor.
Arm B: N calls, each through the REAL production bridge (fresh loop each)
       -> forced per-loop reconnect.
B - A = connection/handshake cost per call, per provider.

Judgement F1: this instrument is mechanism-proof + decomposition; the
FR-711 verdict is rendered on the DEPLOYED (Fly) numbers.
Judgement F2: cached-client cross-loop reuse is field-verified (FR-709);
an Arm-B error is itself a finding, recorded not swallowed.

Usage: python scripts/fr711_conn_witness.py
Writes: docs/analysis/fr711-conn-witness-2026-07-10.txt
"""

from __future__ import annotations

import asyncio
import statistics
import time
from pathlib import Path

N = 20
MSG = "Say OK."
OUT = Path("docs/analysis/fr711-conn-witness-2026-07-10.txt")

# (provider, model, key env var). google = fleet's gRPC-suspect family
# (locally substitutes vertex per Judgement F3 — same SDK transport);
# azure = fleet member (local default deployment, not the fleet's
# aaa-gpt-5.4-mini — annotated); anthropic = control.
ARMS = [
    ("google", "gemini-2.5-flash", "GOOGLE_API_KEY"),
    ("azure", None, "AZURE_AI_API_KEY"),
    ("anthropic", "claude-haiku-4-5", "ANTHROPIC_API_KEY"),
]


def _pct(values: list[float], p: float) -> float:
    values = sorted(values)
    idx = min(len(values) - 1, max(0, round(p / 100 * (len(values) - 1))))
    return values[idx]


def _measure(provider: str, model: str | None) -> dict:
    from yamlgraph.node_factory.race_node import _run_coro_sync_safe
    from yamlgraph.utils.llm_factory import create_llm

    t0 = time.perf_counter()
    llm = create_llm(provider=provider, model=model)
    construct_s = time.perf_counter() - t0

    async def _arm_a() -> tuple[float, list[float]]:
        t0 = time.perf_counter()
        await llm.ainvoke(MSG)  # warm-up: first connection in this loop
        first = time.perf_counter() - t0
        times = []
        for _ in range(N):
            t1 = time.perf_counter()
            await llm.ainvoke(MSG)
            times.append(time.perf_counter() - t1)
        return first, times

    first_call_s, a_times = asyncio.run(_arm_a())

    b_times = []
    b_errors: list[str] = []
    for _ in range(N):

        async def _one() -> None:
            # Production topology (post-FR-712): create_llm PER CALL —
            # identity-stable via _llm_cache for cached providers, fresh
            # client per call for loop-affine google/vertex. The witness
            # previously reused one pre-created object across loops, which
            # is the exact topology FR-712 retired for google.
            client = create_llm(provider=provider, model=model)
            await client.ainvoke(MSG)

        t1 = time.perf_counter()
        try:
            _run_coro_sync_safe(_one())  # the REAL bridge: fresh loop (AC-02)
        except Exception as exc:  # F2: an Arm-B error is a finding
            b_errors.append(f"{type(exc).__name__}: {exc}")
        b_times.append(time.perf_counter() - t1)

    return {
        "provider": provider,
        "model": model or "(env default)",
        "construct_s": construct_s,
        "first_call_s": first_call_s,
        "a_times": a_times,
        "b_times": b_times,
        "b_errors": b_errors,
    }


def main() -> None:
    import os

    from dotenv import load_dotenv

    load_dotenv()  # keys live in .env, as the framework's config.py loads them

    lines = [
        "FR-711 connection-reuse latency witness — local instrument",
        f"date: 2026-07-10  N={N}/arm  msg={MSG!r}",
        "Arm A = one loop, sequential (reuse). Arm B = fresh loop per call",
        "via the production _run_coro_sync_safe bridge (forced reconnect).",
        "",
        f"{'provider':<10} {'A p50':>7} {'A p95':>7} {'B p50':>7} {'B p95':>7} "
        f"{'Δp50':>7} {'Δmin':>7} {'cold1st':>8}",
    ]
    for provider, model, key in ARMS:
        if not os.getenv(key):
            lines.append(f"{provider:<10} SKIPPED — {key} not set")
            continue
        r = _measure(provider, model)
        a, b = r["a_times"], r["b_times"]
        d50 = statistics.median(b) - statistics.median(a)
        dmin = min(b) - min(a)
        lines.append(
            f"{r['provider']:<10} {_pct(a, 50):>7.3f} {_pct(a, 95):>7.3f} "
            f"{_pct(b, 50):>7.3f} {_pct(b, 95):>7.3f} {d50:>+7.3f} "
            f"{dmin:>+7.3f} {r['first_call_s']:>8.3f}"
        )
        if r["b_errors"]:
            lines.append(f"  Arm-B errors ({len(r['b_errors'])}): {r['b_errors'][:3]}")
        lines.append(f"  raw A: {' '.join(f'{t:.3f}' for t in a)}")
        lines.append(f"  raw B: {' '.join(f'{t:.3f}' for t in b)}")
    report = "\n".join(lines)
    print(report)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report + "\n")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
