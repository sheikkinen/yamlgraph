#!/usr/bin/env python3
"""FR-737: graveyard hook — prior-art retrieval on FR creation.

Unmarked per FR-737 F5 (follows test_fr_checks.py's own convention).
Pins witnessed: IDF ranking (F1), rare-noun floor ≤20 files / silence
otherwise (F2+A1), self-exclusion (F3), tracked-file skip (trigger),
stopword/prefix noun extraction.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from conftest import make_payload, run_hook

REPO_ROOT = Path(__file__).resolve().parents[3]


def _fr_dir(tmpdir: str) -> Path:
    d = Path(tmpdir) / "feature-requests"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _msg(out: str) -> str:
    return json.loads(out).get("systemMessage", "") if out else ""


def test_new_fr_with_rejected_prior_art_warns() -> None:
    """AC-01: rejected-FR noun overlap emits the block with status tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        (fr_dir / "070-gui-web-playground.md").write_text(
            "# FR-070 Web Playground\n**Status:** Rejected\n"
            "A web playground for graphs.\n",
            encoding="utf-8",
        )
        (fr_dir / "FR-100-other-thing.md").write_text(
            "# FR-100\n**Status:** Completed\nUnrelated content.\n",
            encoding="utf-8",
        )
        new_fr = fr_dir / "FR-900-wasm-playground-runtime.md"
        new_fr.write_text("# FR-900\nA wasm playground runtime.\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        msg = _msg(out)
        assert "prior art" in msg.lower()
        assert "070-gui-web-playground.md" in msg
        assert "REJECTED" in msg


def test_tracked_fr_edit_is_silent() -> None:
    """Trigger pin: files already in git ls-files never re-nag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        (fr_dir / "070-gui-web-playground.md").write_text(
            "**Status:** Rejected\nplayground\n", encoding="utf-8"
        )
        tracked = fr_dir / "FR-901-wasm-playground.md"
        tracked.write_text("wasm playground\n", encoding="utf-8")
        git = shutil.which("git") or "git"
        subprocess.run([git, "init", "-q"], cwd=tmpdir, check=True)
        subprocess.run([git, "add", "-A"], cwd=tmpdir, check=True)

        code, out = run_hook(
            "fr-checks.sh", make_payload("replace_string_in_file", str(tracked))
        )
        assert code == 0
        assert "prior art" not in _msg(out).lower()


def test_stopword_only_filename_is_silent() -> None:
    """Noun extraction drops prefixes and stopwords; nothing left = silence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        (fr_dir / "FR-100-fix-add-support.md").write_text(
            "**Status:** Completed\nfix add support\n", encoding="utf-8"
        )
        new_fr = fr_dir / "FR-902-add-fix-support.md"
        new_fr.write_text("adds fix support\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        assert "prior art" not in _msg(out).lower()


def test_common_noun_emits_nothing_a1_spike_witness() -> None:
    """A1: a noun in >20 corpus files is not rare; no rare noun = silence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        for i in range(25):
            (fr_dir / f"FR-{100 + i}-spike-old-{i}.md").write_text(
                f"**Status:** Completed\nspike number {i}\n", encoding="utf-8"
            )
        new_fr = fr_dir / "FR-903-spike.md"
        new_fr.write_text("another spike\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        assert "prior art" not in _msg(out).lower()


def test_new_file_never_a_candidate() -> None:
    """F3: the created file's own body must not surface as prior art."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        new_fr = fr_dir / "FR-904-quantum-teleport.md"
        new_fr.write_text("quantum teleport quantum teleport\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        assert "prior art" not in _msg(out).lower()


def test_idf_ranking_rare_noun_first() -> None:
    """F1: one rare noun (freq 1) outranks a generic one (freq 10)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = _fr_dir(tmpdir)
        (fr_dir / "FR-200-flux-capacitor.md").write_text(
            "**Status:** Rejected\nflux capacitor design\n", encoding="utf-8"
        )
        for i in range(10):
            (fr_dir / f"FR-{300 + i}-widget-{i}.md").write_text(
                f"**Status:** Completed\nwidget iteration {i}\n", encoding="utf-8"
            )
        new_fr = fr_dir / "FR-905-flux-widget.md"
        new_fr.write_text("flux widget\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        msg = _msg(out)
        assert "prior art" in msg.lower()
        lines = [ln for ln in msg.splitlines() if ".md" in ln and "File:" not in ln]
        assert lines, f"no candidate lines in: {msg!r}"
        assert "FR-200-flux-capacitor.md" in lines[0]


def test_counterfactual_fr070_surfaces_on_real_corpus() -> None:
    """AC-02 witness: replaying the motivating incident on a copy of the
    real corpus surfaces 070-gui-web-playground.md [REJECTED] in top 5."""
    real_corpus = REPO_ROOT / "feature-requests"
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        shutil.copytree(real_corpus, fr_dir)
        new_fr = fr_dir / "FR-999-pyodide-playground.md"
        new_fr.write_text("A pyodide playground page.\n", encoding="utf-8")

        code, out = run_hook("fr-checks.sh", make_payload("create_file", str(new_fr)))
        assert code == 0
        msg = _msg(out)
        assert "070-gui-web-playground.md" in msg
        assert "REJECTED" in msg
