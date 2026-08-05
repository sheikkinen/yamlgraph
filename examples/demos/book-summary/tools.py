"""Demo-local loop helpers for the book-summary example (FR-775, D-5).

Python nodes around the cursor loop: envelope gates (R-4), batch
planning without inline arithmetic (R-1), page-identity accumulation
(R-3 — the collect key persists across iterations with _map_index
restarting per batch, so membership in the current batch is decided by
absolute page, never by list position), and cursor advance.

Each function receives the full graph state dict and returns an update
dict that LangGraph merges into state.
"""

BATCH_SIZE = 10


def _require_success(envelope: dict, step: str) -> dict:
    """Raise on a failed tool envelope (FR-775 R-4/AC-07)."""
    if not envelope.get("success"):
        raise ValueError(f"{step} failed: {envelope.get('error')}")
    return envelope["result"]


def gate_probe(state: dict) -> dict:
    """Seed total page count and cursor from the mode=info probe."""
    result = _require_success(state["probe_result"], "probe (pdfinfo)")
    return {"total": result["total"], "cursor": 1}


def prepare_batch(state: dict) -> dict:
    """Compute the current fetch window from cursor/total (R-1)."""
    cursor = state["cursor"]
    return {
        "batch_start": cursor,
        "batch_end": min(cursor + BATCH_SIZE - 1, state["total"]),
    }


def gate_fetch(state: dict) -> dict:
    """Unwrap the fetch envelope; expose chunks for map fan-out."""
    result = _require_success(state["fetch_result"], "fetch (pdftotext)")
    return {"chunks": result["chunks"]}


def accumulate(state: dict) -> dict:
    """Extract the current window's summaries by absolute page (R-3).

    Filters the ever-growing collect key to batch_start..batch_end,
    verifies each page was actually fetched this iteration, drops blank
    pages (empty summaries), sorts by page, and returns ONLY the new
    fragment — the ``add`` reducer on all_summaries appends it.
    """
    fetched_pages = {
        c["page"] for c in _require_success(state["fetch_result"], "fetch")["chunks"]
    }
    lo, hi = state["batch_start"], state["batch_end"]
    window = []
    for entry in state.get("page_summaries") or []:
        if not isinstance(entry, dict):
            continue
        if "_error" in entry:
            raise ValueError(
                f"page summary failed in window {lo}-{hi}: {entry['_error']}"
            )
        page = entry.get("page")
        if page is None or not lo <= page <= hi:
            continue
        if page not in fetched_pages:
            raise ValueError(
                f"summary claims page {page} in window {lo}-{hi} but that page "
                f"is not among fetched pages {sorted(fetched_pages)}"
            )
        window.append(entry)
    pages = [e["page"] for e in window]
    if len(pages) != len(set(pages)):
        raise ValueError(
            f"duplicate page summaries in window {lo}-{hi}: {sorted(pages)}"
        )
    fragment = sorted(
        (
            {"page": e["page"], "summary": e["summary"]}
            for e in window
            if str(e.get("summary") or "").strip()
        ),
        key=lambda e: e["page"],
    )
    return {"all_summaries": fragment}


def advance(state: dict) -> dict:
    """Move the cursor to the next batch window."""
    return {"cursor": state["cursor"] + BATCH_SIZE}


# --- FR-776 vision fallback (R-1..R-4) ---


def preflight_vision(state: dict) -> dict:
    """Validate the vision provider before any rendering (FR-776 R-3).

    No-op when vision_fallback is off; raises the allowlist error before
    the loop starts (and thus before any pdftoppm invocation) when the
    flag is on and the ambient provider cannot do vision.
    """
    if not state.get("vision_fallback"):
        return {}
    from examples.shared import vision_tool as vt

    vt.validate_vision_provider()
    return {}


def partition_chunks(state: dict) -> dict:
    """Split the fetched window into text/empty chunks (FR-776 R-1/R-4).

    text_seen accumulates across windows: once any window yields text the
    document is not OCR-less. vision_route decides the window's path —
    "vision" only when the flag is on AND blank pages exist.
    """
    chunks = state.get("chunks") or []
    text_chunks = [c for c in chunks if str(c.get("text") or "").strip()]
    empty_chunks = [c for c in chunks if not str(c.get("text") or "").strip()]
    route = "vision" if state.get("vision_fallback") and empty_chunks else "direct"
    # Empty Send fan-out dead-ends a LangGraph branch (verified: zero Sends
    # means downstream nodes never run). On the direct route an all-blank
    # window keeps its blank chunks (FR-775 behavior: empty summaries are
    # dropped by accumulate) so the loop stays alive.
    out_chunks = text_chunks if (text_chunks or route == "vision") else chunks
    return {
        "text_chunks": text_chunks,
        "empty_chunks": empty_chunks,
        "chunks": out_chunks,
        "text_seen": bool(state.get("text_seen")) or bool(text_chunks),
        "vision_route": route,
    }


def gate_render(state: dict) -> dict:
    """Window-filter render results by absolute page (FR-776 R-4).

    The collect key persists across iterations; stale out-of-window
    entries are dropped, in-window pages must belong to this window's
    empty_chunks, and errors or duplicates raise.
    """
    lo, hi = state["batch_start"], state["batch_end"]
    empty_pages = {c["page"] for c in state.get("empty_chunks") or []}
    window = []
    for entry in state.get("render_results") or []:
        if not isinstance(entry, dict):
            continue
        if "success" in entry:  # tool_call envelope — normalize at the boundary
            if not entry.get("success"):
                raise ValueError(
                    f"render failed in window {lo}-{hi}: {entry.get('error')}"
                )
            entry = {"_map_index": entry.get("_map_index"), **(entry["result"] or {})}
        if "_error" in entry:
            raise ValueError(f"render failed in window {lo}-{hi}: {entry['_error']}")
        page = entry.get("page")
        if page is None or not lo <= page <= hi:
            continue
        if page not in empty_pages:
            raise ValueError(
                f"render claims page {page} in window {lo}-{hi} but that page "
                f"is not among this window's empty pages {sorted(empty_pages)}"
            )
        window.append(entry)
    pages = [e["page"] for e in window]
    if len(pages) != len(set(pages)):
        raise ValueError(f"duplicate page renders in window {lo}-{hi}: {sorted(pages)}")
    return {
        "renders": sorted(
            ({"page": e["page"], "image": e["image"]} for e in window),
            key=lambda e: e["page"],
        )
    }


def transcribe_render(state: dict) -> dict:
    """Map subnode: transcribe one rendered page (FR-776 R-2)."""
    from examples.shared import vision_tool as vt

    render = state["render"]
    result = vt.transcribe_page(render["image"], render["page"])
    return {"transcription": result.model_dump()}


def merge_vision(state: dict) -> dict:
    """Merge transcriptions with text chunks into one sorted window (R-4).

    Same window discipline as gate_render: stale entries filtered by
    absolute page, in-window pages must be known empty pages, errors and
    duplicates raise. Blank transcriptions are dropped — genuinely empty
    pages stay nonfatal (R-1). Returns the single merged ``chunks`` list
    consumed by summarize_pages.
    """
    lo, hi = state["batch_start"], state["batch_end"]
    empty_pages = {c["page"] for c in state.get("empty_chunks") or []}
    window = []
    for entry in state.get("transcriptions") or []:
        if not isinstance(entry, dict):
            continue
        if "_error" in entry:
            raise ValueError(
                f"transcription failed in window {lo}-{hi}: {entry['_error']}"
            )
        page = entry.get("page")
        if page is None or not lo <= page <= hi:
            continue
        if page not in empty_pages:
            raise ValueError(
                f"transcription claims page {page} in window {lo}-{hi} but that "
                f"page is not among this window's empty pages {sorted(empty_pages)}"
            )
        window.append(entry)
    pages = [e["page"] for e in window]
    if len(pages) != len(set(pages)):
        raise ValueError(
            f"duplicate page transcriptions in window {lo}-{hi}: {sorted(pages)}"
        )
    merged = list(state.get("text_chunks") or [])
    merged.extend(
        {"page": e["page"], "text": e["text"]}
        for e in window
        if not e.get("is_blank") and str(e.get("text") or "").strip()
    )
    merged.sort(key=lambda c: c["page"])
    # Same dead-end protection as partition_chunks: a fully blank window
    # (every transcription is_blank) passes blank chunks through so the
    # summarize map still fans out and the loop advances.
    if not merged:
        merged = [dict(c) for c in state.get("empty_chunks") or []]
    return {"chunks": merged}


def guard_extractable(state: dict) -> dict:
    """Document-level OCR-less guard at the combine boundary (FR-776 R-1).

    Fires only when the WHOLE document yielded no text and the vision
    flag is off — blank internal windows stay nonfatal (FR-775).
    """
    if not state.get("vision_fallback") and not state.get("text_seen"):
        raise ValueError(
            f"no extractable text in {state.get('pdf')} — scanned/image-only "
            f"PDF? enable the vision fallback with --var vision_fallback=true "
            f"(FR-776)"
        )
    return {}
