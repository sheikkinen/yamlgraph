"""FR-1123 AC-07: the walker agrees with Anthropic's strict transform.

The ONLY module that imports the SDK's private ``transform_schema``. Parity is
limited to the missing-keyword rejection (judgement R-3): any other SDK error
propagates from the oracle instead of being folded into the comparison.
"""

from __future__ import annotations

import copy

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


# FR-1125 AC-07: content parity — what the transform PRODUCES, not only whether it raises.
# Canonical concrete-object paths: $defs under "$defs.<name>", $ref is a stop, compositions
# branch as "<kw>[i]", then properties and items. Never dereference a $ref into a second path.

HOLLOW = {"type": "object", "properties": {}, "additionalProperties": False}


def _concrete_objects(
    schema: dict, path: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], dict]]:
    out: list[tuple[tuple[str, ...], dict]] = []
    for name, sub in (schema.get("$defs") or {}).items():
        out += _concrete_objects(sub, (*path, "$defs", name))
    if "$ref" in schema:
        return out
    for kw in ("anyOf", "oneOf", "allOf"):
        variants = schema.get(kw)
        if isinstance(variants, list):
            for i, v in enumerate(variants):
                out += _concrete_objects(v, (*path, f"{kw}[{i}]"))
            return out
    if schema.get("type") == "object":
        out.append((path, schema))
        for key, sub in (schema.get("properties") or {}).items():
            out += _concrete_objects(sub, (*path, key))
    elif schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        out += _concrete_objects(schema["items"], (*path, "items"))
    return out


def _at(node: dict, path: tuple[str, ...]) -> dict:
    for segment in path:
        if segment == "$defs":
            node = node["$defs"]
            continue
        if segment == "items":
            node = node["items"]
            continue
        if segment[-1] == "]" and "[" in segment:
            kw, idx = segment[:-1].split("[")
            node = node[kw][int(idx)]
            continue
        # a $defs name or a property name: whichever the current node carries
        if "properties" in node and segment in node["properties"]:
            node = node["properties"][segment]
        else:
            node = node[segment]
    return node


def content_mismatches(schema: dict) -> list[str]:
    """Empty when the walker's open-object findings match what the transform hollows."""
    from yamlgraph.utils import schema_walk as sw

    find_open_objects = getattr(
        sw, "find_open_objects", lambda s: []
    )  # behavioural RED
    try:
        transformed = transform.transform_schema(copy.deepcopy(schema))
    except ValueError as err:
        if str(err) == MISSING_KEYWORD:
            return []  # the untyped oracle owns this schema
        raise
    problems: list[str] = []
    flagged = set(find_open_objects(schema))
    for path, node in _concrete_objects(schema):
        dotted = ".".join(path) or "(root)"
        t = _at(transformed, path)
        declared = node.get("properties") or {}
        if not declared:
            if dotted not in flagged:
                problems.append(
                    f"{dotted}: transform hollows it but the walker did not flag it"
                )
            if {k: t.get(k) for k in HOLLOW} != HOLLOW:
                problems.append(
                    f"{dotted}: expected the hollow triple, transform gave {t}"
                )
        else:
            if dotted in flagged:
                problems.append(
                    f"{dotted}: walker flagged an object with declared properties"
                )
            if set(t.get("properties") or {}) != set(declared):
                problems.append(
                    f"{dotted}: transform lost properties {set(declared) ^ set(t.get('properties') or {})}"
                )
    for extra in flagged - {
        ".".join(p) or "(root)" for p, _ in _concrete_objects(schema)
    }:
        problems.append(f"{extra}: walker flagged a path that is not a concrete object")
    return problems


_SPIKE_FORMS = {
    "A_list_dict": lambda: _model("list[dict]").model_json_schema(),
    "B_list_any": lambda: _model("list[Any]").model_json_schema(),
    "C_output_schema": lambda: (
        __import__(
            "tests.unit.test_fr1125_open_objects", fromlist=["_ranker_output_schema"]
        )
        ._ranker_output_schema()
        .model_json_schema()
    ),
    "D_dict": lambda: _model("dict").model_json_schema(),
}


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize("form", sorted(_SPIKE_FORMS))
def test_ac07_content_parity_spike_forms(form: str) -> None:
    assert content_mismatches(_SPIKE_FORMS[form]()) == []


@pytest.mark.req("REQ-YG-712")
@pytest.mark.parametrize(
    "schema",
    _NESTED
    + [
        {
            "type": "object",
            "properties": {"o": {"type": "object", "additionalProperties": True}},
        },
        {
            "type": "object",
            "properties": {
                "o": {"type": "object", "additionalProperties": {"type": "string"}}
            },
        },
        {"type": "object", "properties": {"o": {"type": "object", "properties": {}}}},
        {
            "$defs": {"I": {"type": "object"}},
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/I"}},
        },
    ],
)
def test_ac07_content_parity_nested(schema: dict) -> None:
    assert content_mismatches(schema) == []


@pytest.mark.req("REQ-YG-712")
def test_ac07_content_parity_committed_census() -> None:
    problems = []
    for path in committed_prompt_schemas():
        model = load_schema_from_yaml(path)
        if model is None:
            continue
        for problem in content_mismatches(model.model_json_schema()):
            problems.append(f"{path.relative_to(ROOT)}: {problem}")
    assert problems == []
