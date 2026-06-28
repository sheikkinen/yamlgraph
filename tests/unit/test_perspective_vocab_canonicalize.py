"""FR-593 unit tests for the deterministic story-level vocabulary stage.

The Judgement (2026-06-25) froze the contained, deterministic core:

- ``StoryVocab`` (``schema/vocab.py``) is the validated structured binding for the
  ``extract_vocab`` output — it MUST reject a bare string, making the FR-592
  markdown-string regression impossible to reintroduce (Judge correction #4).
- ``canonicalize_glosses`` (``nodes/tools.py``) is a pure, deterministic alias
  substitution: case-insensitive, longest-alias-first, word-boundary aware. It is
  **additive** — it writes a new ``canonical_gloss`` field and leaves the original
  ``gloss`` byte-identical, so no other gloss-consuming layer (L4/L6/L7/L8) is
  perturbed (Judge correction #1, containment).

These pin the deterministic witness; the corpus precision/recall gate is a separate
acceptance run (PRIMARY/REVERT: world_recall >= 0.47 over two runs).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "plot_modeller"


def _load_tools():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    spec = importlib.util.spec_from_file_location(
        "plot_modeller_tools_fr593", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_vocab_schema():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    from schema.vocab import StoryVocab

    return StoryVocab


_mod = _load_tools()
canonicalize_glosses = _mod.canonicalize_glosses
StoryVocab = _load_vocab_schema()


# ---------------------------------------------------------------------------
# StoryVocab — validated structured binding (FR-592 string-regression guard)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_story_vocab_binds_structured_object():
    v = StoryVocab(
        locations=["Vantari Labs", "Warehouse"],
        objects=["Ledger"],
        aliases={"the lab": "Vantari Labs"},
    )
    assert isinstance(v.locations, list)
    assert isinstance(v.objects, list)
    assert isinstance(v.aliases, dict)
    assert v.aliases["the lab"] == "Vantari Labs"


@pytest.mark.req("REQ-YG-020")
def test_story_vocab_defaults_are_empty_collections():
    v = StoryVocab()
    assert v.locations == []
    assert v.objects == []
    assert v.aliases == {}


@pytest.mark.req("REQ-YG-020")
def test_story_vocab_rejects_bare_string():
    """The FR-592 failure: vocab arrived as a markdown string and was inert."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StoryVocab.model_validate("locations:\n  - Vantari Labs\n")


# ---------------------------------------------------------------------------
# canonicalize_glosses — deterministic, additive, contained
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_canonicalize_adds_field_and_leaves_original_intact():
    """Containment (PRIMARY): write canonical_gloss, never touch gloss."""
    glosses = [{"id": "F1", "gloss": "Mara enters the lab", "chapter": 1}]
    vocab = {"aliases": {"the lab": "Vantari Labs"}}

    out = canonicalize_glosses(glosses, vocab)

    assert out[0]["canonical_gloss"] == "Mara enters Vantari Labs"
    # original gloss byte-identical — no shared-token mutation
    assert out[0]["gloss"] == "Mara enters the lab"
    # caller's input list/dicts not mutated in place
    assert "canonical_gloss" not in glosses[0]


@pytest.mark.req("REQ-YG-020")
def test_canonicalize_is_case_insensitive_and_longest_alias_first():
    glosses = [{"id": "F1", "gloss": "They reach The Old Lab at dawn"}]
    vocab = {"aliases": {"lab": "Wrong", "the old lab": "Vantari Labs"}}

    out = canonicalize_glosses(glosses, vocab)

    assert out[0]["canonical_gloss"] == "They reach Vantari Labs at dawn"


@pytest.mark.req("REQ-YG-020")
def test_canonicalize_respects_word_boundaries():
    """'lab' must not match inside 'label'."""
    glosses = [{"id": "F1", "gloss": "She prints the label"}]
    vocab = {"aliases": {"lab": "Vantari Labs"}}

    out = canonicalize_glosses(glosses, vocab)

    assert out[0]["canonical_gloss"] == "She prints the label"


@pytest.mark.req("REQ-YG-020")
def test_canonicalize_idempotent_when_no_alias_matches():
    glosses = [{"id": "F1", "gloss": "Mara walks to the harbor"}]
    vocab = {"aliases": {"the lab": "Vantari Labs"}}

    out = canonicalize_glosses(glosses, vocab)

    assert out[0]["canonical_gloss"] == "Mara walks to the harbor"


@pytest.mark.req("REQ-YG-020")
def test_canonicalize_accepts_story_vocab_model():
    glosses = [{"id": "F1", "gloss": "Mara enters the lab"}]
    vocab = StoryVocab(locations=["Vantari Labs"], aliases={"the lab": "Vantari Labs"})

    out = canonicalize_glosses(glosses, vocab)

    assert out[0]["canonical_gloss"] == "Mara enters Vantari Labs"
