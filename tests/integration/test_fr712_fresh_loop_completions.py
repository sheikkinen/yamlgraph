"""FR-712 integration witness: completed google calls in fresh loops, zero errors.

Seam: cached-client-completion-in-fresh-loop — the path FR-709 structurally
could not walk (its google candidate was always the cancelled loser) and
FR-711's Arm B condemned: 10/20 completed calls errored with
`Executor shutdown has been called` / `Timeout context manager should be
used inside a task`.

Zero errors over 10 completed calls ≈ 0.1% false-pass odds at the observed
50% error rate (Judgement F2).
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
def test_google_completes_cleanly_in_fresh_loops() -> None:
    from yamlgraph.node_factory.race_node import _run_coro_sync_safe
    from yamlgraph.utils import llm_factory

    llm_factory.clear_cache()
    errors: list[str] = []
    for _ in range(N):
        # Production topology: create_llm at node level, invocation through
        # the bridge (fresh loop). Post-FR-712 each call gets a fresh client
        # whose session is born in its own loop.
        llm = llm_factory.create_llm(provider="google", model="gemini-2.5-flash")

        async def _one(client=llm):
            await client.ainvoke("Say OK.")

        try:
            _run_coro_sync_safe(_one())
        except Exception as exc:  # the condemned class
            errors.append(f"{type(exc).__name__}: {exc}")

    assert not errors, (
        f"{len(errors)}/{N} completed fresh-loop calls errored "
        f"(FR-711 Finding A class): {errors[:3]}"
    )
