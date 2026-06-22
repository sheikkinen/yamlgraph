"""Author + validate the v3 plot lane (FR-563 M4a) -- the LLM-JSON boundary into the typed plan.

Two leaf-pure pieces, no engine, no I/O:

* :func:`parse_plot_plan` -- the tolerant boundary parse mirroring
  :func:`world_state.parse_world_state`. The authoring LLM's JSON is untrusted input, so unknown
  top-level fields and off-alphabet functions/atoms are dropped rather than raised on; a
  structurally hopeless payload yields an empty plan. Normalize at the boundary; never substitute a
  plausible-but-wrong plan, return the empty truth.
* :func:`plot_validate_plan` -- the ``python``-node function the ``plot_plan.yaml`` graph routes on.
  It returns ``{"validation": {"ok", "flaws"}}`` -- a dict the python node merges at state top level,
  so the deterministic edge condition ``validation.ok == true`` resolves (FR-563 J1). Authoring is
  engine-free: only the four pure narrative-invariant checks run, never the optional UP solve (J4).
"""

from __future__ import annotations

import logging
from typing import get_args

from .schema import AffectKind, Function, FunctionKind, PlotPlan, WorldPred
from .validate import validate_plan

logger = logging.getLogger(__name__)

_FUNCTION_KINDS = frozenset(get_args(FunctionKind))
_WORLD_PREDS = frozenset(get_args(WorldPred))
_AFFECT_KINDS = frozenset(get_args(AffectKind))
_PLAN_FIELDS = frozenset(PlotPlan.model_fields)
_FUNCTION_FIELDS = frozenset(Function.model_fields)


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _is_grounded_fluent(raw: object) -> bool:
    return isinstance(raw, dict) and raw.get("pred") in _WORLD_PREDS


def _is_grounded_belief(raw: object) -> bool:
    return (
        isinstance(raw, dict)
        and isinstance(raw.get("fluent"), dict)
        and raw["fluent"].get("pred") in _WORLD_PREDS
    )


def _clean_function(raw: object) -> dict | None:
    """Keep only known fields and on-alphabet atoms; ``None`` if the kind is off-alphabet."""
    if not isinstance(raw, dict) or raw.get("kind") not in _FUNCTION_KINDS:
        return None
    func = {k: v for k, v in raw.items() if k in _FUNCTION_FIELDS}
    for world_key in ("pre_world", "eff_world"):
        if world_key in func:
            func[world_key] = [
                a for a in _as_list(func[world_key]) if _is_grounded_fluent(a)
            ]
    for belief_key in ("pre_belief", "eff_belief"):
        if belief_key in func:
            func[belief_key] = [
                b for b in _as_list(func[belief_key]) if _is_grounded_belief(b)
            ]
    if "eff_affect" in func:
        func["eff_affect"] = [
            a
            for a in _as_list(func["eff_affect"])
            if isinstance(a, dict) and a.get("kind") in _AFFECT_KINDS
        ]
    return func


def parse_plot_plan(raw: object) -> PlotPlan:
    """Validate authoring JSON into a :class:`PlotPlan`, tolerant at the boundary.

    A well-formed dict is cleaned (unknown fields and off-alphabet functions/atoms dropped) and
    validated; anything else -- a prose string, ``None``, junk -- yields an empty plan rather than
    raising mid-pipeline. Mirrors :func:`world_state.parse_world_state`.
    """
    if not isinstance(raw, dict):
        return PlotPlan()
    data = {k: v for k, v in raw.items() if k in _PLAN_FIELDS}
    data["functions"] = [
        f
        for f in (_clean_function(r) for r in _as_list(data.get("functions")))
        if f is not None
    ]
    data["initial_world"] = [
        a for a in _as_list(data.get("initial_world")) if _is_grounded_fluent(a)
    ]
    data["goals"] = [a for a in _as_list(data.get("goals")) if _is_grounded_fluent(a)]
    data["initial_belief"] = [
        b for b in _as_list(data.get("initial_belief")) if _is_grounded_belief(b)
    ]
    try:
        return PlotPlan.model_validate(data)
    except Exception:
        return PlotPlan()


def plot_validate_plan(state: dict) -> dict:
    """Graph node: parse ``state['raw']`` and run the four pure checks -> routable verdict.

    Returns ``{"validation": {"ok": bool, "flaws": [...]}}``. The python node merges this dict at
    the state top level, so the ``plot_plan.yaml`` edges route on ``validation.ok == true`` /
    ``validation.ok == false`` (FR-563 J1). Engine-free: only :func:`validate_plan`'s pure checks
    run, never the optional UP solve (J4).
    """
    raw = state.get("raw")
    if raw is None:
        raw = state.get("plan_raw")
    plan = parse_plot_plan(raw)
    result = validate_plan(plan)
    return {
        "validation": {
            "ok": result.ok,
            "flaws": [flaw.model_dump() for flaw in result.flaws],
        }
    }


__all__ = ["parse_plot_plan", "plot_validate_plan"]
