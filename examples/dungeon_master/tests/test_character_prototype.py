"""Prototype tests for DM v2 character-sheet faction + inventory (FR-498).

A *visibility* harness, not a governance gate (FR-474 J3): no ``@pytest.mark.req``.
These pin the **prompt contract** the front-boundary continuity fix depends on —
that the character sheet declares a canonical ``FACTION:`` token and an
``INVENTORY:`` list, and that the director's ``continuity`` channel is told to flag
faction-mismatch and unprovenanced-inventory use. They also guard the FR-496
no-leak invariant for the two new labels.

Pure file reads over the prompt YAML — no LLM, no I/O. The behavioural proof (a
regenerated book whose clan-flip break is gone) is the live witness, not a unit.

Run directly:
    pytest examples/dungeon_master/tests/test_character_prototype.py --no-cov
"""

from __future__ import annotations

from pathlib import Path

import yaml

from examples.dungeon_master.api import render

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def _prompt_text(name: str) -> str:
    """The full system+user template text of a prompt YAML, lower-cased keys aside."""
    data = yaml.safe_load((PROMPTS / name).read_text(encoding="utf-8"))
    return "\n".join(str(data.get(k, "")) for k in ("system", "user"))


def test_character_sheet_declares_faction_and_inventory_labels():
    # FR-498 J1/J2: the sheet is labeled PROSE (not a schema), so the fix is two
    # new EXACT uppercase labels — a single-token FACTION and an INVENTORY list.
    text = _prompt_text("character.yaml")
    assert "FACTION:" in text
    assert "INVENTORY:" in text


def test_character_sheet_faction_is_a_single_canonical_token():
    # J1: FACTION must be ONE canonical token (a clan/side or "unaligned"), not a
    # prose phrase — that is what later chapters carry forward unchanged.
    text = _prompt_text("character.yaml").lower()
    assert "faction:" in text
    # The instruction names the single-token / unaligned contract.
    assert "unaligned" in text


def test_inventory_subsumes_what_they_carry_from_appearance():
    # J2: kill the duplication — possessions live under INVENTORY, not also as
    # APPEARANCE's "what they carry" bullets.
    text = _prompt_text("character.yaml")
    appearance = text.split("APPEARANCE:", 1)[1].split("INVENTORY:", 1)[0]
    assert "what they carry" not in appearance.lower()


def test_director_continuity_flags_faction_and_inventory():
    # J4: detection-only this FR — the director's continuity channel must be told
    # to surface a faction-mismatch and an unprovenanced item, not just an
    # actor-not-in-roster.
    text = _prompt_text("turn_direct.yaml").lower()
    assert "faction" in text
    assert "inventory" in text


def test_render_cast_never_leaks_faction_or_inventory_labels():
    # FR-498 J3 (no-leak): adding FACTION:/INVENTORY: to the sheet must not leak
    # either label into the rendered Cast line — the gloss is the SUMMARY value
    # alone (FR-496 generic guard), proven here for the two new labels.
    doc = {
        "tagline": "t",
        "synopsis": {"text": "s", "reviewed": True},
        "characters": {
            "reviewed": True,
            "roster": ["hilde"],
            "cards": {
                "hilde": {
                    "name": "Hilde",
                    "text": (
                        "SUMMARY: A war-leader who came to kill and stayed.\n"
                        "ROLE: Band leader.\n"
                        "FACTION: Aschenwulf.\n"
                        "INVENTORY: flint spear, river-hide cloak.\n"
                        "FLAW: Cannot forgive herself."
                    ),
                    "reviewed": True,
                },
            },
        },
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "text": "Hilde musters the band.",
                    "world_state": "WS1.",
                },
            },
        },
    }
    md = render.render_story_markdown(doc)
    assert "**Hilde** — A war-leader who came to kill and stayed." in md
    assert "FACTION:" not in md
    assert "INVENTORY:" not in md
