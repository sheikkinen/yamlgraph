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
P2 swaps the draft stub) without re-wiring the spine.
"""

from __future__ import annotations

from typing import Any


def stub_derive_cast(state: dict[str, Any]) -> dict[str, Any]:
    """P0 stub: a constant cast line. Replaced by an LLM node in P1 (FR-611)."""
    return {"cast": "Mara - pilot, guards a secret. Jonas - engineer, seeks the truth."}


def stub_outline_briefs(state: dict[str, Any]) -> dict[str, Any]:
    """P0 stub: two constant chapter briefs reserving the P1 affect-arc shape.

    Each brief carries authored ``scene_type`` and an ``eff_affect`` list so the
    coherence gate has the exact shape to walk once P1 fills them with real
    open/close ops (decision (a): closure is measured over the authored plan).
    The ``eff_affect`` lists are empty at P0 — emission is P1's job.
    """
    briefs = [
        {
            "chapter_id": 1,
            "title": "Chapter 1 - The Signal",
            "summary": "Mara intercepts a signal and decides to act.",
            "cast": ["Mara"],
            "beats": [
                "intercepts the signal",
                "weighs the risk",
                "commits to the launch",
            ],
            "entry_state": "Mara is grounded and idle.",
            "exit_state": "Mara has launched toward the source.",
            "scene_type": "proactive",
            "eff_affect": [],
        },
        {
            "chapter_id": 2,
            "title": "Chapter 2 - The Drive in Her Bag",
            "summary": "Mara confronts what the signal means and lets herself believe Jonas.",
            "cast": ["Mara", "Jonas"],
            "beats": ["reaches the source", "argues with Jonas", "accepts the truth"],
            "entry_state": "Mara distrusts Jonas.",
            "exit_state": "Mara trusts Jonas.",
            "scene_type": "reactive",
            "eff_affect": [],
        },
    ]
    return {"briefs": briefs}


def stub_draft_chapter(state: dict[str, Any]) -> dict[str, Any]:
    """P0 stub map sub-node: emit a placeholder draft for one brief.

    The map injects the current brief as ``state['brief']``. The returned draft
    carries ``chapter_id`` so :func:`assemble_book` can impose a deterministic
    order independent of the non-deterministic map fan-in. Replaced by an LLM
    prose node in P2 (FR-612).
    """
    brief = state.get("brief") or {}
    chapter_id = brief.get("chapter_id", 0)
    title = brief.get("title", f"Chapter {chapter_id}")
    return {
        "draft": {
            "chapter_id": chapter_id,
            "title": title,
            "text": f"[stub prose for {title}]",
        }
    }


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
    book = "\n\n".join(f"## {d['title']}\n\n{d['text']}" for d in ordered)
    if not book.strip():
        raise ValueError("assemble_book: assembled book is empty")
    return {"book": book, "chapter_count": len(ordered)}


def coherence_gate(state: dict[str, Any]) -> dict[str, Any]:
    """P0 stub gate: an empty coherence report.

    P3 (FR-613) fills this with the deterministic ``authored_dangling_rate``
    walk over the authored briefs' ``eff_affect`` ops, split by ``scene_type``.
    """
    return {"coherence": {}}
