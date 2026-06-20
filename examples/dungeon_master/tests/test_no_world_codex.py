"""FR-550: the World Codex (FR-548) is rolled back — permanent re-introduction guard.

The synopsis-derived World Codex was removed because it authored *prose, before the
action exists, from a plot synopsis* — a placement defect that leaked non-roster
characters (``Reinmar``) and plot-derived "factions" ("Wenda's people") into immutable
world texture (verified live in 10034-BC ``story.json``). Its length/depth goal is
re-earned soundly by FR-551 (supporting-cast tier) and FR-552 (world bible).

This is the kept one-line guard from the FR-550 J3 condition: it fails the moment any
codex symbol or the ``final_cut`` weave is re-introduced, so the rollback cannot silently
regress. Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import doc_ops, final_cut, tree
from examples.dungeon_master.api.final_cut import final_cut_context


def _final_cut_doc() -> dict:
    """A minimal two-chapter doc ``final_cut_context(doc, "2")`` can assemble."""
    return {
        "synopsis": {"text": "synopsis"},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "c1",
                    "beats": ["Hilde holds the ridge"],
                    "cast": ["Hilde"],
                    "text": "Hilde held the ridge.",
                    "world_state": {"characters": []},
                },
                "2": {
                    "summary": "c2",
                    "beats": ["Hilde presses on"],
                    "cast": ["Hilde"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": ["beat"]},
                            "recap": {"text": "recap"},
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde"],
            "cards": {"hilde": {"name": "Hilde", "reviewed": True}},
        },
    }


def test_codex_symbols_are_gone():
    """No codex boundary survives on ``doc_ops`` / ``final_cut`` / ``tree``."""
    assert not hasattr(doc_ops, "expand_codex")
    assert not hasattr(doc_ops, "_normalize_codex")
    assert not hasattr(doc_ops, "_codex_entries")
    assert not hasattr(final_cut, "_format_world_codex")
    assert not hasattr(tree, "WORLD_CODEX_GRAPH")


def test_final_cut_context_has_no_world_codex_key():
    """The Final Cut weave is gone: no ``world_codex`` variable reaches the prompt."""
    ctx = final_cut_context(_final_cut_doc(), "2")
    assert "world_codex" not in ctx
