#!/usr/bin/env python3
"""FR-604 — per-kind affect detector spike (arm B), with arm A baseline.

The FR-596->603 arc exhausted single-pass prompt levers: FR-602 ruled out beat
tolerance, FR-603's hope-open cue was REFUTED (over-emission, sub-noise). The
residual has two STRUCTURAL causes a direct read of the quest 0/4 isolated:

  1. the FR-598 one-op-per-beat cap forfeits 25% of the recall ceiling
     (7/28 GT deltas are the 2nd+ on a multi-affect beat);
  2. the merged GT-roster sprays supporting-character deltas the protagonist-only
     gate scores as false positives (precision 0.12 is a merge artifact).

This spike measures two arms so the gain is ATTRIBUTABLE (J: correction 1):

  arm A  char-pinned single pass — re-score the EXISTING results/l7/<genre>.yaml
         predictions restricted to the focal protagonist. Cannot change recall;
         isolates the precision win of dropping merged-roster false positives.
         This is the honest benchmark, NOT the 0.12 merged number (J: correction 2).

  arm B  per-kind sweep — six narrow detectors (one abstract kind at a time),
         char pinned to the protagonist, unioned with NO cap. Must justify its
         6x-call cost by its MARGIN over arm A on recall AND per-kind precision.

Removing the cap AND the six-way competition together is the maximal
over-emission configuration, so the FR-598 invention guard is preserved hard in
each detector and precision is a HARD floor: arm B precision must be >= arm A's
char-pinned precision, else the per-kind architecture is REFUTED and reverted
(FR-603 precedent). Recall is read as the mean of >=N draws at temp 0.7 with its
run-to-run band (FR-603 noise-floor discipline — no single-draw claims).

Raw detector output is stored under results/l7_perkind/throughlines/<genre>/
<kind>.yaml so >=3 samples can be READ before the aggregate (read_raw_output_first).

Run:
  set -a; source .env; set +a
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    python examples/plot_modeller/spike_affect_per_kind.py --draws 3
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
from nodes.tools import (  # noqa: E402
    _strip_code_fences,
    combine_affects,
    load_glosses_with_kinds,
)

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"
PINNED_L7 = RESULTS_DIR / "l7"  # arm A reads the existing single-pass predictions
PERKIND_L7 = RESULTS_DIR / "l7_perkind"  # arm B writes here (pinned baseline untouched)

KINDS = ["loss", "guilt", "betrayal", "retaliation", "hidden_blessing", "hope"]

# One abstract concept per detector: definition + open/close resolution signature
# + 2-3 concrete, genre-neutral exemplars (NOT copied from the test GT).
KIND_SPECS: dict[str, dict] = {
    "loss": {
        "definition": "grief at something or someone taken away.",
        "open_cue": "someone the character loves dies or is taken, or a home or "
        "object central to them is destroyed, and the text shows their grief.",
        "close_cue": "the lost person or thing is recovered, buried, or openly "
        "mourned, ending the grief.",
        "relational": False,
        "exemplars": [
            "Open: the character watches their mentor cut down and cannot reach them.",
            "Open: the character returns to find their home burned and family gone.",
            "Close: the character recovers what was stolen, or lays the dead to rest.",
        ],
    },
    "guilt": {
        "definition": "self-blame for a wrong the character themselves did to another.",
        "open_cue": "the character blames THEMSELVES for a wrong they did to "
        "someone else.",
        "close_cue": "the character confesses, atones for, or earns back their "
        "place for that wrong.",
        "relational": True,
        "toward_hint": "the person the character wronged",
        "exemplars": [
            "Open: the character realizes their order got a comrade killed and "
            "carries the blame.",
            "Open: the character abandoned someone who trusted them and knows it.",
            "Close: the character confesses the wrong to the one they wronged, or "
            "earns back their place among them.",
        ],
    },
    "betrayal": {
        "definition": "the character's trust broken by another.",
        "open_cue": "someone the character trusted breaks that trust against them.",
        "close_cue": "the betrayer is exposed, named, or reckoned with.",
        "relational": True,
        "toward_hint": "the person who broke the character's trust",
        "exemplars": [
            "Open: the character learns their ally has been informing the enemy.",
            "Open: a sworn friend hands the character to their captors.",
            "Close: the character unmasks the traitor, or the betrayer is brought "
            "to account.",
        ],
    },
    "retaliation": {
        "definition": "the character's drive to avenge a wrong.",
        "open_cue": "the character resolves to avenge a wrong done to them or theirs.",
        "close_cue": "that vengeance is carried out.",
        "relational": False,
        "exemplars": [
            "Open: over the body of the slain, the character swears to make the "
            "killer pay.",
            "Open: the character sets out hunting the one who wronged them.",
            "Close: the character strikes down the wrongdoer, the vengeance fulfilled.",
        ],
    },
    "hidden_blessing": {
        "definition": "an apparent setback that proves to be a gift.",
        "open_cue": "an apparent setback befalls the character (a loss, a detour, "
        "a wound).",
        "close_cue": "that very setback is revealed to have been a gift.",
        "relational": False,
        "exemplars": [
            "Open: the character is exiled, loses the contest, or is wounded and "
            "forced to stop.",
            "Close: the exile or wound turns out to have saved them or opened the "
            "true path.",
        ],
    },
    "hope": {
        "definition": "belief that things can yet be made right.",
        "open_cue": "the character comes to believe things can yet be made right "
        "— aid arrives, a path opens, or courage returns to THEM.",
        "close_cue": "the just outcome actually arrives and things are set right.",
        "relational": False,
        "exemplars": [
            "Open: a stranger offers the character the means to go on (a charm, a "
            "map, a promise) — the hope is the RECEIVER's, not the giver's.",
            "Open: against the odds the character glimpses a way through and takes "
            "heart.",
            "Close: the rightful order is restored — the crown is placed, the king "
            "returns, justice lands.",
        ],
    },
}


def _norm(s: object) -> str:
    return " ".join(str(s or "").split()).strip().lower()


def _protagonist(truth_by_id: dict) -> str:
    """The single GT feeler (the gate is protagonist-anchored)."""
    chars: dict[str, int] = {}
    for deltas in truth_by_id.values():
        for d in deltas:
            chars[d.get("char")] = chars.get(d.get("char"), 0) + 1
    return max(chars, key=chars.get) if chars else ""


def _parse(raw: str) -> list:
    try:
        data = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError:
        return []
    return data if isinstance(data, list) else []


def _detect_kind(
    glosses: list, agent: str, kind: str, provider: str, model: str, out_dir: Path
) -> list:
    spec = KIND_SPECS[kind]
    raw = execute_prompt(
        "affect_detect_kind",
        state={
            "glosses": glosses,
            "agent": agent,
            "kind": kind,
            "definition": spec["definition"],
            "open_cue": spec["open_cue"],
            "close_cue": spec["close_cue"],
            "relational": spec["relational"],
            "toward_hint": spec.get("toward_hint", ""),
            "exemplars": spec["exemplars"],
        },
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{kind}.yaml").write_text(str(raw or ""), encoding="utf-8")
    return _parse(raw)


# --- scoring (reuses the FROZEN gate's own matchers) --------------------------


def _pred_by_id(combined: list) -> dict:
    out: dict[str, list] = {}
    for item in combined:
        if isinstance(item, dict) and item.get("id"):
            ea = item.get("eff_affect")
            out[item["id"]] = ea if isinstance(ea, list) else []
    return out


def _per_kind_precision(combined: list, truth_by_id: dict) -> dict:
    """Per-kind precision: of the deltas a detector emitted, how many match GT.

    Uses the frozen ``_affect_matches`` so 'flooded' detectors are named (J:
    correction 2 — on a precision failure, report WHICH detector over-emitted).
    """
    pred_by_id = _pred_by_id(combined)
    stats = {k: {"pred": 0, "hit": 0} for k in KINDS}
    for bid, p_deltas in pred_by_id.items():
        t_deltas = truth_by_id.get(bid, [])
        used: set[int] = set()
        for p in p_deltas:
            k = _norm(p.get("kind"))
            if k not in stats:
                continue
            stats[k]["pred"] += 1
            for j, t in enumerate(t_deltas):
                if j in used:
                    continue
                if ev._affect_matches(p, t):
                    stats[k]["hit"] += 1
                    used.add(j)
                    break
    return stats


def _arm_a_baseline() -> dict:
    """Char-pinned re-score of the EXISTING single-pass predictions (no LLM)."""
    agg = {"rh": 0, "gt": 0, "ph": 0, "pred": 0}
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _norm(_protagonist(tbi))
        rp = PINNED_L7 / f"{genre}.yaml"
        if not rp.exists():
            continue
        pred = yaml.safe_load(rp.read_text(encoding="utf-8"))
        pinned = []
        if isinstance(pred, list):
            for item in pred:
                if not isinstance(item, dict):
                    continue
                ea = [
                    d
                    for d in (item.get("eff_affect") or [])
                    if _norm(d.get("char")) == prot
                ]
                pinned.append({"id": item.get("id"), "eff_affect": ea})
        c = ev._l7_counts(pinned, tbi)
        agg["rh"] += c["recall_hits"]
        agg["gt"] += c["gt"]
        agg["ph"] += c["precision_hits"]
        agg["pred"] += c["pred"]
    return {
        "recall": agg["rh"] / agg["gt"] if agg["gt"] else 0.0,
        "precision": agg["ph"] / agg["pred"] if agg["pred"] else 0.0,
        "counts": agg,
    }


def _run_draw(draw: int, provider: str, model: str) -> dict:
    """One arm-B corpus pass: six detectors per protagonist, unioned, scored."""
    agg = {"rh": 0, "gt": 0, "ph": 0, "pred": 0}
    per_kind = {k: {"pred": 0, "hit": 0} for k in KINDS}
    multi_recovered: list[str] = []
    nonprot = 0

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _protagonist(tbi)
        glosses = load_glosses_with_kinds(gt_path)
        out_dir = PERKIND_L7 / "throughlines" / f"draw{draw}" / genre

        records = []
        for idx, kind in enumerate(KINDS):
            try:
                beats = _detect_kind(glosses, prot, kind, provider, model, out_dir)
            except Exception as exc:  # hard failure -> empty, not a crash
                print(f"  x {genre}/{prot}/{kind}: {exc}")
                beats = []
            records.append({"_map_index": idx, "affects": beats})

        combined = combine_affects(records)
        (PERKIND_L7 / f"{genre}.yaml").write_text(
            yaml.safe_dump(combined, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        c = ev._l7_counts(combined, tbi)
        agg["rh"] += c["recall_hits"]
        agg["gt"] += c["gt"]
        agg["ph"] += c["precision_hits"]
        agg["pred"] += c["pred"]
        pk = _per_kind_precision(combined, tbi)
        for k in KINDS:
            per_kind[k]["pred"] += pk[k]["pred"]
            per_kind[k]["hit"] += pk[k]["hit"]

        # diagnostics: cap-forfeit recovery + wrong-feeler poison
        prot_n = _norm(prot)
        pred_by_id = _pred_by_id(combined)
        for bid, t_deltas in tbi.items():
            if len(t_deltas) > 1:
                hits = ev._match_count(t_deltas, pred_by_id.get(bid, []))
                if hits >= 2:
                    multi_recovered.append(f"{genre}:{bid}({hits})")
        for item in combined:
            for d in item.get("eff_affect") or []:
                if _norm(d.get("char")) != prot_n:
                    nonprot += 1

    return {
        "recall": agg["rh"] / agg["gt"] if agg["gt"] else 0.0,
        "precision": agg["ph"] / agg["pred"] if agg["pred"] else 0.0,
        "counts": agg,
        "per_kind": per_kind,
        "multi_recovered": multi_recovered,
        "nonprot": nonprot,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="FR-604 per-kind affect spike")
    ap.add_argument("--draws", type=int, default=3)
    args = ap.parse_args()
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    PERKIND_L7.mkdir(parents=True, exist_ok=True)

    arm_a = _arm_a_baseline()
    print("== arm A (char-pinned single pass, baseline) ==")
    print(
        f"  recall    {arm_a['recall']:.3f} "
        f"({arm_a['counts']['rh']}/{arm_a['counts']['gt']})  [unchanged by pinning]"
    )
    print(
        f"  precision {arm_a['precision']:.3f} "
        f"({arm_a['counts']['ph']}/{arm_a['counts']['pred']})  "
        f"<- the benchmark, NOT 0.12"
    )

    print(f"\n== arm B (per-kind sweep, {args.draws} draws @ temp 0.7) ==")
    draws = []
    for d in range(1, args.draws + 1):
        res = _run_draw(d, provider, model)
        draws.append(res)
        print(
            f"  draw {d}: recall {res['recall']:.3f} "
            f"({res['counts']['rh']}/{res['counts']['gt']})  "
            f"precision {res['precision']:.3f} "
            f"({res['counts']['ph']}/{res['counts']['pred']})  "
            f"multi-recovered {res['multi_recovered']}  nonprot {res['nonprot']}"
        )

    recalls = [d["recall"] for d in draws]
    precisions = [d["precision"] for d in draws]
    r_mean = statistics.mean(recalls)
    p_mean = statistics.mean(precisions)
    print("\n== arm B aggregate ==")
    print(
        f"  recall    mean {r_mean:.3f}  band [{min(recalls):.3f}, {max(recalls):.3f}]"
    )
    print(
        f"  precision mean {p_mean:.3f}  band [{min(precisions):.3f}, "
        f"{max(precisions):.3f}]"
    )

    # per-kind precision (corpus, summed over draws) — names a flooded detector
    print("\n== arm B per-kind precision (summed over draws) ==")
    pk = {k: {"pred": 0, "hit": 0} for k in KINDS}
    for d in draws:
        for k in KINDS:
            pk[k]["pred"] += d["per_kind"][k]["pred"]
            pk[k]["hit"] += d["per_kind"][k]["hit"]
    for k in KINDS:
        pr = pk[k]["hit"] / pk[k]["pred"] if pk[k]["pred"] else 0.0
        print(f"  {k:16} {pr:.2f}  ({pk[k]['hit']}/{pk[k]['pred']})")

    # verdict — margin over arm A, with the hard precision floor (J corrections 1/2)
    print("\n== verdict (margin over arm A) ==")
    r_margin = r_mean - arm_a["recall"]
    p_floor_ok = p_mean >= arm_a["precision"]
    print(f"  recall margin vs arm A : {r_margin:+.3f}")
    print(
        f"  precision floor (>= arm A {arm_a['precision']:.3f}) : "
        f"{'OK' if p_floor_ok else 'VIOLATED'} ({p_mean:.3f})"
    )
    if not p_floor_ok:
        print(
            "  REFUTED: arm B bought recall by spraying — precision fell below the "
            "char-pinned arm A floor. Per-kind precision above names the flooded "
            "detector. Revert (FR-603 precedent)."
        )
    elif r_mean >= 0.50:
        print(
            f"  GO/REVISE: recall {r_mean:.3f} clears KILL with precision held. "
            "Per-kind decomposition earns its 6x cost."
        )
    else:
        print(
            f"  KILL persists: recall {r_mean:.3f} < 0.50 even with cap removed and "
            "char pinned. The bottleneck is not the cap — it is the model's reading "
            "of WHICH beat carries WHICH kind for the protagonist."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
