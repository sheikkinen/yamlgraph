"""FR-713 Part B integration witness: warm CACHED google client on the
persistent bridge loop — completed calls, zero errors.

Re-derivation of the FR-712 witness (instrument-rot rule: a witness
encoding the retired fresh-loop topology measures a retired world). The
FR-712 claim was "a cached client errors on ~50% of completed calls in
FRESH loops"; FR-713 Part A gave clients one stable loop, Part B restored
their cache eligibility. This witness exercises the exact seam that
condemned the cache: ONE client object, reused across N bridged calls.

Zero errors over 10 completed calls ≈ 0.1% false-pass odds at the
condemned 50% error rate (FR-712 Judgement F2). Vertex rides the
same-class inference (F17) — witnessed for google, skip-with-reason
pattern applies if a vertex-keyed environment ever runs this.
"""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set",
    ),
]

N = 10


@pytest.mark.req("REQ-YG-540")
def test_cached_google_completes_cleanly_on_bridge_loop() -> None:
    from yamlgraph.utils import llm_factory
    from yamlgraph.utils.bridge import run_coro_sync_safe

    llm_factory.clear_cache()
    errors: list[str] = []
    clients: set[int] = set()
    for _ in range(N):
        # Production topology post-Part-B: create_llm at node level is a
        # CACHE HIT after first use; every call runs on the one persistent
        # bridge loop, so the aiohttp session's loop affinity is honored.
        llm = llm_factory.create_llm(provider="google", model="gemini-2.5-flash")
        clients.add(id(llm))

        async def _one(client=llm):
            await client.ainvoke("Say OK.")

        try:
            run_coro_sync_safe(_one(), verdict_budget=60.0)
        except Exception as exc:  # the condemned class
            errors.append(f"{type(exc).__name__}: {exc}")

    assert len(clients) == 1, (
        f"expected one cached client across {N} calls, got {len(clients)} — "
        "the witness must exercise the seam that condemned the cache"
    )
    assert not errors, (
        f"{len(errors)}/{N} completed warm-cached calls errored on the "
        f"persistent loop (FR-711 Finding A class): {errors[:3]}"
    )
