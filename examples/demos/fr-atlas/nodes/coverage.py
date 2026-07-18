"""FR-748 coverage post-pass — the honesty spine (REQ-YG-566).

Every population id lands in exactly one theme or explicit ``misc``;
count-in == count-out asserted (the recap FR-703/704 silent-join-drop
lesson mechanized). Themes referencing unknown ids raise — a model
inventing an FR id is a fabrication, not a rounding error.
"""

from __future__ import annotations


def enforce_coverage(themes: list[dict], population: list[str]) -> list[dict]:
    """Deterministic reconciliation of model theme claims (judged F5:
    single membership is a deliberate distortion — duplicates keep the
    FIRST occurrence)."""
    known = set(population)
    seen: set[str] = set()
    out: list[dict] = []
    for theme in themes:
        ids: list[str] = []
        for fr_id in theme.get("fr_ids") or []:
            if fr_id not in known:
                raise ValueError(
                    f"theme {theme.get('name')!r} references unknown id "
                    f"{fr_id!r} — model claims reconcile against the "
                    f"collected population, never trusted"
                )
            if fr_id in seen:
                continue  # duplicate: first occurrence won
            seen.add(fr_id)
            ids.append(fr_id)
        out.append({**theme, "fr_ids": ids})
    unassigned = [fr_id for fr_id in population if fr_id not in seen]
    if unassigned:
        out.append(
            {
                "name": "misc",
                "arc": "FRs no theme claimed — explicit, never silent.",
                "fr_ids": unassigned,
            }
        )
    total = sum(len(t["fr_ids"]) for t in out)
    if total != len(population):
        raise ValueError(
            f"coverage mismatch: {total} assigned != {len(population)} "
            f"collected — silent drop or double count"
        )
    return out


def remap_chunk_themes(merged: list[dict], chunk_themes: list[dict]) -> list[dict]:
    """Deterministic join: final theme ← merged_from chunk-theme keys ←
    fr_ids. The model never carries FR ids at the merge level."""
    by_key = {ct["key"]: ct for ct in chunk_themes}
    used: set[str] = set()
    out: list[dict] = []
    for theme in merged:
        ids: list[str] = []
        for key in theme.get("merged_from") or []:
            source = by_key.get(key)
            if source is None:
                continue  # unknown key: contributes nothing, orphans → misc
            if key in used:
                continue
            used.add(key)
            ids.extend(source.get("fr_ids") or [])
        out.append({"name": theme["name"], "arc": theme.get("arc", ""), "fr_ids": ids})
    # Chunk themes no merged theme claimed still carry their FRs —
    # their ids fall through to misc in enforce_coverage.
    return out
