"""FR-748 pipeline joins — the code between the three judgements.

Assemble chunk-theme candidates with globally unique keys after the map
fan-out; remap, reconcile, and decorate after the merge. The model
never carries FR ids across the merge boundary — keys join, code maps.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    mod_name = f"fr_atlas_{name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _repair_id(claim: str) -> str:
    """Token-fidelity repair at the map boundary: models echo the
    [bracket] sigils the digest block displays, and (third live strike,
    2026-07-18) append title parentheticals — 'FR-219 (Prompt Caching
    Demo)'. Strip decoration, keep the claim; genuine fabrications still
    die in enforce_coverage."""
    claim = claim.strip().strip("[]").strip("`'\" ").strip()
    # Trailing ' (…)' is decoration; a paren embedded in the slug is not.
    claim = re.sub(r"\s+\([^)]*\)$", "", claim)
    return claim.strip()


def _head(fr_id: str) -> str:
    """Numeric head of an id: 'FR-514-…' → 'FR-514', '070-old' → '070'."""
    parts = fr_id.split("-")
    return "-".join(parts[:2]) if parts and parts[0].upper() == "FR" else parts[0]


# Calibrated on the first live strike-pair: the true head-mate scored
# 0.59, the wrong one 0.308 (FR-424 paraphrase). Floor sits between.
_SIMILARITY_FLOOR = 0.5


def _reconcile_id(claim: str, population: set[str], heads: dict[str, list[str]]) -> str:
    """Reconcile a model claim against the collected population.

    Exact match → keep. Dropped FR- prefix → restore it (081-copilot-node
    for FR-081-copilot-node; unprefixed stems like 070-* stay exact
    matches). Unique numeric-head match → repair to the population id
    (models shorten slugs: FR-514-dm-v2-x → FR-514-x). Duplicate heads
    (two real FR-424 files exist) → repair to the strictly closest slug
    above a similarity floor; ties and misses pass through untouched and
    enforce_coverage raises loudly. Repair within the floor, reject below."""
    if claim in population:
        return claim
    if f"FR-{claim}" in population:
        return f"FR-{claim}"
    matches = heads.get(_head(claim), [])
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        scored = sorted(
            ((SequenceMatcher(None, claim, m).ratio(), m) for m in matches),
            reverse=True,
        )
        if scored[0][0] >= _SIMILARITY_FLOOR and scored[0][0] > scored[1][0]:
            return scored[0][1]
    return claim


def assemble_candidates(state: dict) -> dict:
    """map_results → chunk_themes (unique keys) + candidates_block."""
    population = set(state.get("fr_population") or [])
    heads: dict[str, list[str]] = {}
    for pid in population:
        heads.setdefault(_head(pid), []).append(pid)
    chunk_themes: list[dict] = []
    for result in state.get("map_results") or []:
        payload = (result or {}).get("chunk_verdicts") or result or {}
        chunk_id = payload.get("chunk_id") or f"c{len(chunk_themes)}"
        for theme in payload.get("themes") or []:
            key = f"{chunk_id}:{theme['name'].strip().lower().replace(' ', '-')}"
            chunk_themes.append(
                {
                    "key": key,
                    "name": theme["name"],
                    "arc": theme.get("arc", ""),
                    "fr_ids": [
                        _reconcile_id(_repair_id(i), population, heads)
                        for i in theme.get("fr_ids") or []
                    ],
                }
            )
    if not chunk_themes:
        raise ValueError("map stage yielded zero candidate themes")
    block = "\n".join(
        f"{ct['key']} — {ct['name']} ({len(ct['fr_ids'])} FRs): {ct['arc']}"
        for ct in chunk_themes
    )
    return {"chunk_themes": chunk_themes, "candidates_block": block}


def finalize_themes(state: dict) -> dict:
    """merge output → reconciled, module-decorated, story-ready themes."""
    coverage = _load("coverage")
    collect = _load("collect")
    merged = (state.get("merged") or {}).get("themes") or []
    themes = coverage.remap_chunk_themes(merged, state["chunk_themes"])
    themes = coverage.enforce_coverage(themes, state["fr_population"])

    by_id = {d["id"]: d for d in state["fr_digests"]}
    module_index = state.get("module_index") or {}
    for theme in themes:
        modules: list[str] = []
        for fr_id in theme["fr_ids"]:
            head = (
                fr_id.split("-")[0] + "-" + fr_id.split("-")[1]
                if "-" in fr_id
                else fr_id
            )
            modules += module_index.get(head, [])
            modules += by_id[fr_id].get("paths") or []
        counts: dict[str, int] = {}
        for m in modules:
            counts[m] = counts.get(m, 0) + 1
        theme["modules"] = [
            m for m, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:8]
        ]

    histogram = collect.status_histogram(state["fr_digests"])
    story_input = "\n".join(
        [f"Project: {Path(state['project_dir']).resolve().name}"]
        + [f"- {t['name']} ({len(t['fr_ids'])} FRs): {t['arc']}" for t in themes]
        + ["Status histogram: " + ", ".join(f"{k} {v}" for k, v in histogram.items())]
    )
    return {"final_themes": themes, "story_input": story_input}
