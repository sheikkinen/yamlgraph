#!/usr/bin/env python3
"""FR-738: prior-art disposition gate + U-2 ranking + U-3 status.

Unmarked per parent convention (FR-737 F5). Judged pins witnessed:
F2 staged-blob divergence, F3 mechanical weight rule (filename/H1/
Summary = 2, body = 1, ties by match count then name), F5 judgement
companions inherit parent status, orphans excluded.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
CHECKS_DIR = HOOKS_ROOT / "scripts" / "checks"
GATE = CHECKS_DIR / "prior_art_gate.py"
GIT = shutil.which("git") or "git"


def _load_prior_art():
    spec = importlib.util.spec_from_file_location(
        "prior_art", CHECKS_DIR / "prior_art.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo_with_corpus(tmpdir: str, corpus: dict[str, str]) -> Path:
    """Init a git repo with committed corpus files under feature-requests/."""
    root = Path(tmpdir)
    fr_dir = root / "feature-requests"
    fr_dir.mkdir(parents=True, exist_ok=True)
    for name, content in corpus.items():
        (fr_dir / name).write_text(content, encoding="utf-8")
    subprocess.run([GIT, "init", "-q"], cwd=root, check=True)
    subprocess.run([GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [GIT, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "corpus"],
        cwd=root,
        check=True,
    )
    return root


def _run_gate(root: Path, *paths: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(GATE), *paths],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout + r.stderr


CORPUS = {
    "070-gui-web-playground.md": (
        "# FR-070 Web Playground\n**Status:** Rejected\nA web playground.\n"
    ),
    "FR-100-other.md": "# FR-100\n**Status:** Completed\nUnrelated.\n",
}


class TestGate:
    """AC-01 — the pre-commit floor."""

    def test_added_fr_with_hits_no_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_with_corpus(tmpdir, CORPUS)
            new = root / "feature-requests" / "FR-900-wasm-playground.md"
            new.write_text("# FR-900\nwasm playground\n", encoding="utf-8")
            subprocess.run([GIT, "add", str(new)], cwd=root, check=True)
            code, out = _run_gate(root, "feature-requests/FR-900-wasm-playground.md")
            assert code != 0
            assert "070-gui-web-playground.md" in out
            assert "Prior art" in out

    def test_added_fr_with_marker_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_with_corpus(tmpdir, CORPUS)
            new = root / "feature-requests" / "FR-900-wasm-playground.md"
            new.write_text(
                "# FR-900\n**Prior art:** FR-070 dispositioned.\nwasm playground\n",
                encoding="utf-8",
            )
            subprocess.run([GIT, "add", str(new)], cwd=root, check=True)
            code, _ = _run_gate(root, "feature-requests/FR-900-wasm-playground.md")
            assert code == 0

    def test_added_fr_without_hits_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_with_corpus(tmpdir, CORPUS)
            new = root / "feature-requests" / "FR-901-xylophone-quorum.md"
            new.write_text("# FR-901\nxylophone quorum\n", encoding="utf-8")
            subprocess.run([GIT, "add", str(new)], cwd=root, check=True)
            code, _ = _run_gate(root, "feature-requests/FR-901-xylophone-quorum.md")
            assert code == 0

    def test_modified_fr_never_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = dict(CORPUS)
            corpus["FR-902-wasm-playground.md"] = "# FR-902\nwasm playground\n"
            root = _repo_with_corpus(tmpdir, corpus)
            target = root / "feature-requests" / "FR-902-wasm-playground.md"
            target.write_text("# FR-902\nwasm playground edited\n", encoding="utf-8")
            subprocess.run([GIT, "add", str(target)], cwd=root, check=True)
            code, _ = _run_gate(root, "feature-requests/FR-902-wasm-playground.md")
            assert code == 0

    def test_staged_divergence_fails(self) -> None:
        """F2: marker added to the working tree AFTER git add must not pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_with_corpus(tmpdir, CORPUS)
            new = root / "feature-requests" / "FR-903-wasm-playground.md"
            new.write_text("# FR-903\nwasm playground\n", encoding="utf-8")
            subprocess.run([GIT, "add", str(new)], cwd=root, check=True)
            new.write_text(
                "# FR-903\n**Prior art:** added too late.\nwasm playground\n",
                encoding="utf-8",
            )  # not re-staged
            code, _ = _run_gate(root, "feature-requests/FR-903-wasm-playground.md")
            assert code != 0


class TestRankingWeights:
    """AC-02 — F3's mechanical weight rule."""

    def test_title_match_outranks_body_prose(self) -> None:
        pa = _load_prior_art()
        with tempfile.TemporaryDirectory() as tmpdir:
            fr_dir = Path(tmpdir) / "feature-requests"
            fr_dir.mkdir(parents=True)
            (fr_dir / "FR-500-other-name.md").write_text(
                "# Zephyr engine\n**Status:** Completed\ncontent\n", encoding="utf-8"
            )
            (fr_dir / "FR-501-misc.md").write_text(
                "# FR-501\n**Status:** Completed\nzephyr in passing prose\n",
                encoding="utf-8",
            )
            new = fr_dir / "FR-904-zephyr.md"
            new.write_text("zephyr\n", encoding="utf-8")
            out = pa.build_prior_art(new)
            lines = [ln for ln in out.splitlines() if ln.startswith("  ")]
            assert "FR-500-other-name.md" in lines[0]

    def test_score_tie_breaks_by_match_count(self) -> None:
        pa = _load_prior_art()
        with tempfile.TemporaryDirectory() as tmpdir:
            fr_dir = Path(tmpdir) / "feature-requests"
            fr_dir.mkdir(parents=True)
            # X matches alpha(freq2)+beta(freq2) in body: 0.5+0.5 = 1.0
            (fr_dir / "FR-200-x.md").write_text(
                "# FR-200\n**Status:** Completed\nzalpha zbeta\n", encoding="utf-8"
            )
            # Y matches zgamma(freq1) in body: 1/1 = 1.0 — tie, fewer matches
            (fr_dir / "FR-100-y.md").write_text(
                "# FR-100\n**Status:** Completed\nzgamma\n", encoding="utf-8"
            )
            (fr_dir / "FR-300-fill1.md").write_text(
                "# FR-300\n**Status:** Completed\nzalpha\n", encoding="utf-8"
            )
            (fr_dir / "FR-301-fill2.md").write_text(
                "# FR-301\n**Status:** Completed\nzbeta\n", encoding="utf-8"
            )
            new = fr_dir / "FR-905-zalpha-zbeta-zgamma.md"
            new.write_text("new\n", encoding="utf-8")
            out = pa.build_prior_art(new)
            lines = [ln for ln in out.splitlines() if ln.startswith("  ")]
            # X (2 matched nouns) beats Y (1) despite Y's earlier name.
            x_pos = next(i for i, ln in enumerate(lines) if "FR-200-x.md" in ln)
            y_pos = next(i for i, ln in enumerate(lines) if "FR-100-y.md" in ln)
            assert x_pos < y_pos


class TestJudgementCompanions:
    """AC-03 — F5's one mechanism."""

    def test_companion_inherits_parent_status(self) -> None:
        pa = _load_prior_art()
        with tempfile.TemporaryDirectory() as tmpdir:
            fr_dir = Path(tmpdir) / "feature-requests"
            fr_dir.mkdir(parents=True)
            (fr_dir / "FR-600-zeta.md").write_text(
                "# FR-600\n**Status:** Rejected\nzeta\n", encoding="utf-8"
            )
            (fr_dir / "FR-600-zeta.judgement.md").write_text(
                "judgement of zeta\n", encoding="utf-8"
            )
            new = fr_dir / "FR-906-zeta.md"
            new.write_text("zeta\n", encoding="utf-8")
            out = pa.build_prior_art(new)
            companion = [
                ln for ln in out.splitlines() if "FR-600-zeta.judgement.md" in ln
            ]
            assert companion, f"companion missing from: {out!r}"
            assert "[REJECTED]" in companion[0]
            assert "[?]" not in out

    def test_orphan_judgement_excluded(self) -> None:
        pa = _load_prior_art()
        with tempfile.TemporaryDirectory() as tmpdir:
            fr_dir = Path(tmpdir) / "feature-requests"
            fr_dir.mkdir(parents=True)
            (fr_dir / "FR-601-orphan.judgement.md").write_text(
                "orphaned zeta judgement\n", encoding="utf-8"
            )
            new = fr_dir / "FR-907-zeta.md"
            new.write_text("zeta\n", encoding="utf-8")
            out = pa.build_prior_art(new)
            assert out == ""


def test_gate_output_is_json_free() -> None:
    """The gate speaks to a terminal, not the hook harness — plain text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _repo_with_corpus(tmpdir, CORPUS)
        new = root / "feature-requests" / "FR-908-wasm-playground.md"
        new.write_text("# FR-908\nwasm playground\n", encoding="utf-8")
        subprocess.run([GIT, "add", str(new)], cwd=root, check=True)
        _, out = _run_gate(root, "feature-requests/FR-908-wasm-playground.md")
        try:
            json.loads(out)
            raise AssertionError("gate output should not be JSON")
        except (ValueError, json.JSONDecodeError):
            pass
