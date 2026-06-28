"""FR-606 — optional affect rationale field (default-off legibility).

Proves the two AC pillars the judge bound:

  Parity   — with ``state.explain`` unset, the rendered ``affect_locate`` /
             ``affect_set`` user prompts are BYTE-IDENTICAL to golden snapshots
             captured from the pre-change templates; the ``rationale`` / ``reasons``
             tokens are absent. Turning ``explain`` on ADDS the field.
  Quote     — the code-side ``_rationale_quotes_beat`` lint (J: don't trust the
             model to self-validate) requires >=3 consecutive beat words; an
             ungrounded "novel" (FR-598 trap) fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from spike_affect_twopass import _rationale_quotes_beat

from yamlgraph.executor_base import format_prompt
from yamlgraph.utils.prompts import load_prompt

EXAMPLE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = EXAMPLE_DIR / "prompts"
GOLD = EXAMPLE_DIR / "tests" / "fixtures" / "affect_prompts"

_GLOSSES = [
    {
        "id": "F1",
        "chapter": 1,
        "kind": "lack",
        "gloss": "Brynn learns the Sunken Crown is lost.",
    },
    {
        "id": "F4",
        "chapter": 2,
        "kind": "struggle",
        "gloss": "Brynn dives; the Watcher takes Fen; Fen is gone.",
    },
    {
        "id": "F6",
        "chapter": 3,
        "kind": "victory",
        "gloss": "Brynn surfaces with the Sunken Crown.",
    },
    {
        "id": "F8",
        "chapter": 4,
        "kind": "liquidation",
        "gloss": "Brynn places the Crown on Queen Livia's head; the lack is liquidated.",
    },
]
_SKELETON = [
    {"phase": "setup", "beats": ["F1"]},
    {"phase": "turn", "beats": ["F4"]},
    {"phase": "resolution", "beats": ["F6", "F8"]},
]
_SET_STATE = {
    "glosses": _GLOSSES,
    "agent": "Brynn",
    "kinds": ["loss", "hope", "guilt", "betrayal"],
    "glossary": {
        "loss": "a goal is gone",
        "hope": "a goal looks reachable",
        "guilt": "self harmed another",
        "betrayal": "ally defected",
    },
}
_LOC_NONREL = {
    "glosses": _GLOSSES,
    "agent": "Brynn",
    "kind": "loss",
    "definition": "a goal/possession is gone",
    "open_cue": "first shows the loss",
    "close_cue": "the loss resolves",
    "relational": False,
    "toward_hint": "",
    "skeleton": _SKELETON,
}
_LOC_REL = {
    **_LOC_NONREL,
    "kind": "betrayal",
    "definition": "an ally defects from a shared goal",
    "open_cue": "first feels betrayed",
    "close_cue": "the betrayal resolves",
    "relational": True,
    "toward_hint": "the ally who defected",
}


def _render(name: str, state: dict) -> str:
    content = load_prompt(name, prompts_dir=PROMPTS_DIR)
    return format_prompt(content["user"], {}, state=state)


PARITY_CASES = [
    ("affect_set", _SET_STATE, "affect_set_user.txt", "reasons"),
    ("affect_locate", _LOC_NONREL, "affect_locate_nonrel_user.txt", "rationale"),
    ("affect_locate", _LOC_REL, "affect_locate_rel_user.txt", "rationale"),
]


@pytest.mark.parametrize("name,state,golden,field", PARITY_CASES)
def test_explain_off_is_byte_identical_to_pre_change(name, state, golden, field):
    """Default-off render == pre-change golden, and the explain field is absent.

    Goldens were captured from the pre-change templates; the only permitted
    difference is the single trailing newline the ``end-of-file-fixer`` pre-commit
    hook enforces on the fixture file (not part of the prompt content), so both
    sides are compared with trailing newlines normalized.
    """
    rendered = _render(name, state)  # explain unset
    expected = (GOLD / golden).read_text(encoding="utf-8")
    assert rendered.rstrip("\n") == expected.rstrip(
        "\n"
    ), f"{name} explain-off render drifted from {golden}"
    assert field not in rendered


@pytest.mark.parametrize("name,state,golden,field", PARITY_CASES)
def test_explain_on_adds_the_field(name, state, golden, field):
    """Turning explain on injects the diagnostic field (and only then)."""
    on = _render(name, {**state, "explain": True})
    assert field in on


def test_quote_check_accepts_a_grounded_rationale():
    beat = "Brynn dives; the Watcher takes Fen; Fen is gone."
    assert _rationale_quotes_beat("Loss opens when the Watcher takes Fen.", beat)


def test_quote_check_rejects_an_ungrounded_novel():
    """FR-598 trap: a confident essay that quotes no span of the beat fails."""
    beat = "Brynn dives; the Watcher takes Fen; Fen is gone."
    novel = (
        "This delta captures a profound emotional rupture in the protagonist's arc, "
        "a bereavement that reverberates through the narrative's thematic core."
    )
    assert not _rationale_quotes_beat(novel, beat)


def test_quote_check_requires_three_consecutive_words():
    """Two matching words is not enough; the run must be >=3 consecutive."""
    beat = "Brynn surfaces with the Sunken Crown."
    assert not _rationale_quotes_beat("She found the crown at last.", beat)
    assert _rationale_quotes_beat("She surfaces with the prize.", beat)
