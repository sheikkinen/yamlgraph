#!/usr/bin/env python
"""FR-605 — two-pass affect detection (what-then-where) spike.

Splits the L7 protagonist affect classifier into two LLM passes:

  Pass 1 (affect_set):     name the unordered SET of feelings the protagonist
                           carries — no localization. This is the support-gate:
                           a kind it does not name never runs pass 2, so
                           zero-support kinds cannot flood (fixes FR-604 arm B).
  Pass 2 (affect_locate):  for each named kind, locate its open beat and close
                           beat INDEPENDENTLY (distinct / same / absent permitted,
                           text-grounded — J: correction 1). A beat arc skeleton
                           derived purely from beat SEQUENCE (never the affect GT —
                           J: correction 3) anchors open vs close to structure.

Reports, over >= 3 draws @ temp 0.7 (FR-603 noise floor):
  - arm A baseline (char-pinned single pass, from FR-604) for the margin,
  - pass-1 SET recall (did pass 1 name every GT protagonist kind? — J: correction 2),
  - final corpus recall + precision (vs the FROZEN gate's own _l7_counts),
  - per-kind precision, and the wrong_beat share (collapse) vs the 71% baseline.

Verdict (J / frozen scope): recall > arm A 0.214 AND precision >= arm A 0.375 = GO;
recall up but precision below arm A 0.375 = REFUTED (FR-604 precedent).

Run from repo root:
  set -a; source .env; set +a; \
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    .venv/bin/python examples/plot_modeller/spike_affect_twopass.py --draws 3
"""

from __future__ import annotations

import argparse
import os
import re
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
    KINDS,
    _arm_a_baseline,
    _norm,
    _protagonist,
)

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"
TWOPASS_L7 = RESULTS_DIR / "l7_twopass"

GLOSSARY = {k: KIND_SPECS[k]["definition"] for k in KINDS}


def _beat_num(bid: object) -> int | None:
    m = re.search(r"(\d+)", str(bid))
    return int(m.group(1)) if m else None


def _words(text: str) -> list[str]:
    """Lowercase word tokens, punctuation stripped to spaces."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).split()


def _rationale_quotes_beat(rationale: str, beat_text: str, min_words: int = 3) -> bool:
    """FR-606 quote-check (code-side, J: don't trust the model to self-validate).

    True iff ``rationale`` contains >= ``min_words`` CONSECUTIVE words drawn verbatim
    (case-insensitive, punctuation-insensitive) from ``beat_text``. This is the hard
    constraint that defeats the FR-598 "novel" trap: an ungrounded essay quotes no
    span of the beat and fails the lint.
    """
    r = _words(rationale)
    b = _words(beat_text)
    if len(r) < min_words or len(b) < min_words:
        return False
    beat_ngrams = {tuple(b[i : i + min_words]) for i in range(len(b) - min_words + 1)}
    return any(
        tuple(r[i : i + min_words]) in beat_ngrams
        for i in range(len(r) - min_words + 1)
    )


def _skeleton(glosses: list) -> list[dict]:
    """Setup/turn/resolution from beat SEQUENCE only — no affect GT (J: correction 3).

    Splits the ordered beat ids into three contiguous phases by position. This uses
    nothing but the order the model already sees in the gloss list; no eff_affect
    field is read, so it cannot leak the answer.
    """
    ids = [g.get("id") for g in glosses if g.get("id")]
    n = len(ids)
    if n == 0:
        return []
    a = max(1, n // 3)
    b = max(a + 1, (2 * n) // 3)
    return [
        {"phase": "setup", "beats": ids[:a]},
        {"phase": "turn", "beats": ids[a:b]},
        {"phase": "resolution", "beats": ids[b:]},
    ]


def _pass1_set(
    glosses: list,
    agent: str,
    provider: str,
    model: str,
    out_dir: Path,
    explain: bool = False,
) -> list[str]:
    raw = execute_prompt(
        "affect_set",
        state={
            "glosses": glosses,
            "agent": agent,
            "kinds": KINDS,
            "glossary": GLOSSARY,
            "explain": explain,
        },
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_set.yaml").write_text(str(raw or ""), encoding="utf-8")
    try:
        data = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError:
        return []
    if isinstance(data, dict):
        data = data.get("kinds", [])
    if not isinstance(data, list):
        return []
    return [_norm(k) for k in data if _norm(k) in KINDS]


def _pass2_locate(
    glosses: list,
    agent: str,
    kind: str,
    skeleton: list,
    provider: str,
    model: str,
    out_dir: Path,
    explain: bool = False,
) -> dict:
    spec = KIND_SPECS[kind]
    raw = execute_prompt(
        "affect_locate",
        state={
            "glosses": glosses,
            "agent": agent,
            "kind": kind,
            "definition": spec["definition"],
            "open_cue": spec["open_cue"],
            "close_cue": spec["close_cue"],
            "relational": spec["relational"],
            "toward_hint": spec.get("toward_hint", ""),
            "skeleton": skeleton,
            "explain": explain,
        },
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


def _build_predictions(located: dict, agent: str, valid_ids: set) -> list[dict]:
    """located: {kind: {open, close, toward}} -> [{id, eff_affect:[delta...]}].

    open and close are taken independently (J: correction 1); a null/invalid beat
    contributes nothing. For relational kinds the located ``toward`` rides along.
    """
    by_beat: dict[str, list] = {}
    for kind, loc in located.items():
        spec = KIND_SPECS[kind]
        toward = loc.get("toward") if spec["relational"] else None
        for op in ("open", "close"):
            bid = _valid_beat(loc.get(op), valid_ids)
            if bid is None:
                continue
            delta = {"op": op, "char": agent, "kind": kind}
            if spec["relational"] and toward:
                delta["toward"] = toward
            by_beat.setdefault(bid, []).append(delta)
    return [{"id": bid, "eff_affect": deltas} for bid, deltas in by_beat.items()]


SUPPORTED = ["loss", "hope", "guilt", "betrayal"]


def _explain_run(provider: str, model: str) -> int:
    """FR-606 explain-mode autopsy: ONE draw, beat-quoted rationale per delta, linted.

    NOT scored (J: correction 1 — the rationale demand perturbs the output
    distribution, so an explain draw must never be mixed into a recall number). This
    prints, per located delta, the model's own one-line reason, the code-side
    quote-check verdict, and the cited beat's gold prose — the FR-605 autopsy for free.
    Dumps live under results/l7_twopass_explain/ (separate from scored draws).
    """
    explain_dir = RESULTS_DIR / "l7_twopass_explain"
    print("== FR-606 EXPLAIN MODE (one draw, NOT scored) ==")
    print(
        "  rationale demand perturbs placement (J: correction 1) -> this draw is a "
        "diagnostic, never a recall number.\n"
    )
    total = 0
    quote_ok = 0
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _protagonist(tbi)
        glosses = load_glosses_with_kinds(gt_path)
        gloss_by_id = {str(g.get("id")): str(g.get("gloss", "")) for g in glosses}
        skeleton = _skeleton(glosses)
        out_dir = explain_dir / "throughlines" / genre

        named = _pass1_set(glosses, prot, provider, model, out_dir, explain=True)
        print(f"-- {genre} / {prot} -- named: {', '.join(named) or '(none)'}")
        for kind in named:
            try:
                loc = _pass2_locate(
                    glosses,
                    prot,
                    kind,
                    skeleton,
                    provider,
                    model,
                    out_dir,
                    explain=True,
                )
            except Exception as exc:  # hard failure -> skip, not a crash
                print(f"  x {kind}: {exc}")
                continue
            rationale = str(loc.get("rationale") or "").strip()
            cited = " ".join(
                gloss_by_id.get(str(loc.get(op)), "")
                for op in ("open", "close")
                if loc.get(op) is not None
            )
            ok = bool(rationale) and _rationale_quotes_beat(rationale, cited)
            total += 1
            quote_ok += int(ok)
            flag = "quote-OK" if ok else "NO-QUOTE"
            print(
                f"  {kind:12} open={str(loc.get('open')):>4} "
                f"close={str(loc.get('close')):>4}  [{flag}]"
            )
            print(f"      reason: {rationale or '(empty)'}")
        print()
    print(
        f"== quote-check: {quote_ok}/{total} rationales quoted >=3 consecutive words "
        f"from a cited beat =="
    )
    print(f"   explain dumps: {explain_dir}")
    return 0


def _autopsy(pred: list, tbi: dict, prot: str, order: dict) -> dict:
    """Bucket each supported-kind protagonist miss like the FR-605 autopsy."""
    pred_by_id = {p["id"]: p.get("eff_affect", []) for p in pred}
    flat = [
        (bid, _norm(d.get("op")), _norm(d.get("kind")))
        for bid, ds in pred_by_id.items()
        for d in ds
    ]
    b = {"hit": 0, "wrong_beat": 0, "off_by_one": 0, "op_flipped": 0, "dropped": 0}
    prot_n = _norm(prot)
    for bid, deltas in tbi.items():
        for t in deltas:
            if _norm(t.get("char")) != prot_n or _norm(t.get("kind")) not in SUPPORTED:
                continue
            top, tk = _norm(t.get("op")), _norm(t.get("kind"))
            if any(ev._affect_matches(p, t) for p in pred_by_id.get(bid, [])):
                b["hit"] += 1
                continue
            same = [(pb, po) for (pb, po, pk) in flat if pk == tk]
            if not same:
                b["dropped"] += 1
            elif any(pb == bid and po != top for pb, po in same):
                b["op_flipped"] += 1
            elif _beat_num(bid) is not None and any(
                po == top
                and _beat_num(pb) is not None
                and abs(_beat_num(pb) - _beat_num(bid)) == 1
                for pb, po in same
            ):
                b["off_by_one"] += 1
            else:
                b["wrong_beat"] += 1
    return b


def _run_draw(draw: int, provider: str, model: str) -> dict:
    agg = {"rh": 0, "gt": 0, "ph": 0, "pred": 0}
    per_kind = {k: {"pred": 0, "hit": 0} for k in KINDS}
    set_named = 0
    set_gt = 0
    autopsy = {
        "hit": 0,
        "wrong_beat": 0,
        "off_by_one": 0,
        "op_flipped": 0,
        "dropped": 0,
    }

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = ev._genre_name(gt_path)
        tbi = ev._load_gt_affects(gt_path)
        prot = _protagonist(tbi)
        glosses = load_glosses_with_kinds(gt_path)
        valid_ids = {str(g.get("id")) for g in glosses if g.get("id")}
        order = {str(g.get("id")): i for i, g in enumerate(glosses)}
        skeleton = _skeleton(glosses)
        out_dir = TWOPASS_L7 / "throughlines" / f"draw{draw}" / genre

        # pass 1 — the SET
        named = _pass1_set(glosses, prot, provider, model, out_dir)
        gt_kinds = {_norm(d.get("kind")) for ds in tbi.values() for d in ds}
        set_gt += len(gt_kinds)
        set_named += len(gt_kinds & set(named))

        # pass 2 — locate each named kind
        located: dict = {}
        for kind in named:
            try:
                located[kind] = _pass2_locate(
                    glosses, prot, kind, skeleton, provider, model, out_dir
                )
            except Exception as exc:  # hard failure -> skip, not a crash
                print(f"  x {genre}/{prot}/{kind}: {exc}")

        pred = _build_predictions(located, prot, valid_ids)
        (TWOPASS_L7 / f"{genre}.yaml").write_text(
            yaml.safe_dump(pred, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        c = ev._l7_counts(pred, tbi)
        agg["rh"] += c["recall_hits"]
        agg["gt"] += c["gt"]
        agg["ph"] += c["precision_hits"]
        agg["pred"] += c["pred"]

        # per-kind precision (reuse frozen matcher)
        pred_by_id = {p["id"]: p.get("eff_affect", []) for p in pred}
        for bid, p_deltas in pred_by_id.items():
            t_deltas = tbi.get(bid, [])
            used: set[int] = set()
            for p in p_deltas:
                k = _norm(p.get("kind"))
                if k not in per_kind:
                    continue
                per_kind[k]["pred"] += 1
                for j, t in enumerate(t_deltas):
                    if j in used:
                        continue
                    if ev._affect_matches(p, t):
                        per_kind[k]["hit"] += 1
                        used.add(j)
                        break

        a = _autopsy(pred, tbi, prot, order)
        for key in autopsy:
            autopsy[key] += a[key]

    return {
        "recall": agg["rh"] / agg["gt"] if agg["gt"] else 0.0,
        "precision": agg["ph"] / agg["pred"] if agg["pred"] else 0.0,
        "counts": agg,
        "per_kind": per_kind,
        "set_recall": set_named / set_gt if set_gt else 0.0,
        "set_counts": (set_named, set_gt),
        "autopsy": autopsy,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="FR-605 two-pass affect spike")
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument(
        "--explain",
        action="store_true",
        help=(
            "FR-606: run ONE explain-mode draw that emits a beat-quoted rationale per "
            "delta, lint each rationale's quote, and print it next to the gold prose. "
            "NOT scored (J: explain perturbs the distribution) — never folded into a "
            "recall number; returns before the scored verdict."
        ),
    )
    args = ap.parse_args()
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    TWOPASS_L7.mkdir(parents=True, exist_ok=True)

    if args.explain:
        return _explain_run(provider, model)

    arm_a = _arm_a_baseline()
    print("== arm A (char-pinned single pass, baseline from FR-604) ==")
    print(
        f"  recall    {arm_a['recall']:.3f} "
        f"({arm_a['counts']['rh']}/{arm_a['counts']['gt']})"
    )
    print(
        f"  precision {arm_a['precision']:.3f} "
        f"({arm_a['counts']['ph']}/{arm_a['counts']['pred']})  <- the benchmark"
    )

    print(f"\n== two-pass ({args.draws} draws @ temp 0.7) ==")
    draws = []
    for d in range(1, args.draws + 1):
        res = _run_draw(d, provider, model)
        draws.append(res)
        print(
            f"  draw {d}: recall {res['recall']:.3f} "
            f"({res['counts']['rh']}/{res['counts']['gt']})  "
            f"precision {res['precision']:.3f} "
            f"({res['counts']['ph']}/{res['counts']['pred']})  "
            f"set-recall {res['set_recall']:.3f} "
            f"({res['set_counts'][0]}/{res['set_counts'][1]})"
        )

    recalls = [d["recall"] for d in draws]
    precisions = [d["precision"] for d in draws]
    set_recalls = [d["set_recall"] for d in draws]
    r_mean = statistics.mean(recalls)
    p_mean = statistics.mean(precisions)
    s_mean = statistics.mean(set_recalls)
    print("\n== two-pass aggregate ==")
    print(
        f"  recall      mean {r_mean:.3f}  band [{min(recalls):.3f}, {max(recalls):.3f}]"
    )
    print(
        f"  precision   mean {p_mean:.3f}  band "
        f"[{min(precisions):.3f}, {max(precisions):.3f}]"
    )
    print(
        f"  set-recall  mean {s_mean:.3f}  band "
        f"[{min(set_recalls):.3f}, {max(set_recalls):.3f}]  "
        f"(J: correction 2 — upper bound on final recall)"
    )

    # per-kind precision
    print("\n== per-kind precision (summed over draws) ==")
    pk = {k: {"pred": 0, "hit": 0} for k in KINDS}
    for d in draws:
        for k in KINDS:
            pk[k]["pred"] += d["per_kind"][k]["pred"]
            pk[k]["hit"] += d["per_kind"][k]["hit"]
    for k in KINDS:
        pr = pk[k]["hit"] / pk[k]["pred"] if pk[k]["pred"] else 0.0
        print(f"  {k:16} {pr:.2f}  ({pk[k]['hit']}/{pk[k]['pred']})")

    # collapse (wrong_beat) vs 71% baseline
    ap_tot = {key: sum(d["autopsy"][key] for d in draws) for key in draws[0]["autopsy"]}
    miss = sum(v for key, v in ap_tot.items() if key != "hit")
    wb_share = ap_tot["wrong_beat"] / miss if miss else 0.0
    print("\n== collapse autopsy (two-pass, supported kinds, summed) ==")
    print(f"  hits {ap_tot['hit']}  misses {miss}")
    print(
        f"  wrong_beat {ap_tot['wrong_beat']} ({wb_share * 100:.0f}% of misses)  "
        f"[baseline 71%]  off_by_one {ap_tot['off_by_one']}  "
        f"op_flipped {ap_tot['op_flipped']}  dropped {ap_tot['dropped']}"
    )

    # verdict
    print("\n== verdict (margin over arm A) ==")
    r_margin = r_mean - arm_a["recall"]
    p_floor_ok = p_mean >= arm_a["precision"]
    print(f"  recall margin vs arm A : {r_margin:+.3f} (arm A {arm_a['recall']:.3f})")
    print(
        f"  precision floor (>= arm A {arm_a['precision']:.3f}) : "
        f"{'OK' if p_floor_ok else 'VIOLATED'} ({p_mean:.3f})"
    )
    if not p_floor_ok:
        print(
            "  REFUTED: two-pass bought recall below the char-pinned arm A precision "
            "floor — the located endpoints over-emit. Revert (FR-604 precedent)."
        )
    elif r_margin <= 0:
        print(
            "  REFUTED: two-pass did not beat arm A recall. Decomposition did not help "
            "localization."
        )
    elif r_mean >= 0.50:
        print(
            f"  GO/REVISE: recall {r_mean:.3f} clears KILL with precision held. "
            "What-then-where earns its 2x cost."
        )
    else:
        print(
            f"  PARTIAL: recall {r_mean:.3f} beats arm A (+{r_margin:.3f}) at precision "
            f">= floor, but still < 0.50 KILL. Localization improved, not solved."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
