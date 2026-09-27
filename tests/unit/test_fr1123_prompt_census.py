"""FR-1123 AC-08: no committed prompt schema carries an untyped subschema.

The census walks every prompt YAML with an output schema under ``examples/``,
``graphs/`` and ``.github/``; the twelve R-4 migrations are pinned by type.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yamlgraph.schema_loader import load_schema_from_yaml
from yamlgraph.utils.schema_walk import find_untyped_subschemas

pytestmark = pytest.mark.process

ROOT = Path(__file__).resolve().parents[2]
CENSUS_ROOTS = ("examples", "graphs", ".github")


def committed_prompt_schemas() -> list[Path]:
    found = []
    for root in CENSUS_ROOTS:
        for path in sorted((ROOT / root).rglob("*.yaml")):
            if "prompts" not in path.relative_to(ROOT).parts:
                continue
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and (
                isinstance(doc.get("schema"), dict) or "output_schema" in doc
            ):
                found.append(path)
    return found


@pytest.mark.req("REQ-YG-712")
def test_ac08_census_is_nonempty_and_clean() -> None:
    paths = committed_prompt_schemas()
    assert len(paths) > 50
    offenders = {
        str(p.relative_to(ROOT)): hits
        for p in paths
        if (
            hits := find_untyped_subschemas(
                load_schema_from_yaml(p).model_json_schema()
            )
        )
    }
    assert offenders == {}


# FR-1123 R-4 pinned twelve migrations by `fields` type. FR-1125 found that
# `list[dict]`/`dict` are hollowed by Anthropic constrained decoding and
# retyped the Anthropic-bound rows to the `output_schema` form with declared
# item properties (ledger docs/issues-2026-09-27-fr1125-census.md). The three
# codegen rows run on mistral and keep their `fields` types.
R4_FIELDS = {
    ("codegen", "plan_discovery", "tasks"): "list[dict]",
    ("codegen", "synthesize", "target_files"): "list[dict]",
    ("codegen", "synthesize", "dependencies"): "list[str]",
    ("codegen", "synthesize", "test_coverage"): "dict",
    ("codegen", "synthesize", "patterns_to_follow"): "list[str]",
}
R4_DECLARED = {
    ("daily_digest", "rank_stories", "stories"): [
        "title",
        "url",
        "summary",
        "relevance",
        "reason",
    ],
    ("book_translator", "extract_terms", "terms"): [
        "source_term",
        "translation",
        "context",
        "importance",
    ],
    ("book_translator", "identify_chapters", "markers"): [
        "marker",
        "title",
        "estimated_size",
    ],
    ("book_translator", "translate_chunk", "difficult_passages"): ["original", "issue"],
    ("yamlgraph_gen", "generate_tools", "tools"): [
        "filename",
        "content",
        "tool_name",
        "description",
    ],
    ("yamlgraph_gen", "assemble_graph", "node_list"): ["name", "type", "prompt_path"],
    ("yamlgraph_gen", "generate_prompts", "prompts"): [
        "filename",
        "content",
        "explanation",
    ],
}


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize(("where", "expected"), sorted(R4_FIELDS.items()))
def test_ac08_r4_migration_types(where: tuple[str, str, str], expected: str) -> None:
    example, prompt, field = where
    doc = yaml.safe_load(
        (ROOT / "examples" / example / "prompts" / f"{prompt}.yaml").read_text(
            encoding="utf-8"
        )
    )
    field_def = doc["schema"]["fields"][field]
    assert field_def["type"] == expected
    assert "Any" not in field_def["type"]


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize(("where", "expected"), sorted(R4_DECLARED.items()))
def test_ac08_r4_declared_properties(
    where: tuple[str, str, str], expected: list[str]
) -> None:
    """FR-1125: the Anthropic-bound rows declare their item properties (no open object)."""
    example, prompt, field = where
    doc = yaml.safe_load(
        (ROOT / "examples" / example / "prompts" / f"{prompt}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert "schema" not in doc, "the fields form cannot declare item properties"
    prop = doc["output_schema"]["properties"][field]
    items = prop["items"] if prop.get("type") == "array" else prop
    assert sorted(items["properties"]) == sorted(expected)
    assert sorted(items.get("required", [])) == sorted(expected)
