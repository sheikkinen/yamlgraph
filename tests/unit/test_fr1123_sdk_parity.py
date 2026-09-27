"""FR-1123 AC-07: the walker agrees with Anthropic's strict transform.

The ONLY module that imports the SDK's private ``transform_schema``. Parity is
limited to the missing-keyword rejection (judgement R-3): any other SDK error
propagates from the oracle instead of being folded into the comparison.
"""

from __future__ import annotations

import pytest

from tests.unit.test_fr1123_prompt_census import ROOT, committed_prompt_schemas
from tests.unit.test_fr1123_untyped_subschema import _model
from yamlgraph.schema_loader import load_schema_from_yaml
from yamlgraph.utils.schema_walk import find_untyped_subschemas

transform = pytest.importorskip("anthropic.lib._parse._transform")

pytestmark = [pytest.mark.slow, pytest.mark.process]

MISSING_KEYWORD = "Schema must have a 'type', 'anyOf', 'oneOf', or 'allOf' field."


def sdk_rejects_untyped(schema: dict) -> bool:
    try:
        transform.transform_schema(schema)
    except ValueError as err:
        if str(err) == MISSING_KEYWORD:
            return True
        raise
    return False


_NESTED = [
    {
        "type": "object",
        "properties": {"a": {"type": "object", "properties": {"b": {}}}},
    },
    {"type": "object", "properties": {"c": {"anyOf": [{}, {"type": "null"}]}}},
    {"type": "object", "properties": {"c": {"oneOf": [{"type": "string"}, {}]}}},
    {"type": "object", "properties": {"c": {"allOf": [{}]}}},
    {
        "type": "object",
        "properties": {"c": {"anyOf": [{"type": "string"}], "oneOf": [{}]}},
    },
    {
        "$defs": {"Item": {"type": "object", "properties": {"v": {}}}},
        "type": "object",
        "properties": {"i": {"$ref": "#/$defs/Item"}},
    },
    {"type": "object", "properties": {"r": {"$ref": "#/$defs/X"}}},
    {"type": "object", "properties": {"p": {"type": "array", "prefixItems": [{}]}}},
    {
        "type": "object",
        "properties": {
            "d": {
                "type": "object",
                "additionalProperties": {"type": "array", "items": {}},
            }
        },
    },
]


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize(
    "field_type", ["Any", "list[Any]", "dict", "list[dict]", "list[str]"]
)
def test_ac07_parity_five_rows(field_type: str) -> None:
    schema = _model(field_type).model_json_schema()
    assert sdk_rejects_untyped(schema) == bool(find_untyped_subschemas(schema))


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize("schema", _NESTED)
def test_ac07_parity_nested(schema: dict) -> None:
    assert sdk_rejects_untyped(schema) == bool(find_untyped_subschemas(schema))


@pytest.mark.req("REQ-YG-712")
def test_ac07_parity_committed_census() -> None:
    mismatches = []
    for path in committed_prompt_schemas():
        schema = load_schema_from_yaml(path).model_json_schema()
        if sdk_rejects_untyped(schema) != bool(find_untyped_subschemas(schema)):
            mismatches.append(str(path.relative_to(ROOT)))
    assert mismatches == []


@pytest.mark.req("REQ-YG-712")
def test_ac07_private_sdk_import_lives_in_one_test_module() -> None:
    needle = "anthropic.lib._parse"
    hits = sorted(
        str(p.relative_to(ROOT))
        for top in ("yamlgraph", "tests")
        for p in (ROOT / top).rglob("*.py")
        if needle in p.read_text(encoding="utf-8")
    )
    assert hits == ["tests/unit/test_fr1123_sdk_parity.py"]
