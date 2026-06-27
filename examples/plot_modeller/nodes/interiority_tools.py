"""Interiority A/B experiment — deterministic leaf tools (no LLM).

Two side-effect-free helpers the ``interiority_ab`` graph calls:

- :func:`build_blind_pairs` shuffles the three arm sketches into two blinded
  pairwise comparisons (B-vs-A1, B-vs-A0) so the judge cannot tell which arm it
  reads. The shuffle is *deterministic* in the run ``seed`` (reproducible, yet
  varied across draws), and the true arm behind each slot is preserved so
  :func:`tally_ab` can de-anonymise the verdict afterward.
- :func:`tally_ab` joins each blind verdict back to its arm, records the winning
  arm per contrast, and counts interiority defects per arm. One graph run yields
  one observation; aggregate across runs (seeds x draws) for a preference rate.
"""

from __future__ import annotations

VALID_WINNERS = {"A", "B", "TIE"}


def _as_dict(value: object) -> dict:
    """Normalise a state value (dict or Pydantic model) to a plain dict (boundary).

    A schema'd judge node returns a ``PairVerdict`` Pydantic model, not a dict, so
    coerce here at the consumption boundary before any ``.get`` — never downstream.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value if isinstance(value, dict) else {}


def _norm_winner(raw: object) -> str:
    """Normalise a judge ``winner`` field to ``A`` / ``B`` / ``TIE`` at the boundary."""
    token = str(raw or "").strip().upper()
    if token.startswith("TIE") or token == "T":
        return "TIE"
    if token.startswith("A"):
        return "A"
    if token.startswith("B"):
        return "B"
    return "TIE"


def _swap(seed: int, offset: int) -> bool:
    """Deterministic slot-swap decision for a contrast, keyed by (seed, offset)."""
    return (int(seed) + offset) % 2 == 1


def build_blind_pairs(state: dict) -> dict:
    """Shuffle the three arm sketches into two blinded pairwise comparisons.

    Reads ``sketch_a0`` / ``sketch_a1`` / ``sketch_b`` and ``seed``. Emits, for
    each contrast, the blinded slot texts (``*_a_text`` / ``*_b_text``), the true
    arm behind each slot (``*_a_arm`` / ``*_b_arm``), and a stable ``*_pair_id``.
    """
    sketch_b = state.get("sketch_b", "")
    sketch_a1 = state.get("sketch_a1", "")
    sketch_a0 = state.get("sketch_a0", "")
    seed = state.get("seed", 0)

    out: dict = {}

    # Contrast 1: B vs A1
    if _swap(seed, 0):
        out.update(p1_a_text=sketch_a1, p1_a_arm="A1", p1_b_text=sketch_b, p1_b_arm="B")
    else:
        out.update(p1_a_text=sketch_b, p1_a_arm="B", p1_b_text=sketch_a1, p1_b_arm="A1")
    out["p1_pair_id"] = "B_vs_A1"

    # Contrast 2: B vs A0 (opposite default parity so the two contrasts vary)
    if _swap(seed, 1):
        out.update(p2_a_text=sketch_a0, p2_a_arm="A0", p2_b_text=sketch_b, p2_b_arm="B")
    else:
        out.update(p2_a_text=sketch_b, p2_a_arm="B", p2_b_text=sketch_a0, p2_b_arm="A0")
    out["p2_pair_id"] = "B_vs_A0"

    return out


def _resolve(verdict: dict, a_arm: str, b_arm: str) -> dict:
    """De-anonymise one blind verdict: winning arm + per-arm defect counts."""
    winner = _norm_winner(verdict.get("winner"))
    if winner == "A":
        winner_arm = a_arm
    elif winner == "B":
        winner_arm = b_arm
    else:
        winner_arm = "tie"
    a_defects = verdict.get("a_defects") or []
    b_defects = verdict.get("b_defects") or []
    return {
        "winner_arm": winner_arm,
        "defects": {a_arm: len(a_defects), b_arm: len(b_defects)},
    }


def tally_ab(state: dict) -> dict:
    """Join both blind verdicts back to arms; record winners and defect counts.

    One observation per run. ``verdict.b_wins_ba1`` / ``b_wins_ba0`` are the
    booleans to aggregate across seeds x draws for the B-vs-A1 / B-vs-A0
    preference rates that decide GO / KILL / REVISE.
    """
    ba1 = _resolve(
        _as_dict(state.get("verdict_ba1")),
        state.get("p1_a_arm", "A"),
        state.get("p1_b_arm", "B"),
    )
    ba0 = _resolve(
        _as_dict(state.get("verdict_ba0")),
        state.get("p2_a_arm", "A"),
        state.get("p2_b_arm", "B"),
    )
    return {
        "verdict": {
            "ba1": ba1,
            "ba0": ba0,
            "b_wins_ba1": ba1["winner_arm"] == "B",
            "b_wins_ba0": ba0["winner_arm"] == "B",
            "note": (
                "single observation; aggregate b_wins_* across seeds x draws for "
                "a preference rate (GO if B beats A1 in a clear majority)"
            ),
        }
    }
