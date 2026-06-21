"""Compile a (throwaway) ``PlotPlan`` into a ``unified-planning`` problem -- FR-559 spike ONLY.

Three load-bearing encoding rules from the FR judgement:

* **Belief-as-fluent.** ``Belief(observer, fluent, held)`` becomes a plain boolean fluent
  ``bel_<obs>_<pred>_<args>``, independent of the world fluent ``w_<pred>_<args>``. F1 can flip
  ``bel_clan_alive_arnulf := False`` while leaving ``w_alive_arnulf := True`` -- the floodmark
  distinction, carried by a *classical* planner with no epistemic model.

* **Mandatory goal-required steps (J2).** A classical planner does not *fail* on an action with
  an unsatisfiable precondition -- it simply skips it. So every ``Function`` compiles to an action
  with a unique ``done_<id>`` effect, and the goal ``G`` conjoins every ``done_<id>``. An
  unschedulable beat then makes the *goal* unreachable -> proven unsolvable, instead of
  solved-by-skipping.

* **Chapter ordinal as a strict sequencing chain (J3).** STRIPS has no clock. Chapters become
  mutually-exclusive ``at_chapter_<n>`` markers advanced by ``advance_<ci>_<cj>`` actions whose
  preconditions require *every* chapter-``ci`` beat done. A beat at chapter ``c`` requires
  ``at_chapter_<c>``, so you cannot fire a Ch3 beat after advancing to Ch6 -- which is exactly
  what makes the early-reveal variant provably unsolvable.
"""

from __future__ import annotations

from unified_planning.model import Fluent as UpFluent
from unified_planning.model import InstantaneousAction, Problem
from unified_planning.shortcuts import BoolType, Not

from .schema import Belief, Fluent, PlotPlan


def _slug(*parts: str) -> str:
    return "_".join(str(p) for p in parts).replace(" ", "_").lower()


def _world_name(f: Fluent) -> str:
    return _slug("w", f.pred, *f.args)


def _belief_name(b: Belief) -> str:
    return _slug("bel", b.observer, b.fluent.pred, *b.fluent.args)


def _ensure(problem: Problem, fluents: dict[str, UpFluent], name: str) -> UpFluent:
    if name not in fluents:
        f = UpFluent(name, BoolType())
        problem.add_fluent(f, default_initial_value=False)
        fluents[name] = f
    return fluents[name]


def _require_bool(f: Fluent) -> bool:
    if not isinstance(f.value, bool):
        raise NotImplementedError(
            f"spike supports only boolean world fluents; got {f.pred}={f.value!r}"
        )
    return f.value


def build_problem(plan: PlotPlan) -> Problem:
    """``PlotPlan`` -> ``up.Problem`` with belief reified and mandatory ``done_<id>`` steps."""
    problem = Problem("floodmark_spike")
    fluents: dict[str, UpFluent] = {}

    # --- declare + initialise world / belief fluents ---------------------------------------
    for wf in plan.initial_world:
        f = _ensure(problem, fluents, _world_name(wf))
        problem.set_initial_value(f(), _require_bool(wf))
    for bf in plan.initial_belief:
        f = _ensure(problem, fluents, _belief_name(bf))
        problem.set_initial_value(f(), bool(bf.held))

    # --- chapter sequencing chain (J3) -----------------------------------------------------
    chapters = sorted({fn.chapter for fn in plan.functions})
    chapter_markers: dict[int, UpFluent] = {
        c: _ensure(problem, fluents, _slug("at_chapter", str(c))) for c in chapters
    }
    if chapters:
        problem.set_initial_value(chapter_markers[chapters[0]](), True)

    # --- per-function ``done`` markers (J2) ------------------------------------------------
    done: dict[str, UpFluent] = {
        fn.id: _ensure(problem, fluents, _slug("done", fn.id)) for fn in plan.functions
    }

    # --- one action per authored beat ------------------------------------------------------
    predecessors: dict[str, list[str]] = {fn.id: [] for fn in plan.functions}
    for before, after in plan.order:
        predecessors.setdefault(after, []).append(before)

    for fn in plan.functions:
        act = InstantaneousAction(_slug("do", fn.id))
        act.add_precondition(chapter_markers[fn.chapter]())
        act.add_precondition(Not(done[fn.id]()))
        for pred_id in predecessors.get(fn.id, []):
            act.add_precondition(done[pred_id]())
        for wf in fn.pre_world:
            f = _ensure(problem, fluents, _world_name(wf))
            act.add_precondition(f() if _require_bool(wf) else Not(f()))
        for bf in fn.pre_belief:
            f = _ensure(problem, fluents, _belief_name(bf))
            act.add_precondition(f() if bf.held else Not(f()))

        act.add_effect(done[fn.id](), True)
        for wf in fn.eff_world:
            f = _ensure(problem, fluents, _world_name(wf))
            act.add_effect(f(), _require_bool(wf))
        for bf in fn.eff_belief:
            f = _ensure(problem, fluents, _belief_name(bf))
            act.add_effect(f(), bool(bf.held))
        problem.add_action(act)

    # --- advance actions: no chapter may be left with an unfired beat ----------------------
    for ci, cj in zip(chapters, chapters[1:], strict=False):
        adv = InstantaneousAction(_slug("advance", str(ci), str(cj)))
        adv.add_precondition(chapter_markers[ci]())
        for fn in plan.functions:
            if fn.chapter == ci:
                adv.add_precondition(done[fn.id]())
        adv.add_effect(chapter_markers[ci](), False)
        adv.add_effect(chapter_markers[cj](), True)
        problem.add_action(adv)

    # --- goal: every beat fired (J2) + authored world invariants ---------------------------
    for fn in plan.functions:
        problem.add_goal(done[fn.id]())
    for gf in plan.goals:
        f = _ensure(problem, fluents, _world_name(gf))
        problem.add_goal(f() if _require_bool(gf) else Not(f()))

    return problem


__all__ = ["build_problem"]
