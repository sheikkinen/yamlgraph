"""Chapter-open lifecycle gates and scene-cast admission for DM v2 (FR-536).

The deterministic guards that run before a chapter plays: the memory-precedence
and lifecycle seam gates (turn 1), the chapter-open onepager compiler, the
within-chapter exit filter, and the reviewed-roster cast admission. Split from
the turn play loop (:mod:`turn_ops`) so the admission contract — who may act in
a chapter and the raises that block a violation — lives in one place. Reads the
turn primitives from :mod:`turn_state`; never the play loop, so this module sits
below it without a cycle.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.lifecycle_resolver import (
    _norm_name,
    state_conflict_violations,
)
from examples.dungeon_master.api.seam_packet import (
    parse_seam_packet,
    validate_character_lifecycle,
)
from examples.dungeon_master.api.turn_state import (
    _chapter_cast_exits,
    chapter_beat_list,
)

_LOG = logging.getLogger(__name__)


class LifecycleGateError(RuntimeError):
    """Deterministic chapter-open lifecycle violation gate failure."""

    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(f"LIFECYCLE_GATE_VIOLATION: {payload}")


class ContinuityMemoryConflictError(LifecycleGateError):
    """Deterministic chapter-open memory-precedence conflict gate failure."""

    def __init__(self, payload: dict):
        self.payload = payload
        super(LifecycleGateError, self).__init__()
        RuntimeError.__init__(self, f"CONTINUITY_MEMORY_CONFLICT: {payload}")


def _opening_source_pointer(doc: dict, cid: str) -> dict:
    """Deterministic source pointer for chapter-open seam memory resolution."""
    prev_cid = chapter_nav.previous_chapter_id(doc, cid) or ""
    seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    digest = hashlib.sha256(
        json.dumps(seam, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "chapter_id": prev_cid,
        "seam_hash": digest,
        "resolved_at": datetime.now(UTC).isoformat(),
    }


def enforce_memory_precedence_gate(doc: dict, cid: str, n: int) -> None:
    """Block chapter turn-1 execution on deterministic memory source conflicts.

    Precedence logic lives in :mod:`lifecycle_resolver` (FR-534) so the gate and
    prose-side ``protected_characters`` share one ordering; the gate owns only the
    turn-1 guard, payload assembly, and the raise.
    """
    if n != 1:
        return
    if not chapter_nav.previous_chapter_id(doc, cid):
        return

    violations = state_conflict_violations(doc, cid)
    if not violations:
        return
    payload = {
        "code": "CONTINUITY_MEMORY_CONFLICT",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
        "source_pointer": _opening_source_pointer(doc, cid),
    }
    _LOG.warning("Continuity memory conflict: %s", payload)
    raise ContinuityMemoryConflictError(payload)


def compile_opening_onepager(doc: dict, cid: str) -> dict:
    """Compile deterministic chapter-open onepager from structured memory layers."""
    prev_cid = chapter_nav.previous_chapter_id(doc, cid)
    prev_card = chapter_nav.chapter_card(doc, prev_cid) if prev_cid else {}
    chapter_memory = dict(prev_card.get("chapter_memory") or {})
    seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))

    must_include = list(seam.get("must_carry_facts") or [])
    for fact in list(chapter_memory.get("irreversible_facts") or []):
        if fact not in must_include:
            must_include.append(fact)

    must_exclude = list(seam.get("opening_constraints") or [])
    for item in list(chapter_memory.get("forbidden_regressions") or []):
        if item not in must_exclude:
            must_exclude.append(item)

    # FR-560 M1 strangler-fig seam: when a validated PlotPlan is attached, union its
    # exclusion_set (presumed-dead-before-reveal characters) into must_exclude BEFORE the [:12]
    # truncation, so a late-added exclusion is never silently dropped. Additive only -- it can add
    # an exclusion the reconstruction missed, never remove a v2 constraint -- and byte-for-byte
    # unchanged when no plan is attached. cid -> integer ordinal via _chapter_index (J3a); M1 is
    # scoped to id == display_name, so the bare character id string is unioned in (J3b).
    plan = chapter_nav.attached_plot_plan(doc)
    if plan is not None:
        from examples.dungeon_master.api.plot.project import exclusion_set

        for char_id in sorted(exclusion_set(plan, _chapter_index(doc, cid))):
            if char_id not in must_exclude:
                must_exclude.append(char_id)

    active_cast_constraints: list[str] = []
    for item in list(seam.get("character_lifecycle") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        state = str(item.get("existence_state") or "").strip()
        visibility = str(item.get("visibility_mode") or "").strip()
        allowed = item.get("allowed_reappearance_from_chapter")
        if not name:
            continue
        extra = (
            f", allowed_reappearance_from_chapter={allowed}"
            if isinstance(allowed, int)
            else ""
        )
        active_cast_constraints.append(
            f"{name}: existence_state={state}, visibility_mode={visibility}{extra}"
        )

    checks = [
        f"source_pointer.chapter_id={_opening_source_pointer(doc, cid).get('chapter_id')}",
        "respect must_exclude constraints",
    ]
    return {
        "opening_truths": must_include[:12],
        "must_include": must_include[:12],
        "must_exclude": must_exclude[:12],
        "active_cast_constraints": active_cast_constraints[:12],
        "continuity_checks": checks,
    }


def format_opening_onepager(onepager: dict) -> str:
    """Render opening onepager to deterministic prompt text."""
    lines: list[str] = ["OPENING ONEPAGER CONTRACT:"]
    labels = (
        ("opening_truths", "Opening Truths"),
        ("must_include", "Must Include"),
        ("must_exclude", "Must Exclude"),
        ("active_cast_constraints", "Active Cast Constraints"),
        ("continuity_checks", "Continuity Checks"),
    )
    wrote = False
    for key, label in labels:
        values = list(onepager.get(key) or [])
        if not values:
            continue
        wrote = True
        lines.append(f"{label}:")
        lines.extend(f"- {v}" for v in values)
    return "\n".join(lines) if wrote else ""


def _chapter_index(doc: dict, cid: str) -> int:
    """Resolve chapter id to 1-based chapter index for lifecycle gates."""
    order = doc.get("chapters", {}).get("order", [])
    if cid in order:
        return order.index(cid) + 1
    if str(cid).isdigit():
        n = int(cid)
        return n if n >= 1 else 1
    return 1


def enforce_lifecycle_gate(doc: dict, cid: str, n: int, cast: list[dict]) -> None:
    """Block chapter turn-1 execution when lifecycle seam constraints are violated."""
    if n != 1:
        return
    packet = chapter_nav.inherited_seam_packet(doc, cid)
    active_cast_names = [str(c.get("name") or "").strip() for c in cast]
    violations = validate_character_lifecycle(
        packet,
        chapter_id=_chapter_index(doc, cid),
        active_cast_names=active_cast_names,
    )
    if not violations:
        return

    payload = {
        "code": "LIFECYCLE_GATE_VIOLATION",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
    }
    _LOG.warning("Lifecycle gate violation: %s", payload)
    raise LifecycleGateError(payload)


def filter_roster_for_lifecycle(
    doc: dict, chars: dict, cid: str, n: int, roster: list[str]
) -> list[str]:
    """Apply deterministic chapter-open lifecycle filtering to reviewed roster ids.

    Two layers, both source-side leak reductions (the hard lifecycle gate remains):

    - **Within-chapter exits (FR-521 S2):** drop any roster member the director has
      benched on an earlier turn of *this* chapter (its structured ``cast_exits``).
      The witnessed fix — a swept-away actor kept full agency because an advisory
      in the scene was ignored; only removing it from the cast stops the break.
      Never empties the cast (a chapter with everyone gone closes on its turn cap).
    - **Chapter-open seam gate:** at turn 1, admission uses the previous chapter's
      committed seam packet as lifecycle authority.
    """
    roster = _drop_within_chapter_exits(doc, chars, cid, n, roster)
    if n != 1:
        return roster

    packet = chapter_nav.inherited_seam_packet(doc, cid)
    chapter_idx = _chapter_index(doc, cid)
    names_by_id = {
        char_id: str(chars["cards"].get(char_id, {}).get("name") or char_id).strip()
        for char_id in roster
    }
    candidate_names = [name for name in names_by_id.values() if name]
    violations = validate_character_lifecycle(
        packet,
        chapter_id=chapter_idx,
        active_cast_names=candidate_names,
    )
    if not violations:
        return roster

    blocked = {_norm_name(v.get("name")) for v in violations}
    filtered = [
        char_id
        for char_id in roster
        if _norm_name(names_by_id.get(char_id)) not in blocked
    ]
    if filtered:
        return filtered

    payload = {
        "code": "LIFECYCLE_GATE_VIOLATION",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
    }
    _LOG.warning("Lifecycle gate violation: %s", payload)
    raise LifecycleGateError(payload)


def _drop_within_chapter_exits(
    doc: dict, chars: dict, cid: str, n: int, roster: list[str]
) -> list[str]:
    """Drop roster ids the director benched earlier this chapter (FR-521 S2).

    Reads the accumulated ``cast_exits`` for chapter ``cid`` before turn ``n`` and
    removes any roster id whose display name matches (case-insensitive). Guards
    against handing the turn an empty cast: if every member has exited, the
    unfiltered roster is kept (the chapter's turn cap closes it instead).
    """
    exits = {_norm_name(name) for name in _chapter_cast_exits(doc, cid, n)}
    if not exits:
        return roster
    filtered = [
        char_id
        for char_id in roster
        if _norm_name(str(chars["cards"].get(char_id, {}).get("name") or char_id))
        not in exits
    ]
    return filtered or roster


_NAME_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _name_tokens(text: str) -> list[str]:
    """Lowercased alphanumeric word tokens of ``text`` (for word-bounded matching)."""
    return _NAME_TOKEN_RE.findall(str(text or "").lower())


def _contains_token_run(haystack: list[str], needle: list[str]) -> bool:
    """True when ``needle`` appears as a contiguous run of tokens in ``haystack``.

    Word-bounded so a roster name is matched only as whole words (``Ron`` does not
    match inside ``around``); multi-word names match an exact contiguous run.
    """
    if not needle or len(needle) > len(haystack):
        return False
    span = len(needle)
    return any(
        haystack[i : i + span] == needle for i in range(len(haystack) - span + 1)
    )


def resolve_chapter_cast(doc: dict, cid: str) -> set[str]:
    """The chapter's focal cast: authored ``cast`` ∪ roster names in its beats (FR-537).

    The single source of "who is in this chapter" — a SCOPE narrowing distinct from
    the lifecycle STATUS gates (a present, alive, reviewed character can still be
    off-stage for a chapter). Two normalized inputs, unioned:

    - **authored cast:** the chapter card's ``cast`` field (focal principals the
      outline named), restricted to the roster — a defensive second guard over the
      ``expand_chapters`` boundary normalization (``the_one_law``).
    - **beats-floor:** every roster character word-named in the chapter's authored
      ``beats`` (``turn_state.chapter_beat_list``). Beats are the load-bearing
      contract; a character the chapter must portray is in its cast by construction.

    Returns normalized (lowercased/whitespace-collapsed) names. Empty when the
    chapter declares no cast and no roster name appears in its beats — the callers
    then fall back to the full reviewed roster (this is an additive feature, never a
    silent narrowing of a cast-less story).
    """
    chars = dict(doc.get("characters") or {})
    cards = dict(chars.get("cards") or {})
    roster_names = [
        str(dict(cards.get(char_id) or {}).get("name") or char_id).strip()
        for char_id in (chars.get("roster") or [])
    ]
    roster_names = [name for name in roster_names if name]
    roster_norm = {_norm_name(name) for name in roster_names}

    card = chapter_nav.chapter_card(doc, cid)
    authored = {_norm_name(n) for n in (card.get("cast") or []) if _norm_name(n)}
    authored &= roster_norm

    beat_token_runs = [_name_tokens(beat) for beat in chapter_beat_list(doc, cid)]
    floor = {
        _norm_name(name)
        for name in roster_names
        if any(_contains_token_run(run, _name_tokens(name)) for run in beat_token_runs)
    }
    return authored | floor


def _scope_names_to_chapter_cast(doc: dict, cid: str, names: list[str]) -> list[str]:
    """Narrow display ``names`` to the chapter's focal cast, in input order (FR-537).

    Returns ``names`` unchanged when the chapter declares no resolvable cast, or when
    the intersection would empty the list (never hand a chapter an empty cast — the
    per-chapter turn cap closes a degenerate chapter, matching the lifecycle filters'
    posture). The single narrowing applied at the prose-control site.
    """
    cast = resolve_chapter_cast(doc, cid)
    if not cast:
        return names
    scoped = [name for name in names if _norm_name(name) in cast]
    return scoped or names


def scope_roster_to_chapter_cast(
    doc: dict, chars: dict, cid: str, roster: list[str]
) -> list[str]:
    """Narrow reviewed roster ids to the chapter's focal cast, in roster order (FR-537).

    The id-shape twin of :func:`_scope_names_to_chapter_cast` for the per-turn intents
    roster built inline in :func:`turn_ops.invoke_turn` (the measured defect: that path
    never resolved the chapter cast, so off-chapter characters were animated every
    turn). Returns ``roster`` unchanged when the chapter has no resolvable cast or when
    the intersection would empty it (same empty-cast fallback as the prose-control
    site, single-sourced through :func:`resolve_chapter_cast`).
    """
    cast = resolve_chapter_cast(doc, cid)
    if not cast:
        return roster
    cards = dict(chars.get("cards") or {})
    scoped = [
        char_id
        for char_id in roster
        if _norm_name(str(dict(cards.get(char_id) or {}).get("name") or char_id))
        in cast
    ]
    return scoped or roster


def build_allowed_scene_cast(doc: dict, cid: str) -> list[str]:
    """Build deterministic allowed cast names for chapter-close prose control.

    Source-of-truth contract:
    1) iterate ``characters.roster`` in roster order,
    2) keep reviewed cards only,
    3) apply lifecycle exclusions against inherited seam packet for chapter-open,
    4) normalize names by lowercased/whitespace-collapsed matching keys.

    Returned values are display names in stable roster order.
    """
    chars = dict(doc.get("characters") or {})
    cards = dict(chars.get("cards") or {})
    roster = list(chars.get("roster") or [])

    reviewed_ids = [
        char_id
        for char_id in roster
        if bool(dict(cards.get(char_id) or {}).get("reviewed"))
    ]
    if not reviewed_ids:
        return []

    name_by_id = {
        char_id: str(dict(cards.get(char_id) or {}).get("name") or char_id).strip()
        for char_id in reviewed_ids
    }
    candidate_names = [name for name in name_by_id.values() if name]
    if not candidate_names:
        return []

    violations = validate_character_lifecycle(
        chapter_nav.inherited_seam_packet(doc, cid),
        chapter_id=_chapter_index(doc, cid),
        active_cast_names=candidate_names,
    )
    blocked = {_norm_name(v.get("name")) for v in violations}
    out: list[str] = []
    seen: set[str] = set()
    for char_id in reviewed_ids:
        name = name_by_id.get(char_id, "")
        if not name:
            continue
        key = _norm_name(name)
        if key in blocked or key in seen:
            continue
        seen.add(key)
        out.append(name)
    return _scope_names_to_chapter_cast(doc, cid, out)
