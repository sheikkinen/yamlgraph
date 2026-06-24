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


def validate_kinds(state: dict) -> dict:
    """Parse and validate the classify node's raw YAML output (J1).

    Reads ``kinds_raw`` (raw text). On success writes the parsed list to
    ``kinds`` plus ``validation``. On failure writes **only** ``validation``,
    leaving ``kinds`` absent.
    """
    raw = state.get("kinds_raw", "")
    try:
        items = yaml.safe_load(raw)
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
        data = yaml.safe_load(raw)
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
        data = yaml.safe_load(raw)
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
        data = yaml.safe_load(raw)
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
        items = yaml.safe_load(raw)
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
