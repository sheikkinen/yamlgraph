"""FR-534: protected-character projection into prose generation (RED witness).

Pins the gap the FR-533 spike found: DM v2 holds plan-over-prose precedence at
chapter open (``_enforce_memory_precedence_gate``) but never feeds it to prose
generation, so the turn director / final-cut can narrate the death of a
plan-protected character the ledger is sworn to keep alive (ch7 Witta).

The doc below is an inline minimal fixture (the established DM test convention;
see ``test_dead_character_prose.py``). It is committed, unlike the gitignored
``10026-BC`` live output — satisfying Judgement J3's intent.

Membership rule under test (Judgement J4 — the conjunction):
  protected = (highest-precedence state is alive/active)
              AND (a plan guard names the character:
                   forbidden_regressions "X is dead" / irreversible_facts
                   "X is alive" / live_synopsis presence).
"""

from __future__ import annotations

from examples.dungeon_master.api.turn_ops import final_cut_context


def _doc_protected_witta() -> dict:
    """ch7→ch8 seam: Witta plan-protected-alive (multi-guard); Gerda transient.

    - Witta: chapter_memory delta alive (highest precedence) + forbidden_regressions
      "Witta is dead" + irreversible_facts + live_synopsis → PROTECTED.
    - Gerda: chapter_memory delta alive only, named by NO plan guard → NOT protected
      (negative control for the conjunction rule, J4).
    - ch7 ``text`` carries the death sentence the spike found (the prose that
      resurrects Witta at the ch8 seam).
    """
    return {
        "live_synopsis": {
            "character_states": {"Witta": "alive"},
        },
        "chapters": {
            "order": ["7", "8"],
            "cards": {
                "7": {
                    "chapter_memory": {
                        "character_state_deltas": [
                            {"name": "Witta", "to_state": "alive"},
                            {"name": "Gerda", "to_state": "alive"},
                        ],
                        "irreversible_facts": [
                            "Witta is alive at the end of the chapter, "
                            "not dead or swept away",
                        ],
                        "forbidden_regressions": ["Witta is dead"],
                    },
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Witta",
                                "existence_state": "alive",
                                "visibility_mode": "present",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 7,
                            }
                        ],
                    },
                    "turns": [],
                    "summary": "ch7",
                    "beats": ["a"],
                    "text": (
                        "She vanished into the flood as it seized her, and the "
                        "valley swallowed the judgment she had called down on them."
                    ),
                },
                "8": {
                    "turns": [],
                    "summary": "ch8",
                    "beats": ["b"],
                },
            },
        },
    }


def test_protected_characters_includes_plan_protected_witta():
    """The shared resolver names Witta protected (alive + plan guard, J4)."""
    from examples.dungeon_master.api.lifecycle_resolver import protected_characters

    protected = protected_characters(_doc_protected_witta(), "8")
    names = {entry["name"] for entry in protected.values()}
    assert "Witta" in names


def test_protected_characters_excludes_unguarded_transient():
    """Conjunction rule (J4): alive-only-in-memory with no plan guard is NOT protected."""
    from examples.dungeon_master.api.lifecycle_resolver import protected_characters

    protected = protected_characters(_doc_protected_witta(), "8")
    names = {entry["name"] for entry in protected.values()}
    assert "Gerda" not in names


def test_protected_characters_shares_precedence_with_open_gate():
    """Resolver and the open-gate read the SAME precedence (one source of truth, J2)."""
    from examples.dungeon_master.api import lifecycle_resolver, turn_ops

    # The gate must consume the resolver's extractors, not its own private copies.
    assert turn_ops._state_map_from_memory is lifecycle_resolver._state_map_from_memory
    assert (
        turn_ops._state_map_from_synopsis is lifecycle_resolver._state_map_from_synopsis
    )
    assert turn_ops._state_map_from_seam is lifecycle_resolver._state_map_from_seam


def test_final_cut_context_emits_protected_cast_for_witta():
    """final_cut_context must carry the symmetric may-not-die channel (FR-519 parity)."""
    ctx = final_cut_context(_doc_protected_witta(), "8")
    assert "protected_cast" in ctx
    assert "Witta" in ctx["protected_cast"]
    assert "Gerda" not in ctx["protected_cast"]
