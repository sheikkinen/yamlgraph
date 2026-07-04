"""Deterministic tool for the first-class verification demo (FR-677).

No LLM, no network — the demo runs offline so the guard and verify
behaviour is fully reproducible.
"""


def score_batch(state: dict) -> dict:
    """Sum a list of integer readings into a single score.

    Args:
        state: Contains ``readings`` (list of ints), injected by variables:.

    Returns:
        Dict with the computed ``score``.
    """
    readings = state["readings"]
    return {"score": sum(readings)}
