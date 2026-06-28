"""Abstraction-span example tools (FR-589).

Two Layer-3 Python tools, both returning dicts that merge into graph state
(``tools/python_tool`` contract: a dict return merges directly; ``state_key`` is
ignored for dict returns). No LLM is called here — orchestration and the single
LLM judgement live in ``graph.yaml`` / ``prompts/abstraction_span.yaml``.

- ``load_corpus``      — file I/O: read the manifest, load each referenced prompt
                         body, return ``{"corpus": [{name, text, label}]}``.
- ``separation_verdict`` — pure compute: the Gate. Given the collected per-prompt
                         scores + labels, decide whether the LLM reproduces the
                         monolith/clean separation. Never calls a model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# examples/abstraction_span/nodes/tools.py -> repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).resolve().parents[1] / "corpus" / "manifest.yaml"

# Label bands. The boundary prompt must land between the two; the measured-failure
# anchor must sit in the monolith band (FR-585 / FR-586 hand tagging).
MONOLITH = "monolith"
CLEAN = "clean"
BOUNDARY = "boundary"
ANCHOR = "assign_pre_eff"  # the one prompt with a measured L5 failure rate


def _prompt_text(path: Path) -> str:
    """Return the instruction body of a prompt YAML (system + user concatenated)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    parts = [str(data.get("system", "")).strip(), str(data.get("user", "")).strip()]
    return "\n\n".join(p for p in parts if p)


def load_corpus(state: dict[str, Any]) -> dict[str, Any]:
    """Read the manifest and load each referenced prompt's text.

    Returns a dict so it merges into state as ``corpus`` (python-tool contract).
    """
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    entries = manifest.get("prompts") or []
    if not entries:
        raise ValueError(f"Empty or missing corpus manifest: {MANIFEST}")

    corpus: list[dict[str, Any]] = []
    for entry in entries:
        prompt_path = REPO_ROOT / entry["path"]
        if not prompt_path.exists():
            raise FileNotFoundError(f"Corpus prompt not found: {prompt_path}")
        corpus.append(
            {
                "name": entry["name"],
                "text": _prompt_text(prompt_path),
                "label": entry["label"],
            }
        )
    return {"corpus": corpus}


def _align_scores(
    corpus: list[dict[str, Any]], scores: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Associate each map-collected score with its corpus item via ``_map_index``.

    The map node fans out in corpus order and tags each result with ``_map_index``;
    the collected list may arrive unordered, so align by that index.
    """
    if len(scores) != len(corpus):
        raise ValueError(
            f"Score/corpus length mismatch: {len(scores)} scores, {len(corpus)} prompts"
        )

    rows: list[dict[str, Any]] = []
    for score in scores:
        if "_error" in score:
            raise ValueError(f"A map branch failed: {score.get('_error')}")
        idx = score.get("_map_index")
        if idx is None or not (0 <= idx < len(corpus)):
            raise ValueError(f"Score missing valid _map_index: {score}")
        if "level_count" not in score:
            raise ValueError(f"Score missing level_count: {score}")
        item = corpus[idx]
        rows.append(
            {
                "name": item["name"],
                "label": item["label"],
                "level_count": int(score["level_count"]),
            }
        )
    return rows


def _render_table(rows: list[dict[str, Any]]) -> str:
    """Render a ranking table sorted by descending abstraction-span."""
    ordered = sorted(rows, key=lambda r: r["level_count"], reverse=True)
    lines = ["span  label      prompt", "----  ---------  ------"]
    for r in ordered:
        lines.append(f"{r['level_count']:>4}  {r['label']:<9}  {r['name']}")
    return "\n".join(lines)


def compute_verdict(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure separation gate over aligned ``[{name, label, level_count}]`` rows.

    PASS requires every monolith to score strictly above every clean prompt
    (``min(monolith) > max(clean)``, gap >= 1), the boundary prompt to land
    between the two bands, and the measured-failure anchor to sit in the monolith
    band. Otherwise KILL: the LLM cannot reproduce the hand tagging.
    """
    monolith = [r["level_count"] for r in rows if r["label"] == MONOLITH]
    clean = [r["level_count"] for r in rows if r["label"] == CLEAN]
    boundary = [r["level_count"] for r in rows if r["label"] == BOUNDARY]
    if not monolith or not clean:
        raise ValueError(
            "Corpus must contain at least one monolith and one clean prompt"
        )

    min_monolith = min(monolith)
    max_clean = max(clean)
    gap = min_monolith - max_clean

    # Boundary prompt(s) must land strictly between the clean ceiling and the
    # monolith floor (inclusive of the edges of the gap).
    goals_between = (
        all(max_clean <= b <= min_monolith for b in boundary) if boundary else True
    )

    anchor_rows = [r["level_count"] for r in rows if r["name"] == ANCHOR]
    anchor_in_band = bool(anchor_rows) and min(anchor_rows) >= min_monolith

    passed = (
        (min_monolith > max_clean) and (gap >= 1) and goals_between and anchor_in_band
    )

    return {
        "passed": passed,
        "min_monolith": min_monolith,
        "max_clean": max_clean,
        "gap": gap,
        "goals_between": goals_between,
        "anchor_in_band": anchor_in_band,
        "table": _render_table(rows),
        "ranking": sorted(rows, key=lambda r: r["level_count"], reverse=True),
    }


def separation_verdict(state: dict[str, Any]) -> dict[str, Any]:
    """Graph node: compute the separation verdict from state corpus + scores.

    Returns a dict so it merges into state as ``verdict`` (python-tool contract).
    """
    corpus = state.get("corpus") or []
    scores = state.get("scores") or []
    if not corpus:
        raise ValueError("No corpus in state — did the load node run?")
    if not scores:
        raise ValueError("No scores in state — did the map node run?")

    rows = _align_scores(corpus, scores)
    verdict = compute_verdict(rows)

    decision = "GO (PASS)" if verdict["passed"] else "KILL (null result)"
    print("\n=== Abstraction-span separation gate ===")
    print(verdict["table"])
    print(
        f"\nmin(monolith)={verdict['min_monolith']}  max(clean)={verdict['max_clean']}  "
        f"gap={verdict['gap']}  goals_between={verdict['goals_between']}  "
        f"anchor_in_band={verdict['anchor_in_band']}"
    )
    print(f"Verdict: {decision}\n")

    return {"verdict": verdict}
