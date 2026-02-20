"""Chaos tool for streaming fault injection tests (FR-062).

Used by tests/fixtures/chaos_graph.yaml to simulate failure modes
in the streaming pipeline. Failure mode controlled by CHAOS_MODE env var.
"""

import os
import time


class SimulatedRateLimitError(Exception):
    """Mock rate limit for testing — real providers use different classes."""

    pass


def chaos_respond(state: dict) -> dict:
    """Python node that simulates various failure modes based on env vars.

    Modes (set via CHAOS_MODE env var):
        normal: return a normal response (default)
        fail: raise RuntimeError
        rate_limit: raise SimulatedRateLimitError
        slow: sleep for CHAOS_DELAY seconds (default 5)
    """
    mode = os.environ.get("CHAOS_MODE", "normal")

    if mode == "fail":
        raise RuntimeError("Simulated LLM failure")
    elif mode == "rate_limit":
        raise SimulatedRateLimitError("429 Too Many Requests")
    elif mode == "slow":
        time.sleep(float(os.environ.get("CHAOS_DELAY", "5")))
        return {"response": "delayed response"}
    else:
        return {"response": "normal response"}
