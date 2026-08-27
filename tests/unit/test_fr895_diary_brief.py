"""FR-895 D-5/AC-07 witnesses: diary brief step + top-finding check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.demos.corpus_census.adapters import census_brief, diary_recurrence

pytestmark = pytest.mark.process

CANDIDATES = [
    {
        "label": "alias_of_doctrine",
        "entries": 12,
        "citations": ["docs/diary/a.md", "docs/diary/b.md"],
        "first_seen": "2026-01-01",
        "last_seen": "2026-08-01",
    },
    {
        "label": "stale_msg_file",
        "entries": 5,
        "citations": ["docs/diary/c.md"],
        "first_seen": "2026-02-01",
        "last_seen": "2026-07-01",
    },
]


def _claims(citations: list[str]) -> list[dict]:
    return [
        {
            "claim_id": "c1",
            "text": "Top finding.",
            "citations": citations,
            "confidence": 0.9,
        }
    ]


@pytest.mark.req("REQ-YG-625")
def test_top_finding_cited_accepts_family_match():
    claims = _claims(["label:alias_of_doctrine"])
    assert census_brief.top_finding_cited(claims, CANDIDATES) is True


@pytest.mark.req("REQ-YG-625")
def test_top_finding_cited_rejects_when_headline_uncited():
    claims = _claims(["label:stale_msg_file"])
    assert census_brief.top_finding_cited(claims, CANDIDATES) is False


@pytest.mark.req("REQ-YG-625")
def test_emit_diary_brief_writes_accepted_brief(tmp_path: Path):
    brief_path = tmp_path / "brief-2026-08-27.md"

    def fake_synthesize(rows: list[dict], rubric: str) -> list[dict]:
        assert all(set(r) <= set(census_brief.ALLOWED_INPUT_COLUMNS) for r in rows)
        return _claims(["label:alias_of_doctrine"])

    result = diary_recurrence.emit_diary_brief(
        CANDIDATES,
        str(brief_path),
        "what recurs?",
        run_meta={"model": "test"},
        synthesize_fn=fake_synthesize,
    )
    assert result["accepted"] is True
    assert result["top_finding_cited"] is True
    text = brief_path.read_text(encoding="utf-8")
    assert "## Findings" in text


@pytest.mark.req("REQ-YG-625")
def test_emit_diary_brief_fails_closed_on_fabricated_citation(tmp_path: Path):
    brief_path = tmp_path / "brief-2026-08-27.md"

    def fake_synthesize(rows: list[dict], rubric: str) -> list[dict]:
        return _claims(["label:invented_trap"])

    result = diary_recurrence.emit_diary_brief(
        CANDIDATES,
        str(brief_path),
        "what recurs?",
        run_meta={},
        synthesize_fn=fake_synthesize,
    )
    assert result["accepted"] is False
    assert not brief_path.exists()
    rejected = brief_path.with_name(brief_path.stem + ".REJECTED.md")
    assert rejected.exists()


@pytest.mark.req("REQ-YG-625")
def test_emit_diary_brief_flags_uncited_headline(tmp_path: Path):
    brief_path = tmp_path / "brief.md"

    def fake_synthesize(rows: list[dict], rubric: str) -> list[dict]:
        return _claims(["label:stale_msg_file"])

    result = diary_recurrence.emit_diary_brief(
        CANDIDATES,
        str(brief_path),
        "what recurs?",
        run_meta={},
        synthesize_fn=fake_synthesize,
    )
    assert result["accepted"] is True
    assert result["top_finding_cited"] is False


@pytest.mark.req("REQ-YG-625")
def test_synthesize_prompt_schema_builds_output_model():
    """Regression: direct execute_prompt calls need the inline schema
    materialized as output_model — first census run returned raw str."""
    from pathlib import Path

    from yamlgraph.schema_loader import load_schema_from_yaml

    prompt = Path("examples/demos/corpus_census/prompts") / "synthesize_brief.yaml"
    model = load_schema_from_yaml(prompt)
    assert model is not None
    assert "claims" in model.model_fields


@pytest.mark.req("REQ-YG-625")
def test_diary_brief_input_is_public_safe(tmp_path: Path):
    dirty = [dict(CANDIDATES[0], evidence_span="RAW SECRET TEXT")]
    seen: list[list[dict]] = []

    def fake_synthesize(rows: list[dict], rubric: str) -> list[dict]:
        seen.append(rows)
        return _claims(["label:alias_of_doctrine"])

    diary_recurrence.emit_diary_brief(
        dirty,
        str(tmp_path / "b.md"),
        "r",
        run_meta={},
        synthesize_fn=fake_synthesize,
    )
    assert seen and all("evidence_span" not in r for r in seen[0])
    assert "RAW SECRET TEXT" not in json.dumps(seen)
