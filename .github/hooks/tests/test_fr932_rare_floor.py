#!/usr/bin/env python3
"""FR-932: rare_floor opt-out for the research consumer.

The rarity floor is a notification policy, not a retrieval policy. The
hook consumers interrupt an author and need silence over noise; the
research consumer grounds a context window and needs the ranked hits.

Pins the measured miss (FR-932 measurement A): at 854 files the
absolute RARE_MAX_FILES=20 floor disqualifies every noun with ordinary
currency and build_prior_art returns "". Unmarked, following the
FR-737 F5 convention of this directory.
"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
CHECKS_DIR = HOOKS_ROOT / "scripts" / "checks"


def _load_prior_art():
    spec = importlib.util.spec_from_file_location(
        "prior_art", CHECKS_DIR / "prior_art.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _common_noun_corpus(tmpdir: str, pa) -> Path:
    """Corpus where every matching noun exceeds RARE_MAX_FILES."""
    fr_dir = Path(tmpdir) / "feature-requests"
    fr_dir.mkdir(parents=True, exist_ok=True)
    n = pa.RARE_MAX_FILES + 5
    for i in range(n):
        (fr_dir / f"FR-{500 + i}-retrieval-note.md").write_text(
            f"# FR-{500 + i} Retrieval Note\n"
            "**Status:** Approved\n"
            "Discusses retrieval and precedent handling.\n",
            encoding="utf-8",
        )
    return fr_dir


def test_common_noun_is_silent_with_default_floor() -> None:
    """AC-01: the hook consumers keep their silence-over-noise floor."""
    pa = _load_prior_art()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _common_noun_corpus(tmpdir, pa)
        new = fr_dir / "FR-999-retrieval-precedent.md"
        new.write_text("# FR-999\n", encoding="utf-8")

        assert pa.build_prior_art(new) == ""
        assert pa.build_prior_art(new, rare_floor=True) == ""


def test_common_noun_retrieves_with_floor_lifted() -> None:
    """AC-02: rare_floor=False lifts BOTH rare gates, not just the first.

    The early return (`if not rare`) and the candidate filter
    (`any(n in rare for n in matched)`) each independently zero the
    result. Lifting only one ships a no-op that still returns "".
    """
    pa = _load_prior_art()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _common_noun_corpus(tmpdir, pa)
        new = fr_dir / "FR-999-retrieval-precedent.md"
        new.write_text("# FR-999\n", encoding="utf-8")

        out = pa.build_prior_art(new, rare_floor=False)

        assert out, "floor lifted but retrieval still empty"
        hits = [ln for ln in out.splitlines() if ln.startswith("  FR-")]
        assert len(hits) == pa.TOP_N, f"expected TOP_N hits, got {len(hits)}"
        assert all("[Approved]" in ln for ln in hits), "status tags lost"
        assert "retrieval" in out


def test_floor_lifted_preserves_self_exclusion_and_ranking() -> None:
    """AC-02: scoring, weighting and F3 self-exclusion survive the opt-out."""
    pa = _load_prior_art()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _common_noun_corpus(tmpdir, pa)
        # One file carries the query's rarer noun in its weighted zone.
        (fr_dir / "FR-800-precedent-only.md").write_text(
            "# FR-800 Precedent Only\n**Status:** Rejected\n"
            "## Summary\nPrecedent handling.\n",
            encoding="utf-8",
        )
        new = fr_dir / "FR-999-retrieval-precedent.md"
        new.write_text("# FR-999 retrieval precedent\nprecedent\n", encoding="utf-8")

        out = pa.build_prior_art(new, rare_floor=False)

        assert "FR-999" not in out, "F3 self-exclusion broken"
        hits = [ln for ln in out.splitlines() if ln.startswith("  FR-")]
        assert "FR-800-precedent-only.md" in hits[0], "IDF ranking lost"
        assert "[Rejected]" in hits[0], "status tag lost on top hit"


def test_no_noun_matches_any_file_returns_empty_even_unfloored() -> None:
    """AC-05 precondition: `none-retrieved` means a genuine zero, not a floor."""
    pa = _load_prior_art()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _common_noun_corpus(tmpdir, pa)
        new = fr_dir / "FR-999-xyzzy-plugh.md"
        new.write_text("# FR-999\n", encoding="utf-8")

        assert pa.build_prior_art(new, rare_floor=False) == ""
