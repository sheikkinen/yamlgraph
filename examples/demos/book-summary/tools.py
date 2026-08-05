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
