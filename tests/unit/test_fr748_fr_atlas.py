"""FR-748 RED witness: FR Atlas — the deterministic spine (REQ-YG-566).

Condemns the collector (id = filename stem, never a prefix regex —
F2: the unprefixed elders ARE the graveyard; companion exclusion F4;
headerless files reported not dropped), the chunker (every id exactly
once across chunks), the status normalization (verbatim + first-word
bucket + visible other, F3), the coverage post-pass (count-in ==
count-out; unknown id raises; unassigned ids land in misc — the recap
FR-703/704 silent-join-drop lesson), and the graveyard render (a
rejected FR appears with its verbatim status line).
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "demos" / "fr-atlas"


def _load(module_filename: str):
    path = EXAMPLE / "nodes" / module_filename
    assert path.exists(), f"FR-748 module missing: {path}"
    name = f"fr748_{module_filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _corpus(tmp_path: Path) -> Path:
    fr_dir = tmp_path / "feature-requests"
    fr_dir.mkdir(parents=True)
    (fr_dir / "FR-001-span-alignment.md").write_text(
        "# FR-001: Span alignment\n\n**Status:** Implemented (2026-01-01)\n\n"
        "## Problem\n\nSpans drift and fabrications pass unchecked.\n"
    )
    # F2: unprefixed elder — id must be the filename stem.
    (fr_dir / "070-gui-web-playground.md").write_text(
        "# 070: GUI web playground\n\n**Status:** Rejected — no UI, ever.\n\n"
        "## Problem\n\nPeople want a playground.\n"
    )
    # Headerless: reported, never dropped.
    (fr_dir / "FR-002-headerless.md").write_text(
        "# FR-002: Headerless\n\n## Problem\n\nNo status header here.\n"
    )
    # F4: companions excluded, not invisible.
    (fr_dir / "TEMPLATE.md").write_text("# Template\n\n**Status:** n/a\n")
    (fr_dir / "FR-001-span-alignment.judgement.md").write_text("# Judgement\n")
    return tmp_path


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class TestCollector:
    @pytest.mark.req("REQ-YG-566")
    def test_population_ids_are_filename_stems(self, tmp_path):
        collect = _load("collect.py")
        out = collect.collect_frs({"project_dir": str(_corpus(tmp_path))})
        ids = {d["id"] for d in out["fr_digests"]}
        assert ids == {
            "FR-001-span-alignment",
            "070-gui-web-playground",
            "FR-002-headerless",
        }, "unprefixed elders and headerless files are population members"

    @pytest.mark.req("REQ-YG-566")
    def test_companions_excluded_not_invisible(self, tmp_path):
        collect = _load("collect.py")
        out = collect.collect_frs({"project_dir": str(_corpus(tmp_path))})
        notes = out["parse_notes"]
        assert notes["excluded"] == 2  # TEMPLATE.md + *.judgement.md
        assert notes["headerless"] == ["FR-002-headerless"]

    @pytest.mark.req("REQ-YG-566")
    def test_digest_carries_verbatim_status_and_problem_excerpt(self, tmp_path):
        collect = _load("collect.py")
        out = collect.collect_frs({"project_dir": str(_corpus(tmp_path))})
        by_id = {d["id"]: d for d in out["fr_digests"]}
        rejected = by_id["070-gui-web-playground"]
        assert rejected["status"] == "Rejected — no UI, ever."
        assert rejected["status_bucket"] == "rejected"
        assert "playground" in rejected["excerpt"]
        assert by_id["FR-002-headerless"]["status_bucket"] == "other"

    @pytest.mark.req("REQ-YG-566")
    def test_missing_corpus_actionable_error(self, tmp_path):
        collect = _load("collect.py")
        with pytest.raises(FileNotFoundError, match="feature-requests"):
            collect.collect_frs({"project_dir": str(tmp_path / "nowhere")})


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------


class TestChunker:
    @pytest.mark.req("REQ-YG-566")
    def test_every_id_exactly_once_across_chunks(self, tmp_path):
        collect = _load("collect.py")
        digests = [
            {
                "id": f"FR-{i:03d}-x",
                "title": "t",
                "status": "Proposed",
                "status_bucket": "proposed",
                "excerpt": "e",
            }
            for i in range(120)
        ]
        chunks = collect.chunk_digests(digests, size=50)
        assert [len(c["ids"]) for c in chunks] == [50, 50, 20]
        seen = [i for c in chunks for i in c["ids"]]
        assert len(seen) == len(set(seen)) == 120
        assert "FR-000-x" in chunks[0]["digest_block"]


# ---------------------------------------------------------------------------
# Coverage post-pass (the honesty spine)
# ---------------------------------------------------------------------------

_POPULATION = ["FR-001-a", "FR-002-b", "070-old"]


class TestCoverage:
    @pytest.mark.req("REQ-YG-566")
    def test_unassigned_ids_land_in_misc_and_counts_match(self, tmp_path):
        coverage = _load("coverage.py")
        themes = [{"name": "Boundaries", "arc": "spans", "fr_ids": ["FR-001-a"]}]
        out = coverage.enforce_coverage(themes, _POPULATION)
        misc = next(t for t in out if t["name"] == "misc")
        assert set(misc["fr_ids"]) == {"FR-002-b", "070-old"}
        assert sum(len(t["fr_ids"]) for t in out) == len(_POPULATION)

    @pytest.mark.req("REQ-YG-566")
    def test_unknown_id_raises(self, tmp_path):
        coverage = _load("coverage.py")
        themes = [{"name": "X", "arc": "a", "fr_ids": ["FR-999-invented"]}]
        with pytest.raises(ValueError, match="unknown"):
            coverage.enforce_coverage(themes, _POPULATION)

    @pytest.mark.req("REQ-YG-566")
    def test_duplicate_assignment_keeps_first_and_counts_hold(self, tmp_path):
        coverage = _load("coverage.py")
        themes = [
            {"name": "A", "arc": "a", "fr_ids": ["FR-001-a", "FR-002-b"]},
            {"name": "B", "arc": "b", "fr_ids": ["FR-001-a", "070-old"]},
        ]
        out = coverage.enforce_coverage(themes, _POPULATION)
        assert sum(len(t["fr_ids"]) for t in out) == len(_POPULATION)
        assert "FR-001-a" in next(t for t in out if t["name"] == "A")["fr_ids"]
        assert "FR-001-a" not in next(t for t in out if t["name"] == "B")["fr_ids"]


# ---------------------------------------------------------------------------
# Render: graveyard presence
# ---------------------------------------------------------------------------


class TestRender:
    @pytest.mark.req("REQ-YG-566")
    def test_graveyard_lists_rejected_with_verbatim_status(self, tmp_path):
        render = _load("render.py")
        digests = [
            {
                "id": "070-gui-web-playground",
                "title": "GUI web playground",
                "status": "Rejected — no UI, ever.",
                "status_bucket": "rejected",
                "excerpt": "x",
                "last_activity": "2026-02-21",
            },
            {
                "id": "FR-001-a",
                "title": "A",
                "status": "Implemented",
                "status_bucket": "implemented",
                "excerpt": "x",
                "last_activity": "2026-07-01",
            },
        ]
        themes = [
            {
                "name": "UI",
                "arc": "arc",
                "fr_ids": ["070-gui-web-playground", "FR-001-a"],
                "modules": [],
            }
        ]
        text = render.render_atlas(
            story="p1\n\np2\n\np3",
            themes=themes,
            digests=digests,
            parse_notes={"excluded": 0, "headerless": []},
            project_name="demo",
        )
        assert "## Graveyard" in text
        assert "no UI, ever" in text
        gy = text[text.index("## Graveyard") :]
        assert "FR-001-a" not in gy, "non-rejected FRs stay out of the graveyard"
