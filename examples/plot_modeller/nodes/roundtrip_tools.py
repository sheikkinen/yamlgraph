"""Round-trip walking-skeleton leaf tools (FR-610 P0 scaffold).

The skeleton's only Python is leaf tools — all flow is declared in
``graphs/roundtrip_skeleton.yaml`` and run via ``yamlgraph graph run`` (no
Python runner). At P0 every "smart" node is a **stub returning a constant** so
the spine (premise -> cast -> briefs -> draft-map -> assemble -> gate) is proven
lint-green and end-to-end before any node is made intelligent.

The one genuinely non-stub leaf is :func:`assemble_book`: a deterministic,
no-LLM, *ordered* concatenation. Map fan-in order is non-deterministic, so the
order is imposed here by sorting on ``chapter_id`` (FR-610 / FR-612 corr 2), and
an empty assembly raises — so P0 cannot go green on a broken map fan-in that
would otherwise only surface in P2.

Later phases *fill* these nodes (P1 swaps the cast/brief stubs for LLM nodes,
P2 swaps the draft stub for an LLM prose node) without re-wiring the spine.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def assemble_book(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministically concatenate chapter drafts in ``chapter_id`` order.

    No LLM (the FR-492 whole-book discipline). Map fan-in order is
    non-deterministic, so the order is imposed here by sorting on
    ``chapter_id`` (FR-610 / FR-612 corr 2). An empty assembly raises so P0
    cannot go green on a broken map fan-in.
    """
    drafts = list(state.get("chapter_drafts") or [])
    if not drafts:
        raise ValueError(
            "assemble_book: no chapter_drafts to assemble - the map fan-in is empty"
        )
    ordered = sorted(drafts, key=lambda d: d["chapter_id"])
    ids = [d["chapter_id"] for d in ordered]
    if len(set(ids)) != len(ids):
        raise ValueError(
            f"assemble_book: duplicate chapter_id in drafts {ids} - an LLM draft"
            " echoed the wrong chapter_id, so the order is not well-defined"
        )
    book = "\n\n".join(f"## {d['title']}\n\n{d['text']}" for d in ordered)
    if not book.strip():
        raise ValueError("assemble_book: assembled book is empty")
    return {"book": book, "chapter_count": len(ordered)}


def validate_authored_arc(briefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministically reject the invalid arcs the FR-613 K=6 read condemned.

    Walks the authored ``briefs`` arc in ``chapter_id`` order (no LLM, no prose)
    and returns structural violations (FR-622 move 2 / C2). Each is a dict
    ``{kind, chapter_id, char, affect, detail}``. Three rules, each anchored to a
    specific defect the read found:

    - ``phantom_close`` - a ``close`` for a ``(char, kind)`` thread not currently
      open (loom draw2: ``close Mara/hope`` for a thread never opened). The bare
      pop-walk swallowed these silently.
    - ``final_chapter_open`` - an ``open`` in the last chapter, which cannot close
      by position (salt-road ``relief`` ch8; horror ``loss`` ch4).
    - ``scene_type_dose`` - a ``proactive`` chapter that accumulates >= 2 opens
      with no close (horror 4/4 proactive over grief/guilt/loss). Per the MRU
      prescription a proactive scene spends feeling through action (low dose); a
      lingering, accumulating interior load is reactive-class work mislabelled
      proactive. A single visceral spike (1 open) and an all-close climax
      (feeling spent through the disaster) are legitimate and never flagged.
    """
    chapters = sorted(
        (briefs or {}).get("chapters") or [],
        key=lambda c: c.get("chapter_id", 0),
    )
    if not chapters:
        return []
    last_chapter_id = chapters[-1].get("chapter_id", 0)

    violations: list[dict[str, Any]] = []
    live: set[tuple[str | None, str | None]] = set()
    for ch in chapters:
        cid = ch.get("chapter_id", 0)
        scene_type = ch.get("scene_type", "unknown")
        ops = ch.get("eff_affect") or []
        opens_here = 0
        closes_here = 0
        for delta in ops:
            key = (delta.get("char"), delta.get("kind"))
            if delta.get("op") == "open":
                opens_here += 1
                live.add(key)
                if cid == last_chapter_id and len(chapters) > 1:
                    violations.append(
                        {
                            "kind": "final_chapter_open",
                            "chapter_id": cid,
                            "char": key[0],
                            "affect": key[1],
                            "detail": "affect opened in the last chapter cannot close by position",
                        }
                    )
            elif delta.get("op") == "close":
                closes_here += 1
                if key not in live:
                    violations.append(
                        {
                            "kind": "phantom_close",
                            "chapter_id": cid,
                            "char": key[0],
                            "affect": key[1],
                            "detail": "close of a (char, kind) thread never opened",
                        }
                    )
                else:
                    live.discard(key)
        if scene_type == "proactive" and opens_here >= 2 and closes_here == 0:
            violations.append(
                {
                    "kind": "scene_type_dose",
                    "chapter_id": cid,
                    "char": None,
                    "affect": None,
                    "detail": (
                        f"proactive chapter accumulates {opens_here} unclosed opens; "
                        "a proactive scene spends feeling (low dose), it does not linger"
                    ),
                }
            )
    return violations


def coherence_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic coherence gate: ``authored_dangling_rate`` over the plan.

    Decision (a) (FR-613): the gate measures the **authored briefs'** affect
    arc, never the prose. It walks the ``eff_affect`` open/close ops the briefs
    carry, in ``chapter_id`` order, and reports how many authored opens never
    close — split by the chapter's authored ``scene_type``.

    The algorithm mirrors :func:`validators.affects.check_affect_closure`
    (FR-571) — an ordered, last-open-wins pop-walk keyed on ``(char, kind)`` —
    but the brief is a plain JSON dict, not a ``PlotPlan.Function``, and the
    metric needs per-``scene_type`` denominators the validator does not emit, so
    the same deterministic walk is implemented directly here (no LLM judge on
    the path).

    Pre-registered denominators (FR-613/FR-614): per ``scene_type``,
    ``authored_dangling_rate = unclosed authored opens / all authored opens``,
    where a dangling open is attributed to the ``scene_type`` of the chapter
    that *opened* it. This is a **plan-closure** number, not a prose claim —
    whether the prose delivers the authored close is P5's job (FR-615).
    """
    chapters = sorted(
        (state.get("briefs") or {}).get("chapters") or [],
        key=lambda c: c.get("chapter_id", 0),
    )

    opens_by_type: dict[str, int] = {}
    live: dict[tuple[str | None, str | None], str] = {}
    for ch in chapters:
        scene_type = ch.get("scene_type", "unknown")
        for delta in ch.get("eff_affect") or []:
            key = (delta.get("char"), delta.get("kind"))
            if delta.get("op") == "open":
                opens_by_type[scene_type] = opens_by_type.get(scene_type, 0) + 1
                live[key] = scene_type
            elif delta.get("op") == "close":
                live.pop(key, None)

    dangling_by_type: dict[str, int] = {}
    for origin_scene_type in live.values():
        dangling_by_type[origin_scene_type] = (
            dangling_by_type.get(origin_scene_type, 0) + 1
        )

    by_scene_type: dict[str, dict[str, Any]] = {}
    for scene_type in sorted(set(opens_by_type) | set(dangling_by_type)):
        opens = opens_by_type.get(scene_type, 0)
        dangling = dangling_by_type.get(scene_type, 0)
        by_scene_type[scene_type] = {
            "authored_opens": opens,
            "dangling": dangling,
            "authored_dangling_rate": (dangling / opens) if opens else 0.0,
        }

    total_opens = sum(opens_by_type.values())
    total_dangling = sum(dangling_by_type.values())
    violations = validate_authored_arc(state.get("briefs") or {})
    arc_valid = not violations
    report = {
        "authored_dangling_rate": (total_dangling / total_opens)
        if total_opens
        else 0.0,
        "authored_opens": total_opens,
        "dangling": total_dangling,
        "by_scene_type": by_scene_type,
        # FR-622 move 2 (C2): an invalid arc must not silently score 0.0. The
        # verdict fails on a structural violation OR an unclosed authored open.
        "arc_valid": arc_valid,
        "arc_violations": violations,
        "verdict": "pass" if arc_valid and total_dangling == 0 else "fail",
    }
    return {"coherence": report}


def persist_run(state: dict[str, Any]) -> dict[str, Any]:
    """Write the round-trip run's artifacts to a run-stamped directory (FR-623).

    Deterministic side-effect leaf (no LLM): the tail of the skeleton spine. Each
    finished stage key is written as its own file under
    ``<base>/<run_id>/`` where ``base`` is ``YAMLGRAPH_ROUNDTRIP_OUT`` (default
    ``outputs/roundtrip/``) and ``run_id`` is ``<UTC ts, microsecond>-<premise
    hash>``. The microsecond stamp (Corr 3) keeps two draws of one premise
    distinct so the Loom 0.40-vs-0.00 case is separable after the fact.

    ``provider``/``model`` are NOT in graph state (Corr 1) — they are sourced from
    the run environment (``PROVIDER`` / ``ANTHROPIC_MODEL``/``*_MODEL``) and
    recorded as ``"(unset)"`` when absent. Raises if any of ``cast``/``briefs``/
    ``book``/``coherence`` is missing, mirroring :func:`assemble_book`, so a broken
    upstream stage cannot yield a silent/empty run dir.
    """
    for required in ("cast", "briefs", "book", "coherence"):
        if state.get(required) is None:
            raise ValueError(
                f"persist_run: missing required stage '{required}' - an upstream"
                " node did not produce it, so the run dir would be incomplete"
            )

    premise = state.get("premise") or ""
    premise_hash = hashlib.sha256(premise.encode("utf-8")).hexdigest()[:8]
    now = datetime.now(UTC)
    run_id = f"{now.strftime('%Y%m%dT%H%M%S-%f')}Z-{premise_hash}"

    base = Path(os.environ.get("YAMLGRAPH_ROUNDTRIP_OUT") or "outputs/roundtrip")
    run_dir = base / run_id
    # The microsecond stamp distinguishes draws; a counter suffix guards the
    # (rare) same-microsecond collision so artifacts never clobber (Corr 3).
    suffix = 1
    while run_dir.exists():
        run_id = f"{now.strftime('%Y%m%dT%H%M%S-%f')}Z-{premise_hash}-{suffix}"
        run_dir = base / run_id
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)

    provider = os.environ.get("PROVIDER") or "(unset)"
    model = os.environ.get("ANTHROPIC_MODEL") or os.environ.get("MODEL") or "(unset)"
    manifest = {
        "run_id": run_id,
        "created_utc": now.isoformat(),
        "premise": premise,
        "genre": state.get("genre") or "",
        "provider": provider,
        "model": model,
        "chapter_count": state.get("chapter_count"),
        "note": "per-node model overrides (FR-622) are not captured by a single field",
    }

    def _dump_json(name: str, obj: Any) -> str:
        (run_dir / name).write_text(
            json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return name

    files = [
        _dump_json("manifest.json", manifest),
        _dump_json("cast.json", state["cast"]),
        _dump_json("briefs.json", state["briefs"]),
        _dump_json("coherence.json", state["coherence"]),
    ]
    (run_dir / "book.md").write_text(state["book"], encoding="utf-8")
    files.append("book.md")

    return {
        "artifacts": {
            "run_dir": str(run_dir),
            "run_id": run_id,
            "files": files,
        }
    }
