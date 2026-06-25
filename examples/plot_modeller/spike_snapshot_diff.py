#!/usr/bin/env python3
"""FR-587 Gate 1 — snapshot-then-diff spike (throwaway measurement harness).

Tests the FR-587 hypothesis in isolation: if the LLM ONLY *comprehends* (emits a
per-beat world-state SNAPSHOT — what is physically true now) and *code* computes
the *change* by diffing consecutive snapshots, does the journey-waypoint `at`
flood that capped FR-585 Pass-2 precision shrink at its source?

Pipeline:
  1. Node A (LLM, prompts/assign_pre_eff_snapshot.yaml) emits, per beat, the
     COMPLETE current world state as `subject | relation | object` triples,
     starting from an opening `F0` baseline (no delta, no salience judgment).
  2. The SAME deliberately dumb adapter as FR-585 (`_type_triple`) maps each
     triple to a typed fluent by keyword lookup ONLY — no LLM (J:C1 carries over).
  3. `diff_snapshots` (deterministic, no LLM) diffs the typed snapshots into
     per-beat pre/eff, collapsing intra-chapter `at`-runs to net displacement and
     suppressing late departures (the salience rule the model could not apply).
  4. The result is written to results/l5/<genre>.yaml, scored by the UNCHANGED
     evaluator, and dissected by analyze_l5_confusion.py.

Run:
  set -a; source .env; set +a
  PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    python examples/plot_modeller/spike_snapshot_diff.py

Gate 1 decider (FR-587 corrections #1/#2): `at`-FP falling materially below the
FR-585 Pass-2 baseline 86 (toward <= 30) with recall holding (>= 0.50, no
catastrophic 0-beat run) is the adapter-robust GO/KILL signal; precision >= 0.40
corroborates but does not gate on the dumb adapter. KILL → FR-578 escalation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from nodes.tools import (  # noqa: E402
    _strip_code_fences,
    diff_snapshots,
    load_glosses_with_kinds,
)
from spike_salience_gate import _load_gt_agents, _type_triple  # noqa: E402

from yamlgraph.executor import execute_prompt  # noqa: E402

GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
RESULTS_DIR = EXAMPLE_DIR / "results"


def _type_snapshot(snap: dict, chapter_by_id: dict) -> dict:
    """Type one Node-A snapshot ({id, world:[triple]}) into typed fluents."""
    world = [f for t in (snap.get("world") or []) if (f := _type_triple(t))]
    return {
        "id": snap.get("id"),
        "chapter": chapter_by_id.get(snap.get("id")),
        "world": world,
    }


def _strip_stray_continuations(text: str) -> str:
    """Drop malformed indented ``key: value`` continuation lines (J:measurement).

    The model occasionally splits a fact across two lines (e.g. a ``rel`` fact
    followed by an indented ``rel_type: …``), which makes the whole document
    unparseable and would zero an entire fixture. Removing only those stray
    mapping-continuation lines salvages the valid facts above them so one slip
    does not invalidate the measurement. ``id:`` and ``world:`` keys are kept.
    """
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        leading = line[: len(line) - len(line.lstrip())]
        is_mapping = ":" in stripped and not stripped.startswith(("-", "#"))
        key = stripped.split(":", 1)[0] if is_mapping else ""
        if leading and is_mapping and key not in ("id", "world"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _parse_snapshots(raw: str) -> list:
    """Parse Node A output to a list of snapshots, salvaging stray lines once."""
    text = _strip_code_fences(str(raw))
    try:
        snaps = yaml.safe_load(text)
    except yaml.YAMLError:
        snaps = yaml.safe_load(_strip_stray_continuations(text))
    return snaps if isinstance(snaps, list) else []


def _run_fixture(gt_path: Path, provider: str, model: str) -> list:
    glosses = load_glosses_with_kinds(gt_path)
    agents = _load_gt_agents(gt_path)
    chapter_by_id = {g["id"]: g.get("chapter") for g in glosses}
    raw = execute_prompt(
        "assign_pre_eff_snapshot",
        state={"glosses": glosses, "agents": agents},
        prompts_dir=PROMPTS_DIR,
        temperature=0.7,
        provider=provider,
        model=model,
    )
    snaps = _parse_snapshots(raw)
    if not snaps:
        print("  ✗ Node A produced no parseable snapshots")
        return []
    typed = [_type_snapshot(s, chapter_by_id) for s in snaps if isinstance(s, dict)]
    return diff_snapshots(typed)


def main() -> int:
    provider = os.getenv("PROVIDER", "anthropic")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    l5_dir = RESULTS_DIR / "l5"
    l5_dir.mkdir(parents=True, exist_ok=True)

    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        print(f"▶ snapshot-diff spike for {genre} ...")
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

    print("\n── L5 evaluation (snapshot-diff spike) ──")
    return evaluate_l5(["--provider", provider, "--model", model])


if __name__ == "__main__":
    raise SystemExit(main())
