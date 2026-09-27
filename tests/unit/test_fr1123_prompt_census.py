"""FR-1123 AC-08: no committed prompt schema carries an untyped subschema.

The census walks every prompt YAML with an output schema under ``examples/``,
``graphs/`` and ``.github/``; the twelve R-4 migrations are pinned by type.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from yamlgraph.utils.schema_walk import find_untyped_subschemas

from yamlgraph.schema_loader import load_schema_from_yaml

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


R4 = {
    ("daily_digest", "rank_stories", "stories"): "list[dict]",
    ("book_translator", "extract_terms", "terms"): "list[dict]",
    ("book_translator", "identify_chapters", "markers"): "list[dict]",
    ("book_translator", "translate_chunk", "difficult_passages"): "list[dict]",
    ("yamlgraph_gen", "generate_tools", "tools"): "list[dict]",
    ("yamlgraph_gen", "assemble_graph", "node_list"): "list[dict]",
    ("yamlgraph_gen", "generate_prompts", "prompts"): "list[dict]",
    ("codegen", "plan_discovery", "tasks"): "list[dict]",
    ("codegen", "synthesize", "target_files"): "list[dict]",
    ("codegen", "synthesize", "dependencies"): "list[str]",
    ("codegen", "synthesize", "test_coverage"): "dict",
    ("codegen", "synthesize", "patterns_to_follow"): "list[str]",
}


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize(("where", "expected"), sorted(R4.items()))
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
