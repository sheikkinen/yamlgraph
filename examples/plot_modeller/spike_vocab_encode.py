"""FR-591 spike: oracle controlled-vocabulary encode test.

Tests the hypothesis that binding L5 encoding to a story-specific controlled
vocabulary lifts world recall. Uses ORACLE vocab (extracted from the ground
truth) to measure the recall *ceiling*, reusing the already-generated viewpoints
on disk so ONLY the encode step varies (single-variable test).

Usage:
    set -a; source .env; set +a; \
    PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
    .venv/bin/python examples/plot_modeller/spike_vocab_encode.py [genre]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parent.parent
sys.path.insert(0, str(EXAMPLE_DIR))
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402
from evaluate import _load_gt_pre_eff, score_l5  # noqa: E402
from nodes.tools import (  # noqa: E402
    _parse_beats,
    combine_perspectives,
    load_glosses_with_kinds,
)

from yamlgraph.executor import execute_prompt  # noqa: E402

PROMPTS_DIR = EXAMPLE_DIR / "prompts"
GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
PERSP_DIR = EXAMPLE_DIR / "results" / "perspectives"
L5_DIR = EXAMPLE_DIR / "results" / "l5"


def _safe_name(name: object) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name or ""))
    return cleaned.strip("_") or "agent"


def extract_oracle_vocab(gt_path: Path) -> dict:
    """Collect the closed token set the ground truth actually scores on."""
    data = yaml.safe_load(gt_path.read_text(encoding="utf-8"))
    locations: set[str] = set()
    objects: set[str] = set()
    characters: set[str] = set(data.get("agents", []) or [])
    relationships: set[str] = set()

    def scan(fluents: list | None) -> None:
        for f in fluents or []:
            if not isinstance(f, dict):
                continue
            pred = f.get("pred")
            args = f.get("args", []) or []
            val = f.get("value")
            if pred == "at" and len(args) >= 2:
                locations.add(str(args[1]))
            elif pred == "holds" and len(args) >= 2:
                objects.add(str(args[1]))
            elif pred == "rel":
                if len(args) >= 2:
                    characters.add(str(args[1]))
                if isinstance(val, str):
                    relationships.add(val)

    scan(data.get("initial_world"))
    for fn in data.get("functions", []) or []:
        scan(fn.get("pre_world"))
        scan(fn.get("eff_world"))
    return {
        "locations": sorted(locations),
        "objects": sorted(objects),
        "characters": sorted(characters),
        "relationships": sorted(relationships),
    }


def main(genre: str, provider: str, model: str) -> int:
    gt_path = GT_DIR / f"{genre}.yaml"
    if not gt_path.exists():
        print(f"No ground truth for {genre}")
        return 1

    vocab = extract_oracle_vocab(gt_path)
    print("── ORACLE VOCAB ──")
    for k, v in vocab.items():
        print(f"  {k}: {v}")

    glosses = load_glosses_with_kinds(gt_path)
    agents = yaml.safe_load(gt_path.read_text(encoding="utf-8")).get("agents", []) or []
    persp_dir = PERSP_DIR / genre

    perspectives: list[dict] = []
    for i, agent in enumerate(agents):
        vp_path = persp_dir / f"{_safe_name(agent)}.md"
        viewpoint = vp_path.read_text(encoding="utf-8") if vp_path.exists() else ""
        if not viewpoint.strip():
            print(f"  ! no viewpoint on disk for {agent} ({vp_path.name}); skipping")
            continue
        raw = execute_prompt(
            "encode_perspective",
            variables={},
            state={
                "agent": agent,
                "glosses": glosses,
                "viewpoint": viewpoint,
                "vocab": vocab,
            },
            prompts_dir=PROMPTS_DIR,
            provider=provider,
            model=model,
            temperature=0.0,
        )
        beats = _parse_beats(raw)
        print(f"  ✓ {agent}: {len(beats)} beats encoded")
        perspectives.append(
            {"agent": agent, "viewpoint": viewpoint, "beats": beats, "_map_index": i}
        )

    l5 = combine_perspectives(perspectives)
    truth_by_id = _load_gt_pre_eff(gt_path)
    ev = score_l5(genre, l5, truth_by_id, provider, model)

    L5_DIR.mkdir(parents=True, exist_ok=True)
    out = L5_DIR / f"{genre}.vocab-oracle.yaml"
    out.write_text(yaml.safe_dump(l5, sort_keys=False, allow_unicode=True), "utf-8")

    print("\n── VOCAB-ORACLE L5 EVAL ──")
    print(yaml.safe_dump(ev["summary"], sort_keys=False).rstrip())
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    g = sys.argv[1] if len(sys.argv) > 1 else "scifi-hybrid-the-loom"
    raise SystemExit(
        main(
            g,
            os.environ.get("PROVIDER", "anthropic"),
            os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
        )
    )
