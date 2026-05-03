"""Acceptance tests for FR-317 sanity-check diary filename derivation."""

from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
SANITY_PROMPT = (
    WORKTREE
    / ".chaplain"
    / "graphs"
    / "watcher-enforce"
    / "prompts"
    / "sanity-check-session.yaml"
)


def _load_prompt() -> str:
    assert SANITY_PROMPT.exists(), f"Missing sanity-check prompt: {SANITY_PROMPT}"
    return SANITY_PROMPT.read_text()


@pytest.mark.req("REQ-YG-316")
class TestFR317WatcherSanityCheckDiaryFilenameFromFrPath:
    def test_ac01_no_hardcoded_fr316_diary_filename(self):
        content = _load_prompt().lower()
        assert "reflection-fr-316-watcher2-sanity-check-state" not in content

    def test_ac02_diary_filename_is_derived_from_fr_path_variable(self):
        content = _load_prompt().lower()
        assert "derived from {{ fr_path }}" in content

    def test_ac03_prompt_defines_reflection_derived_fr_stem_path_pattern(self):
        content = _load_prompt()
        assert "docs/diary/YYYY-MM-DD-reflection-<derived-fr-stem>.md" in content

    def test_ac04_prompt_includes_concrete_fr_path_to_diary_example(self):
        content = _load_prompt()
        assert "feature-requests/FR-317-reference-docs-review.md" in content
        assert (
            "docs/diary/YYYY-MM-DD-reflection-fr-317-reference-docs-review.md"
            in content
        )

    def test_ac05_prompt_still_requires_seed_section(self):
        content = _load_prompt().lower()
        assert "seed:" in content
