"""FR-713 pending-task census: does a constant flow of races accumulate
zombie tasks on the ONE persistent bridge loop?

Seam (name_the_seam): loser-task-census-on-shared-loop. The old topology
isolated a pending-forever loser in its own throwaway loop; the persistent
loop is a shared container — population = arrival rate × effective
lifetime (rate-layer diary 2026-07-10). NC-366 saw deployed google spans
pending-forever. This witness runs N sequential races where the slower
candidate is cancelled mid-flight, then CENSUSES the bridge loop: every
leftover task is named (read_raw_output_first), and the population must
return to zero within the FR-708 client timeout + margin — proving
lifetime is bounded and rate cannot compound.

Fleet pairings: azure+vertex (the ninchat fleet — runs on a box with
those keys) and anthropic+google (local instrument). Skip-with-reason
per pairing (FR-711 F3).
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from pathlib import Path

import pytest

from yamlgraph.node_factory.race_node import (
    AllCandidatesFailedError,
    create_race_node,
)
from yamlgraph.utils import bridge

pytestmark = [pytest.mark.slow]

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "fixtures" / "prompts"
RACE_TIMEOUT = 2.0  # tight: the slower candidate is cancelled mid-flight
CLIENT_TIMEOUT = 10.0  # google/vertex deadline floor (FR-710)
SETTLE_MARGIN = 3.0
RACES = 3

FLEETS = {
    "azure-vertex": (
        [
            {"provider": "azure", "model": None},
            {"provider": "vertex", "model": "gemini-2.5-flash"},
        ],
        ("AZURE_AI_API_KEY", "VERTEX_API_KEY"),
    ),
    "anthropic-google": (
        [
            {"provider": "anthropic", "model": "claude-haiku-4-5"},
            {"provider": "google", "model": "gemini-2.5-pro"},
        ],
        ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"),
    ),
}


def _census() -> list[str]:
    """Name every task alive on the bridge loop except the probe itself."""

    async def _look() -> list[str]:
        cur = asyncio.current_task()
        return sorted(t.get_name() for t in asyncio.all_tasks() if t is not cur)

    return bridge.run_coro_sync_safe(_look(), verdict_budget=5.0)


def _settle_to_empty() -> list[str]:
    """Poll until the loop census is empty within client timeout + margin."""
    deadline = time.monotonic() + CLIENT_TIMEOUT + SETTLE_MARGIN
    leftovers = _census()
    while time.monotonic() < deadline and leftovers:
        time.sleep(0.5)
        leftovers = _census()
    return leftovers


@pytest.mark.req("REQ-YG-541")
@pytest.mark.parametrize("fleet", sorted(FLEETS))
def test_loser_tasks_do_not_accumulate_on_bridge_loop(fleet, monkeypatch) -> None:
    candidates, required_keys = FLEETS[fleet]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        pytest.skip(f"{fleet}: missing {', '.join(missing)}")

    monkeypatch.setenv("LLM_REQUEST_TIMEOUT", str(CLIENT_TIMEOUT))

    node_config = {
        "type": "race",
        "prompt": "teardown_probe",
        "state_key": "answer",
        "timeout": RACE_TIMEOUT,
        "parse_json": True,
        "candidates": [dict(c) for c in candidates],
    }
    node_fn = create_race_node(
        f"census_race_{fleet}",
        node_config,
        defaults={"prompts_dir": str(PROMPTS_DIR)},
    )

    per_race: list[str] = []
    for i in range(RACES):
        try:
            result = node_fn({"_loop_counts": {}, "errors": []})
            winner = (result.get("_race_winner") or {}).get("provider", "?")
            shape = f"winner={winner}"
        except AllCandidatesFailedError as exc:
            shape = f"neither-completed ({exc})"

        snapshot = _census()
        per_race.append(f"race{i + 1}: {shape} loop-tasks={snapshot}")

    # read_raw_output_first: the censuses ARE the artifact.
    report = "\n".join(per_race)
    logger.info("bridge loop census:\n%s", report)
    print(f"\nFR-713 census ({fleet}):\n{report}")

    # Population must return to ZERO within the FR-708 lifetime bound —
    # otherwise constant flow compounds it (rate × lifetime).
    leftovers = _settle_to_empty()
    print(f"final census after settle: {leftovers}")
    assert not leftovers, (
        f"{len(leftovers)} task(s) survived client-timeout+margin on the "
        f"shared bridge loop — pending-forever population would grow "
        f"without bound under constant race flow: {leftovers}"
    )

    # The substrate itself must not have multiplied.
    loop_threads = [
        t.name for t in threading.enumerate() if t.name == bridge.BRIDGE_THREAD_NAME
    ]
    assert len(loop_threads) == 1, loop_threads
