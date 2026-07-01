"""Reference gate adapter for plot path beats.

Extracts all entity references from a plot path's beats and checks
they resolve against the canon. Reuses the same orphan-detection logic
as ref_gate but operates on the plot_path shape, not drafted_page.
"""

from __future__ import annotations

from typing import Any


def check_path_references(state: dict[str, Any]) -> dict[str, Any]:
    """Check all references in plot path beats resolve to canon entities.

    Reads:
        state["plot_path"]: dict with "beats" list, each beat has
            "actors", "references", and "moves_tension.edge"
        state["canon"]: dict keyed by page id

    Returns:
        {"gate_result": {"valid": bool, "violations": list[str]}}
    """
    plot_path = state.get("plot_path", {})
    canon = state.get("canon", {})

    # Pydantic model → dict
    if hasattr(plot_path, "model_dump"):
        plot_path = plot_path.model_dump()

    existing_ids = set(canon.keys())
    violations: list[str] = []

    beats = plot_path.get("beats", [])
    for i, beat in enumerate(beats):
        beat_data = dict(beat) if isinstance(beat, dict) else beat

        # Check actors
        for actor in beat_data.get("actors", []):
            if actor not in existing_ids:
                violations.append(f"beat {i}: orphan actor '{actor}'")

        # Check references
        for ref in beat_data.get("references", []):
            if ref not in existing_ids:
                violations.append(f"beat {i}: orphan reference '{ref}'")

        # Check moves_tension edge targets
        tension = beat_data.get("moves_tension", {})
        if isinstance(tension, dict):
            edge = tension.get("edge", "")
            if edge and "->" in edge:
                parts = edge.split("->")
                for part in parts:
                    part = part.strip()
                    if part and part not in existing_ids:
                        violations.append(f"beat {i}: orphan edge target '{part}'")

    return {
        "gate_result": {"valid": not violations, "violations": violations},
    }
