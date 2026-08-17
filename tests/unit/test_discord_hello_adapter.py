"""FR-812: pure Discord `/hello` adapter slice — zero network, zero discord.py.

Covers option→state mapping, embed rendering from a canned greeting dict,
and the visible-error path (AC-02).
"""

from __future__ import annotations

import pytest

from examples.discord_bot.adapter import (
    STYLE_CHOICES,
    error_message,
    greeting_to_embed,
    options_to_state,
)


@pytest.mark.req("REQ-YG-600")
class TestOptionsToState:
    def test_maps_name_and_style_to_initial_state(self):
        assert options_to_state("Maija", "playful") == {
            "name": "Maija",
            "style": "playful",
        }

    def test_strips_surrounding_whitespace(self):
        assert options_to_state("  Maija ", "formal")["name"] == "Maija"

    @pytest.mark.parametrize("style", ["formal", "casual", "playful"])
    def test_accepts_every_declared_style_choice(self, style):
        assert style in STYLE_CHOICES
        assert options_to_state("Maija", style)["style"] == style

    def test_rejects_unknown_style(self):
        with pytest.raises(ValueError, match="style"):
            options_to_state("Maija", "sarcastic")

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="name"):
            options_to_state("   ", "formal")

    def test_rejects_name_over_80_chars(self):
        with pytest.raises(ValueError, match="name"):
            options_to_state("x" * 81, "formal")


@pytest.mark.req("REQ-YG-600")
class TestGreetingToEmbed:
    CANNED = {
        "greeting": "Hyvää päivää, Maija!",
        "emoji": "🌞",
        "formality_level": "formal",
    }

    def test_renders_title_from_emoji_and_greeting(self):
        embed = greeting_to_embed(self.CANNED)
        assert embed["title"] == "🌞 Hyvää päivää, Maija!"

    def test_renders_footer_from_formality_level(self):
        assert greeting_to_embed(self.CANNED)["footer"] == "formal"

    @pytest.mark.parametrize("missing", ["greeting", "emoji", "formality_level"])
    def test_missing_field_raises_instead_of_fallback(self, missing):
        broken = {k: v for k, v in self.CANNED.items() if k != missing}
        with pytest.raises(ValueError, match=missing):
            greeting_to_embed(broken)

    def test_empty_greeting_raises_instead_of_fallback(self):
        broken = {**self.CANNED, "greeting": "  "}
        with pytest.raises(ValueError, match="greeting"):
            greeting_to_embed(broken)


@pytest.mark.req("REQ-YG-600")
class TestErrorMessage:
    def test_includes_correlation_id(self):
        assert "1234-abcd" in error_message("1234-abcd")

    def test_does_not_leak_exception_details(self):
        msg = error_message("cid-1")
        assert "Traceback" not in msg and "Exception" not in msg
