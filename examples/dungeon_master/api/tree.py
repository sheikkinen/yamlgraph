"""Stage tree + breadcrumb model for DM v2 (FR-475).

The preplan is a tree, not a linear chain:

    Synopsis (root, gates children)
    ├── Key Scene          (static leaf)
    └── Characters         (roster — non-visitable; spawns one card per name)
        ├── char:elara     (dynamic leaf)
        └── char:coil      (dynamic leaf)

Static stages live in ``STAGES``. Per-character cards are *not* in ``STAGES``:
they are addressed by id (``char:<slug>``) and resolved at runtime from the
roster the synopsis-accept derives. ``resolve_stage`` returns a synthetic
``Stage`` for those (A1), carrying the character's display name so the shared
``character.yaml`` graph can be parameterised by it (A3).

All functions here are pure operations on the story ``doc`` — no I/O, no LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

GRAPH_DIR = "examples/dungeon_master"
CHARACTER_GRAPH = f"{GRAPH_DIR}/character.yaml"
CHARACTER_SEED = "Draft this one character from the synopsis."
CHAR_PREFIX = "char:"


@dataclass(frozen=True)
class Stage:
    """One story stage: its graph, label, and the prior stages it reads as context."""

    name: str
    label: str
    graph: str
    # Names of earlier stages whose accepted text is passed in as graph variables.
    context: tuple[str, ...] = ()
    # Default instruction used to auto-draft this stage the moment it is entered,
    # so the DM never lands on a blank card. Empty seed => wait for a manual prompt.
    seed: str = ""
    # The parent stage that must be reviewed before this one unlocks (None = root).
    parent: str | None = None
    # "" for an ordinary stage, "roster" for the non-visitable Characters group.
    kind: str = ""
    # Character display name injected as the ``name`` graph variable (char stages).
    var_name: str = ""
    # The graph's output state_key, when it differs from ``name`` (e.g. roster, char).
    output_key: str = ""


# The static stage tree. Adding a static stage extends the app; per-character
# cards are built at runtime (see ``resolve_stage``).
STAGES: tuple[Stage, ...] = (
    Stage("synopsis", "Synopsis", f"{GRAPH_DIR}/synopsis.yaml"),
    Stage(
        "key_scene",
        "Key Scene",
        f"{GRAPH_DIR}/key_scene.yaml",
        context=("synopsis",),
        parent="synopsis",
        seed="Write the single pivotal key scene implied by the synopsis.",
    ),
    Stage(
        "characters",
        "Characters",
        f"{GRAPH_DIR}/character_roster.yaml",
        context=("synopsis",),
        parent="synopsis",
        kind="roster",
        seed="Name the characters the synopsis requires (names only).",
        output_key="roster",
    ),
)
STAGE_BY_NAME = {s.name: s for s in STAGES}
FIRST_STAGE = STAGES[0]


def _slug(name: str) -> str:
    """Slugify a character name to an id (lowercase, alnum + hyphens)."""
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "character"


def unique_slug(name: str, seen: set[str]) -> str:
    """A slug for ``name`` not already in ``seen`` (suffix -2, -3… on collision)."""
    base = _slug(name)
    cid = base
    n = 2
    while cid in seen:
        cid = f"{base}-{n}"
        n += 1
    return cid


def split_roster(raw: str) -> list[str]:
    """Split a plain-text roster (names on lines or commas) into proper names."""
    names: list[str] = []
    for part in re.split(r"[\n,]+", raw or ""):
        # Strip bullets, numbering, and surrounding punctuation/space.
        name = part.strip().lstrip("-*•").strip()
        name = re.sub(r"^\d+[.)]\s*", "", name).strip()
        if name:
            names.append(name)
    return names


def resolve_stage(doc: dict, name: str) -> Stage:
    """The ``Stage`` for ``name`` — a static one, or a synthetic char stage (A1)."""
    if name.startswith(CHAR_PREFIX):
        cid = name[len(CHAR_PREFIX) :]
        card = doc.get("characters", {}).get("cards", {}).get(cid, {})
        label = card.get("name") or cid
        return Stage(
            name=name,
            label=label,
            graph=CHARACTER_GRAPH,
            context=("synopsis",),
            seed=CHARACTER_SEED,
            parent="characters",
            var_name=label,
            output_key="character",
        )
    return STAGE_BY_NAME.get(name, FIRST_STAGE)


def breadcrumb(doc: dict) -> list[dict]:
    """The breadcrumb control model (FR-475): Story / Synopsis / branch peers.

    Each crumb is ``{label, stage, current, reviewed, group?, member?}``. ``stage``
    is the nav target (``None`` => not clickable). Branch peers (Key Scene,
    Characters) appear only once the synopsis is reviewed; inside the Characters
    branch the cast is listed inline as member peers.
    """
    current = doc.get("stage", FIRST_STAGE.name)
    syn = doc.get("synopsis", {})
    crumbs: list[dict] = [
        {"label": "Story", "stage": None, "current": False, "reviewed": False},
        {
            "label": "Synopsis",
            "stage": "synopsis",
            "current": current == "synopsis",
            "reviewed": bool(syn.get("reviewed")),
        },
    ]
    if not syn.get("reviewed"):
        return crumbs

    key_scene = doc.get("key_scene", {})
    crumbs.append(
        {
            "label": "Key Scene",
            "stage": "key_scene",
            "current": current == "key_scene",
            "reviewed": bool(key_scene.get("reviewed")),
        }
    )

    chars = doc.get("characters", {})
    cards = chars.get("cards", {})
    roster = chars.get("roster", [])
    in_chars = current.startswith(CHAR_PREFIX)
    all_reviewed = bool(roster) and all(
        cards.get(cid, {}).get("reviewed") for cid in roster
    )
    crumbs.append(
        {
            "label": "Characters",
            "stage": (CHAR_PREFIX + roster[0]) if roster else None,
            "current": False,
            "reviewed": all_reviewed,
            "group": True,
        }
    )
    if in_chars:
        for cid in roster:
            card = cards.get(cid, {})
            crumbs.append(
                {
                    "label": card.get("name") or cid,
                    "stage": CHAR_PREFIX + cid,
                    "current": current == CHAR_PREFIX + cid,
                    "reviewed": bool(card.get("reviewed")),
                    "member": True,
                }
            )
    return crumbs
