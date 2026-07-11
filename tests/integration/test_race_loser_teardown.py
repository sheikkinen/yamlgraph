"""FR-709: real-provider race loser-teardown witness (integration).

Seam (name_the_seam): race-loser-teardown-live-transport — the FR-705..708
arc is witnessed only by mocks; cancellation of live TLS work is a physical
phenomenon (mock_escape_hatch). This test races two live providers with a
3 s timeout and asserts the teardown invariants in WHICHEVER outcome shape
occurs (assert_path_not_destination): "gemini will lose" is a bias, not a
contract.

Judgement pins:
- F1: SDKs spawn persistent pool/poller threads on first use — the thread
  baseline is taken AFTER a per-provider warm-up call, never pre-race.
  FR-713 extends this: the persistent bridge loop thread
  (yamlgraph-bridge-loop) is architecture, not leakage — warmed up before
  the baseline like the SDK pools.
- F2: an abandoned loser legally lives until the CLIENT timeout (FR-708),
  not CLEANUP_GRACE — LLM_REQUEST_TIMEOUT=5 fixture; settle window =
  client timeout + margin.
- F4: explicit shape dispatch; an unrecognized shape fails.
- FR-713 AC-02 re-derivation: the old `race-bridge` survivor assertion
  became vacuous with the thread rename — re-pinned to: exactly ONE
  yamlgraph-bridge-loop thread, zero per-invocation bridge threads.
"""

from __future__ import annotations

import contextlib
import logging
import os
import threading
import time
from pathlib import Path

import pytest

from yamlgraph.node_factory.race_node import (
    CLEANUP_GRACE,
    AllCandidatesFailedError,
    create_race_node,
)

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
    pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set",
    ),
]

PROMPTS_DIR = Path(__file__).parent / "fixtures" / "prompts"
RACE_TIMEOUT = 3.0
# F2 wanted 5s, but the field said no: google rejects deadlines < 10s
# ("Manually set deadline 5s is too short. Minimum allowed deadline is 10s.")
# — a real-transport fact no mock could produce; recorded in the FR.
CLIENT_TIMEOUT = 10.0
SETTLE_MARGIN = 3.0
VERDICT_BUDGET = RACE_TIMEOUT + CLEANUP_GRACE + 1.0
RACES = 3

CANDIDATES = [
    # Bias, not contract: the heavier gemini model is more likely to lose
    # a 3 s race against haiku. Whoever loses gets their teardown verified.
    {"provider": "anthropic", "model": "claude-haiku-4-5"},
    {"provider": "google", "model": "gemini-2.5-pro"},
]

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _propagate_yamlgraph_logs():
    """yamlgraph logger has propagate=False; caplog needs propagation."""
    parent = logging.getLogger("yamlgraph")
    original = parent.propagate
    parent.propagate = True
    yield
    parent.propagate = original


def _warm_up(node_fn) -> None:
    """F1: first use spawns persistent SDK pool/poller threads — do it
    before the baseline so the baseline is architecture, not leakage.

    FR-713: one full uncounted race warms the persistent bridge loop AND
    its executor pool (asyncio_N workers spawn on first to_thread use and
    persist by design) — the counted races must reuse, not grow, them."""
    from yamlgraph.utils.llm_factory import create_llm

    for cand in CANDIDATES:
        llm = create_llm(provider=cand["provider"], model=cand["model"])
        llm.invoke("Say OK.")
    with contextlib.suppress(AllCandidatesFailedError):
        node_fn({"_loop_counts": {}, "errors": []})
        # warm-up cares about machinery, not outcome
    # F2 window: the warm-up loser may hold an executor worker busy until
    # the CLIENT timeout; baseline must be taken at steady idle.
    time.sleep(CLIENT_TIMEOUT + 1.0)


def _settle_to(baseline_count: int) -> tuple[int, list[str]]:
    """Poll until thread count returns to baseline within the F2 window."""
    deadline = time.monotonic() + CLIENT_TIMEOUT + SETTLE_MARGIN
    while time.monotonic() < deadline:
        threads = threading.enumerate()
        if len(threads) <= baseline_count:
            break
        time.sleep(0.2)
    threads = threading.enumerate()
    return len(threads), sorted(t.name for t in threads)


@pytest.mark.req("REQ-YG-269")
def test_race_loser_teardown_live(monkeypatch, caplog) -> None:
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT", str(CLIENT_TIMEOUT))

    node_config = {
        "type": "race",
        "prompt": "teardown_probe",
        "state_key": "answer",
        "timeout": RACE_TIMEOUT,
        "parse_json": True,
        "candidates": [dict(c) for c in CANDIDATES],
    }
    node_fn = create_race_node(
        "teardown_probe_race",
        node_config,
        defaults={"prompts_dir": str(PROMPTS_DIR)},
    )

    _warm_up(node_fn)
    baseline_count = len(threading.enumerate())
    baseline_names = sorted(t.name for t in threading.enumerate())
    logger.info("post-warm-up baseline: %d threads %s", baseline_count, baseline_names)

    shapes: list[str] = []
    # FR-713: drain WARNINGs are emitted by yamlgraph.utils.bridge now —
    # capture the whole yamlgraph namespace (propagation via fixture).
    with caplog.at_level(logging.WARNING, logger="yamlgraph"):
        for i in range(RACES):
            start = time.monotonic()
            # F4: explicit shape dispatch — an unrecognized shape fails.
            try:
                result = node_fn({"_loop_counts": {}, "errors": []})
            except AllCandidatesFailedError as exc:
                duration = time.monotonic() - start
                shape = "neither-completed"
                # FR-705 contract: BOTH candidates named.
                assert "anthropic/" in str(exc) and "google/" in str(exc), str(exc)
            else:
                duration = time.monotonic() - start
                winner = result.get("_race_winner") or {}
                assert winner.get("provider") in {
                    "anthropic",
                    "google",
                }, f"unrecognized shape: no winner in {result.keys()}"
                loser = next(
                    c["provider"]
                    for c in CANDIDATES
                    if c["provider"] != winner["provider"]
                )
                shape = f"winner={winner['provider']} loser={loser}"

            shapes.append(f"race{i + 1}: {shape} verdict={duration:.2f}s")

            # Invariant 1: verdict within budget on real transport.
            assert duration < VERDICT_BUDGET, (
                f"race {i + 1}: verdict took {duration:.2f}s "
                f"(budget {VERDICT_BUDGET}s) — {shape}"
            )

            # Invariant 2 (F1/F2): threads settle to post-warm-up baseline
            # within client-timeout + margin. FR-713 AC-02: exactly one
            # persistent loop thread; zero per-invocation bridge threads.
            count, names = _settle_to(baseline_count)
            assert (
                count <= baseline_count
            ), f"race {i + 1}: thread growth {baseline_count} -> {count}: {names}"
            assert names.count("yamlgraph-bridge-loop") == 1, (
                f"race {i + 1}: expected exactly one persistent bridge loop "
                f"thread: {names}"
            )
            assert not any(
                "race-bridge" in n for n in names
            ), f"race {i + 1}: per-invocation bridge thread survived: {names}"

    # Invariant 3: log discipline — clean drain, or WARNING naming the
    # abandoned candidate; anything anonymous fails.
    abandons = [r for r in caplog.records if "abandoned" in r.getMessage()]
    for rec in abandons:
        msg = rec.getMessage()
        assert "race-" in msg, f"anonymous abandon WARNING: {msg}"

    # Invariant 4: repeatability — zero net growth after all races
    # (the Fly-freeze accumulation signature, against real channels).
    final_count, final_names = _settle_to(baseline_count)
    assert final_count <= baseline_count, (
        f"net thread growth after {RACES} races: "
        f"{baseline_count} -> {final_count}: {final_names}"
    )

    # read_raw_output_first: the shapes taken are part of the artifact.
    logger.info("shapes: %s | abandon-warnings: %d", "; ".join(shapes), len(abandons))
    print(f"\nFR-709 shapes: {'; '.join(shapes)} | abandon-warnings: {len(abandons)}")
