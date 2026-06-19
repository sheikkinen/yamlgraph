"""FR-539 end-to-end: the seam-aware Final Cut prose closes the entrance gap.

The deterministic suite (``test_cast_entrances`` / ``test_final_cut_seam_context``)
proves the manifest + prior-prose tail REACH the narrator. This integration test
proves the generative half the FR defers to a real compose: when the seam-aware
narrator runs, the composed PROSE stages the entrant's arrival, so FR-538's
``seam_entrance_gap`` drops to zero — and it drops because of the prose, never
because the entrant is listed in ``cast_entrances`` (paired B1; the detector never
reads the manifest).

The feature exists because of a generative phenomenon (a narrator establishing an
arrival), so the test exercises the real narrator rather than a mock
(``mock_escape_hatch``). Causation is pinned deterministically: the SAME doc with
the raw turn-recap as Ch2's text (an unbridged "Hilde and Arnulf drove the
assault…", no arrival) reports ``gap_count == 1`` with NO LLM call — proving the
harness discriminates — and the real seam-aware compose then closes it.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from examples.dungeon_master.api.cast_entrances import derive_cast_entrances
from examples.dungeon_master.api.final_cut import (
    _format_cast_entrances,
    _prior_chapter_tail,
    invoke_final_cut,
)
from examples.dungeon_master.api.seam_entrance import seam_entrance_gap

# Load .env so a locally-configured provider (PROVIDER + its key) is available; the
# generation scripts do the same before any LLM call.
load_dotenv()

# Any one provider credential is enough — the final-cut graph uses the default
# PROVIDER. Skip (never fail) when the box has no LLM creds, matching the repo's
# integration posture.
_PROVIDER_KEYS = (
    "ANTHROPIC_API_KEY",
    "AZURE_AI_API_KEY",
    "OPENAI_API_KEY",
    "MISTRAL_API_KEY",
    "VERTEX_API_KEY",
    "GOOGLE_API_KEY",
)
_HAS_PROVIDER = any(os.environ.get(k) for k in _PROVIDER_KEYS)

# The raw Ch2 turn recap: Arnulf acts with no narrated arrival. This is the prose a
# seam-BLIND narrator would carry forward, and the deterministic baseline the
# detector flags.
_UNBRIDGED_CH2_TEXT = (
    "Hilde and Arnulf drove the assault up the slope together, shields locked, "
    "breaking the enemy line at the crest."
)


def _played_doc(ch2_text: str = "") -> dict:
    """Two played chapters; Ch2 brings in roster member Arnulf, absent from Ch1.

    ``ch2_text`` seeds Ch2's final-cut prose (for the deterministic baseline). Left
    empty, the real compose fills it. Ch1's prose never names Arnulf, so he is a
    genuine unbridged entrant (the detector's on-page lens is pure name-presence —
    a negated "no sign of Arnulf" would falsely read as present, so he is simply
    omitted).
    """
    return {
        "synopsis": {"text": "A clan defends the high passes through the great thaw."},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "Hilde holds the ridge alone while the clan retreats.",
                    "reviewed": True,
                    "cast": ["Hilde"],
                    "beats": ["Hilde holds the ridge alone"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {
                                "beats_satisfied": ["Hilde holds the ridge alone"]
                            },
                            "recap": {
                                "text": (
                                    "Hilde set her shield against the ridge stones "
                                    "and held the narrow path as the clan streamed "
                                    "back toward the ford below."
                                ),
                                "reviewed": True,
                            },
                            "intents": {
                                "hilde": {
                                    "intent": "holds the ridge",
                                    "thinking": "buy them time",
                                    "dialogue": "Go! I will hold here.",
                                    "expression": "jaw set",
                                }
                            },
                        }
                    ],
                    "text": (
                        "The enemy fell back from the ridge as dusk came on. Hilde "
                        "lowered her shield at last, alone on the cold stones, and "
                        "looked down to where the clan had crossed the ford to "
                        "safety. The wounded were being carried up from the water's "
                        "edge below, out of her sight in the failing light."
                    ),
                    "world_state": {
                        "characters": [
                            {
                                "name": "Hilde",
                                "status": "holding the ridge",
                                "location": "the ridge",
                            },
                            {
                                "name": "Arnulf",
                                "status": "covering the wounded",
                                "location": "the ford",
                            },
                        ]
                    },
                },
                "2": {
                    "summary": "Hilde and Arnulf press the assault to the crest.",
                    "reviewed": True,
                    "cast": ["Hilde", "Arnulf"],
                    "beats": ["Hilde and Arnulf press the assault"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {
                                "beats_satisfied": [
                                    "Hilde and Arnulf press the assault"
                                ]
                            },
                            "recap": {"text": _UNBRIDGED_CH2_TEXT, "reviewed": True},
                            "intents": {
                                "hilde": {
                                    "intent": "presses the assault",
                                    "thinking": "now we push",
                                    "dialogue": "With me!",
                                    "expression": "fierce",
                                },
                                "arnulf": {
                                    "intent": "presses the assault",
                                    "thinking": "for the clan",
                                    "dialogue": "At your side.",
                                    "expression": "grim",
                                },
                            },
                        }
                    ],
                    **({"text": ch2_text} if ch2_text else {}),
                },
            },
        },
        "characters": {
            "reviewed": True,
            "roster": ["hilde", "arnulf"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "arnulf": {"name": "Arnulf", "reviewed": True},
            },
        },
    }


def test_unbridged_recap_is_flagged_without_llm():
    """Deterministic baseline: the raw Ch2 recap leaves Arnulf's entrance unbridged.

    No LLM — proves the harness discriminates, so a later ``gap_count == 0`` is a
    real result of the seam-aware prose, not a fixture that can never fail.
    """
    doc = _played_doc(ch2_text=_UNBRIDGED_CH2_TEXT)
    gap = seam_entrance_gap(doc, "2")
    assert gap["gap_count"] == 1
    assert gap["gaps"][0]["name"] == "Arnulf"
    assert gap["gaps"][0]["kind"] == "new"

    # And the seam context the narrator is handed deterministically names Arnulf as
    # the entrant to establish, with Ch1's closing prose to bridge from — the input
    # the generative test then exercises.
    manifest = _format_cast_entrances(derive_cast_entrances(doc, "2"))
    assert "Arnulf (new)" in manifest
    assert "Hilde lowered her shield" in _prior_chapter_tail(doc, "2")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not _HAS_PROVIDER,
    reason=f"no LLM provider credential set (one of {', '.join(_PROVIDER_KEYS)})",
)
def test_seam_aware_compose_closes_the_entrance_gap():
    """A real seam-aware Final Cut compose stages Arnulf's arrival → gap drops to 0.

    The acceptance criterion FR-539 defers to a real compose: the SAME doc the
    deterministic baseline flags (gap 1) composes to zero because the seam-aware
    narrator opens by establishing the entrant in PROSE — an arrival the FR-538
    detector finds. The gap is measured over the composed text; the detector never
    reads ``cast_entrances`` (paired B1).
    """
    import asyncio

    doc = _played_doc()
    text = asyncio.run(invoke_final_cut(doc, "2"))
    assert text.strip(), "final cut returned empty prose"

    doc["chapters"]["cards"]["2"]["text"] = text
    gap = seam_entrance_gap(doc, "2")
    assert gap["gap_count"] == 0, (
        "seam-aware prose left an unbridged entrance:\n"
        f"{gap}\n--- composed prose ---\n{text}"
    )
