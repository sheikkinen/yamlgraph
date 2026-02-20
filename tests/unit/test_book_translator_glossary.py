"""Unit tests for book translator glossary merge function."""

import sys
from pathlib import Path

import pytest

# Add examples to path for testing
examples_path = Path(__file__).parent.parent.parent / "examples" / "book_translator"
sys.path.insert(0, str(examples_path))

from nodes.tools import merge_terms  # noqa: E402


class TestMergeTerms:
    """Tests for glossary term merging."""

    @pytest.mark.req("REQ-YG-014")
    def test_merge_empty_state(self):
        """Handle empty state gracefully."""
        state = {}
        result = merge_terms(state)

        assert "glossary" in result
        assert result["glossary"] == {}

    @pytest.mark.req("REQ-YG-014")
    def test_merge_with_existing_glossary(self):
        """Preserve existing glossary terms."""
        state = {
            "glossary": {"Hello": "Hola", "World": "Mundo"},
            "term_extractions": [],
        }
        result = merge_terms(state)

        assert result["glossary"]["Hello"] == "Hola"
        assert result["glossary"]["World"] == "Mundo"

    @pytest.mark.req("REQ-YG-014")
    def test_merge_new_extractions(self):
        """Add new terms from extractions (flatten_output format FR-052)."""
        state = {
            "glossary": {},
            "term_extractions": [
                {
                    "_map_index": 0,
                    "terms": [{"source_term": "Hello", "translation": "Hola"}],
                },
                {
                    "_map_index": 1,
                    "terms": [{"source_term": "World", "translation": "Mundo"}],
                },
            ],
        }
        result = merge_terms(state)

        assert result["glossary"]["Hello"] == "Hola"
        assert result["glossary"]["World"] == "Mundo"

    @pytest.mark.req("REQ-YG-014")
    def test_existing_terms_not_overwritten(self):
        """Existing terms take priority over new extractions."""
        state = {
            "glossary": {"Hello": "existing_translation"},
            "term_extractions": [
                {
                    "_map_index": 0,
                    "terms": [
                        {"source_term": "Hello", "translation": "new_translation"}
                    ],
                },
            ],
        }
        result = merge_terms(state)

        # Existing translation should be preserved
        assert result["glossary"]["Hello"] == "existing_translation"

    @pytest.mark.req("REQ-YG-014")
    def test_handle_empty_extractions(self):
        """Handle empty term_extractions list."""
        state = {
            "glossary": {"existing": "value"},
            "term_extractions": [],
        }
        result = merge_terms(state)

        assert result["glossary"]["existing"] == "value"

    @pytest.mark.req("REQ-YG-014")
    def test_handle_none_extraction_items(self):
        """Handle None values in extractions list."""
        state = {
            "glossary": {},
            "term_extractions": [
                None,
                {
                    "_map_index": 0,
                    "terms": [{"source_term": "Valid", "translation": "Válido"}],
                },
                None,
            ],
        }
        result = merge_terms(state)

        assert result["glossary"]["Valid"] == "Válido"

    @pytest.mark.req("REQ-YG-014")
    def test_handle_missing_terms_key(self):
        """Handle extractions without terms key."""
        state = {
            "glossary": {},
            "term_extractions": [
                {"_map_index": 0, "other_key": "value"},
                {
                    "_map_index": 1,
                    "terms": [{"source_term": "Test", "translation": "Prueba"}],
                },
            ],
        }
        result = merge_terms(state)

        assert result["glossary"]["Test"] == "Prueba"
        assert len(result["glossary"]) == 1

    @pytest.mark.req("REQ-YG-014")
    def test_handle_malformed_terms(self):
        """Handle terms missing required fields."""
        state = {
            "glossary": {},
            "term_extractions": [
                {
                    "_map_index": 0,
                    "terms": [
                        {"source_term": "", "translation": "Empty source"},
                        {"source_term": "Valid", "translation": "Válido"},
                        {"translation": "Missing source"},  # No source_term
                    ],
                },
            ],
        }
        result = merge_terms(state)

        assert "Valid" in result["glossary"]
        assert "" not in result["glossary"]
        assert len(result["glossary"]) == 1

    @pytest.mark.req("REQ-YG-014")
    def test_multiple_terms_per_extraction(self):
        """Handle multiple terms in single extraction."""
        state = {
            "glossary": {},
            "term_extractions": [
                {
                    "_map_index": 0,
                    "terms": [
                        {"source_term": "One", "translation": "Uno"},
                        {"source_term": "Two", "translation": "Dos"},
                        {"source_term": "Three", "translation": "Tres"},
                    ],
                },
            ],
        }
        result = merge_terms(state)

        assert len(result["glossary"]) == 3
        assert result["glossary"]["One"] == "Uno"
        assert result["glossary"]["Two"] == "Dos"
        assert result["glossary"]["Three"] == "Tres"

    @pytest.mark.req("REQ-YG-014")
    def test_glossary_from_json_string(self):
        """Handle glossary passed as JSON string from CLI."""
        state = {
            "glossary": '{"existing": "value"}',
            "term_extractions": [
                {
                    "_map_index": 0,
                    "terms": [{"source_term": "New", "translation": "Nuevo"}],
                },
            ],
        }
        result = merge_terms(state)

        assert result["glossary"]["existing"] == "value"
        assert result["glossary"]["New"] == "Nuevo"
