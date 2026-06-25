"""FR-570 — Plot Modeller L4 spike: validator + corpus loaders.

The classify LLM node writes raw YAML *text* to ``kinds_raw`` (a non-JSON LLM
node returns the raw response string — ``llm_nodes.py``). ``validate_kinds``
parses that text, checks it, and — only on success — writes the parsed list to
``kinds``. On failure it writes **only** ``validation``, leaving ``kinds``
absent so a later read never sees a raw string where a list is expected (J1).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from schema.kinds import FunctionKind

# The 17-kind Propp-derived alphabet — derived from the schema enum (FR-571 AC#7).
VALID_KINDS = {k.value for k in FunctionKind}


def _strip_code_fences(raw: str) -> str:
    """Strip a leading/trailing Markdown code fence from an LLM YAML response.

    Boundary normalization: at temp>0 the model sporadically wraps its YAML in
    a ```` ```yaml ... ``` ```` block. The raw backtick crashes
    ``yaml.safe_load`` -> validator retry -> loop limit -> 0 beats. Normalize
    here, where the external LLM text enters, not downstream.
    """
    text = raw.strip()
    if not text.startswith("```"):
        return raw
    lines = text.splitlines()
    # Drop the opening fence line (``` or ```yaml).
    lines = lines[1:]
    # Drop the closing fence line if present.
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)


def validate_kinds(state: dict) -> dict:
    """Parse and validate the classify node's raw YAML output (J1).

    Reads ``kinds_raw`` (raw text). On success writes the parsed list to
    ``kinds`` plus ``validation``. On failure writes **only** ``validation``,
    leaving ``kinds`` absent.
    """
    raw = state.get("kinds_raw", "")
    try:
        items = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    # yaml.safe_load("") returns None; a scalar is also not a list (J1 crash guard).
    if not isinstance(items, list):
        return {"validation": {"ok": False, "flaws": ["expected a YAML list of items"]}}

    flaws: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            flaws.append(f"non-mapping item: {item!r}")
            continue
        if item.get("kind") not in VALID_KINDS:
            flaws.append(f"{item.get('id', '?')}: unknown kind '{item.get('kind')}'")
        if not item.get("subject"):
            flaws.append(f"{item.get('id', '?')}: missing subject")

    expected = {g["id"] for g in state.get("glosses", [])}
    got = {item.get("id") for item in items if isinstance(item, dict)}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(str(m) for m in missing))}")

    if flaws:
        # J1: do NOT write `kinds` on failure — leave it absent.
        return {"validation": {"ok": False, "flaws": flaws}}

    return {
        "kinds": items,
        "validation": {"ok": True, "flaws": []},
    }


def validate_agents(state: dict) -> dict:
    """Parse and validate the extract_agents node's raw YAML output (J1).

    Reads ``agents_raw`` (raw text). On success writes ``agents``,
    ``initial_world``, ``initial_belief``, and ``validation``. On failure
    writes **only** ``validation``, leaving the others absent.
    """
    raw = state.get("agents_raw", "")
    try:
        data = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(data, dict):
        return {
            "validation": {
                "ok": False,
                "flaws": [
                    "expected a YAML mapping with agents/initial_world/initial_belief"
                ],
            }
        }

    flaws: list[str] = []

    # --- agents ---
    agents_list = data.get("agents")
    if not isinstance(agents_list, list) or not agents_list:
        flaws.append("agents: expected non-empty list of character names")
    elif not all(isinstance(a, str) for a in agents_list):
        flaws.append("agents: all items must be strings")

    agents_set = set(agents_list) if isinstance(agents_list, list) else set()

    # --- initial_world ---
    from schema.predicates import Belief, Fluent

    world = data.get("initial_world", [])
    if not isinstance(world, list):
        flaws.append("initial_world: expected list")
        world = []
    else:
        for i, w in enumerate(world):
            try:
                Fluent.model_validate(w)
            except Exception as e:
                flaws.append(f"initial_world[{i}]: invalid fluent — {e}")

    # --- initial_belief ---
    belief = data.get("initial_belief", [])
    if not isinstance(belief, list):
        flaws.append("initial_belief: expected list")
        belief = []
    else:
        for i, b in enumerate(belief):
            try:
                Belief.model_validate(b)
            except Exception as e:
                flaws.append(f"initial_belief[{i}]: invalid belief — {e}")

    # --- referential checks (only if agents_list is valid) ---
    if (
        isinstance(agents_list, list)
        and agents_list
        and all(isinstance(a, str) for a in agents_list)
    ):
        # Agents referenced in alive predicates
        alive_agents: set[str] = set()
        for w in world:
            if isinstance(w, dict) and w.get("pred") == "alive":
                args = w.get("args", [])
                if args:
                    alive_agents.add(args[0])

        # Every alive predicate's agent must be in agents list
        for agent in alive_agents - agents_set:
            flaws.append(f"referenced in initial_world but not in agents list: {agent}")

        # Every agent must have at least one alive predicate
        for agent in sorted(agents_set - alive_agents):
            flaws.append(f"{agent}: missing alive predicate in initial_world")

        # Belief observers must be in agents list
        for b in belief:
            if isinstance(b, dict):
                obs = b.get("observer")
                if obs and obs not in agents_set:
                    flaws.append(f"initial_belief observer '{obs}' not in agents list")

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    return {
        "agents": agents_list,
        "initial_world": world,
        "initial_belief": belief,
        "validation": {"ok": True, "flaws": []},
    }


VALID_PREDS = {"alive", "at", "holds", "rel", "faction"}


def validate_goals(state: dict) -> dict:
    """Parse and validate the extract_goals node's raw YAML output (J1).

    Reads ``goals_raw`` (raw text) and ``agents`` (list of agent names).
    On success writes ``goals`` + ``validation``. On failure writes only
    ``validation``.
    """
    raw = state.get("goals_raw", "")
    try:
        data = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(data, list):
        return {
            "validation": {
                "ok": False,
                "flaws": ["expected a YAML list of goal fluents"],
            }
        }

    if not data:
        return {
            "validation": {
                "ok": False,
                "flaws": ["goals list must have at least one goal"],
            }
        }

    from schema.predicates import Fluent

    agents_list = state.get("agents", [])
    agents_set = (
        {a.lower() for a in agents_list} if isinstance(agents_list, list) else set()
    )

    flaws: list[str] = []
    seen: set[str] = set()

    for i, item in enumerate(data):
        # Validate as Fluent
        try:
            Fluent.model_validate(item)
        except Exception as e:
            flaws.append(f"goals[{i}]: invalid fluent — {e}")
            continue

        if not isinstance(item, dict):
            continue

        # Check predicate is in vocabulary
        pred = item.get("pred", "")
        if pred not in VALID_PREDS:
            flaws.append(
                f"goals[{i}]: unknown predicate '{pred}' (allowed: {', '.join(sorted(VALID_PREDS))})"
            )

        # Check agent references
        args = item.get("args", [])
        for arg in args:
            # Only check args that look like agent names (not objects/locations)
            # For alive pred, the arg is always an agent
            if pred == "alive" and str(arg).lower() not in agents_set:
                flaws.append(f"goals[{i}]: agent '{arg}' not in agents list")
            elif pred in ("rel", "faction") and str(args[0]).lower() not in agents_set:
                flaws.append(f"goals[{i}]: agent '{args[0]}' not in agents list")

        # Check duplicates (same pred+args+value)
        key = f"{pred}|{'|'.join(str(a) for a in args)}|{item.get('value', True)}"
        if key in seen:
            flaws.append(
                f"goals[{i}]: duplicate goal {pred}({', '.join(str(a) for a in args)})"
            )
        seen.add(key)

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    return {
        "goals": data,
        "validation": {"ok": True, "flaws": []},
    }


def validate_glosses(state: dict) -> dict:
    """Parse and validate the extract_glosses node's raw YAML output (J1).

    Reads ``glosses_raw`` (raw text). On success writes ``glosses`` +
    ``validation``. On failure writes only ``validation``.
    """
    import re

    raw = state.get("glosses_raw", "")
    try:
        data = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(data, list):
        return {
            "validation": {
                "ok": False,
                "flaws": ["expected a YAML list of beat objects"],
            }
        }

    flaws: list[str] = []

    # Count bounds
    if len(data) < 5:
        flaws.append(f"too few beats ({len(data)}): at least 5 expected")
    if len(data) > 20:
        flaws.append(f"too many beats ({len(data)}): at most 20 expected")

    prev_chapter = 0
    expected_idx = 1
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            flaws.append(f"beats[{i}]: expected a mapping, got {type(item).__name__}")
            continue

        # Required keys
        beat_id = item.get("id")
        gloss = item.get("gloss")
        chapter = item.get("chapter")

        if not beat_id:
            flaws.append(f"beats[{i}]: missing 'id'")
        if not gloss:
            flaws.append(f"beats[{i}]: missing 'gloss'")
        if chapter is None:
            flaws.append(f"beats[{i}]: missing 'chapter'")

        # Sequential IDs: F1, F2, F3, ...
        if beat_id:
            m = re.match(r"^F(\d+[a-z]?)$", str(beat_id))
            if m:
                idx_str = m.group(1)
                # Handle sub-beats like F2b — they don't break sequence
                if idx_str.isdigit():
                    idx = int(idx_str)
                    if idx != expected_idx:
                        flaws.append(
                            f"beats[{i}]: non-sequential id '{beat_id}' (expected F{expected_idx})"
                        )
                    expected_idx = idx + 1

        # Gloss length
        if isinstance(gloss, str):
            word_count = len(gloss.split())
            if word_count < 10:
                flaws.append(
                    f"beats[{i}] ({beat_id}): gloss too short ({word_count} words, min 10)"
                )

        # Chapters: non-decreasing
        if isinstance(chapter, int):
            if chapter < prev_chapter:
                flaws.append(
                    f"beats[{i}] ({beat_id}): chapter {chapter} < previous {prev_chapter} (must be non-decreasing)"
                )
            prev_chapter = chapter

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    return {
        "glosses": data,
        "validation": {"ok": True, "flaws": []},
    }


def load_glosses(ground_truth_path: str | Path) -> list[dict]:
    """Extract glosses from a ground-truth plot, stripping kind/subject labels.

    Mode 1 (isolate L4): the model receives only ``id``, ``gloss``, ``chapter``
    and must predict ``kind`` and ``subject`` itself.
    """
    data = yaml.safe_load(Path(ground_truth_path).read_text(encoding="utf-8"))
    glosses: list[dict] = []
    for fn in data.get("functions", []):
        glosses.append(
            {
                "id": fn["id"],
                "gloss": " ".join(str(fn.get("gloss", "")).split()),
                "chapter": fn.get("chapter"),
            }
        )
    return glosses


def load_synopsis(synopsis_path: str | Path) -> str:
    """Read a prose synopsis fixture as plain text."""
    return Path(synopsis_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# FR-576 L5 — assign world/belief pre/eff to classified beats
# ---------------------------------------------------------------------------

_PRE_EFF_SLICES = ("pre_world", "eff_world", "pre_belief", "eff_belief")


def validate_pre_eff(state: dict) -> dict:
    """Parse and validate the assign_pre_eff node's raw YAML output (J1).

    Reads ``pre_eff_raw`` (raw text), ``glosses`` (classified beats, for id
    coverage) and ``agents`` (for the membership check). On success writes
    ``pre_eff`` + ``validation``; on failure writes **only** ``validation``,
    leaving ``pre_eff`` absent (J1).

    Deliberately enforces **no kind->effect semantic rule** (J:C2): a ``death``
    beat need not produce ``alive=false`` — the corpus models one death as a
    relationship change. Coherence is the evaluator's job, not the validator's.
    """
    from schema.predicates import Belief, Fluent

    raw = state.get("pre_eff_raw", "")
    try:
        items = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(items, list):
        return {
            "validation": {
                "ok": False,
                "flaws": ["expected a YAML list of per-beat pre/eff objects"],
            }
        }

    agents_set = {_norm_name(a) for a in state.get("agents", []) if isinstance(a, str)}

    flaws: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            flaws.append(f"non-mapping item: {item!r}")
            continue
        bid = item.get("id", "?")
        for slot in ("pre_world", "eff_world"):
            for i, w in enumerate(item.get(slot) or []):
                try:
                    Fluent.model_validate(w)
                except Exception as e:
                    flaws.append(f"{bid}.{slot}[{i}]: invalid fluent — {e}")
                    continue
                if w.get("pred") not in VALID_PREDS:
                    flaws.append(
                        f"{bid}.{slot}[{i}]: unknown predicate '{w.get('pred')}'"
                    )
                _check_agent_args(bid, slot, i, w, agents_set, flaws)
        for slot in ("pre_belief", "eff_belief"):
            for i, b in enumerate(item.get(slot) or []):
                try:
                    Belief.model_validate(b)
                except Exception as e:
                    flaws.append(f"{bid}.{slot}[{i}]: invalid belief — {e}")
                    continue
                obs = b.get("observer")
                if agents_set and _norm_name(obs) not in agents_set:
                    flaws.append(
                        f"{bid}.{slot}[{i}]: observer '{obs}' not in agents list"
                    )

    expected = {g["id"] for g in state.get("glosses", [])}
    got = {item.get("id") for item in items if isinstance(item, dict)}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(str(m) for m in missing))}")
    orphans = got - expected
    if orphans:
        flaws.append(f"orphan ids: {', '.join(sorted(str(o) for o in orphans))}")

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    return {"pre_eff": items, "validation": {"ok": True, "flaws": []}}


def _norm_name(name: object) -> str:
    """Normalise a character name for membership comparison."""
    return " ".join(str(name or "").split()).strip().lower()


def _check_agent_args(
    bid: str,
    slot: str,
    i: int,
    fluent: dict,
    agents_set: set[str],
    flaws: list[str],
) -> None:
    """Check that agent-position args reference known agents (tolerant).

    Only args known to be characters are checked: ``alive`` takes a single
    agent; ``rel``/``faction`` take an agent in position 0. ``at``/``holds``
    args can be objects/locations and are not membership-checked (mirrors the
    L2 ``validate_goals`` policy).
    """
    if not agents_set:
        return
    pred = fluent.get("pred")
    args = fluent.get("args", []) or []
    # For alive/rel/faction the character is in arg position 0; at/holds args
    # may be objects/locations and are not membership-checked (mirrors L2).
    if (
        pred in ("alive", "rel", "faction")
        and args
        and _norm_name(args[0]) not in agents_set
    ):
        flaws.append(f"{bid}.{slot}[{i}]: agent '{args[0]}' not in agents list")


def load_glosses_with_kinds(ground_truth_path: str | Path) -> list[dict]:
    """Load classified beats (id, gloss, chapter, kind, subject) for L5 input.

    Mode 1 (isolate L5): the model receives the ground-truth glosses *and*
    kinds, and must assign only the pre/eff predicates — isolating L5 accuracy
    from L3/L4 error.
    """
    data = yaml.safe_load(Path(ground_truth_path).read_text(encoding="utf-8"))
    out: list[dict] = []
    for fn in data.get("functions", []):
        out.append(
            {
                "id": fn["id"],
                "gloss": " ".join(str(fn.get("gloss", "")).split()),
                "chapter": fn.get("chapter"),
                "kind": fn.get("kind"),
                "subject": fn.get("subject"),
            }
        )
    return out


# ---------------------------------------------------------------------------
# FR-587 L5 — snapshot-then-diff: derive per-beat pre/eff from world snapshots
# ---------------------------------------------------------------------------


def _fluent_key(fluent: dict) -> tuple:
    """Identity of a fluent: predicate + normalized arg tuple (value excluded)."""
    args = tuple(_norm_name(a) for a in (fluent.get("args") or []))
    return (fluent.get("pred"), args)


def _clean_fluent(fluent: dict) -> dict:
    """Strip a typed fluent down to the three scored fields."""
    return {
        "pred": fluent.get("pred"),
        "args": list(fluent.get("args") or []),
        "value": fluent.get("value"),
    }


def _entity_of(fluent: dict) -> str | None:
    """First argument (the moving/owning entity) of a fluent, normalized."""
    args = fluent.get("args") or []
    return _norm_name(args[0]) if args else None


def _collapse_at_runs(raw: list[dict]) -> None:
    """Collapse intra-chapter `at`-arrival runs to the run's terminus (in place).

    When the same entity arrives somewhere on two consecutive same-chapter beats,
    the earlier arrival is an intermediate travel waypoint the ground truth does
    not score — drop it, keeping only the later (terminus) arrival.
    """
    for i in range(1, len(raw)):
        if raw[i]["chapter"] != raw[i - 1]["chapter"]:
            continue
        cur_arrivals = {
            _entity_of(f)
            for f in raw[i]["eff"]
            if f.get("pred") == "at" and f.get("value") is True
        }
        if not cur_arrivals:
            continue
        prev = raw[i - 1]
        prev["eff"] = [
            f
            for f in prev["eff"]
            if not (
                f.get("pred") == "at"
                and f.get("value") is True
                and _entity_of(f) in cur_arrivals
            )
        ]


def _suppress_late_departures(raw: list[dict]) -> None:
    """Keep only each entity's FIRST `at`-departure; drop later ones (in place).

    Ground truth scores the departure (``at(origin)=false``) only for an entity's
    first relocation from its established origin; every later relocation is
    arrival-only. Later departures — and the precondition they reference — are the
    journey-waypoint flood, so they are removed.
    """
    seen: set[str | None] = set()
    for r in raw:
        kept: list[dict] = []
        dropped_keys: set[tuple] = set()
        for f in r["eff"]:
            if f.get("pred") == "at" and f.get("value") is False:
                entity = _entity_of(f)
                if entity in seen:
                    dropped_keys.add(_fluent_key(f))
                    continue
                seen.add(entity)
            kept.append(f)
        r["eff"] = kept
        if dropped_keys:
            r["pre"] = [p for p in r["pre"] if _fluent_key(p) not in dropped_keys]


def diff_snapshots(snapshots: list[dict]) -> list[dict]:
    """Derive per-beat pre/eff world slices by diffing ordered state snapshots.

    FR-587 Stage 2 (deterministic, no LLM). Each input snapshot is
    ``{id, chapter, world: [typed fluent, …]}`` — the COMPLETE world state at a
    moment. The first snapshot (``F0``) is the opening scene used purely as the
    baseline and is not emitted; the rest (``F1…Fn``) are diffed against their
    predecessor:

    - A fluent that **appears** or **changes value** is an effect (new value); the
      prior fluent it acts on becomes a precondition.
    - A tracked boolean fact that **disappears** is an effect at value ``false``.
    - ``at`` is single-valued per character, so every move yields a departure
      (``at(old)=false``) + arrival (``at(new)=true``) pair. Ground truth scores
      only *salient* relocation, so two deterministic collapses run afterwards:
      intra-chapter arrival-run collapse, then first-departure-only. These are the
      precision rule the model could not apply; both are validated against the GT
      ``at … value: false`` departures (FR-587 correction #2).

    Belief slices stay empty (FR-585: belief is not the L5 wound).
    """
    raw: list[dict] = []
    prev: dict[tuple, dict] = {}
    seeded = False
    for snap in snapshots:
        if not isinstance(snap, dict):
            continue
        cur: dict[tuple, dict] = {}
        for f in snap.get("world") or []:
            if isinstance(f, dict) and f.get("pred"):
                cur[_fluent_key(f)] = f
        if not seeded:
            # First snapshot (F0) anchors the baseline; emit nothing for it.
            prev = cur
            seeded = True
            continue
        eff: list[dict] = []
        pre: list[dict] = []
        for key, f in cur.items():
            pf = prev.get(key)
            if pf is None:
                eff.append(_clean_fluent(f))
            elif pf.get("value") != f.get("value"):
                eff.append(_clean_fluent(f))
                pre.append(_clean_fluent(pf))
        for key, pf in prev.items():
            if key in cur:
                continue
            if pf.get("pred") == "at":
                eff.append(
                    {"pred": "at", "args": list(pf.get("args") or []), "value": False}
                )
                pre.append(_clean_fluent(pf))
            elif pf.get("value") is True:
                eff.append(
                    {
                        "pred": pf.get("pred"),
                        "args": list(pf.get("args") or []),
                        "value": False,
                    }
                )
                pre.append(_clean_fluent(pf))
        raw.append(
            {
                "id": snap.get("id"),
                "chapter": snap.get("chapter"),
                "eff": eff,
                "pre": pre,
            }
        )
        prev = cur

    _collapse_at_runs(raw)
    _suppress_late_departures(raw)

    return [
        {
            "id": r["id"],
            "pre_world": r["pre"],
            "eff_world": r["eff"],
            "pre_belief": [],
            "eff_belief": [],
        }
        for r in raw
    ]


# ---------------------------------------------------------------------------
# FR-590/591 L5 — multi-perspective: per-agent viewpoint + encoding -> per-beat L5
# ---------------------------------------------------------------------------


def _dedup_fluents(fluents: list[dict]) -> list[dict]:
    """Drop fluents sharing a ``_fluent_key`` (pred + normalized args), first wins.

    Symmetric facts (``rel``/``faction``) are reported from BOTH participants'
    perspectives; collapsing on the value-free key keeps one copy without any
    salience judgment (FR-590 combine is deterministic, no LLM).
    """
    seen: set[tuple] = set()
    out: list[dict] = []
    for f in fluents:
        if not isinstance(f, dict) or not f.get("pred"):
            continue
        key = _fluent_key(f)
        if key in seen:
            continue
        seen.add(key)
        out.append(_clean_fluent(f))
    return out


def _parse_beats(raw: str) -> list[dict]:
    """Parse an ``encode_perspective`` YAML payload into a list of beat dicts.

    Tolerant by contract (FR-591): code fences are stripped, a parse error or a
    non-list payload yields ``[]`` (the agent contributes nothing rather than
    crashing the whole conversion). Moved from the retired ``spike_perspective.py``
    so the graph's ``parse_perspective`` tool can depend on it.
    """
    text = _strip_code_fences(str(raw))
    try:
        beats = yaml.safe_load(text)
    except yaml.YAMLError:
        return []
    return [b for b in beats if isinstance(b, dict)] if isinstance(beats, list) else []


def parse_perspective(state: dict) -> dict:
    """Assemble one agent's perspective record for the FR-591 inner subgraph.

    Reads ``agent`` (the character), ``viewpoint`` (POV prose) and ``encoded_raw``
    (the encode node's YAML text) from state, and returns a single self-describing
    ``perspective`` dict ``{agent, viewpoint, beats}`` — the prose joined to its
    typed encoding so per-stage error attribution stays localizable. The encoding
    contract is **provisional** (recall-preserving, precision-open — FR-591 J1).
    """
    return {
        "perspective": {
            "agent": state.get("agent"),
            "viewpoint": state.get("viewpoint", ""),
            "beats": _parse_beats(state.get("encoded_raw", "")),
        }
    }


def _perspective_beats(item: object) -> list[dict]:
    """Extract an agent's beat list from a collected perspective item.

    Tolerates the three shapes the map collector can yield: a self-describing
    ``{..., beats: [...]}`` record (FR-591 graph), a nested ``{perspective: {...}}``
    wrapper, or a bare ``list`` of beats (direct callers / unit tests).
    """
    if isinstance(item, dict):
        if isinstance(item.get("beats"), list):
            return item["beats"]
        persp = item.get("perspective")
        if isinstance(persp, dict) and isinstance(persp.get("beats"), list):
            return persp["beats"]
        return []
    if isinstance(item, list):
        return item
    return []


def combine_perspectives(perspectives: list | dict) -> list[dict] | dict:
    """Merge per-agent encodings into the unified per-beat L5 (FR-590/591).

    Each element is one agent's perspective — a ``{agent, viewpoint, beats}``
    record (FR-591 graph) or a bare list of ``{id, pre_world, eff_world}`` beats
    (direct callers). The combine groups every agent's fluents by beat ``id``,
    unions each world slice, and dedups symmetric fluents by ``_fluent_key``.
    Belief slices stay empty (FR-585: belief is not the L5 wound). No salience
    logic and no LLM — the per-agent *framing* is the salience filter; combine
    only assembles what each perspective already chose. Items are ordered by
    ``_map_index`` when present so the fan-out's collect order is deterministic.

    Dual-mode: as a graph python tool it receives the full state dict and returns
    ``{"l5": [...]}``; called directly (unit tests, library use) it receives the
    perspective list and returns the per-beat L5 list.
    """
    if isinstance(perspectives, dict):
        return {"l5": combine_perspectives(perspectives.get("perspectives") or [])}
    if perspectives and all(isinstance(p, dict) for p in perspectives):
        perspectives = sorted(perspectives, key=lambda p: p.get("_map_index", 0))
    order: list[str] = []
    pre_by_id: dict[str, list[dict]] = {}
    eff_by_id: dict[str, list[dict]] = {}
    for item in perspectives or []:
        for beat in _perspective_beats(item):
            if not isinstance(beat, dict):
                continue
            bid = beat.get("id")
            if not bid:
                continue
            if bid not in pre_by_id:
                order.append(bid)
                pre_by_id[bid] = []
                eff_by_id[bid] = []
            pre_by_id[bid].extend(beat.get("pre_world") or [])
            eff_by_id[bid].extend(beat.get("eff_world") or [])
    return [
        {
            "id": bid,
            "pre_world": _dedup_fluents(pre_by_id[bid]),
            "eff_world": _dedup_fluents(eff_by_id[bid]),
            "pre_belief": [],
            "eff_belief": [],
        }
        for bid in order
    ]


# ---------------------------------------------------------------------------
# FR-577 L6 — assign causality (enables / motivation / threatens) to beats
# ---------------------------------------------------------------------------

_CAUSALITY_KEYS = {"id", "enables", "motivation", "threatens"}


def validate_causality(state: dict) -> dict:
    """Parse and validate the assign_causality node's raw YAML output (J1).

    Reads ``causality_raw`` (raw text), ``glosses`` (classified beats, in
    narrative order) and ``agents`` (for the membership check). On success
    writes the parsed list to ``causality`` plus ``validation``; on failure
    writes **only** ``validation``, leaving ``causality`` absent (J1).

    The validator enforces structural and referential integrity, including the
    **forward-only** ``enables`` invariant (J:C2): a beat may only enable a
    beat that appears *later* in narrative order. A backward (or self) link is
    a validation failure that forces a retry — not merely an evaluator miss.
    ``motivation``/``threatens`` are informational ({agent, goal}|null) and are
    checked only for shape and agent membership, never for correctness (J:C3).
    """
    from schema.functions import Motivation

    raw = state.get("causality_raw", "")
    try:
        items = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(items, list):
        return {
            "validation": {
                "ok": False,
                "flaws": ["expected a YAML list of per-beat causality objects"],
            }
        }

    glosses = state.get("glosses", [])
    # Narrative order = the glosses list order. Index defines "later".
    order = {
        g["id"]: i
        for i, g in enumerate(glosses)
        if isinstance(g, dict) and g.get("id") is not None
    }
    valid_ids = set(order)
    agents_set = {_norm_name(a) for a in state.get("agents", []) if isinstance(a, str)}

    flaws: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            flaws.append(f"non-mapping item: {item!r}")
            continue
        bid = item.get("id", "?")
        extra = set(item) - _CAUSALITY_KEYS
        if extra:
            flaws.append(f"{bid}: unknown keys {sorted(extra)}")

        enables = item.get("enables", [])
        if not isinstance(enables, list):
            flaws.append(
                f"{bid}.enables: expected a list, got {type(enables).__name__}"
            )
        else:
            src_idx = order.get(item.get("id"))
            for tgt in enables:
                if tgt not in valid_ids:
                    flaws.append(
                        f"{bid}.enables: invalid target '{tgt}' (not a beat id)"
                    )
                elif src_idx is not None and order[tgt] <= src_idx:
                    flaws.append(
                        f"{bid}.enables: backward link to '{tgt}' "
                        "(a beat may only enable a later beat)"
                    )

        for slot in ("motivation", "threatens"):
            val = item.get(slot)
            if val is None:
                continue
            try:
                Motivation.model_validate(val)
            except Exception as e:
                flaws.append(f"{bid}.{slot}: invalid — {e}")
                continue
            if agents_set and _norm_name(val.get("agent")) not in agents_set:
                flaws.append(
                    f"{bid}.{slot}: agent '{val.get('agent')}' not in agents list"
                )

    expected = {
        g["id"] for g in glosses if isinstance(g, dict) and g.get("id") is not None
    }
    got = {item.get("id") for item in items if isinstance(item, dict)}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(str(m) for m in missing))}")
    orphans = got - expected
    if orphans:
        flaws.append(f"orphan ids: {', '.join(sorted(str(o) for o in orphans))}")

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    # Normalise absent optional keys to explicit null so downstream readers and
    # the evaluator see a stable shape (boundary normalization).
    for item in items:
        item.setdefault("enables", [])
        item.setdefault("motivation", None)
        item.setdefault("threatens", None)

    return {"causality": items, "validation": {"ok": True, "flaws": []}}


# ---------------------------------------------------------------------------
# FR-578 L7 — assign affects (eff_affect: list[AffectDelta]) to beats
# ---------------------------------------------------------------------------

_AFFECT_KEYS = {"id", "eff_affect"}


def validate_affects(state: dict) -> dict:
    """Parse and validate the assign_affects node's raw YAML output (J1).

    Reads ``affects_raw`` (raw text), ``glosses`` (classified beats, for id
    coverage) and ``agents`` (for the char/toward membership check). On success
    writes the parsed list to ``affects`` plus ``validation``; on failure writes
    **only** ``validation``, leaving ``affects`` absent (J1).

    The validator checks STRUCTURE only (C1): each ``eff_affect`` item must be a
    valid ``AffectDelta`` (closed ``AffectKind`` enum — C4, no tolerance; binary
    ``op``; ``extra="forbid"``) with ``char``/``toward`` drawn from the agent
    list. It deliberately does **not** enforce open/close balance — that
    cross-beat plan invariant belongs to the merge node (FR-579), not here.
    """
    from schema.affects import AffectDelta

    raw = state.get("affects_raw", "")
    try:
        items = yaml.safe_load(_strip_code_fences(raw))
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    if not isinstance(items, list):
        return {
            "validation": {
                "ok": False,
                "flaws": ["expected a YAML list of per-beat affect objects"],
            }
        }

    glosses = state.get("glosses", [])
    agents_set = {_norm_name(a) for a in state.get("agents", []) if isinstance(a, str)}

    flaws: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            flaws.append(f"non-mapping item: {item!r}")
            continue
        bid = item.get("id", "?")
        extra = set(item) - _AFFECT_KEYS
        if extra:
            flaws.append(f"{bid}: unknown keys {sorted(extra)}")

        eff_affect = item.get("eff_affect", [])
        if not isinstance(eff_affect, list):
            flaws.append(
                f"{bid}.eff_affect: expected a list, got {type(eff_affect).__name__}"
            )
            continue
        for i, delta in enumerate(eff_affect):
            try:
                model = AffectDelta.model_validate(delta)
            except Exception as e:
                flaws.append(f"{bid}.eff_affect[{i}]: invalid AffectDelta — {e}")
                continue
            if agents_set and _norm_name(model.char) not in agents_set:
                flaws.append(
                    f"{bid}.eff_affect[{i}]: char '{model.char}' not in agents list"
                )
            if (
                model.toward is not None
                and agents_set
                and _norm_name(model.toward) not in agents_set
            ):
                flaws.append(
                    f"{bid}.eff_affect[{i}]: toward '{model.toward}' not in agents list"
                )

    expected = {
        g["id"] for g in glosses if isinstance(g, dict) and g.get("id") is not None
    }
    got = {item.get("id") for item in items if isinstance(item, dict)}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(str(m) for m in missing))}")
    orphans = got - expected
    if orphans:
        flaws.append(f"orphan ids: {', '.join(sorted(str(o) for o in orphans))}")

    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}

    # Normalise the absent eff_affect key to an explicit empty list (boundary).
    for item in items:
        item.setdefault("eff_affect", [])

    return {"affects": items, "validation": {"ok": True, "flaws": []}}
