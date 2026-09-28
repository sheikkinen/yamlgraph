#!/usr/bin/env python3
"""FR-1134: prior-art output for FR ids above FR-819 is fixed by value.

The FR knowledge graph ends at FR-819, so its cluster boost and tag
never fired for these ids. The literal below was captured with the graph
still loaded; it must hold unchanged after the graph is retired.
Unmarked, following the FR-737 F5 convention of this directory.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = HOOKS_ROOT.parents[1]
CHECKS_DIR = HOOKS_ROOT / "scripts" / "checks"

CORPUS = {
    "FR-2001-ledger-census-gate.md": "**Status:** Approved\nLedger census gate.\n",
    "FR-2002-ledger-rollup.md": "**Status:** Proposed\nA ledger rollup.\n",
    "FR-2003-census-sampling.md": "**Status:** Implemented\nCensus sampling.\n",
    "FR-2004-unrelated-voice.md": "**Status:** Approved\nVoice pipeline.\n",
}

EXPECTED = (
    "⚠ prior art for FR-2010-ledger-census-drift.md (nouns: ledger, census, drift):\n"
    "  FR-2001-ledger-census-gate.md  [Approved]  matches: ledger, census\n"
    "  FR-2002-ledger-rollup.md  [Proposed]  matches: ledger\n"
    "  FR-2003-census-sampling.md  [Implemented]  matches: census\n"
    "Disposition required in the FR or its judgement (Scripture: Judge step).\n"
)


def _load_prior_art():
    spec = importlib.util.spec_from_file_location(
        "prior_art", CHECKS_DIR / "prior_art.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_output_above_fr819_is_unchanged() -> None:
    pa = _load_prior_art()
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        fr_dir.mkdir()
        for name, body in CORPUS.items():
            (fr_dir / name).write_text(f"# {name}\n{body}", encoding="utf-8")
        new = fr_dir / "FR-2010-ledger-census-drift.md"
        new.write_text("# FR-2010\n", encoding="utf-8")
        os.chdir(REPO_ROOT)  # the retired graph was read relative to cwd
        try:
            out = pa.build_prior_art(new)
        finally:
            os.chdir(cwd)

    assert out == EXPECTED
