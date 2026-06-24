"""FR-575 — L3 validator tests: validate_glosses contract (RED first)."""

from __future__ import annotations

from nodes.tools import validate_glosses

VALID_RAW = (
    "- id: F1\n"
    "  gloss: The villain attacks the village, burning homes and taking hostages.\n"
    "  chapter: 1\n"
    "- id: F2\n"
    "  gloss: The hero discovers the village destroyed and vows to pursue the villain.\n"
    "  chapter: 1\n"
    "- id: F3\n"
    "  gloss: The hero sets out on the road toward the mountain fortress.\n"
    "  chapter: 2\n"
    "- id: F4\n"
    "  gloss: A mysterious stranger tests the hero with a riddle at the bridge.\n"
    "  chapter: 2\n"
    "- id: F5\n"
    "  gloss: The hero defeats the villain in combat and frees the hostages.\n"
    "  chapter: 3\n"
)


class TestValidateGlossesSuccess:
    """Golden path — valid glosses extraction."""

    def test_golden_success(self):
        out = validate_glosses({"glosses_raw": VALID_RAW})
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert len(out["glosses"]) == 5

    def test_many_beats(self):
        """Up to 20 beats is fine."""
        lines = []
        for i in range(1, 13):
            lines.append(
                f"- id: F{i}\n  gloss: Beat number {i} where something important happens to the hero and the story moves forward significantly.\n  chapter: {(i - 1) // 3 + 1}\n"
            )
        raw = "".join(lines)
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is True
        assert len(out["glosses"]) == 12


class TestValidateGlossesFailure:
    """Each flaw → validation fails, glosses not written (J1)."""

    def test_empty_raw(self):
        out = validate_glosses({"glosses_raw": ""})
        assert out["validation"]["ok"] is False
        assert "glosses" not in out

    def test_invalid_yaml(self):
        out = validate_glosses({"glosses_raw": "- id: : :\n"})
        assert out["validation"]["ok"] is False

    def test_non_list(self):
        out = validate_glosses({"glosses_raw": "just text\n"})
        assert out["validation"]["ok"] is False

    def test_too_few_beats(self):
        raw = "- id: F1\n  gloss: A single beat is not enough for a story.\n  chapter: 1\n"
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("at least" in f or "few" in f for f in out["validation"]["flaws"])

    def test_too_many_beats(self):
        lines = []
        for i in range(1, 25):
            lines.append(
                f"- id: F{i}\n  gloss: Beat {i} things happen here in the story.\n  chapter: 1\n"
            )
        raw = "".join(lines)
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("many" in f or "20" in f for f in out["validation"]["flaws"])

    def test_missing_id(self):
        raw = "- gloss: A beat without an id.\n  chapter: 1\n"
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False

    def test_missing_gloss(self):
        raw = "- id: F1\n  chapter: 1\n"
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False

    def test_missing_chapter(self):
        raw = "- id: F1\n  gloss: A beat without a chapter number.\n"
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False

    def test_non_sequential_ids(self):
        raw = (
            "- id: F1\n  gloss: First beat of the story with characters.\n  chapter: 1\n"
            "- id: F3\n  gloss: Skipped F2 going straight to third beat.\n  chapter: 1\n"
            "- id: F4\n  gloss: Fourth beat continues the story forward.\n  chapter: 2\n"
            "- id: F5\n  gloss: Fifth beat brings us to the climax.\n  chapter: 2\n"
            "- id: F6\n  gloss: Sixth beat resolves the story conflict.\n  chapter: 3\n"
        )
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("sequential" in f or "F2" in f for f in out["validation"]["flaws"])

    def test_non_increasing_chapters(self):
        raw = (
            "- id: F1\n  gloss: First beat happens in chapter two of story.\n  chapter: 2\n"
            "- id: F2\n  gloss: Second beat goes back to chapter one somehow.\n  chapter: 1\n"
            "- id: F3\n  gloss: Third beat is in chapter one continuing.\n  chapter: 1\n"
            "- id: F4\n  gloss: Fourth beat continues in chapter two now.\n  chapter: 2\n"
            "- id: F5\n  gloss: Fifth beat concludes the story finally.\n  chapter: 3\n"
        )
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("chapter" in f.lower() for f in out["validation"]["flaws"])

    def test_gloss_too_short(self):
        """Gloss under 10 words is suspicious."""
        raw = (
            "- id: F1\n  gloss: Too short.\n  chapter: 1\n"
            "- id: F2\n  gloss: A proper beat has more than ten words in it.\n  chapter: 1\n"
            "- id: F3\n  gloss: Another proper beat with enough words to be valid.\n  chapter: 2\n"
            "- id: F4\n  gloss: Yet another beat with sufficient word count.\n  chapter: 2\n"
            "- id: F5\n  gloss: Final beat wraps up the story with enough detail.\n  chapter: 3\n"
        )
        out = validate_glosses({"glosses_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("short" in f or "word" in f for f in out["validation"]["flaws"])

    def test_failure_does_not_write_glosses(self):
        out = validate_glosses({"glosses_raw": "garbage"})
        assert "glosses" not in out
        assert "validation" in out
