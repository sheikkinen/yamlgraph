"""Structured world_state ledger for DM v2 (FR-499 Phase A).

The forward-carry ledger that threads across chapters was a free-prose ``str`` —
which let the model silently contradict an earlier chapter's facts (a clan-flip,
a phantom hand-axe, a seized staff wielded again). This module replaces it with a
**typed** ledger validated at the boundary and a deterministic formatter that
renders it back into the play/close prompts.

The shape (the canonical state the next chapter inherits):

    {
      "characters":    [{name, faction, status, location, inventory: [str]}],
      "objects":       [{name, holder, location}],
      "facts":         [str],
      "relationships": [{between: [str], type, status, tensions: [str],
                         last_interaction, recap_citations: [str]}],  # FR-513
    }

The model emits this as JSON (``parse_json`` in ``chapter_close.yaml``);
:func:`parse_world_state` validates + normalizes it at the close boundary, and the
stored value is a plain ``dict`` (JSON-serializable for ``story.json``).
:func:`format_world_state` renders it back to terse prompt text — never a raw dict
repr, never into the rendered manuscript.

Pure: no LLM, no I/O.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Character(BaseModel):
    """One principal's standing in the ledger."""

    name: str = ""
    faction: str = ""
    status: str = ""
    location: str = ""
    inventory: list[str] = Field(default_factory=list)


class WorldObject(BaseModel):
    """A story object whose holder/location later chapters must not contradict."""

    name: str = ""
    holder: str = ""
    location: str = ""


class Relationship(BaseModel):
    """An emotional / alliance fact that persists across chapter boundaries (FR-513).

    Relationships were *implicit* — derived from character proximity in the
    context window — so they reset at every chapter break (lovers re-met as
    strangers). This makes them explicit ledger state. ``recap_citations`` is the
    grounding contract: a relationship with no recap evidence is dropped at the
    boundary (:func:`parse_world_state`), never carried as a hallucination.
    """

    between: list[str] = Field(default_factory=list)
    type: str = ""
    status: str = ""
    tensions: list[str] = Field(default_factory=list)
    last_interaction: str = ""
    recap_citations: list[str] = Field(default_factory=list)
    # Bi-temporal markers (FR-515): the chapter ordinal at which this edge version
    # opened, and the ordinal at which a contradicting op closed it. ``valid_to
    # is None`` ⇒ currently valid. Integer ordinals, never strings (FR-514 J2):
    # decay (FR-517) and retrieval recency (FR-516) are arithmetic, not parsing.
    valid_from: int = 0
    valid_to: int | None = None
    # Decay clock (FR-517): the ordinal this edge was last confirmed still true
    # (set on ``add`` and every ``reaffirm``). Distinct from ``valid_from`` — that
    # records when the version opened and must not move, or the history breaks.
    last_reaffirmed: int = 0


class WorldState(BaseModel):
    """The end-of-chapter ledger the next chapter inherits (FR-499A)."""

    characters: list[Character] = Field(default_factory=list)
    objects: list[WorldObject] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


# Statuses excluded from turn context (FR-513 refinement 2): a paused or
# conclusively resolved relationship must not reinvoke stale tensions in play.
_INACTIVE_STATUSES = {"dormant", "archived"}

# An active edge not reaffirmed for more than this many chapters is demoted to
# dormant by code, not by the LLM's recollection (FR-517 §4.3; matches the FR-513
# "dormant = paused 2+ chapters" guidance).
DECAY_AFTER = 2

# Turn context carries at most this many cast-relevant relationships, ranked by
# salience (FR-516 §4.4) — a long saga must not drag every bond into every turn.
RETRIEVAL_TOPK = 6

_DELTA_OPS = {"add", "reaffirm", "update", "invalidate"}

_EMPTY: dict = {"characters": [], "objects": [], "facts": [], "relationships": []}


def _norm_token(name: object) -> str:
    """Lowercased, whitespace-collapsed name for keying and cast matching."""
    return " ".join(str(name or "").lower().split())


def _rel_key(rel: dict) -> tuple[str, ...]:
    """Edge identity = the participant set, type-independent (FR-514 J1).

    Type-independence is load-bearing: ``enmity`` and ``romantic_bond`` for the
    same pair share a key so a contradicting op reconciles onto the *same* edge
    (FR-515) rather than spawning a parallel one.
    """
    return tuple(
        sorted(_norm_token(n) for n in rel.get("between", []) if str(n).strip())
    )


def parse_world_state(raw: object) -> dict:
    """Validate a raw ledger into the typed shape, tolerant at the boundary.

    A well-formed dict is validated (missing keys default to empty); anything
    else — the legacy prose string, ``None``, junk — yields an empty typed ledger
    rather than raising mid-pipeline (normalize at the boundary; never substitute
    a plausible-but-wrong value, return the empty truth).
    """
    if not isinstance(raw, dict):
        return dict(_EMPTY)
    try:
        ledger = WorldState.model_validate(raw).model_dump()
    except Exception:
        return dict(_EMPTY)
    # Grounding gate (FR-513 refinements 1 + 4): a relationship with no recap
    # citation is ungrounded — drop it at the boundary rather than let a
    # hallucinated bond contaminate the ledger or the next chapter's turn context.
    ledger["relationships"] = [
        r
        for r in ledger["relationships"]
        if [c for c in r.get("recap_citations", []) if str(c).strip()]
        and len([n for n in r.get("between", []) if str(n).strip()]) >= 2
    ]
    return ledger


def _is_empty(ws: dict) -> bool:
    return not (
        ws.get("characters")
        or ws.get("objects")
        or ws.get("facts")
        or ws.get("relationships")
    )


def _is_active(rel: dict) -> bool:
    """A relationship belongs in turn context unless paused/resolved (FR-513)."""
    return str(rel.get("status", "")).strip().lower() not in _INACTIVE_STATUSES


def _format_relationship(rel: dict, *, show_status: bool) -> str:
    """One compact relationship line (FR-513 refinement 3): semantic, not a dict.

    ``"- Hilde and Gunnar: romantic_bond (tensions: clan_feud, public_secrecy)"`` —
    the turn prompt reads relationships as prose, never a serialized object.
    """
    names = [n for n in rel.get("between", []) if str(n).strip()]
    pair = " and ".join(names) if names else "(unknown)"
    rel_type = rel.get("type") or "connection"
    line = f"- {pair}: {rel_type}"
    if show_status and rel.get("status"):
        line += f" [{rel['status']}]"
    tensions = [t for t in rel.get("tensions", []) if str(t).strip()]
    if tensions:
        line += f" (tensions: {', '.join(tensions)})"
    if rel.get("last_interaction"):
        line += f"; last: {rel['last_interaction']}"
    return line


def format_world_state(ws: object, *, relationships: str = "all") -> str:
    """Render a structured ledger to terse prompt text; ``""`` when empty.

    Deterministic (input order preserved) so the play/close prompts read a stable
    ledger and tests can pin the text. An empty or missing ledger renders to ``""``
    so callers keep their "no prior world state" opening fallback.

    ``relationships`` selects which relationship rows reach the text (FR-513):
    ``"all"`` (default — used by chapter-close carry-forward so dormant bonds are
    preserved), ``"active"`` (only non-dormant/archived, compact — the turn
    context, refinements 2 + 3), or ``"none"``.
    """
    ledger = parse_world_state(ws)
    if _is_empty(ledger):
        return ""
    lines: list[str] = []
    if ledger["characters"]:
        lines.append("Characters:")
        for c in ledger["characters"]:
            faction = c["faction"] or "unaligned"
            status = c["status"] or "alive"
            location = c["location"] or "whereabouts unknown"
            line = f"- {c['name']} ({faction}) — {status}, at {location}"
            if c["inventory"]:
                line += f"; holds: {', '.join(c['inventory'])}"
            lines.append(line)
    if ledger["objects"]:
        lines.append("Objects:")
        for o in ledger["objects"]:
            holder = o["holder"] or "no one"
            location = o["location"] or "location unknown"
            lines.append(f"- {o['name']} — held by {holder}, at {location}")
    if ledger["facts"]:
        lines.append("Facts:")
        for fact in ledger["facts"]:
            lines.append(f"- {fact}")
    if relationships != "none":
        active_only = relationships == "active"
        # Turn context ("active") carries only currently-valid, non-paused edges:
        # an edge a contradiction has closed (FR-515 ``valid_to`` set) is history,
        # not present truth, so it must not reinvoke stale tensions in play.
        rows = [
            r
            for r in ledger["relationships"]
            if not active_only or (_is_active(r) and r.get("valid_to") is None)
        ]
        if rows:
            lines.append("Relationships:")
            for r in rows:
                lines.append(_format_relationship(r, show_status=not active_only))
    return "\n".join(lines)


# ── Delta-close: the LLM proposes operations, code applies them (FR-514) ──────
#
# The relationship lane stops being regenerated whole each chapter (which let a
# single forgetful close zero the store — 10020-BC Ch5) and becomes an
# update-delta against the inherited ledger, like every surveyed agent-memory
# system. The inherited active set is the FLOOR: zero ops carry it forward.


def _op_grounded(names: list[str], cites: list[str]) -> bool:
    """A delta op is applied only if grounded: ≥2 named parties and ≥1 recap cite.

    The FR-513 grounding gate, now enforced per-operation rather than over a
    regenerated ledger — an ungrounded op is dropped at the boundary.
    """
    return len(names) >= 2 and bool(cites)


def _new_edge(op: dict, names: list[str], cites: list[str], current_index: int) -> dict:
    """Open a fresh current edge stamped at ``current_index`` (FR-514/515/517)."""
    return {
        "between": list(names),
        "type": str(op.get("type", "")).strip(),
        "status": str(op.get("status", "")).strip() or "active",
        "tensions": [t for t in op.get("tensions", []) if str(t).strip()],
        "last_interaction": str(op.get("last_interaction", "")).strip(),
        "recap_citations": list(cites),
        "valid_from": current_index,
        "valid_to": None,
        "last_reaffirmed": current_index,
    }


def _update_edge_fields(
    edge: dict, op: dict, cites: list[str], current_index: int
) -> None:
    """Update a current edge in place (no type change) and refresh its decay clock."""
    for fld in ("type", "status", "last_interaction"):
        val = str(op.get(fld, "")).strip()
        if val:
            edge[fld] = val
    tensions = [t for t in op.get("tensions", []) if str(t).strip()]
    if tensions:
        edge["tensions"] = tensions
    merged = list(edge.get("recap_citations", []))
    for c in cites:
        if c not in merged:
            merged.append(c)
    edge["recap_citations"] = merged
    edge["last_reaffirmed"] = current_index


def apply_ledger_delta(
    inherited: object,
    operations: object,
    current_index: int,
    *,
    decay_after: int = DECAY_AFTER,
) -> dict:
    """Apply chapter-close relationship operations to the inherited ledger (FR-514).

    Pure. ``inherited`` is the previous chapter's full typed ledger (the floor);
    ``operations`` is the close LLM's list of ``add``/``reaffirm``/``update``/
    ``invalidate`` ops; ``current_index`` is the closing chapter's 0-based ordinal
    (FR-514 J3 — apply never resolves ordinals itself). Returns the full typed
    ledger with the relationship lane delta-applied; the other three lanes are
    carried from the inherited floor (the caller overlays the close's emitted
    lanes via :func:`apply_lane_floor`).

    Semantics (FR-514 J1: at most one *current* edge per participant set):

    - ``add``      open a new current edge, or fold onto the existing one.
    - ``reaffirm`` refresh the decay clock; revive a dormant edge to active.
    - ``update``   change fields in place; a *type* change reconciles bi-temporally
      (FR-515) — the old edge is closed (``valid_to`` set) and a new one opened.
    - ``invalidate`` archive the edge and close it (``valid_to`` set).

    After the ops, an active edge unrefreshed for more than ``decay_after``
    chapters is demoted to dormant by code (FR-517). An ungrounded op is dropped.
    """
    base = parse_world_state(inherited)
    rels: list[dict] = [dict(r) for r in base["relationships"]]

    def current_edge(key: tuple[str, ...]) -> dict | None:
        for r in rels:
            if _rel_key(r) == key and r.get("valid_to") is None:
                return r
        return None

    for op in operations if isinstance(operations, list) else []:
        if not isinstance(op, dict):
            continue
        kind = str(op.get("op", "")).strip().lower()
        if kind not in _DELTA_OPS:
            continue
        names = [n for n in op.get("between", []) if str(n).strip()]
        cites = [c for c in op.get("recap_citations", []) if str(c).strip()]
        if not _op_grounded(names, cites):
            continue
        key = _rel_key({"between": names})
        cur = current_edge(key)
        if kind == "add":
            if cur is None:
                rels.append(_new_edge(op, names, cites, current_index))
            else:
                _update_edge_fields(cur, op, cites, current_index)
        elif kind == "reaffirm":
            if cur is None:
                rels.append(_new_edge(op, names, cites, current_index))
            else:
                if str(cur.get("status", "")).lower() in _INACTIVE_STATUSES:
                    cur["status"] = "active"
                _update_edge_fields(cur, op, cites, current_index)
        elif kind == "update":
            new_type = str(op.get("type", "")).strip()
            if cur is None:
                rels.append(_new_edge(op, names, cites, current_index))
            elif new_type and new_type != str(cur.get("type", "")).strip():
                cur["valid_to"] = current_index  # FR-515: close, do not overwrite
                rels.append(_new_edge(op, names, cites, current_index))
            else:
                _update_edge_fields(cur, op, cites, current_index)
        elif kind == "invalidate" and cur is not None:
            cur["status"] = "archived"
            cur["valid_to"] = current_index

    for r in rels:  # FR-517 mechanical decay
        if r.get("valid_to") is None and str(r.get("status", "")).lower() == "active":
            last = int(r.get("last_reaffirmed") or r.get("valid_from") or 0)
            if current_index - last > decay_after:
                r["status"] = "dormant"

    out = dict(base)
    out["relationships"] = rels
    return out


def apply_lane_floor(emitted: object, inherited: object) -> dict:
    """Floor the non-relationship lanes: an emptied lane carries forward (FR-514 J4).

    The ``characters``/``objects``/``facts`` lanes keep full-ledger emission, but a
    missing or empty lane in the close payload must not zero established state — it
    carries the inherited lane forward unchanged. The ``relationships`` lane is the
    delta path (:func:`apply_ledger_delta`) and is set by the caller; here it is
    returned empty.
    """
    emit = parse_world_state(emitted)
    prior = parse_world_state(inherited)
    return {
        "characters": emit["characters"] or prior["characters"],
        "objects": emit["objects"] or prior["objects"],
        "facts": emit["facts"] or prior["facts"],
        "relationships": [],
    }


def rank_relationships(
    rels: object, *, cast_names: list[str], k: int = RETRIEVAL_TOPK
) -> list[dict]:
    """Top-K cast-relevant relationships for turn context, salience-ranked (FR-516).

    Hard filter: an edge must be current (``valid_to is None``), non-paused, and
    bind at least one on-stage name. Among survivors, rank by importance (tension
    count) then recency (``valid_from`` ordinal), and keep the top ``k``. Bounds
    turn context so a long saga does not drag every bond into every turn.
    """
    cast = {_norm_token(n) for n in (cast_names or []) if str(n).strip()}
    on_stage = [
        r
        for r in (rels if isinstance(rels, list) else [])
        if r.get("valid_to") is None
        and _is_active(r)
        and {_norm_token(n) for n in r.get("between", [])} & cast
    ]
    on_stage.sort(
        key=lambda r: (len(r.get("tensions", [])), int(r.get("valid_from") or 0)),
        reverse=True,
    )
    return on_stage[: max(0, k)]


def apply_merges(ledger: object, merges: object, current_index: int) -> dict:
    """Apply grounded consolidation merges to a ledger (FR-518).

    Pure. Each merge names the edges it subsumes (``merge``) and the consolidated
    edge (``into``). A merge is applied only if its result is grounded (FR-513:
    ≥2 parties, ≥1 recap cite); the merged-out sources are *closed* with
    ``valid_to`` (FR-515 history), never deleted. A merge over already-closed or
    missing sources is skipped, so the pass is a no-op on a clean ledger.
    """
    base = parse_world_state(ledger)
    rels: list[dict] = [dict(r) for r in base["relationships"]]

    def find_current(key: tuple[str, ...]) -> dict | None:
        for r in rels:
            if _rel_key(r) == key and r.get("valid_to") is None:
                return r
        return None

    for merge in merges if isinstance(merges, list) else []:
        if not isinstance(merge, dict):
            continue
        into = merge.get("into") if isinstance(merge.get("into"), dict) else {}
        names = [n for n in into.get("between", []) if str(n).strip()]
        cites = [c for c in into.get("recap_citations", []) if str(c).strip()]
        source_keys = [
            _rel_key({"between": s.get("between", [])})
            for s in merge.get("merge", [])
            if isinstance(s, dict)
        ]
        sources = [e for k in source_keys if (e := find_current(k)) is not None]
        if len(sources) < 2 or not _op_grounded(names, cites):
            continue
        for src in sources:
            src["valid_to"] = current_index
        rels.append(_new_edge(into, names, cites, current_index))

    out = dict(base)
    out["relationships"] = rels
    return out
