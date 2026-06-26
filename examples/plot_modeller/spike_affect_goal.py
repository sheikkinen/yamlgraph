#!/usr/bin/env python
"""FR-607 — goal-anchored affect referent spike (does naming the GOAL sharpen WHERE).

Hypothesis: an emotion is an appraisal of events RELATIVE TO A GOAL (Lazarus 1991,
Roseman 1996, OCC). FR-605's two-pass locate is blind to L1/L2/L6 — its prompts
never say "goal". This spike forks pass 2 (affect_locate_goal) to inject the
protagonist's candidate goals and bind each feeling to one, then asks whether that
anchoring moves the FROZEN gate (open/close placement recall).

Three arms, each >= ``--draws`` draws @ temp 0.7:

  control  no goals (FR-605 affect_locate)              -> localization baseline
  modeA    inject GT goals (referents U motivation)     -> CEILING + referent-binding
  modeB    inject MODEL goals (affect_goals mini-L2)    -> production path

Scoring (J corrections):
  strict   ev._l7_counts                       (beat-exact, referent-blind) -> arm-A-comparable
  relaxed  ev._l7_counts_referent(require_referent=False)  (beat -> goal-beat-set)
  referent ev._l7_counts_referent(require_referent=True)   (mode A only: right goal?)

  HONEST LIFT (J correction 1) = modeA.relaxed - control.relaxed  (the goal signal,
  net of the matcher loosening the relaxed scorer applies to BOTH arms equally).

Verdict (J corrections 2-4):
  - referent-recall is REPORTED CONDITIONED ON pass-1 set recall (the cap).
  - CONFIRMED if mode A strict recall clears KILL (0.50) with referent-binding > 0.
  - GO only if mode B strict recall ALSO beats arm A 0.214 (production path helps).
  - else PARTIAL; REFUTED if mode A does not even beat arm A.

Run from repo root (mode B is gated on mode A clearing, to bound API cost):
  set -a; source .env; set +a; \
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    .venv/bin/python examples/plot_modeller/spike_affect_goal.py --draws 2
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

import evaluate as ev  # noqa: E402
from nodes.tools import _strip_code_fences, load_glosses_with_kinds  # noqa: E402
from spike_affect_per_kind import (  # noqa: E402
    KIND_SPECS,
    _arm_a_baseline,
    _norm,
    _protagonist,
)
from spike_affect_twopass import _pass1_set, _skeleton  # noqa: E402

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results" / "l7_goal"
GOAL_DESCS = EXAMPLE_DIR / "fixtures" / "goal_descriptions.yaml"

KILL = 0.50
ARM_A_RECALL = 0.214
LIFT_NOISE = (
    0.02  # honest-lift below this is indistinguishable from draw noise (FR-603)
)


def _gt_goal_set(gt_path: Path, descs: dict) -> list[dict]:
    """Mode A injected set: (referents used) U (protagonist motivation goals), each
    with its leak-audited description. Realistic distractors ride alongside the true
    referents so binding is not a one-option giveaway."""
    data = yaml.safe_load(gt_path.read_text(encoding="utf-8"))
    prot = _protagonist(ev._load_gt_affects(gt_path))
    goals = set()
    for fn in data.get("functions", []):
        mot = fn.get("motivation")
        if isinstance(mot, dict) and mot.get("agent") == prot and mot.get("goal"):
            goals.add(mot["goal"])
        for a in fn.get("eff_affect") or []:
            if isinstance(a, dict) and a.get("referent"):
                goals.add(a["referent"])
    file_descs = descs[gt_path.stem]
    return [{"id": g, "desc": file_descs[g]} for g in sorted(goals) if g in file_descs]


def _model_goal_set(
    glosses: list, agent: str, provider: str, model: str, out_dir: Path
) -> list[dict]:
    """Mode B injected set: the protagonist's NAMED goals as the model proposes them."""
    raw = execute_prompt(
        "affect_goals",
        state={"glosses": glosses, "agent": agent},
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_goals.yaml").write_text(str(raw or ""), encoding="utf-8")
    try:
        data = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if isinstance(item, dict) and item.get("id") and item.get("desc"):
            out.append({"id": str(item["id"]), "desc": str(item["desc"])})
    return out


def _locate_goal(
    glosses: list,
    agent: str,
    kind: str,
    skeleton: list,
    goals: list[dict] | None,
    provider: str,
    model: str,
    out_dir: Path,
) -> dict:
    """Pass 2: locate open/close (and referent when goals are injected)."""
    spec = KIND_SPECS[kind]
    prompt = "affect_locate_goal" if goals else "affect_locate"
    state = {
        "glosses": glosses,
        "agent": agent,
        "kind": kind,
        "definition": spec["definition"],
        "open_cue": spec["open_cue"],
        "close_cue": spec["close_cue"],
        "relational": spec["relational"],
        "toward_hint": spec.get("toward_hint", ""),
        "skeleton": skeleton,
        "explain": False,
    }
    if goals:
        state["goals"] = goals
    raw = execute_prompt(
        prompt,
        state=state,
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{kind}.yaml").write_text(str(raw or ""), encoding="utf-8")
    try:
        data = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _valid_beat(bid: object, valid_ids: set) -> str | None:
    if bid is None:
        return None
    s = str(bid).strip()
    return s if s in valid_ids else None


def _build_predictions(
    located: dict, agent: str, valid_ids: set, goal_ids: set
) -> list[dict]:
    """located: {kind: {open, close, toward, referent}} -> [{id, eff_affect:[...]}].

    Carries the bound referent into each delta (validated against the injected goal
    ids; an off-list referent is dropped to None, never invented)."""
    by_beat: dict[str, list] = {}
    for kind, loc in located.items():
        spec = KIND_SPECS[kind]
        toward = loc.get("toward") if spec["relational"] else None
        ref = loc.get("referent")
        ref = str(ref) if ref is not None and str(ref) in goal_ids else None
        for op in ("open", "close"):
            bid = _valid_beat(loc.get(op), valid_ids)
            if bid is None:
                continue
            delta = {"op": op, "char": agent, "kind": kind}
            if spec["relational"] and toward:
                delta["toward"] = toward
            if ref:
                delta["referent"] = ref
            by_beat.setdefault(bid, []).append(delta)
    return [{"id": bid, "eff_affect": deltas} for bid, deltas in by_beat.items()]


def _run_arm(mode: str, draw: int, provider: str, model: str, descs: dict) -> dict:
    """One draw of one arm. mode in {control, modeA, modeB}."""
    agg = {
        "strict_rh": 0,
        "strict_gt": 0,
        "strict_ph": 0,
        "strict_pred": 0,
        "relax_rh": 0,
        "ref_rh": 0,
        "set_named": 0,
        "set_gt": 0,
    }
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _protagonist(tbi)
        glosses = load_glosses_with_kinds(gt_path)
        valid_ids = {str(g.get("id")) for g in glosses if g.get("id")}
        skeleton = _skeleton(glosses)
        out_dir = RESULTS_DIR / mode / f"draw{draw}" / genre

        if mode == "modeA":
            goals = _gt_goal_set(gt_path, descs)
        elif mode == "modeB":
            goals = _model_goal_set(glosses, prot, provider, model, out_dir)
        else:
            goals = None
        goal_ids = {g["id"] for g in goals} if goals else set()

        named = _pass1_set(glosses, prot, provider, model, out_dir)
        gt_kinds = {_norm(d.get("kind")) for ds in tbi.values() for d in ds}
        agg["set_gt"] += len(gt_kinds)
        agg["set_named"] += len(gt_kinds & set(named))

        located: dict = {}
        for kind in named:
            try:
                located[kind] = _locate_goal(
                    glosses, prot, kind, skeleton, goals, provider, model, out_dir
                )
            except Exception as exc:  # hard failure -> skip, not a crash
                print(f"  x {mode}/{genre}/{prot}/{kind}: {exc}")

        pred = _build_predictions(located, prot, valid_ids, goal_ids)

        strict = ev._l7_counts(pred, tbi)
        relax = ev._l7_counts_referent(pred, tbi, require_referent=False)
        agg["strict_rh"] += strict["recall_hits"]
        agg["strict_gt"] += strict["gt"]
        agg["strict_ph"] += strict["precision_hits"]
        agg["strict_pred"] += strict["pred"]
        agg["relax_rh"] += relax["recall_hits"]
        if mode == "modeA":
            ref = ev._l7_counts_referent(pred, tbi, require_referent=True)
            agg["ref_rh"] += ref["recall_hits"]

    gt = agg["strict_gt"]
    return {
        "strict_recall": agg["strict_rh"] / gt if gt else 0.0,
        "strict_precision": agg["strict_ph"] / agg["strict_pred"]
        if agg["strict_pred"]
        else 0.0,
        "relax_recall": agg["relax_rh"] / gt if gt else 0.0,
        "ref_recall": agg["ref_rh"] / gt if gt else 0.0,
        "set_recall": agg["set_named"] / agg["set_gt"] if agg["set_gt"] else 0.0,
        "counts": agg,
    }


def _mean_arm(draws: list[dict], key: str) -> float:
    return statistics.mean(d[key] for d in draws) if draws else 0.0


def _run_arm_draws(
    mode: str, n: int, provider: str, model: str, descs: dict
) -> list[dict]:
    out = []
    for d in range(1, n + 1):
        res = _run_arm(mode, d, provider, model, descs)
        out.append(res)
        line = (
            f"  {mode} draw {d}: strict {res['strict_recall']:.3f} "
            f"prec {res['strict_precision']:.3f} relax {res['relax_recall']:.3f} "
            f"set {res['set_recall']:.3f}"
        )
        if mode == "modeA":
            line += f" referent {res['ref_recall']:.3f}"
        print(line)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="FR-607 goal-anchored affect spike")
    ap.add_argument("--draws", type=int, default=2)
    args = ap.parse_args()
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    descs = yaml.safe_load(GOAL_DESCS.read_text(encoding="utf-8"))

    arm_a = _arm_a_baseline()
    print("== arm A (char-pinned single pass, FR-604 baseline) ==")
    print(f"  recall {arm_a['recall']:.3f}  precision {arm_a['precision']:.3f}\n")

    print(f"== control (no goals, FR-605 locate), {args.draws} draws ==")
    control = _run_arm_draws("control", args.draws, provider, model, descs)

    print(f"\n== mode A (inject GT goals = ceiling), {args.draws} draws ==")
    modeA = _run_arm_draws("modeA", args.draws, provider, model, descs)

    a_strict = _mean_arm(modeA, "strict_recall")
    a_relax = _mean_arm(modeA, "relax_recall")
    a_ref = _mean_arm(modeA, "ref_recall")
    a_set = _mean_arm(modeA, "set_recall")
    c_relax = _mean_arm(control, "relax_recall")
    c_strict = _mean_arm(control, "strict_recall")

    modeB: list[dict] = []
    if a_strict >= KILL:
        print(f"\n== mode B (inject MODEL goals = production), {args.draws} draws ==")
        modeB = _run_arm_draws("modeB", args.draws, provider, model, descs)
    else:
        print(f"\n== mode B SKIPPED: mode A strict {a_strict:.3f} < KILL {KILL} ==")

    b_strict = _mean_arm(modeB, "strict_recall") if modeB else 0.0

    honest_lift = a_relax - c_relax
    print("\n== FR-607 verdict ==")
    print(f"  control  strict {c_strict:.3f}  relax {c_relax:.3f}")
    print(
        f"  mode A   strict {a_strict:.3f}  relax {a_relax:.3f}  referent {a_ref:.3f}"
    )
    print(f"           set-recall {a_set:.3f} (cap on referent — J corr 4)")
    if modeB:
        print(f"  mode B   strict {b_strict:.3f}")
    print(
        f"  HONEST LIFT (modeA.relax - control.relax) = {honest_lift:+.3f}  (J corr 1)"
    )
    print(f"  arm A strict baseline = {ARM_A_RECALL:.3f}\n")

    if a_strict < ARM_A_RECALL:
        verdict = "REFUTED: goal-anchoring (mode A ceiling) does not beat arm A."
    elif honest_lift <= LIFT_NOISE:
        verdict = (
            f"REFUTED (J corr 1): honest lift {honest_lift:+.3f} <= noise {LIFT_NOISE:.3f}. "
            f"Mode A relax {a_relax:.3f} == control relax {c_relax:.3f}: injecting goals did "
            f"NOT move localization. The +{a_strict - ARM_A_RECALL:.3f} over arm A is the "
            f"two-pass decomposition (control alone), not the goal signal. Referent-binding "
            f"{a_ref:.3f} (cap {a_set:.3f}) shows the model rarely binds the right goal even "
            f"at the GT ceiling — appraisal-anchoring as prompted carries no placement lift."
        )
    elif a_strict < KILL:
        verdict = (
            f"PARTIAL: mode A {a_strict:.3f} beats arm A with positive lift {honest_lift:+.3f} "
            f"but does not clear KILL {KILL}; goal signal real but sub-threshold."
        )
    elif a_ref <= 0:
        verdict = "PARTIAL: mode A clears KILL but referent-binding is zero — placement, not anchoring."
    elif not modeB or b_strict <= ARM_A_RECALL:
        verdict = (
            f"PARTIAL (hypothesis CONFIRMED at ceiling): mode A {a_strict:.3f} clears KILL "
            f"with referent {a_ref:.3f}, but mode B {b_strict:.3f} does not beat arm A "
            f"{ARM_A_RECALL:.3f} — model goals do not yet carry the lift."
        )
    else:
        verdict = (
            f"GO: mode A {a_strict:.3f} clears KILL (referent {a_ref:.3f}) AND mode B "
            f"{b_strict:.3f} beats arm A {ARM_A_RECALL:.3f}. Goal-anchoring earns its cost."
        )
    print(f"  {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
