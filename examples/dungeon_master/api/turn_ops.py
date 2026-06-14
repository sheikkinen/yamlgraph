"""Play-loop operations for DM v2 turns (FR-477).

Pure operations on the story ``doc`` plus the single turn-graph invocation, kept
apart from the stage adapter so the structured turn side-channel (per-character
``intents``) lives in one place and ``session`` stays under the size gate.

A turn's ``recap`` is a plain ``{text, reviewed}`` entry — the same shape every
stage uses — which is what lets the generic weave/edit/accept act on a turn (J3).
``intents`` is the structured side-channel, never a stage entry.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.tree import (
    FINAL_CUT_GRAPH,
    FINAL_CUT_TURNS_GRAPH,
    STAGING_GRAPH,
    TURN_GRAPH,
    WALKTHROUGH_GRAPH,
)


def turn_record(doc: dict, n: int) -> dict:
    """The ``turns[n-1]`` record ``{n, intents, recap}`` (created if absent)."""
    turns = doc.setdefault("turns", [])
    while len(turns) < n:
        m = len(turns) + 1
        turns.append({"n": m, "intents": {}, "recap": {"text": "", "reviewed": False}})
    rec = turns[n - 1]
    rec.setdefault("intents", {})
    rec.setdefault("recap", {"text": "", "reviewed": False})
    return rec


def turn_direction(doc: dict, n: int) -> dict:
    """The director's ``direction`` side-channel for turn ``n`` (empty if absent).

    A structured ``{phase, establishing, beats_satisfied, scene_complete, steer,
    continuity}`` judgement produced alongside the turn's intents (FR-479 J4);
    the recap entry shape stays ``{text, reviewed}`` (FR-477 J3).
    """
    turns = doc.get("turns", [])
    if n < 1 or len(turns) < n:
        return {}
    return turns[n - 1].get("direction") or {}


def turn_intents(doc: dict, chars: dict, n: int) -> list[dict]:
    """The turn's intents as ordered performance cards (cast order).

    Each card is ``{name, thinking, intent, dialogue, expression}`` (FR-486): the
    private ``thinking`` and the decisive ``intent`` the arc reads, plus the
    outward performance layer — the spoken ``dialogue`` and the visible
    ``expression`` that projects the thinking. A turn played before FR-486 carries
    only the first two keys; the new keys default to ``""`` (a silent character is
    legitimate, not a defect — an additive side-channel, never a raise).
    """
    turns = doc.get("turns", [])
    if n < 1 or len(turns) < n:
        return []
    intents = turns[n - 1].get("intents", {})
    out: list[dict] = []
    for cid in chars["roster"]:
        if cid in intents:
            perf = intents[cid]
            out.append(
                {
                    "name": chars["cards"].get(cid, {}).get("name") or cid,
                    "thinking": perf.get("thinking", ""),
                    "intent": perf.get("intent", ""),
                    "dialogue": perf.get("dialogue", ""),
                    "expression": perf.get("expression", ""),
                }
            )
    return out


def prior_intents(doc: dict, n: int) -> dict:
    """Each character's intent from turn ``n-1`` (empty before turn 2, J4)."""
    turns = doc.get("turns", [])
    if n < 2 or len(turns) < n - 1:
        return {}
    prev = turns[n - 2].get("intents", {})
    return {cid: v.get("intent", "") for cid, v in prev.items()}


def running_scene(doc: dict, n: int) -> str:
    """The play context for turn ``n``: the scene plan + what has actually happened.

    The key scene is a *plan* (SUMMARY/BEATS/END describe the intended arc the
    scene drives toward, not events that have already happened); the accumulated
    recaps are the real history. Labelling them apart stops the model from
    reading the scene's ending as established fact and replaying the aftermath —
    on turn 1 nothing has happened yet, so play must begin at the START (J4).
    """
    plan = doc.get("key_scene", {}).get("text", "")
    turns = doc.get("turns", [])
    prior = [t.get("recap", {}).get("text", "") for t in turns[: n - 1]]
    prior = [p for p in prior if p.strip()][-3:]
    so_far = (
        "\n\n".join(prior)
        if prior
        else (
            "Nothing has happened yet — the scene is just beginning. Only the "
            "START state is true; none of the BEATS and not the END have occurred."
        )
    )
    return (
        "THE SCENE (the planned arc — its SUMMARY, BEATS, and END are the "
        "intended destination the scene drives toward, NOT events that have "
        "already happened):\n"
        f"{plan}\n\n"
        "WHAT HAS HAPPENED SO FAR:\n"
        f"{so_far}"
    )


async def invoke_turn(doc: dict, chars: dict, n: int, instruction: str = "") -> str:
    """Run the turn graph for turn ``n``: write its intents + direction, return its recap.

    Builds one ``{name, sheet, previous}`` bundle per reviewed character (J1),
    the bounded running scene (key scene + last-3 recaps, J4) and each
    character's prior intent, runs ``turn.yaml`` once (map → direct → recap), records
    ``turns[n].intents`` keyed by character id and the director's
    ``turns[n].direction`` side-channel (FR-479 J4), and returns the recap text.
    The stage interface stays a pure ``str -> str``; this turn path owns both
    structured side-channels (J3).
    """
    roster = [
        cid for cid in chars["roster"] if chars["cards"].get(cid, {}).get("reviewed")
    ]
    prev = prior_intents(doc, n)
    cast = [
        {
            "name": chars["cards"][cid].get("name") or cid,
            "sheet": chars["cards"][cid].get("text", ""),
            "previous": prev.get(cid, ""),
        }
        for cid in roster
    ]
    result = await get_app(TURN_GRAPH).ainvoke(
        {
            "cast": cast,
            "scene": running_scene(doc, n),
            "turn_n": str(n),
            "instruction": instruction,
            "intents": [],
            "direction": {},
            "recap": "",
        }
    )
    items = result.get("intents") or []
    record = turn_record(doc, n)
    record["intents"] = {
        cid: {
            "thinking": field(item, "thinking"),
            "intent": field(item, "intent"),
            "dialogue": field(item, "dialogue"),
            "expression": field(item, "expression"),
        }
        for cid, item in zip(roster, items, strict=False)
    }
    direction = _direction_dict(result.get("direction"))
    prior = turn_direction(doc, n - 1)
    _clamp_phase(direction, prior)
    _canonicalize_beats(direction, prior, doc.get("key_scene", {}).get("text", ""))
    _filter_continuity(
        direction,
        [c["name"] for c in cast],
        doc.get("key_scene", {}).get("text", ""),
    )
    record["direction"] = direction
    return clean_text(result.get("recap"))


_PHASE_ORDER = {"opening": 0, "rising": 1, "climax": 2, "resolved": 3}


def _clamp_phase(direction: dict, prior: dict) -> None:
    """Floor this turn's ``phase`` at the prior turn's — the arc never runs backwards.

    ``phase`` is "where the arc stands"; once a scene reaches a higher phase it
    cannot un-reach it (FR-481 B2). A model that regresses (e.g. climax → rising
    on a later beat) is clamped up to the phase already declared, deterministically,
    so the recorded arc is monotonic regardless of what the model returns. A
    forward advance is left untouched; an unknown phase string is left as-is.
    """
    prior_phase = prior.get("phase", "") if prior else ""
    cur = direction.get("phase", "")
    if (
        prior_phase in _PHASE_ORDER
        and cur in _PHASE_ORDER
        and _PHASE_ORDER[cur] < _PHASE_ORDER[prior_phase]
    ):
        direction["phase"] = prior_phase


_SECTION_RE = re.compile(r"^[A-Z][A-Z/ ]*:")
_BEAT_FLOOR = 0.6
_BEAT_MARGIN = 0.1


def parse_beats(key_scene_text: str) -> list[str]:
    """The canonical ``BEATS`` bullets from a frozen key-scene card (FR-482).

    The key scene lists ``BEATS:`` as ``- `` bullets between that label and the
    next uppercase section label (e.g. ``END:``). Returns the beat phrases in
    scene order; empty when the card has no parseable BEATS block.
    """
    beats: list[str] = []
    in_beats = False
    for line in key_scene_text.splitlines():
        stripped = line.strip()
        if _SECTION_RE.match(stripped):
            in_beats = stripped.upper().startswith("BEATS:")
            continue
        if in_beats and stripped.startswith("- "):
            beats.append(stripped[2:].strip())
    return beats


def _norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for fuzzy beat matching."""
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())


def _match_beat(phrase: str, canonical: list[str]) -> int | None:
    """Index of the canonical beat ``phrase`` satisfies, or ``None`` (FR-482 M1).

    Ranks every canonical beat by ``difflib`` ratio on normalised text and
    accepts the best **only if** it clears an absolute floor AND beats the
    runner-up by a margin (so a phrase equally close to two beats is dropped, not
    mis-assigned). A phrase that clears nothing is dropped, never invented
    (Commandment 6).
    """
    p = _norm(phrase)
    scored = sorted(
        (
            (SequenceMatcher(None, p, _norm(b)).ratio(), i)
            for i, b in enumerate(canonical)
        ),
        reverse=True,
    )
    if not scored or scored[0][0] < _BEAT_FLOOR:
        return None
    if len(scored) > 1 and scored[0][0] - scored[1][0] < _BEAT_MARGIN:
        return None
    return scored[0][1]


def _canonicalize_beats(direction: dict, prior: dict, key_scene_text: str) -> None:
    """Bind ``beats_satisfied`` to the scene's canonical BEATS, cumulatively (FR-482).

    Matches each phrase the director reported this turn onto the frozen scene's
    BEATS vocabulary, unions it with the prior turn's satisfied set, and records
    the cumulative subset **in scene order** with a ``beats_total`` count. When
    the scene has no parseable BEATS block, there is nothing to bind to: the raw
    phrases are kept (still cumulative and de-duplicated) and ``beats_total`` is 0
    so the card shows no misleading ``k / 0`` (J4).
    """
    canonical = parse_beats(key_scene_text)
    prior_beats = list((prior or {}).get("beats_satisfied") or [])
    raw = list(direction.get("beats_satisfied") or [])
    if not canonical:
        merged: list[str] = []
        for b in prior_beats + raw:
            if b not in merged:
                merged.append(b)
        direction["beats_satisfied"] = merged
        direction["beats_total"] = 0
        return
    index_of = {b: i for i, b in enumerate(canonical)}
    satisfied: set[int] = {index_of[b] for b in prior_beats if b in index_of}
    for phrase in raw:
        i = _match_beat(phrase, canonical)
        if i is not None:
            satisfied.add(i)
    direction["beats_satisfied"] = [canonical[i] for i in sorted(satisfied)]
    direction["beats_total"] = len(canonical)


_NAME_SPLIT_RE = re.compile(r"\s+[—–-]\s+")


def _parse_scene_characters(key_scene_text: str) -> list[str]:
    """The names declared in a frozen key-scene's ``CHARACTERS`` block (FR-483).

    The scene lists ``CHARACTERS:`` as ``- Name — clause`` bullets between that
    label and the next uppercase section label. Returns each bullet's name (the
    text before the dash) in scene order; empty when the card has no CHARACTERS
    block. Mirrors :func:`parse_beats`, reading names instead of beat phrases.
    """
    names: list[str] = []
    in_chars = False
    for line in key_scene_text.splitlines():
        stripped = line.strip()
        if _SECTION_RE.match(stripped):
            in_chars = stripped.upper().startswith("CHARACTERS:")
            continue
        if in_chars and stripped.startswith("- "):
            name = _NAME_SPLIT_RE.split(stripped[2:].strip(), maxsplit=1)[0].strip()
            if name:
                names.append(name)
    return names


def _filter_continuity(
    direction: dict, roster_names: list[str], key_scene_text: str
) -> None:
    """Drop continuity flags about a scene-declared non-roster actor (FR-483 B).

    A breach the DM should see is a name taking decisive action with **no
    provenance** — neither a rostered character nor an actor the frozen scene
    cast. A non-roster actor the scene's CHARACTERS block already names (a beast,
    a third party the synopsis introduced) acting at the turn is *expected*, so
    its flag is noise, not signal. Suppress flags that mention such a
    scene-declared name; keep every other flag — the filter narrows the breach
    definition, it does not silence it.

    Exact-name containment (case-insensitive, word-boundary), not fuzzy. Accepted
    residual (J4): a flag mentioning the scene actor for an unrelated legitimate
    reason is over-suppressed; acceptable in the prototype.
    """
    roster_lower = {n.lower() for n in roster_names}
    declared = [
        n
        for n in _parse_scene_characters(key_scene_text)
        if n.lower() not in roster_lower
    ]
    if not declared:
        return
    flags = direction.get("continuity") or []
    direction["continuity"] = [
        f
        for f in flags
        if not any(
            re.search(rf"\b{re.escape(n.lower())}\b", f.lower()) for n in declared
        )
    ]


def _direction_dict(raw: object) -> dict:
    """Normalise the director's output (dict or pydantic) to a typed dict (J4).

    Unlike ``field`` (which coerces to ``str``), this preserves ``scene_complete``
    as a bool and the list fields as lists, since the session and UI branch on them.
    """
    if not raw:
        return {}

    def _get(key: str, default: object) -> object:
        val = (
            raw.get(key, default)
            if isinstance(raw, dict)
            else getattr(raw, key, default)
        )
        return default if val is None else val

    return {
        "phase": str(_get("phase", "")),
        "establishing": str(_get("establishing", "")),
        "beats_satisfied": list(_get("beats_satisfied", []) or []),
        "scene_complete": bool(_get("scene_complete", False)),
        "steer": str(_get("steer", "")),
        "continuity": list(_get("continuity", []) or []),
    }


def climax_turn(doc: dict) -> int:
    """The 1-based turn index the scene turns on, derived from the phases (FR-484).

    The director's ``phase`` is monotonic (FR-481), so the first turn to reach
    ``"climax"`` is the pivotal beat. When no turn ever recorded a climax phase,
    fall back to the turn that reported ``scene_complete``; failing even that, the
    last turn. Pure code — the Final Cut hands this marker to the model rather than
    asking it to recompute what the recorded arc already knows (FR-482 law).
    """
    turns = doc.get("turns", [])
    for t in turns:
        if (t.get("direction") or {}).get("phase") == "climax":
            return int(t.get("n", turns.index(t) + 1))
    for t in turns:
        if (t.get("direction") or {}).get("scene_complete"):
            return int(t.get("n", turns.index(t) + 1))
    return int(turns[-1].get("n", len(turns))) if turns else 0


def final_cut_context(doc: dict) -> dict:
    """Assemble the WHOLE finished arc as Final Cut graph variables (FR-484).

    A pure function over the story ``doc``: the frozen scene plan, **every** turn
    recap in order (not the 3-turn window the live recap writer sees), each turn's
    director ``phase`` with the pivotal turn marked, the canonical scene BEATS,
    and a derived ``climax`` marker. This is the deterministic seam — the model is
    handed the assembled context and asked only for prose, never to recompute the
    arc's structure.
    """
    key_scene = doc.get("key_scene", {}).get("text", "")
    turns = doc.get("turns", [])
    climax_n = climax_turn(doc)
    lines: list[str] = []
    for t in turns:
        n = t.get("n")
        recap = (t.get("recap") or {}).get("text", "")
        phase = (t.get("direction") or {}).get("phase", "")
        tag = f" [{phase}]" if phase else ""
        mark = "  ← THE CLIMAX" if n == climax_n else ""
        lines.append(f"Turn {n}{tag}{mark}: {recap}")
    beats = parse_beats(key_scene)
    return {
        "key_scene": key_scene,
        "arc": "\n\n".join(lines),
        "beats": "\n".join(f"- {b}" for b in beats),
        "climax": f"Turn {climax_n}" if turns else "",
    }


async def invoke_final_cut(doc: dict, instruction: str = "", draft: str = "") -> str:
    """Compose one continuous scene from the whole arc; never touch the turns (FR-484).

    Runs ``final_cut.yaml`` once over :func:`final_cut_context` plus the current
    draft and a writer's instruction, and returns the cleaned narration. Reads the
    played turns; writes none of them — the Final Cut is a separate ``{text,
    reviewed}`` artifact, so the play-by-play accept contract is preserved.
    """
    result = await get_app(FINAL_CUT_GRAPH).ainvoke(
        {
            **final_cut_context(doc),
            "draft": draft,
            "instruction": instruction,
            "final_cut": "",
        }
    )
    return clean_text(result.get("final_cut"))


def validate_cut_turns(played_turns: list[dict], segments: list[dict]) -> list[dict]:
    """Verify a structured Final Cut maps 1:1 onto the played turns (FR-485).

    The turn-structured cut's reason to exist is that its alignment to the played
    arc is a *deterministic post-condition* — unlike FR-484's continuous blob,
    which can only be judged by eye. This pure validator enforces it: exactly one
    segment per played turn, the emitted ``n``-set equal to the played ``n``-set,
    none missing, none invented, none duplicated. It **raises** on any divergence
    — a misaligned polished play-by-play is a defect, surfaced, never silently
    padded, truncated, nor re-keyed by position (FR-485 OQ3; Commandment 6). The
    model's emitted ``n`` labels are validated, not trusted to be in order.

    Returns the segments as ``[{n, text}]`` ordered by the played turn order.
    """
    played_ns = [int(t.get("n")) for t in played_turns]
    seg_by_n: dict[int, dict] = {}
    for seg in segments:
        raw_n = seg.get("n") if isinstance(seg, dict) else getattr(seg, "n", None)
        if raw_n is None:
            raise ValueError(f"Final Cut segment has no turn number: {seg!r}")
        try:
            n = int(raw_n)
        except (TypeError, ValueError):
            raise ValueError(
                f"Final Cut segment has a non-integer turn number: {seg!r}"
            ) from None
        if n in seg_by_n:
            raise ValueError(f"Final Cut duplicated turn {n}")
        text = seg.get("text") if isinstance(seg, dict) else getattr(seg, "text", "")
        seg_by_n[n] = {"n": n, "text": str(text or "")}
    emitted, expected = set(seg_by_n), set(played_ns)
    if emitted != expected:
        missing = sorted(expected - emitted)
        invented = sorted(emitted - expected)
        raise ValueError(
            "Final Cut misaligned with the played arc: "
            f"missing turns {missing}, invented turns {invented}"
        )
    return [seg_by_n[n] for n in played_ns]


def render_cut_turns(segments: list[dict]) -> str:
    """Join validated ``{n, text}`` segments into a readable turn-structured cut.

    A derived view for the generic edit control (the structured ``segments`` carry
    the alignment guarantee; this is only the human-readable rendering).
    """
    return "\n\n".join(f"Turn {s['n']} — {s['text']}" for s in segments)


async def invoke_final_cut_turns(
    doc: dict, instruction: str = "", draft: str = ""
) -> list[dict]:
    """Compose one polished segment per played turn from the whole arc (FR-485).

    Runs ``final_cut_turns.yaml`` once over :func:`final_cut_context` plus the
    current draft and a writer's instruction, parses the structured
    ``{turns: [{n, text}]}`` output, and validates it aligns 1:1 with the played
    turns (:func:`validate_cut_turns` raises on mismatch). Reads the played turns;
    writes none — the polished track is a separate ``doc["final_cut_turns"]``
    artifact, so the play-by-play accept contract is preserved.
    """
    result = await get_app(FINAL_CUT_TURNS_GRAPH).ainvoke(
        {
            **final_cut_context(doc),
            "draft": draft,
            "instruction": instruction,
            "cut": {},
        }
    )
    raw = result.get("cut")
    if isinstance(raw, dict):
        segments = raw.get("turns") or []
    else:
        segments = getattr(raw, "turns", None) or []
    return validate_cut_turns(doc.get("turns", []), segments)


def _cut_spine(doc: dict) -> list[dict]:
    """The FR-485 turn-structured cut as ``[{n, text}]`` — the walkthrough spine.

    The walkthrough renders this cut, so it is required to be *present* (FR-487
    OQ1). Raises when the cut has never been composed — a walkthrough without its
    spine would have to invent the structural order, the forbidden path
    (Commandment 6; the FR-487 dependency made mechanical).
    """
    spine = (doc.get("final_cut_turns") or {}).get("turns") or []
    if not spine:
        raise ValueError(
            "Walkthrough requires the FR-485 final cut (turns) to be composed first"
        )
    return [{"n": int(s["n"]), "text": str(s.get("text", ""))} for s in spine]


def walkthrough_render_inputs(
    doc: dict, chars: dict, setting: str, staging_by_n: dict
) -> list[dict]:
    """Assemble one full-text render bundle per played turn (FR-487 deterministic seam).

    A pure function over already-authored structures — the FR-485 cut spine
    (``final_cut_turns``), the FR-486 performance (:func:`turn_intents`), the
    scene ``setting`` and the per-turn ``staging`` from the director-staging pass.
    Each bundle is ``{n, cut_text, setting, staging, cast}`` where ``cast`` carries
    only the *outward* performance — ``name``/``dialogue``/``expression``/``intent``.
    The private ``thinking`` is deliberately dropped: it is the one layer the page
    must never render (FR-487 OQ5), so it is removed at the assembly boundary, not
    trusted to be omitted downstream. No LLM — the renderer is handed the composed
    inputs and asked only for prose.
    """
    climax_n = climax_turn(doc)
    bundles: list[dict] = []
    for seg in _cut_spine(doc):
        n = seg["n"]
        cast = [
            {
                "name": c["name"],
                "dialogue": c["dialogue"],
                "expression": c["expression"],
                "intent": c["intent"],
            }
            for c in turn_intents(doc, chars, n)
        ]
        bundles.append(
            {
                "n": n,
                "cut_text": seg["text"],
                "setting": setting,
                "staging": staging_by_n.get(n, ""),
                "climax": n == climax_n,
                "cast": cast,
            }
        )
    return bundles


def walkthrough_staging_context(doc: dict) -> dict:
    """Staging-pass variables: the whole arc plus the rendered cut spine (FR-487).

    Reuses :func:`final_cut_context` (scene plan, played arc, beats, climax) and
    adds the rendered FR-485 cut as ``cut`` so the whole-arc director-staging pass
    sees the polished spine it is staging.
    """
    return {**final_cut_context(doc), "cut": render_cut_turns(_cut_spine(doc))}


async def invoke_walkthrough_staging(
    doc: dict, instruction: str = "", draft: str = ""
) -> tuple[str, dict]:
    """Run the whole-arc director-staging pass: scene ``setting`` + per-turn deltas.

    Returns ``(setting, staging_by_n)`` where ``staging_by_n`` maps each played
    turn number to its location/blocking delta. The staging pass is **whole-arc**
    (FR-487 OQ4): it sees the full sequence, so its per-turn deltas are the seams
    that carry cross-turn continuity between the otherwise-locally-rendered
    passages. A staging note for a turn the pass omits defaults to ``""`` at the
    render boundary (additive; the hard 1:1 gate is on the render, not staging).
    """
    result = await get_app(STAGING_GRAPH).ainvoke(
        {
            **walkthrough_staging_context(doc),
            "draft": draft,
            "instruction": instruction,
            "staging": {},
        }
    )
    raw = result.get("staging")
    if isinstance(raw, dict):
        setting = str(raw.get("setting", ""))
        deltas = raw.get("staging") or []
    else:
        setting = str(getattr(raw, "setting", ""))
        deltas = getattr(raw, "staging", None) or []
    staging_by_n: dict[int, str] = {}
    for d in deltas:
        dn = d.get("n") if isinstance(d, dict) else getattr(d, "n", None)
        dt = d.get("text") if isinstance(d, dict) else getattr(d, "text", "")
        if dn is not None:
            staging_by_n[int(dn)] = str(dt or "")
    return setting, staging_by_n


def render_walkthrough(setting: str, segments: list[dict]) -> str:
    """Join a validated walkthrough into readable full text for the edit control.

    A scene-level ``setting`` header (curtain-up) followed by one full passage per
    played turn. The structured ``segments`` carry the 1:1 alignment guarantee;
    this is only the human-readable rendering for the generic weave/edit control.
    """
    body = "\n\n".join(f"Turn {s['n']}\n{s['text']}" for s in segments)
    header = f"{setting}\n\n" if setting.strip() else ""
    return f"{header}{body}"


def _ordered_render_texts(renders: list, count: int) -> list[str]:
    """Order the map's collected render passages and unwrap them to plain strings.

    A ``map`` node collecting a ``parse_json: false`` (string) sub-result wraps
    each item as ``{"_map_index": i, "value": <text>}`` (``map_compiler``), and the
    collected list order is not guaranteed. This normalizes the boundary: sort by
    the emitted ``_map_index`` and unwrap ``value``, so the renderer's prose — not
    the reducer's bookkeeping — is what reaches the page. A bare string (no
    wrapper) is passed through; the result is truncated/padded to ``count`` so the
    1:1 alignment validator sees exactly one passage per played turn.
    """
    indexed: list[tuple[int, str]] = []
    for i, r in enumerate(renders):
        if isinstance(r, dict):
            idx = int(r.get("_map_index", i))
            val = r.get("value", "")
        else:
            idx = i
            val = r
        indexed.append((idx, clean_text(val)))
    indexed.sort(key=lambda pair: pair[0])
    return [text for _, text in indexed][:count]


async def invoke_walkthrough(
    doc: dict, chars: dict, instruction: str = "", draft: str = ""
) -> dict:
    """Render the full text of each played turn from the authored layers (FR-487).

    The convergence point of the finish arc: runs the whole-arc director-staging
    pass, assembles one render bundle per played turn from the FR-485 cut spine +
    FR-486 performance + staging (:func:`walkthrough_render_inputs`), maps the
    per-turn full-text render over them (``walkthrough.yaml``), and validates the
    result aligns 1:1 with the played turns via the **reused**
    :func:`validate_cut_turns` (no new alignment validator — alignment composes,
    since the cut spine is already 1:1 to the played arc). Returns
    ``{setting, turns: [{n, text}]}``; reads the played turns and the two cuts,
    writes none of them — the walkthrough is a separate ``doc["walkthrough"]``
    artifact (additive).
    """
    setting, staging_by_n = await invoke_walkthrough_staging(
        doc, instruction=instruction, draft=draft
    )
    bundles = walkthrough_render_inputs(doc, chars, setting, staging_by_n)
    result = await get_app(WALKTHROUGH_GRAPH).ainvoke(
        {"bundles": bundles, "renders": []}
    )
    texts = _ordered_render_texts(result.get("renders") or [], len(bundles))
    segments = [
        {"n": b["n"], "text": text} for b, text in zip(bundles, texts, strict=False)
    ]
    validated = validate_cut_turns(doc.get("turns", []), segments)
    return {"setting": setting, "turns": validated}
