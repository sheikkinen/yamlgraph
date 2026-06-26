#!/usr/bin/env python
"""FR-609 — goal-GRAPH-anchored affect referent spike (does the inter-goal causal
structure disambiguate the sibling referent the flat list could not).

FR-607 refuted goal-anchoring with a flat goal LIST (honest lift +0.000): given two
sibling goal NAMES and no relation between them, the model defaulted the referent to
whichever its salient close beat served. Its autopsy named the mechanism (the goal
label is downstream of the close-beat choice) and an upstream read confirmed L6
already DISTINGUISHES the siblings via ``functions[].motivation.goal`` + the beat
``enables`` chain. This spike injects that chain as a BEAT-FREE goal CAUSAL GRAPH
(goals + inter-goal enables/threatens + agent, every ``F#`` stripped) and asks
whether the STRUCTURE lets the model bind the right sibling AND move the frozen gate.

Comparability partition (J corr 1): placement is scored on two disjoint subsets.
  CLEAN       branching genres (horror, historical, scifi) — referent goals form an
              antichain, so chain order carries NO placement signal; a lift here is
              genuine anchoring. GO can be earned ONLY here.
  QUARANTINED total-order genres (quest, detective) — referent goals are a chain
              isomorphic to beat order; a placement win is order-confounded and is
              reported but cannot promote the lever.

Three arms, each >= ``--draws`` draws @ temp 0.7 (goals injected in SHUFFLED order):
  control  no goals (FR-605 affect_locate)              -> localization baseline
  modeA    inject GT goal GRAPH (referents U motivation) -> CEILING + referent-binding
  modeB    inject MODEL goals (gated on mode A clearing) -> production path

Frozen gate (ev._l7_counts / main_l7) is byte-identical; this is additive.

Run from repo root (mode B gated on mode A clearing KILL, to bound API cost):
  set -a; source .env; set +a; \
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    .venv/bin/python examples/plot_modeller/spike_affect_graph.py --draws 3
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import zlib
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

import evaluate as ev  # noqa: E402
from nodes.tools import _strip_code_fences, load_glosses_with_kinds  # noqa: E402
from spike_affect_goal import (  # noqa: E402
    _build_predictions,
    _model_goal_set,
    _valid_beat,
)
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
RESULTS_DIR = EXAMPLE_DIR / "results" / "l7_graph"
GOAL_DESCS = EXAMPLE_DIR / "fixtures" / "goal_descriptions.yaml"

KILL = 0.50
ARM_A_RECALL = 0.214
LIFT_NOISE = 0.02  # honest-lift below this is indistinguishable from draw noise
REF_BASELINE = 0.143  # FR-607 referent-binding at the GT (flat-list) ceiling


def _shuffled(items: list[dict], seed: int) -> list[dict]:
    """Deterministic, reproducible reorder keyed by ``seed`` (J corr 1: chain order
    must not be readable off the listing). crc32 is a stable non-crypto hash, so the
    order is fixed per (seed, goal-id) yet varies across draws."""
    return sorted(items, key=lambda g: zlib.crc32(f"{seed}:{g['id']}".encode()))


def _gt_graph_set(gt_path: Path, descs: dict, seed: int) -> list[dict]:
    """Mode A injected set: the protagonist's goals + the referent goals, EACH with
    its beat-free inter-goal relations (enables / enabled_by / threatened_by) and a
    leak-audited description. Presented in SHUFFLED order so chain order cannot be
    read off the listing (J corr 1)."""
    graph = ev.derive_goal_graph(gt_path)
    prot = graph["protagonist"]
    refs = set(graph["referent_goals"])
    file_descs = descs[gt_path.stem]
    selected = [
        g
        for g in graph["goals"]
        if (g["agent"] == prot or g["id"] in refs) and g["id"] in file_descs
    ]
    out = [
        {
            "id": g["id"],
            "desc": file_descs[g["id"]],
            "agent": g["agent"],
            "enables": g["enables"],
            "enabled_by": g["enabled_by"],
            "threatened_by": g["threatened_by"],
        }
        for g in selected
    ]
    return _shuffled(out, seed)


def _flat_to_graph(goals: list[dict], prot: str, seed: int) -> list[dict]:
    """Mode B: wrap model-proposed flat goals in the graph shape with EMPTY relations
    (the model graph extractor is deferred — mode B is a lower bound, run only if the
    GT-graph ceiling clears KILL)."""
    out = [
        {
            "id": g["id"],
            "desc": g["desc"],
            "agent": prot,
            "enables": [],
            "enabled_by": [],
            "threatened_by": [],
        }
        for g in goals
    ]
    return _shuffled(out, seed)


def _locate_graph(
    glosses: list,
    agent: str,
    kind: str,
    skeleton: list,
    goals: list[dict] | None,
    provider: str,
    model: str,
    out_dir: Path,
) -> dict:
    """Pass 2: locate open/close and bind the referent using the goal GRAPH."""
    spec = KIND_SPECS[kind]
    prompt = "affect_locate_graph" if goals else "affect_locate"
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


def _run_arm(
    mode: str,
    draw: int,
    provider: str,
    model: str,
    descs: dict,
) -> dict:
    """One draw of one arm. mode in {control, modeA, modeB}. Returns overall counts,
    per-genre strict counts (for the comparability partition), and per-(genre,kind)
    close beats + referents (for the close-beat-distribution-shift metric, J corr 2).
    """
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
    per_genre: dict[str, dict] = {}
    close_beats: dict[tuple[str, str], str | None] = {}
    referents: dict[tuple[str, str], str | None] = {}
    seed = 7919 * draw + 31

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _protagonist(tbi)
        glosses = load_glosses_with_kinds(gt_path)
        valid_ids = {str(g.get("id")) for g in glosses if g.get("id")}
        skeleton = _skeleton(glosses)
        out_dir = RESULTS_DIR / mode / f"draw{draw}" / genre

        if mode == "modeA":
            goals = _gt_graph_set(gt_path, descs, seed)
        elif mode == "modeB":
            flat = _model_goal_set(glosses, prot, provider, model, out_dir)
            goals = _flat_to_graph(flat, prot, seed)
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
                located[kind] = _locate_graph(
                    glosses, prot, kind, skeleton, goals, provider, model, out_dir
                )
            except Exception as exc:  # hard failure -> skip, not a crash
                print(f"  x {mode}/{genre}/{prot}/{kind}: {exc}")

        for kind, loc in located.items():
            close_beats[(genre, kind)] = _valid_beat(loc.get("close"), valid_ids)
            ref = loc.get("referent")
            referents[(genre, kind)] = (
                str(ref) if ref is not None and str(ref) in goal_ids else None
            )

        pred = _build_predictions(located, prot, valid_ids, goal_ids)
        strict = ev._l7_counts(pred, tbi)
        relax = ev._l7_counts_referent(pred, tbi, require_referent=False)
        per_genre[genre] = {"rh": strict["recall_hits"], "gt": strict["gt"]}
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
        "per_genre": per_genre,
        "close_beats": close_beats,
        "referents": referents,
    }


def _subset_recall(draws: list[dict], genres: set[str]) -> float:
    """Mean (over draws) strict recall restricted to ``genres`` — the partition cut."""
    vals = []
    for d in draws:
        rh = sum(d["per_genre"][g]["rh"] for g in genres if g in d["per_genre"])
        gt = sum(d["per_genre"][g]["gt"] for g in genres if g in d["per_genre"])
        vals.append(rh / gt if gt else 0.0)
    return statistics.mean(vals) if vals else 0.0


def _close_shift(control: list[dict], modeA: list[dict]) -> float:
    """J corr 2: share of (genre,kind) whose CLOSE beat differs between control and
    mode A, paired by draw. A high referent-relabel rate with a LOW close-shift means
    the referent moved but the placement did not — the causal arrow is salience ->
    referent, and the lever is dead for the frozen gate."""
    fractions = []
    for c, a in zip(control, modeA, strict=False):
        keys = set(c["close_beats"]) & set(a["close_beats"])
        if not keys:
            continue
        moved = sum(1 for k in keys if c["close_beats"][k] != a["close_beats"][k])
        fractions.append(moved / len(keys))
    return statistics.mean(fractions) if fractions else 0.0


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


def _print_topology() -> int:
    """Graduated from tmp/fr609_topology.py: per-fixture beat-free goal graph and the
    CLEAN / QUARANTINED partition that gates the spike's interpretability."""
    part = ev.goal_graph_partition(GT_DIR)
    for path in sorted(GT_DIR.glob("*.yaml")):
        g = ev.derive_goal_graph(path)
        print(f"\n=== {path.stem} ===")
        print(f"  protagonist: {g['protagonist']}")
        print(f"  enables: {g['enables']}")
        print(f"  threatens: {g['threatens']}")
        print(f"  referent goals: {g['referent_goals']}")
        print(f"  incomparable referent pairs: {g['incomparable_pairs'] or 'none'}")
        print(f"  >>> {g['topology']}")
    print(f"\nCLEAN (GO can be earned here): {part['CLEAN']}")
    print(f"QUARANTINED (order-confounded, not promotable): {part['QUARANTINED']}")
    return 0


def _verdict(
    modeA: list[dict],
    control: list[dict],
    modeB: list[dict],
    clean: set[str],
    quar: set[str],
) -> str:
    a_strict = _mean_arm(modeA, "strict_recall")
    a_ref = _mean_arm(modeA, "ref_recall")
    clean_a = _subset_recall(modeA, clean)
    clean_c = _subset_recall(control, clean)
    clean_lift = clean_a - clean_c
    b_strict = _mean_arm(modeB, "strict_recall") if modeB else 0.0

    if a_strict < ARM_A_RECALL:
        return (
            f"REFUTED: mode A ceiling strict {a_strict:.3f} does not beat arm A "
            f"{ARM_A_RECALL:.3f}. The goal graph carries no placement signal."
        )
    if clean_lift <= LIFT_NOISE:
        return (
            f"REFUTED (CLEAN subset, J corr 1): clean-subset lift {clean_lift:+.3f} "
            f"<= noise {LIFT_NOISE:.3f}. On the BRANCHING genres — where chain order "
            f"cannot leak placement — even the GT-graph ceiling does NOT move the "
            f"frozen gate (modeA {clean_a:.3f} vs control {clean_c:.3f}). The "
            f"goal-graph lever is dead with no order-leak escape hatch; the FR-607->609 "
            f"goal-anchoring line closes. Referent-binding {a_ref:.3f} vs FR-607 "
            f"{REF_BASELINE:.3f} is the secondary, mechanism number."
        )
    if clean_a < KILL:
        return (
            f"PARTIAL: clean-subset modeA {clean_a:.3f} beats control with lift "
            f"{clean_lift:+.3f} but does not clear KILL {KILL}; graph signal real but "
            f"sub-threshold."
        )
    if a_ref <= REF_BASELINE:
        return (
            f"PARTIAL: clean-subset placement lift {clean_lift:+.3f} clears noise but "
            f"referent-binding {a_ref:.3f} does not beat FR-607 {REF_BASELINE:.3f} — "
            f"placement moved without better anchoring (read the rationales)."
        )
    if not modeB or b_strict <= ARM_A_RECALL:
        return (
            f"PARTIAL (CONFIRMED at ceiling): clean-subset modeA {clean_a:.3f} clears "
            f"KILL with referent {a_ref:.3f} and lift {clean_lift:+.3f}, but mode B "
            f"{b_strict:.3f} does not beat arm A {ARM_A_RECALL:.3f} — model goals do "
            f"not yet carry the lift."
        )
    return (
        f"GO (CLEAN subset): clean-subset modeA {clean_a:.3f} clears KILL with lift "
        f"{clean_lift:+.3f} and referent {a_ref:.3f}, AND mode B {b_strict:.3f} beats "
        f"arm A {ARM_A_RECALL:.3f}. The goal-GRAPH earns its cost on order-clean genres."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="FR-609 goal-graph-anchored affect spike")
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument(
        "--topology",
        action="store_true",
        help="Print the beat-free goal graphs + CLEAN/QUARANTINED partition and exit.",
    )
    args = ap.parse_args()
    if args.topology:
        return _print_topology()

    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    descs = yaml.safe_load(GOAL_DESCS.read_text(encoding="utf-8"))

    partition = ev.goal_graph_partition(GT_DIR)
    clean, quar = set(partition["CLEAN"]), set(partition["QUARANTINED"])

    arm_a = _arm_a_baseline()
    print("== arm A (char-pinned single pass, FR-604 baseline) ==")
    print(f"  recall {arm_a['recall']:.3f}  precision {arm_a['precision']:.3f}")
    print(f"  CLEAN genres (GO here): {sorted(clean)}")
    print(f"  QUARANTINED (order-confounded): {sorted(quar)}\n")

    print(f"== control (no goals, FR-605 locate), {args.draws} draws ==")
    control = _run_arm_draws("control", args.draws, provider, model, descs)

    print(f"\n== mode A (inject GT goal GRAPH = ceiling), {args.draws} draws ==")
    modeA = _run_arm_draws("modeA", args.draws, provider, model, descs)

    a_strict = _mean_arm(modeA, "strict_recall")
    modeB: list[dict] = []
    if a_strict >= KILL:
        print(f"\n== mode B (inject MODEL goals = production), {args.draws} draws ==")
        modeB = _run_arm_draws("modeB", args.draws, provider, model, descs)
    else:
        print(f"\n== mode B SKIPPED: mode A strict {a_strict:.3f} < KILL {KILL} ==")

    a_relax = _mean_arm(modeA, "relax_recall")
    c_relax = _mean_arm(control, "relax_recall")
    a_ref = _mean_arm(modeA, "ref_recall")
    a_set = _mean_arm(modeA, "set_recall")
    clean_a = _subset_recall(modeA, clean)
    clean_c = _subset_recall(control, clean)
    quar_a = _subset_recall(modeA, quar)
    quar_c = _subset_recall(control, quar)
    shift = _close_shift(control, modeA)

    print("\n== FR-609 verdict ==")
    print(
        f"  control  strict {_mean_arm(control, 'strict_recall'):.3f}  relax {c_relax:.3f}"
    )
    print(
        f"  mode A   strict {a_strict:.3f}  relax {a_relax:.3f}  referent {a_ref:.3f}"
    )
    print(f"           set-recall {a_set:.3f} (cap on referent — J corr 4)")
    print(
        f"  CLEAN    modeA {clean_a:.3f} vs control {clean_c:.3f}  lift {clean_a - clean_c:+.3f}  (the GO test)"
    )
    print(
        f"  QUARANT  modeA {quar_a:.3f} vs control {quar_c:.3f}  lift {quar_a - quar_c:+.3f}  (order-confounded, NOT promotable)"
    )
    print(f"  HONEST LIFT (modeA.relax - control.relax) = {a_relax - c_relax:+.3f}")
    print(
        f"  CLOSE-BEAT SHIFT (control->modeA) = {shift:.3f}  (J corr 2: low shift + relabel = lever dead)"
    )
    print(
        f"  arm A strict baseline = {ARM_A_RECALL:.3f}  |  FR-607 referent {REF_BASELINE:.3f}\n"
    )
    print(f"  {_verdict(modeA, control, modeB, clean, quar)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
