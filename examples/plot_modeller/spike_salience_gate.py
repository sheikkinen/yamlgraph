#!/usr/bin/env python3
"""FR-585 Gate 1 — salience-gate spike (throwaway measurement harness).

Tests the central FR-585 hypothesis in isolation: if the model ONLY decides
*which* world facts a beat depends on / changes (Node A), with no predicate
typing, naming, slice schema, belief nesting, or YAML acrobatics, does the
location-flooding precision wound shrink?

Pipeline:
  1. Node A (LLM, prompts/assign_pre_eff_salience.yaml) emits, per beat, two
     lists of `subject | relation | object` triples (requires / changes).
  2. A DELIBERATELY DUMB adapter (`_type_triple`) maps each triple to a typed
     fluent by keyword lookup ONLY — no LLM, no parsing intelligence (J:C1).
     A triple the table cannot place is dropped (costs recall, never precision).
  3. The typed per-beat pre/eff is written to results/l5/<genre>.yaml, scored by
     the unchanged evaluator, and dissected by analyze_l5_confusion.py.

Run:
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    python examples/plot_modeller/spike_salience_gate.py

Gate 1 verdict (FR-585 AC#1, C3): PASS needs `at`-FP to fall from the baseline
56 to < 30 with recall holding (no new catastrophic 0-beat run); precision ratio
>= 0.40 corroborates. The absolute `at`-FP count is the adapter-robust signal.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from nodes.tools import _strip_code_fences, load_glosses_with_kinds  # noqa: E402

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"

# Keyword → (predicate, value) tables for the dumb adapter. Order matters:
# negation phrases are checked before their positive roots.
_AT_WORDS = ("at", "in", "near", "inside", "reaches", "arrives", "located")
_HOLDS_WORDS = (
    "holds",
    "has",
    "have",
    "carries",
    "possesses",
    "owns",
    "holding",
    "with",
)
_FACTION_WORDS = ("member of", "belongs to", "part of", "faction", "serves")
_ALIVE_WORDS = ("alive", "living", "survives")
_DEAD_WORDS = ("dead", "killed", "deceased", "dies", "no longer alive")


def _load_gt_agents(gt_path: Path) -> list[str]:
    data = yaml.safe_load(gt_path.read_text(encoding="utf-8"))
    return data.get("agents", [])


def _is_negated(rel: str) -> bool:
    return any(
        neg in rel
        for neg in ("no longer", "not ", "without", "loses", "lost", "left", "departs")
    )


def _type_triple(triple: str) -> dict | None:
    """Map one `subject | relation | object` line to a typed fluent — DUMB.

    Keyword lookup only (J:C1): no NL parsing, no LLM. Returns a fluent dict
    ``{pred, args, value}`` or ``None`` if the relation word matches no rule
    (the triple is then dropped — a recall cost, never a precision gain).
    """
    parts = [p.strip() for p in str(triple).split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    subj = parts[0]
    rel = parts[1].lower().strip()
    obj = parts[2] if len(parts) >= 3 else ""
    neg = _is_negated(rel)

    # alive (one-place) — check before location/holds so "no longer alive" wins.
    if any(w in rel for w in _DEAD_WORDS):
        return {"pred": "alive", "args": [subj], "value": False}
    if any(w in rel for w in _ALIVE_WORDS):
        return {"pred": "alive", "args": [subj], "value": not neg}

    if not obj:
        return None  # two-place predicates need an object

    if any(w in rel for w in _FACTION_WORDS):
        return {"pred": "faction", "args": [subj, obj], "value": not neg}
    if rel.split()[-1] in _AT_WORDS or any(
        rel.startswith(w + " ") or rel == w for w in _AT_WORDS
    ):
        return {"pred": "at", "args": [subj, obj], "value": not neg}
    if any(w in rel for w in _HOLDS_WORDS):
        return {"pred": "holds", "args": [subj, obj], "value": not neg}

    # Default: a relationship label. Strip filler so the value is a bare label.
    label = rel
    for filler in ("is ", "to ", "with ", "toward ", "of "):
        if label.startswith(filler):
            label = label[len(filler) :]
    label = label.replace("no longer ", "").strip()
    return {"pred": "rel", "args": [subj, obj], "value": label or "related"}


def _adapt_beat(beat: dict) -> dict:
    """Turn one Node-A beat ({id, requires, changes}) into typed pre/eff."""
    pre = [f for t in (beat.get("requires") or []) if (f := _type_triple(t))]
    eff = [f for t in (beat.get("changes") or []) if (f := _type_triple(t))]
    return {
        "id": beat.get("id"),
        "pre_world": pre,
        "eff_world": eff,
        "pre_belief": [],
        "eff_belief": [],
    }


def _run_fixture(gt_path: Path, provider: str, model: str) -> list:
    glosses = load_glosses_with_kinds(gt_path)
    agents = _load_gt_agents(gt_path)
    raw = execute_prompt(
        "assign_pre_eff_salience",
        state={"glosses": glosses, "agents": agents},
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    try:
        beats = yaml.safe_load(_strip_code_fences(str(raw)))
    except yaml.YAMLError as exc:
        print(f"  ✗ YAML parse error: {exc}")
        return []
    if not isinstance(beats, list):
        print("  ✗ Node A did not return a list")
        return []
    return [_adapt_beat(b) for b in beats if isinstance(b, dict)]


def main() -> int:
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    l5_dir = RESULTS_DIR / "l5"
    l5_dir.mkdir(parents=True, exist_ok=True)

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        print(f"▶ salience-gate spike for {genre} ...")
        try:
            pre_eff = _run_fixture(gt_path, provider, model)
        except Exception as exc:  # hard failure → all-wrong, not a crash
            print(f"  ✗ run failed: {exc}")
            pre_eff = []
        (l5_dir / f"{genre}.yaml").write_text(
            yaml.safe_dump(pre_eff, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"  → wrote pre/eff for {len(pre_eff)} beats")

    from evaluate import main_l5 as evaluate_l5

    print("\n── L5 evaluation (salience-gate spike) ──")
    return evaluate_l5(["--provider", provider, "--model", model])


if __name__ == "__main__":
    raise SystemExit(main())
