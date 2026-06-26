#!/usr/bin/env python3
"""FR-598 — single-pass per-beat affect classifier spike (throwaway harness).

Successor to the FR-596 two-pass spike. FR-598 ("kill the novel") found the L7
affect_recall floor was caused by the prose intermediate: ``affect_throughline``
asked haiku for prose narration, and haiku returned a literary novel that
invented affect (whole arcs for non-characters), blurred kinds, and smeared
beats. The granted Judgement froze two load-bearing changes: (a) replace the
prose with a terse per-beat CLASSIFICATION that emits typed YAML directly, and
(b) DELETE the "every arc that opens should close" mandate (the invention
engine). The two-pass collapses to one node; ``encode_affect`` is retired.

Pipeline (per fixture, per **GROUND-TRUTH agent** — a feeler the extractor would
drop is never structurally unreachable against the GT-anchored gate):
  1. affect_throughline  (LLM, typed YAML)  → results/l7/throughlines/<genre>/<agent>.yaml
  2. combine_affects     (deterministic code, no LLM) → results/l7/<genre>.yaml
  3. evaluate.main_l7    re-scores against GT (the FROZEN FR-578 gate)

Beyond the official conjunctive affect_recall, the spike reports three additive
sub-axis diagnostics that decompose WHERE recall is lost — detection (op+char
alignment, where char is near-free because each cell fixes char to the focal
agent), kind-given-detection, and toward-given-relational — plus the per-genre
agent-coverage ceiling.

Verdict (FR-598 stop rule) reads the sub-axes to NAME the flavor BEFORE citing
the aggregate:
  - detection LOW   → PROSE-MISSED: the per-agent framing is falsified;
                      model-scale escalation (FR-578) is justified.
  - detection HELD but kind-given-detection LOW → KIND CEILING: the ONE format
                      iteration is spent, so a flat kind axis is a real
                      kind-discrimination / taxonomy ceiling — fire the reserved
                      escalation (FR-578 model scale, or revisit the six-kind
                      taxonomy), NOT a second wording pass.
  - affect_recall >= 0.50 with detection HELD and toward off zero → GO: promote
                      the classifier to a graph (FR-579 unblocks on the graph
                      EXISTING; production ACCEPT still needs >= 0.70).

Run:
  set -a; source .env; set +a
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    python examples/plot_modeller/spike_affect.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from evaluate import _load_gt_affects, main_l7  # noqa: E402
from nodes.tools import (  # noqa: E402
    _strip_code_fences,
    affect_balance,
    combine_affects,
    load_glosses_with_kinds,
)

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"

# Verdict thresholds (Judgement correction #3 routing levers).
_GO_RECALL = 0.50
_DETECTION_FLOOR = 0.50
_KIND_FLOOR = 0.60


def _load_gt_agents(gt_path: Path) -> list[str]:
    """Load the ground-truth agent roster (Gate-1 isolation — correction #1)."""
    data = yaml.safe_load(gt_path.read_text(encoding="utf-8"))
    return data.get("agents", []) or []


def _safe_name(name: object) -> str:
    """Filesystem-safe stem for a character's throughline file."""
    cleaned = "".join(
        c if c.isalnum() or c in "-_" else "_" for c in str(name or "")
    ).strip("_")
    return cleaned or "agent"


def _norm(s: object) -> str:
    return " ".join(str(s or "").split()).strip().lower()


def _parse_affect_list(raw: str) -> list:
    """Parse affect_throughline (single-pass classifier) output to beats."""
    try:
        data = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError:
        return []
    return data if isinstance(data, list) else []


def _classify_agent(
    glosses: list, agent: str, provider: str, model: str, genre_dir: Path
) -> dict:
    """Run the single-pass per-beat classifier for one agent.

    FR-598 collapses the FR-596 two-pass (prose throughline -> encode) into one
    node: ``affect_throughline`` now emits typed YAML directly. The raw output is
    stored to ``<agent>.yaml`` so >=3 samples can be READ before the aggregate is
    read (forced-observation discipline, Scripture ``read_raw_output_first``).
    """
    raw = execute_prompt(
        "affect_throughline",
        state={"glosses": glosses, "agent": agent},
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    (genre_dir / f"{_safe_name(agent)}.yaml").write_text(
        str(raw or ""), encoding="utf-8"
    )
    return {
        "agent": agent,
        "throughline": raw,
        "affects": _parse_affect_list(raw),
    }


# --- sub-axis diagnostics (correction #2: decompose where recall is lost) ------


def _subaxis_counts(gt_by_id: dict, pred_by_id: dict) -> dict:
    """Decompose recall into detection / kind-given-detection / toward-given-relational.

    Greedy per-beat match. ``detection`` = op + char aligned (char is near-free
    here because each cell fixes char to the focal agent — recording this keeps
    0.70 from reading as harder than it is). ``kind`` adds the kind axis on top of
    a detection. ``toward`` is scored only over relational (guilt/betrayal) GT
    deltas that were already detected.
    """
    gt = det = kind = rel_gt = rel_toward = 0
    for bid, g_deltas in gt_by_id.items():
        p_deltas = pred_by_id.get(bid, [])
        used = [False] * len(p_deltas)
        for g in g_deltas:
            gt += 1
            g_rel = _norm(g.get("kind")) in ("guilt", "betrayal")
            if g_rel:
                rel_gt += 1
            for i, p in enumerate(p_deltas):
                if used[i]:
                    continue
                if _norm(p.get("op")) == _norm(g.get("op")) and _norm(
                    p.get("char")
                ) == _norm(g.get("char")):
                    used[i] = True
                    det += 1
                    if _norm(p.get("kind")) == _norm(g.get("kind")):
                        kind += 1
                        if g_rel and _norm(p.get("toward")) == _norm(g.get("toward")):
                            rel_toward += 1
                    break
    return {
        "gt": gt,
        "det": det,
        "kind": kind,
        "rel_gt": rel_gt,
        "rel_toward": rel_toward,
    }


def _agent_coverage(gt_by_id: dict, roster: list[str]) -> tuple[int, int]:
    """(# GT affect chars present in roster, # distinct GT affect chars)."""
    roster_norm = {_norm(a) for a in roster}
    gt_chars = {_norm(d.get("char")) for deltas in gt_by_id.values() for d in deltas}
    gt_chars.discard("")
    present = sum(1 for c in gt_chars if c in roster_norm)
    return present, len(gt_chars)


def _pred_by_id(combined: list) -> dict:
    out: dict[str, list] = {}
    for item in combined:
        if isinstance(item, dict) and item.get("id"):
            ea = item.get("eff_affect")
            out[item["id"]] = ea if isinstance(ea, list) else []
    return out


def main() -> int:
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    l7_dir = RESULTS_DIR / "l7"
    tl_root = l7_dir / "throughlines"
    l7_dir.mkdir(parents=True, exist_ok=True)

    totals = {"gt": 0, "det": 0, "kind": 0, "rel_gt": 0, "rel_toward": 0}
    cov_present = cov_total = 0
    dangling: list[str] = []

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        glosses = load_glosses_with_kinds(gt_path)
        agents = _load_gt_agents(gt_path)
        genre_dir = tl_root / genre
        genre_dir.mkdir(parents=True, exist_ok=True)
        print(f"▶ affect-throughline spike for {genre} ({len(agents)} GT agents) ...")

        records: list[dict] = []
        for idx, agent in enumerate(agents):
            try:
                rec = _classify_agent(glosses, agent, provider, model, genre_dir)
            except Exception as exc:  # hard failure → empty, not a crash
                print(f"  ✗ {agent}: {exc}")
                rec = {"agent": agent, "throughline": "", "affects": []}
            rec["_map_index"] = idx
            bal = affect_balance(rec["affects"])
            if not bal["balanced"]:
                dangling.extend(f"{genre}/{agent}:{u}" for u in bal["unclosed"])
            records.append(rec)

        combined = combine_affects(records)
        (l7_dir / f"{genre}.yaml").write_text(
            yaml.safe_dump(combined, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        gt_by_id = _load_gt_affects(gt_path)
        counts = _subaxis_counts(gt_by_id, _pred_by_id(combined))
        for k in totals:
            totals[k] += counts[k]
        present, total = _agent_coverage(gt_by_id, agents)
        cov_present += present
        cov_total += total
        print(
            f"  → {len(combined)} beats; detection {counts['det']}/{counts['gt']}, "
            f"kind {counts['kind']}/{counts['det'] or 1}, "
            f"agent-coverage {present}/{total}"
        )

    # --- official frozen FR-578 gate -----------------------------------------
    print("\n── L7 evaluation (per-agent throughline spike) ──")
    main_l7(["--provider", provider, "--model", model])

    # --- sub-axis aggregate + verdict (corrections #2/#3) --------------------
    det_recall = totals["det"] / totals["gt"] if totals["gt"] else 0.0
    kind_given_det = totals["kind"] / totals["det"] if totals["det"] else 0.0
    toward_given_rel = (
        totals["rel_toward"] / totals["rel_gt"] if totals["rel_gt"] else 0.0
    )
    coverage = cov_present / cov_total if cov_total else 1.0

    print("\n── Sub-axis diagnostics (additive; the official gate is above) ──")
    print(f"  agent-coverage ceiling   : {coverage:.2f} ({cov_present}/{cov_total})")
    print(
        f"  detection recall (op+char): {det_recall:.2f} "
        f"({totals['det']}/{totals['gt']})  [char near-free — focal-agent cell]"
    )
    print(
        f"  kind | detection          : {kind_given_det:.2f} "
        f"({totals['kind']}/{totals['det']})"
    )
    print(
        f"  toward | relational det.  : {toward_given_rel:.2f} "
        f"({totals['rel_toward']}/{totals['rel_gt']})"
    )
    if dangling:
        print(f"  dangling open arcs        : {len(dangling)} (per-cell balance)")

    print("\n── Verdict (flavor named BEFORE aggregate — FR-598 stop rule) ──")
    if det_recall < _DETECTION_FLOOR:
        print(
            f"  KILL flavor = PROSE-MISSED. Detection recall {det_recall:.2f} < "
            f"{_DETECTION_FLOOR:.2f}: the classifier does not even place arcs on "
            "the right beats — the per-agent FRAMING is FALSIFIED. Model-scale "
            "escalation (FR-578) is the justified lever. Raw classifier output is "
            "stored under results/l7/throughlines/<genre>/<agent>.yaml — READ >=3 "
            "before trusting this aggregate (read_raw_output_first)."
        )
        return 0
    if kind_given_det < _KIND_FLOOR:
        print(
            f"  KIND CEILING. Detection recall {det_recall:.2f} is healthy (arcs land "
            f"on the right beats) but kind|detection {kind_given_det:.2f} < "
            f"{_KIND_FLOOR:.2f}. FR-598 already replaced prose with a terse per-beat "
            "classifier and deleted the arc-closure mandate — the ONE format "
            "iteration is spent. A flat kind axis here is a real kind-discrimination "
            "/ taxonomy ceiling, NOT a second wording pass: fire the reserved "
            "escalation (FR-578 model scale, or revisit the six-kind taxonomy)."
        )
        return 0
    print(
        "  GO candidate. Detection HELD and kind|detection cleared their floors with "
        "toward off zero. If the official affect_recall above is >= "
        f"{_GO_RECALL:.2f}, promote the classifier to a graph (FR-579 unblocks on the "
        "graph EXISTING; production ACCEPT still needs >= 0.70 — L7 stays REVISE "
        "until then)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
