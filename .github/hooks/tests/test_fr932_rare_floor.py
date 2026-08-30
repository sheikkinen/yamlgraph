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
import subprocess
import sys
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
        # Same two nouns as the FR-500 block, but both in the weighted zone.
        (fr_dir / "FR-800-precedent-only.md").write_text(
            "# FR-800 retrieval precedent\n**Status:** Rejected\n"
            "## Summary\nretrieval precedent handling.\n",
            encoding="utf-8",
        )
        new = fr_dir / "FR-999-retrieval-precedent.md"
        new.write_text("# FR-999 retrieval precedent\nprecedent\n", encoding="utf-8")

        out = pa.build_prior_art(new, rare_floor=False)

        hits = [ln for ln in out.splitlines() if ln.startswith("  FR-")]
        assert not any("FR-999" in ln for ln in hits), "F3 self-exclusion broken"
        assert "FR-800-precedent-only.md" in hits[0], "_weighted_zone ranking lost"
        assert "[REJECTED]" in hits[0], "status tag lost on top hit"


def test_no_noun_matches_any_file_returns_empty_even_unfloored() -> None:
    """AC-05 precondition: `none-retrieved` means a genuine zero, not a floor."""
    pa = _load_prior_art()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _common_noun_corpus(tmpdir, pa)
        new = fr_dir / "FR-999-xyzzy-plugh.md"
        new.write_text("# FR-999\n", encoding="utf-8")

        assert pa.build_prior_art(new, rare_floor=False) == ""


def test_module_runs_without_pyyaml_installed() -> None:
    """AC-01 blocker: the hook invokes this with system python3 and

    swallows stderr (`2>/dev/null || true` in fr-checks.sh). A module-scope
    `import yaml` therefore kills the whole notification hook silently on
    any interpreter without PyYAML. The FR-814 graph is an optional
    augmentation and must degrade, not abort.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        fr_dir.mkdir(parents=True, exist_ok=True)
        (fr_dir / "070-gui-web-playground.md").write_text(
            "# FR-070 Web Playground\n**Status:** Rejected\nA web playground.\n",
            encoding="utf-8",
        )
        new = fr_dir / "FR-900-wasm-playground-runtime.md"
        new.write_text("# FR-900\nA wasm playground runtime.\n", encoding="utf-8")

        # Hide PyYAML the way a bare system interpreter does.
        script = (
            "import sys\n"
            "sys.meta_path.insert(0, type('B', (), {"
            "'find_module': lambda s, n, p=None: None,"
            "'find_spec': lambda s, n, p=None, t=None: "
            "(_ for _ in ()).throw(ImportError(n)) if n == 'yaml' else None})())\n"
            "import importlib.util\n"
            f"spec = importlib.util.spec_from_file_location('pa', {str(CHECKS_DIR / 'prior_art.py')!r})\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(m)\n"
            "from pathlib import Path\n"
            f"print(m.build_prior_art(Path({str(new)!r})))\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, f"module aborted without PyYAML: {proc.stderr}"
        assert "070-gui-web-playground.md" in proc.stdout
