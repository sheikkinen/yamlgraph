#!/usr/bin/env python3
"""FR-599 — L7 affect-recall miss-decomposition probe (read-only, throwaway).

The FR-578 gate reports one number — ``affect_recall`` — and the FR-598 enforce
left it on the floor (~0.06-0.15) after REFUTING the "kill the novel" hypothesis.
The aggregate cannot say WHICH lever the reserved escalation should pull. This
probe consumes the FROZEN gate's own inputs (the FR-598 classifier output under
``results/l7/<genre>.yaml`` + the ground-truth fixtures) and partitions every
GT delta the gate counts as a MISS into five mutually-exclusive buckets, each
naming a different, differently-priced lever:

  (e) UNLICENSED   the GT anchor beat's own words do not license the affect at all
                   -> GT re-annotation / cross-beat context  (checked FIRST)
  (a) ABSENT       licensed, but the model placed nothing matching anywhere near
                   -> model scale (FR-578)
  (b) BEAT-OFF     right op+char+kind on a neighbour within +/-N, wrong exact beat
                   -> evaluator beat tolerance / GT granularity
  (c) KIND-WRONG   right op+char on the EXACT GT beat, wrong kind
                   -> six-kind taxonomy revision
  (d) TOWARD-WRONG right op+char+kind on the exact relational beat, wrong toward
                   -> relational-direction prompt/taxonomy gap

The probe REPLICATES the frozen ``_l7_counts`` beat-keyed grouping and ties out
to it (reconstructed hits == gate ``recall_hits``) before any bucket is trusted
(Judgement correction #1). Every bucket is reported x window (+/-1/+/-2/+/-3) x op
(open/close) (corrections #2/#3); BEAT-OFF requires a kind-match on the neighbour
(correction #4). Bucket (e) is decided by an LLM licensing pass that is
fixture-pinned to two hand-adjudicated known answers (correction #5) and gated
conservatively with every member dumped for a human read (correction #6).

It changes NOTHING: no evaluator edit, no model run for scoring, no taxonomy
change. It ends in one named dominant lever (or "multi-cause -> split successors").

Run:
  set -a; source .env; set +a
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    .venv/bin/python examples/plot_modeller/probe_l7_misses.py

REQ-YG-020.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

# Run as a script: Python puts this file's dir (examples/plot_modeller) on
# sys.path[0], so ``evaluate`` and ``nodes`` import without path surgery.
from evaluate import _l7_counts, _load_gt_affects
from nodes.tools import _strip_code_fences, load_glosses_with_kinds

from yamlgraph.executor import execute_prompt

EXAMPLE_DIR = Path(__file__).resolve().parent
GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"
L7_DIR = RESULTS_DIR / "l7"

WINDOWS = (1, 2, 3)
_RELATIONAL = ("guilt", "betrayal")
_NEIGHBOR_CTX = 2  # +/- beats of gloss context handed to the licensing pass

# corr.#5 — fixture-pinned known answers the licensing pass MUST reproduce.
# (genre stem, beat id, op, char, kind) -> (licensed, neighbor_licensed)
_LICENSING_FIXTURES: dict[tuple, tuple[bool, bool]] = {
    ("detective-thriller-the-vanished-witness", "F1", "open", "marren", "loss"): (
        False,  # licensed: anchor subject is Hagen, Marren unnamed
        True,  # neighbor_licensed: F2 "Marren discovers ... case collapses"
    ),
    (
        "detective-thriller-the-vanished-witness",
        "F7",
        "open",
        "marren",
        "hidden_blessing",
    ): (
        False,  # licensed: F7 is a clean positive, no setback-that-proves-a-gift
        False,  # neighbor_licensed: licensed by no nearby gloss
    ),
    # close-op known answer (the open-op fixtures above cannot catch an
    # open-biased judge that flags every close as unlicensed): F5 "Pell hands
    # over the ledger ... agrees to testify" RECOVERS the lost case -> close loss
    # IS licensed at its anchor.
    ("detective-thriller-the-vanished-witness", "F5", "close", "marren", "loss"): (
        True,  # licensed: the resolution (recovery) is shown on the anchor beat
        False,  # neighbor_licensed only meaningful when unlicensed
    ),
}


def _norm(s: object) -> str:
    return " ".join(str(s or "").split()).strip().lower()


def _pred_by_id(predicted: list | None) -> dict[str, list]:
    """Beat-keyed predicted deltas — identical grouping to frozen ``_l7_counts``."""
    out: dict[str, list] = {}
    if isinstance(predicted, list):
        for item in predicted:
            if isinstance(item, dict) and item.get("id"):
                ea = item.get("eff_affect")
                out[item["id"]] = ea if isinstance(ea, list) else []
    return out


def _unmatched_gt(t_deltas: list, p_deltas: list) -> list:
    """The GT deltas with no distinct match in ``p_deltas`` (the per-beat MISSES).

    Mirrors the greedy bipartite pairing inside frozen ``_match_count`` exactly,
    but returns the unmatched GT deltas instead of only their count — so
    ``len(t) - len(_unmatched_gt(t, p)) == _match_count(t, p)`` by construction
    (asserted in the tie-out).
    """
    from evaluate import _affect_matches  # local: same matcher the gate uses

    used: set[int] = set()
    misses: list = []
    for a in t_deltas:
        for j, b in enumerate(p_deltas):
            if j in used:
                continue
            if _affect_matches(a, b):
                used.add(j)
                break
        else:
            misses.append(a)
    return misses


def _op_char_on(beat_deltas: list, op: str, char: str) -> list[dict]:
    return [
        d
        for d in beat_deltas
        if isinstance(d, dict)
        and _norm(d.get("op")) == op
        and _norm(d.get("char")) == char
    ]


def _kindwrong_members(truth_by_id: dict, pred_by_id: dict) -> list[dict]:
    """FR-601 — deterministic (c) KIND-WRONG members with the predicted kind.

    A miss is (c) when the model fired op+char on the EXACT GT beat but named a
    different ``kind``. This needs no LLM licensing pass: after FR-600 dropped or
    re-anchored the unlicensed deltas, every residual op+char-on-the-exact-beat
    miss is licensed by construction, so (c) is a pure GT-vs-prediction compare.
    Carries ``pred_kind`` — the predicted mismatched kind — for the confusion
    read the Judge gated the prompt edit behind (FR-601 AC#1).
    """
    out: list[dict] = []
    for bid, t_deltas in truth_by_id.items():
        p_deltas = pred_by_id.get(bid, [])
        for miss in _unmatched_gt(t_deltas, p_deltas):
            op = _norm(miss.get("op"))
            char = _norm(miss.get("char"))
            kind = _norm(miss.get("kind"))
            for p in _op_char_on(p_deltas, op, char):
                if _norm(p.get("kind")) != kind:
                    out.append(
                        {
                            "anchor_id": bid,
                            "op": op,
                            "char": miss.get("char"),
                            "gt_kind": kind,
                            "pred_kind": _norm(p.get("kind")),
                            "toward": miss.get("toward"),
                        }
                    )
                    break
    return out


def _windowed_match(
    anchor_by_id: dict, cand_by_id: dict, order: list[str], window: int
) -> tuple[int, list[dict]]:
    """FR-602 -- greedy windowed bipartite match mirroring frozen ``_match_count``.

    Identical call convention to the gate's ``_match_count`` (``_affect_matches(a, b)``
    with ``a`` from ``anchor_by_id`` and ``b`` from ``cand_by_id``), but a candidate
    on a beat within +/-``window`` of the anchor beat may match -- nearest beat first,
    so an exact-beat match is always preferred and a neighbour is taken only when no
    exact match remains. ``window=0`` reduces EXACTLY to the per-beat gate (asserted
    by the sweep tie-out). Each candidate is used at most once (``(beat, pos)`` keyed),
    so a wider window cannot double-count. Returns ``(hits, neighbour_members)`` where
    members carry only the off!=0 matches (the beat-displaced recoveries to be read).

    Correction #4 is satisfied for free: ``_affect_matches`` requires op+char+kind
    (kind exact), so a +/-1 neighbour that differs in kind is NEVER admitted.
    """
    from evaluate import _affect_matches  # frozen matcher, imported not copied

    idx_of = {b: k for k, b in enumerate(order)}
    offsets = [0]
    for off in range(1, window + 1):
        offsets += [-off, off]  # nearest-first: 0, -1, +1, -2, +2, ...

    used: set[tuple[str, int]] = set()
    hits = 0
    members: list[dict] = []
    for bid, a_deltas in anchor_by_id.items():
        i = idx_of.get(bid)
        for a in a_deltas:
            for off in offsets:
                if off == 0:
                    nb: str | None = bid
                elif i is None:
                    continue
                else:
                    j = i + off
                    nb = order[j] if 0 <= j < len(order) else None
                if nb is None:
                    continue
                hit_here = False
                for pos, b in enumerate(cand_by_id.get(nb, [])):
                    if (nb, pos) in used:
                        continue
                    if _affect_matches(a, b):
                        used.add((nb, pos))
                        hits += 1
                        if off != 0:
                            members.append(
                                {
                                    "anchor_id": bid,
                                    "cand_id": nb,
                                    "off": off,
                                    "op": _norm(a.get("op")),
                                    "char": a.get("char"),
                                    "kind": _norm(a.get("kind")),
                                    "toward": a.get("toward"),
                                }
                            )
                        hit_here = True
                        break
                if hit_here:
                    break
    return hits, members


def _licensing_verdict(
    miss: dict,
    anchor_id: str,
    glosses: list[dict],
    provider: str,
    model: str,
) -> dict:
    """LLM licensing pass for ONE missed GT delta (corr.#5/#6).

    Recognition, not generation: the affect is given; the pass only judges whether
    the anchor beat licenses it (default LICENSED — conservative) and, if not,
    whether a neighbour within +/-_NEIGHBOR_CTX does. Returns a dict with
    ``licensed`` / ``neighbor_licensed`` / ``reason``.
    """
    by_id = {g["id"]: g for g in glosses}
    order = [g["id"] for g in glosses]
    anchor = by_id.get(anchor_id, {})
    idx = order.index(anchor_id) if anchor_id in order else 0
    neighbors = [
        {"id": order[j], "gloss": by_id[order[j]]["gloss"]}
        for j in range(
            max(0, idx - _NEIGHBOR_CTX), min(len(order), idx + _NEIGHBOR_CTX + 1)
        )
        if order[j] != anchor_id
    ]
    raw = execute_prompt(
        "affect_licensing",
        state={
            "op": _norm(miss.get("op")),
            "char": miss.get("char"),
            "kind": _norm(miss.get("kind")),
            "toward": miss.get("toward"),
            "anchor_id": anchor_id,
            "anchor_gloss": anchor.get("gloss", ""),
            "neighbors": neighbors,
        },
        prompts_dir=PROMPTS_DIR,
        temperature=0.0,  # corr.#5: fixture-pin demands a calibratable judge
        provider=provider,
        model=model,
    )
    try:
        parsed = yaml.safe_load(_strip_code_fences(str(raw))) or {}
    except yaml.YAMLError:
        parsed = {}
    licensed = bool(parsed.get("licensed", True))  # corr.#6 default: LICENSED
    return {
        "licensed": licensed,
        # neighbor_licensed only meaningful when unlicensed
        "neighbor_licensed": (not licensed) and bool(parsed.get("neighbor_licensed")),
        "reason": str(parsed.get("reason", "")).strip(),
    }


def _classify_licensed(
    miss: dict, anchor_id: str, pred_by_id: dict, order: list[str], window: int
) -> str:
    """Bucket a LICENSED miss into a/b/c/d at one window (corr.#2/#3/#4)."""
    op = _norm(miss.get("op"))
    char = _norm(miss.get("char"))
    kind = _norm(miss.get("kind"))
    toward = _norm(miss.get("toward"))
    relational = kind in _RELATIONAL

    # exact beat: op+char present -> KIND-WRONG (c) or TOWARD-WRONG (d)
    for p in _op_char_on(pred_by_id.get(anchor_id, []), op, char):
        if _norm(p.get("kind")) == kind:
            if relational and _norm(p.get("toward")) != toward:
                return "d_toward_wrong"
            # same op+char+kind(+toward) on exact beat but still a miss -> residual
            continue
        return "c_kind_wrong"

    # neighbour within +/-window with op+char+KIND match (corr.#4) -> BEAT-OFF (b)
    if anchor_id in order:
        idx = order.index(anchor_id)
        for off in range(1, window + 1):
            for nb in (idx - off, idx + off):
                if 0 <= nb < len(order):
                    for p in _op_char_on(pred_by_id.get(order[nb], []), op, char):
                        if _norm(p.get("kind")) == kind:
                            return "b_beat_off"

    return "a_absent"  # explicit residual


def _blank_buckets() -> dict[str, dict[str, int]]:
    return {
        b: {"open": 0, "close": 0}
        for b in (
            "e_unlicensed",
            "a_absent",
            "b_beat_off",
            "c_kind_wrong",
            "d_toward_wrong",
        )
    }


def _add(buckets: dict, bucket: str, op: str) -> None:
    buckets[bucket]["open" if op == "open" else "close"] += 1


def kindwrong_report() -> int:
    """FR-601 -- deterministic (c) KIND-WRONG confusion read on post-FR-600 GT.

    Re-counts (c) on the re-annotated ground truth and the EXISTING classifier
    output, carrying each member's predicted mismatched kind (AC#1). No LLM, no
    model run, frozen gate untouched. Persists the close-op confusion pairs the
    Judge gated the affect_throughline.yaml edit behind.

    DEVIATION (same rationale the Judge endorsed for FR-600): the full probe's
    _LICENSING_FIXTURES are pinned to the PRE-FR-600 miss set (detective F1 loss,
    F7 hidden_blessing) which FR-600 re-anchored/dropped -- a verbatim live re-run
    would FAIL its own pin and re-introduce the non-determinism the freeze exists
    to kill. (c) is deterministic, so this read needs neither the LLM nor the pin.
    """
    from collections import Counter

    rows: list[dict] = []
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        pred_path = L7_DIR / f"{genre}.yaml"
        if not pred_path.exists():
            print(f"  ! {genre}: no classifier output at {pred_path}")
            continue
        predicted = yaml.safe_load(pred_path.read_text(encoding="utf-8"))
        truth_by_id = _load_gt_affects(gt_path)
        pred_by_id = _pred_by_id(predicted)
        gloss_by_id = {
            g["id"]: g.get("gloss", "") for g in load_glosses_with_kinds(gt_path)
        }
        for m in _kindwrong_members(truth_by_id, pred_by_id):
            m["genre"] = genre
            m["anchor_gloss"] = gloss_by_id.get(m["anchor_id"], "")
            rows.append(m)

    by_op = Counter(r["op"] for r in rows)
    pairs = Counter((r["op"], r["gt_kind"], r["pred_kind"]) for r in rows)
    L7_DIR.mkdir(parents=True, exist_ok=True)
    out_path = L7_DIR / "kindwrong-pairs.txt"
    out_path.write_text(
        yaml.safe_dump(rows, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(
        f"== (c) KIND-WRONG: {len(rows)} members "
        f"(open={by_op.get('open', 0)} close={by_op.get('close', 0)}) -> {out_path} =="
    )
    for r in rows:
        tw = f" toward={r['toward']}" if r.get("toward") else ""
        print(
            f"  [{r['op']}] {r['genre']} {r['anchor_id']} {r['char']}: "
            f"GT={r['gt_kind']} PRED={r['pred_kind']}{tw}"
        )
        print(f"     anchor: {r['anchor_gloss'][:96]}")
    print("\n== confusion pairs (op | gt_kind -> pred_kind) ==")
    for (op, gk, pk), n in pairs.most_common():
        print(f"  [{op}] {gk} -> {pk}: {n}")
    return 0


def sweep_report() -> int:
    """FR-602 -- deterministic gate beat-tolerance window sweep on post-FR-600 GT.

    Scores the re-annotated ground truth against the EXISTING (post-FR-601)
    classifier output at match windows +/-0, +/-1, +/-2, +/-3, reporting BOTH
    ``affect_recall`` and ``affect_precision`` at each (the precision guard the
    Judge held load-bearing). Window 0 ties out to the frozen ``_l7_counts`` per
    genre before any wider window is trusted. NO LLM, NO model run, NO mutation of
    the canonical gate: the windowing lives in this probe (the copy/flag), the gate
    in ``evaluate.py`` is imported read-only and stays strict (+/-0).

    The decision artifact: BEAT-OFF recoverable = recall_hits(+/-1) - recall_hits(0).
    Every off!=0 recall member at +/-1 is dumped (predicted beat id, GT beat id,
    shared op/char/kind) so the genuine one-beat displacements can be read before
    any tolerance is recommended (AC#4). If that count is ~0, FR-602 closes unstarted.

    Persists the committed dump (Judge correction #1) to
    ``fixtures/affect-licensing/fr602-window-sweep.md``.
    """
    windows = (0, 1, 2, 3)
    agg = {w: {"recall_hits": 0, "precision_hits": 0} for w in windows}
    gt_total = 0
    pred_total = 0
    beatoff_at_1: list[dict] = []
    gloss_lookup: dict[str, dict[str, str]] = {}

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        pred_path = L7_DIR / f"{genre}.yaml"
        if not pred_path.exists():
            print(f"  ! {genre}: no classifier output at {pred_path}")
            continue
        predicted = yaml.safe_load(pred_path.read_text(encoding="utf-8"))
        truth_by_id = _load_gt_affects(gt_path)
        order = list(truth_by_id.keys())
        # restrict pred to GT beats -- mirrors the frozen gate denominator exactly
        pred_by_id = {
            b: v for b, v in _pred_by_id(predicted).items() if b in truth_by_id
        }
        gloss_lookup[genre] = {
            g["id"]: g.get("gloss", "") for g in load_glosses_with_kinds(gt_path)
        }
        gt_total += sum(len(v) for v in truth_by_id.values())
        pred_total += sum(len(v) for v in pred_by_id.values())

        # tie-out: window 0 MUST reproduce the frozen gate before trusting wider w
        gate = _l7_counts(predicted, truth_by_id)
        r0, _ = _windowed_match(truth_by_id, pred_by_id, order, 0)
        p0, _ = _windowed_match(pred_by_id, truth_by_id, order, 0)
        assert r0 == gate["recall_hits"], (
            f"{genre}: window-0 recall tie-out FAILED -- {r0} != gate "
            f"{gate['recall_hits']} (windowed matcher does not replicate the gate)"
        )
        assert p0 == gate["precision_hits"], (
            f"{genre}: window-0 precision tie-out FAILED -- {p0} != gate "
            f"{gate['precision_hits']}"
        )

        for w in windows:
            rh, rmem = _windowed_match(truth_by_id, pred_by_id, order, w)
            ph, _ = _windowed_match(pred_by_id, truth_by_id, order, w)
            agg[w]["recall_hits"] += rh
            agg[w]["precision_hits"] += ph
            if w == 1:
                for m in rmem:
                    m["genre"] = genre
                    m["gt_gloss"] = gloss_lookup[genre].get(m["anchor_id"], "")
                    m["pred_gloss"] = gloss_lookup[genre].get(m["cand_id"], "")
                    beatoff_at_1.append(m)

    def _frac(n: int, d: int) -> float:
        return round(n / d, 3) if d else 0.0

    recall = {w: _frac(agg[w]["recall_hits"], gt_total) for w in windows}
    precision = {w: _frac(agg[w]["precision_hits"], pred_total) for w in windows}
    beatoff_recoverable = agg[1]["recall_hits"] - agg[0]["recall_hits"]

    # --- console report -----------------------------------------------------
    print(f"== FR-602 window sweep (GT deltas={gt_total}, pred deltas={pred_total}) ==")
    print(f"{'window':>8} {'recall':>10} {'precision':>11} {'recall_hits':>12}")
    for w in windows:
        print(
            f"{('+/-' + str(w)):>8} {recall[w]:>10.3f} {precision[w]:>11.3f} "
            f"{agg[w]['recall_hits']:>12}"
        )
    print(
        f"\nBEAT-OFF recoverable at +/-1 (recall_hits[1]-recall_hits[0]): "
        f"{beatoff_recoverable}"
    )
    print(
        f"precision +/-0 -> +/-1: {precision[0]:.3f} -> {precision[1]:.3f} "
        f"(delta {precision[1] - precision[0]:+.3f})"
    )
    print(f"\n== {len(beatoff_at_1)} genuine +/-1 BEAT-OFF recall members ==")
    for m in beatoff_at_1:
        tw = f" toward={m['toward']}" if m.get("toward") else ""
        print(
            f"  {m['genre']} GT={m['anchor_id']} -> PRED={m['cand_id']} "
            f"(off {m['off']:+d}) {m['op']} {m['char']} {m['kind']}{tw}"
        )
        print(f"     GT   beat: {m['gt_gloss'][:88]}")
        print(f"     PRED beat: {m['pred_gloss'][:88]}")

    # --- committed dump (Judge correction #1) -------------------------------
    fixtures = EXAMPLE_DIR / "fixtures" / "affect-licensing"
    fixtures.mkdir(parents=True, exist_ok=True)
    dump = fixtures / "fr602-window-sweep.md"
    lines = [
        "# FR-602 Window Sweep (committed dump)",
        "",
        "Deterministic gate beat-tolerance sweep on the **post-FR-600** re-annotated",
        "ground truth and the **post-FR-601** classifier output. No LLM, no model run.",
        "Canonical `main_l7` / `_l7_counts` imported read-only and untouched; window 0",
        "ties out to the frozen gate per genre (asserted).",
        "",
        "Reproduce:",
        "",
        "```bash",
        "cd examples/plot_modeller && ../../.venv/bin/python probe_l7_misses.py --sweep",
        "```",
        "",
        f"GT deltas: {gt_total}  |  pred deltas (on GT beats): {pred_total}",
        "",
        "| window | affect_recall | affect_precision | recall_hits |",
        "|--------|---------------|------------------|-------------|",
    ]
    for w in windows:
        lines.append(
            f"| +/-{w} | {recall[w]:.3f} | {precision[w]:.3f} | {agg[w]['recall_hits']} |"
        )
    lines += [
        "",
        f"**BEAT-OFF recoverable at +/-1** (recall_hits[1]-recall_hits[0]): "
        f"**{beatoff_recoverable}**",
        "",
        f"**Precision guard** +/-0 -> +/-1: {precision[0]:.3f} -> {precision[1]:.3f} "
        f"(delta {precision[1] - precision[0]:+.3f})",
        "",
        f"## Genuine +/-1 BEAT-OFF recall members ({len(beatoff_at_1)})",
        "",
    ]
    if beatoff_at_1:
        lines += [
            "| genre | GT beat | PRED beat | off | op | char | kind |",
            "|-------|---------|-----------|-----|----|----|----|",
        ]
        for m in beatoff_at_1:
            lines.append(
                f"| {m['genre']} | {m['anchor_id']} | {m['cand_id']} | "
                f"{m['off']:+d} | {m['op']} | {m['char']} | {m['kind']} |"
            )
        lines.append("")
        for m in beatoff_at_1:
            lines += [
                f"- **{m['genre']} {m['anchor_id']} -> {m['cand_id']}** "
                f"({m['op']} {m['char']} {m['kind']}):",
                f"  - GT   beat: {m['gt_gloss']}",
                f"  - PRED beat: {m['pred_gloss']}",
            ]
    else:
        lines.append("_None -- no GT delta is recovered by a +/-1 neighbour._")
    dump.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n== committed dump -> {dump} ==")
    return 0


def absent_report() -> int:
    """Investigation -- decompose the (a) ABSENT residual: promptable or scale?

    ABSENT = the model placed NO op+char+kind match within +/-2 of a licensed GT
    beat (the residual after FR-600 re-anchoring + FR-601 kind cues). A prompt cue
    can only convert a perception the model already has, so the lever decision turns
    on WHY each beat is absent. Deterministic, no LLM: for every ABSENT miss this
    splits on what the model DID emit, into descending order of promptability:

      perceived_wrong_op  same char on the EXACT beat, wrong op  -> op-confusion cue
      perceived_near      same char within +/-2 beats            -> anchoring cue
      perceived_elsewhere same char somewhere in the plan        -> coverage cue
      engaged_other_char  a delta on the beat, different char    -> whose-feeling cue
      unperceived         nothing on the beat, char absent       -> detection floor / scale

    The first four mean the model engaged the character or the beat (promptable);
    only ``unperceived`` is the genuine scale ceiling. Also reports op/kind/relational
    splits and beat-position thirds so any structural cluster surfaces. Persists to
    ``results/l7/absent-decomposition.txt`` (gitignored scratch -- investigation, not
    a judged artifact).
    """
    from collections import Counter

    window = 2
    rows: list[dict] = []
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        pred_path = L7_DIR / f"{genre}.yaml"
        if not pred_path.exists():
            print(f"  ! {genre}: no classifier output at {pred_path}")
            continue
        predicted = yaml.safe_load(pred_path.read_text(encoding="utf-8"))
        truth_by_id = _load_gt_affects(gt_path)
        order = list(truth_by_id.keys())
        pred_by_id = _pred_by_id(predicted)
        gloss_by_id = {
            g["id"]: g.get("gloss", "") for g in load_glosses_with_kinds(gt_path)
        }
        pred_chars = {_norm(d.get("char")) for ds in pred_by_id.values() for d in ds}

        for bid, t_deltas in truth_by_id.items():
            for miss in _unmatched_gt(t_deltas, pred_by_id.get(bid, [])):
                if (
                    _classify_licensed(miss, bid, pred_by_id, order, window)
                    != "a_absent"
                ):
                    continue
                op = _norm(miss.get("op"))
                char = _norm(miss.get("char"))
                kind = _norm(miss.get("kind"))
                anchor_deltas = pred_by_id.get(bid, [])
                char_on_anchor = any(
                    _norm(d.get("char")) == char for d in anchor_deltas
                )
                idx = order.index(bid) if bid in order else None
                char_near = False
                if idx is not None:
                    for off in range(-window, window + 1):
                        if off == 0:
                            continue
                        j = idx + off
                        if 0 <= j < len(order) and any(
                            _norm(d.get("char")) == char
                            for d in pred_by_id.get(order[j], [])
                        ):
                            char_near = True
                            break

                if char_on_anchor:
                    perception = "perceived_wrong_op"
                elif char_near:
                    perception = "perceived_near"
                elif char in pred_chars:
                    perception = "perceived_elsewhere"
                elif anchor_deltas:
                    perception = "engaged_other_char"
                else:
                    perception = "unperceived"

                third = "?"
                if idx is not None and order:
                    frac = idx / max(1, len(order) - 1)
                    third = (
                        "early" if frac < 1 / 3 else "mid" if frac < 2 / 3 else "late"
                    )

                # FR-603 -- hope-mechanism split (correction 1/2/3). For a hope
                # miss, decide WHICH lever could recover it from the GT delta count
                # on the beat and the model's EXACT-BEAT emission (mechanical, no
                # impression):
                #   irreducible       the GT beat wants BOTH open hope AND close
                #                     hope for THIS char on ONE beat -- a fine
                #                     distinction a beat-grounded classifier may
                #                     legitimately not make; EXCLUDED from the
                #                     recoverable denominator (correction 3).
                #   cap_blocked       multi-delta beat (>=2 GT deltas) where the
                #                     model already emitted a delta on the EXACT
                #                     beat -- the "at most one operation per beat"
                #                     cap forbids the second (hope) delta
                #                     (mechanism 1).
                #   hope_open_missed  the model emitted nothing on the exact beat
                #                     that consumes the cap -- it simply did not
                #                     name the hope open (mechanism 2).
                gt_count = len(t_deltas)
                exact_emit = [
                    f"{_norm(d.get('op'))} {_norm(d.get('char'))} {_norm(d.get('kind'))}"
                    for d in anchor_deltas
                ]
                mechanism = ""
                if kind == "hope":
                    char_hope_ops = {
                        _norm(d.get("op"))
                        for d in t_deltas
                        if _norm(d.get("char")) == char
                        and _norm(d.get("kind")) == "hope"
                    }
                    if {"open", "close"} <= char_hope_ops:
                        mechanism = "irreducible"
                    elif anchor_deltas and gt_count >= 2:
                        mechanism = "cap_blocked"
                    else:
                        mechanism = "hope_open_missed"

                rows.append(
                    {
                        "genre": genre,
                        "anchor_id": bid,
                        "op": op,
                        "char": miss.get("char"),
                        "kind": kind,
                        "toward": miss.get("toward"),
                        "pos": f"{(idx + 1) if idx is not None else '?'}/{len(order)}",
                        "third": third,
                        "perception": perception,
                        "gt_count": gt_count,
                        "exact_emit": exact_emit,
                        "mechanism": mechanism,
                        "anchor_gloss": gloss_by_id.get(bid, ""),
                    }
                )

    promptable = {
        "perceived_wrong_op",
        "perceived_near",
        "perceived_elsewhere",
        "engaged_other_char",
    }
    n = len(rows)
    n_promptable = sum(1 for r in rows if r["perception"] in promptable)
    n_unperceived = n - n_promptable

    print(f"== (a) ABSENT decomposition: {n} members (window +/-{window}) ==\n")
    order_perc = [
        "perceived_wrong_op",
        "perceived_near",
        "perceived_elsewhere",
        "engaged_other_char",
        "unperceived",
    ]
    perc = Counter(r["perception"] for r in rows)
    for p in order_perc:
        tag = "PROMPTABLE" if p in promptable else "SCALE/FLOOR"
        print(f"  {p:<20} {perc.get(p, 0):>2}  [{tag}]")
    print(
        f"\n  -> promptable (model engaged char or beat): {n_promptable}/{n}"
        f"   |   unperceived (detection floor): {n_unperceived}/{n}"
    )

    print("\n  op split:        ", dict(Counter(r["op"] for r in rows)))
    print("  kind dist:       ", dict(Counter(r["kind"] for r in rows)))
    rel = Counter("relational" if r["kind"] in _RELATIONAL else "solo" for r in rows)
    print("  relational/solo: ", dict(rel))
    print("  position third:  ", dict(Counter(r["third"] for r in rows)))

    # --- FR-603 hope-mechanism split + pre-committed dominance/tie rule -------
    hope_rows = [r for r in rows if r["kind"] == "hope"]
    mech = Counter(r["mechanism"] for r in hope_rows)
    cap_blocked = mech.get("cap_blocked", 0)
    hope_open_missed = mech.get("hope_open_missed", 0)
    irreducible = mech.get("irreducible", 0)
    recoverable = cap_blocked + hope_open_missed  # correction 3 denominator
    dominant_threshold = 6  # FR-603 pre-committed: dominant = >=6 of recoverable
    if cap_blocked >= dominant_threshold:
        lever = "mechanism 1 (cap relaxation) -- DOMINANT (>=6 recoverable)"
    elif hope_open_missed >= dominant_threshold:
        lever = "mechanism 2 (hope-open cue) -- DOMINANT (>=6 recoverable)"
    else:
        lever = (
            "near-tie -> mechanism 2 (hope-open cue) FIRST "
            "(FR-603 tie rule: hope-scoped, low blast radius)"
        )
    print(f"\n== FR-603 hope-mechanism split ({len(hope_rows)} hope ABSENT members) ==")
    print(f"  cap_blocked        {cap_blocked:>2}  [mechanism 1: per-beat cap]")
    print(
        f"  hope_open_missed   {hope_open_missed:>2}  [mechanism 2: hope-open not named]"
    )
    print(
        f"  irreducible        {irreducible:>2}  [open+close same kind/char/beat -- EXCLUDED]"
    )
    print(
        f"  -> recoverable denominator: {recoverable} (irreducible {irreducible} excluded)"
    )
    print(f"  -> SELECTED LEVER: {lever}")
    for r in hope_rows:
        print(
            f"     [{r['mechanism']:<16}] {r['genre']} {r['anchor_id']} "
            f"({r['op']} {r['char']}) gt_deltas_on_beat={r['gt_count']} "
            f"exact_emit={r['exact_emit'] or '[]'}"
        )

    print("\n== members ==")
    for r in sorted(rows, key=lambda x: order_perc.index(x["perception"])):
        tw = f" toward={r['toward']}" if r.get("toward") else ""
        print(
            f"  [{r['perception']:<18}] {r['genre']} {r['anchor_id']} "
            f"({r['pos']},{r['third']}) {r['op']} {r['char']} {r['kind']}{tw}"
        )
        print(f"     anchor: {r['anchor_gloss'][:96]}")

    L7_DIR.mkdir(parents=True, exist_ok=True)
    out_path = L7_DIR / "absent-decomposition.txt"
    out_path.write_text(
        yaml.safe_dump(rows, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(f"\n== dump -> {out_path} ==")

    # --- committed evidence dump -------------------------------------------
    fixtures = EXAMPLE_DIR / "fixtures" / "affect-licensing"
    fixtures.mkdir(parents=True, exist_ok=True)
    md = fixtures / "l7-absent-decomposition.md"
    lines = [
        "# L7 (a) ABSENT Decomposition (committed evidence)",
        "",
        "Deterministic split of the (a) ABSENT residual (post-FR-600 GT,",
        "post-FR-601 predictions) by what the model DID emit -- the lever decision",
        "for whether the next L7 step is prompt engineering or model scale. No LLM.",
        "",
        "Reproduce:",
        "",
        "```bash",
        "cd examples/plot_modeller && ../../.venv/bin/python probe_l7_misses.py --absent",
        "```",
        "",
        f"## Perception split ({n} ABSENT members, window +/-{window})",
        "",
        "| perception | count | lever |",
        "|------------|-------|-------|",
    ]
    for p in order_perc:
        tag = "PROMPTABLE" if p in promptable else "SCALE/FLOOR"
        lines.append(f"| {p} | {perc.get(p, 0)} | {tag} |")
    lines += [
        "",
        f"**Promptable (model engaged char or beat): {n_promptable}/{n}  |  "
        f"unperceived (detection floor): {n_unperceived}/{n}**",
        "",
        "## Structural cuts",
        "",
        f"- op split: {dict(Counter(r['op'] for r in rows))}",
        f"- kind dist: {dict(Counter(r['kind'] for r in rows))}",
        f"- relational/solo: {dict(rel)}",
        f"- position third: {dict(Counter(r['third'] for r in rows))}",
        "",
        "## FR-603 hope-mechanism split",
        "",
        "For each hope ABSENT member, the lever that could recover it, decided from",
        "the GT delta count on the beat and the model's EXACT-BEAT emission:",
        "",
        "- `cap_blocked` -- multi-delta beat (>=2 GT deltas) where the model already",
        '  emitted a delta on the exact beat; the "at most one operation per beat"',
        "  cap forbids the second (hope) delta (mechanism 1).",
        "- `hope_open_missed` -- the model emitted nothing on the exact beat to",
        "  consume the cap; it simply did not name the hope open (mechanism 2).",
        "- `irreducible` -- the beat wants BOTH open hope AND close hope for the same",
        "  char on one beat; EXCLUDED from the recoverable denominator (correction 3).",
        "",
        "| mechanism | count |",
        "|-----------|-------|",
        f"| cap_blocked | {cap_blocked} |",
        f"| hope_open_missed | {hope_open_missed} |",
        f"| irreducible (excluded) | {irreducible} |",
        "",
        f"**Recoverable denominator: {recoverable}** "
        f"(irreducible {irreducible} excluded).",
        "",
        "**Pre-committed dominance/tie rule (FR-603):** dominant = >=6 of "
        "recoverable; else near-tie -> hope-open cue (mechanism 2) first.",
        "",
        f"**Selected lever: {lever}**",
        "",
        "| mechanism | genre | beat | op | char | gt_deltas_on_beat | exact_emit |",
        "|-----------|-------|------|----|----|-------------------|------------|",
    ]
    for r in hope_rows:
        emit = ", ".join(r["exact_emit"]) if r["exact_emit"] else "(none)"
        lines.append(
            f"| {r['mechanism']} | {r['genre']} | {r['anchor_id']} | {r['op']} | "
            f"{r['char']} | {r['gt_count']} | {emit} |"
        )
    lines += [
        "",
        "## Members",
        "",
        "| perception | genre | beat | pos | op | char | kind |",
        "|------------|-------|------|-----|----|----|----|",
    ]
    for r in sorted(rows, key=lambda x: order_perc.index(x["perception"])):
        lines.append(
            f"| {r['perception']} | {r['genre']} | {r['anchor_id']} | "
            f"{r['pos']},{r['third']} | {r['op']} | {r['char']} | {r['kind']} |"
        )
    lines.append("")
    for r in sorted(rows, key=lambda x: order_perc.index(x["perception"])):
        lines.append(
            f"- **{r['genre']} {r['anchor_id']}** [{r['perception']}] "
            f"({r['op']} {r['char']} {r['kind']}): {r['anchor_gloss']}"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"== committed evidence -> {md} ==")
    return 0


def main() -> int:
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # window -> bucket -> {open, close}
    pooled: dict[int, dict] = {w: _blank_buckets() for w in WINDOWS}
    pooled_hits = 0
    pooled_gt = 0
    miss_records: list[dict] = []  # dumped + read (read_raw_output_first)
    e_members: list[dict] = []  # every (e) classification (corr.#6 human-read)
    fixture_results: dict[tuple, tuple[bool, bool]] = {}

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        pred_path = L7_DIR / f"{genre}.yaml"
        if not pred_path.exists():
            print(
                f"  ! {genre}: no classifier output at {pred_path} — run spike_affect first"
            )
            continue
        predicted = yaml.safe_load(pred_path.read_text(encoding="utf-8"))
        truth_by_id = _load_gt_affects(gt_path)
        glosses = load_glosses_with_kinds(gt_path)
        order = [g["id"] for g in glosses]
        pred_by_id = _pred_by_id(predicted)

        # --- tie-out to the FROZEN gate (corr.#1) ----------------------------
        gate = _l7_counts(predicted, truth_by_id)
        recon_hits = 0
        misses: list[tuple[str, dict]] = []  # (anchor beat id, missed GT delta)
        for bid, t_deltas in truth_by_id.items():
            p_deltas = pred_by_id.get(bid, [])
            recon_hits += len(t_deltas) - len(_unmatched_gt(t_deltas, p_deltas))
            for m in _unmatched_gt(t_deltas, p_deltas):
                misses.append((bid, m))
        assert recon_hits == gate["recall_hits"], (
            f"{genre}: tie-out FAILED — reconstructed hits {recon_hits} != "
            f"gate recall_hits {gate['recall_hits']} (probe does not replicate the gate)"
        )
        pooled_hits += gate["recall_hits"]
        pooled_gt += gate["gt"]

        # --- bucket every miss: (e) FIRST, then a/b/c/d per window -----------
        for bid, miss in misses:
            op = _norm(miss.get("op"))
            lic = _licensing_verdict(miss, bid, glosses, provider, model)
            key = (genre, bid, op, _norm(miss.get("char")), _norm(miss.get("kind")))
            if key in _LICENSING_FIXTURES:
                fixture_results[key] = (lic["licensed"], lic["neighbor_licensed"])

            record = {
                "genre": genre,
                "anchor_id": bid,
                "gt_delta": {k: miss.get(k) for k in ("op", "char", "kind", "toward")},
                "anchor_gloss": next(
                    (g["gloss"] for g in glosses if g["id"] == bid), ""
                ),
                "licensing": lic,
            }

            if not lic["licensed"]:  # (e) UNLICENSED — window-independent
                for w in WINDOWS:
                    _add(pooled[w], "e_unlicensed", op)
                record["bucket"] = "e_unlicensed"
                record["neighbor_licensed"] = lic["neighbor_licensed"]
                e_members.append(record)
            else:
                record["bucket_by_window"] = {}
                for w in WINDOWS:
                    bucket = _classify_licensed(miss, bid, pred_by_id, order, w)
                    _add(pooled[w], bucket, op)
                    record["bucket_by_window"][w] = bucket
                if "c_kind_wrong" in record["bucket_by_window"].values():
                    # FR-601: carry the predicted mismatched kind for (c) members
                    for p in _op_char_on(
                        pred_by_id.get(bid, []), op, _norm(miss.get("char"))
                    ):
                        if _norm(p.get("kind")) != _norm(miss.get("kind")):
                            record["pred_kind"] = _norm(p.get("kind"))
                            break
            if len(miss_records) < 12:
                miss_records.append(record)

    # --- corr.#5: fixture-pin — the licensing pass MUST reproduce known answers
    print("\n== Licensing fixture-pin (corr.#5) ==")
    pin_ok = True
    for key, expected in _LICENSING_FIXTURES.items():
        got = fixture_results.get(key)
        ok = got == expected
        pin_ok = pin_ok and ok
        genre, bid, op, char, kind = key
        print(
            f"  [{'OK' if ok else 'FAIL'}] {genre} {bid} {op} {char} {kind}: "
            f"expected licensed/neighbor={expected}, got={got}"
        )
    if not pin_ok:
        print(
            "\nPROBE FAILS: the licensing pass did not reproduce its known-answer "
            "fixtures — an uncalibrated judge is not evidence (corr.#5). Re-run or "
            "fix the licensing prompt before trusting any (e) classification."
        )
        return 1

    # --- forced raw read BEFORE the aggregate (read_raw_output_first) ---------
    L7_DIR.mkdir(parents=True, exist_ok=True)
    samples_path = L7_DIR / "miss-samples.txt"
    samples_path.write_text(
        yaml.safe_dump(miss_records, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    e_path = L7_DIR / "unlicensed-members.txt"
    e_path.write_text(
        yaml.safe_dump(e_members, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    assert len(miss_records) >= 3, "need >=3 miss records dumped to read first"
    print(
        f"\n== {len(miss_records)} miss records dumped -> {samples_path} (READ before the aggregate) =="
    )
    for r in miss_records[:3]:
        d = r["gt_delta"]
        b = r.get("bucket") or r.get("bucket_by_window", {}).get(2, "?")
        print(
            f"  {r['genre']} {r['anchor_id']} [{b}] {d['op']} {d['char']} {d['kind']}"
            f"{(' -> ' + str(d['toward'])) if d.get('toward') else ''}"
        )
        print(f"     anchor: {r['anchor_gloss'][:96]}")
        print(f"     licensing: {r['licensing']['reason'][:96]}")
    print(
        f"\n== {len(e_members)} UNLICENSED (e) members dumped -> {e_path} (corr.#6: read EVERY one) =="
    )
    for r in e_members:
        d = r["gt_delta"]
        print(
            f"  {r['genre']} {r['anchor_id']} {d['op']} {d['char']} {d['kind']} "
            f"neighbor_licensed={r['neighbor_licensed']} :: {r['licensing']['reason'][:80]}"
        )

    # --- aggregate: 5 buckets x window x op, with conservation check ----------
    order_b = [
        "e_unlicensed",
        "a_absent",
        "b_beat_off",
        "c_kind_wrong",
        "d_toward_wrong",
    ]
    label = {
        "e_unlicensed": "(e) UNLICENSED  -> GT re-annotation / cross-beat",
        "a_absent": "(a) ABSENT      -> model scale (FR-578)",
        "b_beat_off": "(b) BEAT-OFF    -> evaluator tolerance / GT granularity",
        "c_kind_wrong": "(c) KIND-WRONG  -> six-kind taxonomy",
        "d_toward_wrong": "(d) TOWARD-WRONG-> relational-direction gap",
    }
    total_misses = pooled_gt - pooled_hits
    print(
        f"\n== Miss decomposition (pooled: {pooled_gt} GT deltas, {pooled_hits} hits, "
        f"{total_misses} misses) =="
    )
    for w in WINDOWS:
        buckets = pooled[w]
        bsum = sum(c["open"] + c["close"] for c in buckets.values())
        assert pooled_hits + bsum == pooled_gt, (
            f"conservation FAILED at window +/-{w}: hits {pooled_hits} + buckets "
            f"{bsum} != GT total {pooled_gt}"
        )
        print(f"\n  window +/-{w}:")
        for b in order_b:
            o, c = buckets[b]["open"], buckets[b]["close"]
            tot = o + c
            pct = (100.0 * tot / total_misses) if total_misses else 0.0
            print(
                f"    {label[b]:<46} {tot:>3} ({pct:4.0f}% of misses)  open={o} close={c}"
            )
        print(
            f"    conservation: {pooled_hits} hits + {bsum} misses == {pooled_gt} GT  [OK]"
        )

    # --- verdict: one dominant lever, or multi-cause -------------------------
    w_ref = 2  # report the dominant lever at the middle window
    buckets = pooled[w_ref]
    totals = {b: buckets[b]["open"] + buckets[b]["close"] for b in order_b}
    dom = max(totals, key=lambda b: totals[b])
    dom_pct = (100.0 * totals[dom] / total_misses) if total_misses else 0.0
    print("\n== Verdict (dominant lever at window +/-2; window-sensitivity carried) ==")
    if dom_pct > 50.0:
        print(f"  DOMINANT: {label[dom]}  ({dom_pct:.0f}% of misses).")
        # op-split call-out for ABSENT (corr.#3): close-heavy points at FR-598's
        # deleted arc-closure mandate, not a model ceiling.
        if (
            dom == "a_absent"
            and buckets["a_absent"]["close"] > buckets["a_absent"]["open"]
        ):
            print(
                "  NOTE: ABSENT is close-heavy -> the FR-598 deleted arc-closure "
                "mandate ('the novel was also the net'), NOT a model ceiling."
            )
        print(
            "  -> name the successor FR carrying THIS lever, with the window-sensitivity "
            "and op-split above as its evidence."
        )
    else:
        print(
            f"  MULTI-CAUSE: no bucket > 50% (top is {label[dom]} at {dom_pct:.0f}%). "
            "Split the escalation into per-bucket successor FRs; do not pull one lever."
        )
    return 0


if __name__ == "__main__":
    import sys

    if "--kindwrong" in sys.argv:  # FR-601: deterministic (c) read, no LLM
        raise SystemExit(kindwrong_report())
    if "--sweep" in sys.argv:  # FR-602: deterministic window sweep, no LLM
        raise SystemExit(sweep_report())
    if "--absent" in sys.argv:  # investigation: decompose (a) ABSENT, no LLM
        raise SystemExit(absent_report())
    raise SystemExit(main())
