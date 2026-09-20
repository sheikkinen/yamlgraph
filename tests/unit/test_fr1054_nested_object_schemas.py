"""FR-1054: nested object schemas must reach the provider.

The JSON-Schema builder read `items.type` and discarded `items.properties`,
so every declared item shape became an unconstrained object and providers
returned `{}` per element. These witnesses hold the recursion to its
declared subset.
"""

import glob

import pytest
import yaml
from pydantic import ValidationError

from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

# FR-756: the inventory witness reads committed examples/**/prompts/*.yaml.
pytestmark = pytest.mark.process

ARRAY_OF_OBJECT = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "score": {"type": "integer"},
                    "justification": {"type": "string"},
                },
                "required": ["name", "score"],
            },
        }
    },
    "required": ["criteria"],
}


def _items_schema(model, field):
    return model.model_json_schema()["properties"][field]


def _resolve(schema, ref):
    return schema["$defs"][ref.rsplit("/", 1)[-1]]


def _item_properties(model, field):
    """Declared item properties as the provider would see them."""
    schema = model.model_json_schema()
    spec = schema["properties"][field]
    items = spec.get("items", spec)
    if "$ref" in items:
        items = _resolve(schema, items["$ref"])
    return set(items.get("properties", {}))


@pytest.mark.req("REQ-YG-044")
def test_array_item_properties_reach_the_generated_schema():
    model = build_pydantic_model_from_json_schema(ARRAY_OF_OBJECT, "Review")
    assert _item_properties(model, "criteria") == {"name", "score", "justification"}


@pytest.mark.req("REQ-YG-044")
def test_a_bare_nested_object_field_keeps_its_properties():
    schema = {
        "type": "object",
        "properties": {
            "profile": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            }
        },
        "required": ["profile"],
    }
    model = build_pydantic_model_from_json_schema(schema, "Discovery")
    assert _item_properties(model, "profile") == {"url", "confidence"}


@pytest.mark.req("REQ-YG-044")
def test_nested_required_is_enforced_and_optional_is_not():
    model = build_pydantic_model_from_json_schema(ARRAY_OF_OBJECT, "Review")

    ok = model(criteria=[{"name": "clarity", "score": 4}])
    assert ok.criteria[0].justification is None

    with pytest.raises(ValidationError):
        model(criteria=[{"justification": "no name, no score"}])


@pytest.mark.req("REQ-YG-044")
def test_an_object_without_properties_stays_an_unconstrained_dict():
    schema = {
        "type": "object",
        "properties": {
            "bag": {"type": "object"},
            "bags": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["bag", "bags"],
    }
    model = build_pydantic_model_from_json_schema(schema, "Loose")
    instance = model(bag={}, bags=[{}])
    assert instance.bag == {}
    assert instance.bags == [{}]


@pytest.mark.req("REQ-YG-044")
def test_two_levels_of_nesting_resolve_and_sibling_models_stay_distinct():
    schema = {
        "type": "object",
        "properties": {
            "chapters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "notes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"body": {"type": "string"}},
                                "required": ["body"],
                            },
                        },
                    },
                    "required": ["title"],
                },
            },
            "appendices": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                },
            },
        },
        "required": ["chapters", "appendices"],
    }
    model = build_pydantic_model_from_json_schema(schema, "Book")

    built = model(
        chapters=[{"title": "one", "notes": [{"body": "deep"}]}],
        appendices=[{"title": "a"}],
    )
    assert built.chapters[0].notes[0].body == "deep"

    chapter = type(built.chapters[0])
    appendix = type(built.appendices[0])
    assert chapter is not appendix
    assert chapter.__name__ != appendix.__name__


@pytest.mark.req("REQ-YG-044")
def test_no_shipped_prompt_loses_its_declared_nested_keys():
    """FR-1054 inventory: 14 declared nested sites, none may lose keys."""
    losses = []
    sites = 0
    for path in sorted(glob.glob("examples/**/prompts/*.yaml", recursive=True)):
        with open(path, encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        if not isinstance(doc, dict):
            continue
        schema = doc.get("output_schema")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            continue
        model = build_pydantic_model_from_json_schema(schema, "Probe")
        for field, spec in (schema.get("properties") or {}).items():
            if not isinstance(spec, dict):
                continue
            nested = spec.get("items") if spec.get("type") == "array" else spec
            if not isinstance(nested, dict) or not nested.get("properties"):
                continue
            sites += 1
            declared = set(nested["properties"])
            generated = _item_properties(model, field)
            if declared - generated:
                losses.append(f"{path}::{field} lost {sorted(declared - generated)}")

    assert sites >= 14, f"inventory shrank to {sites} sites; FR-1054 measured 14"
    assert not losses, "declared nested keys discarded:\n" + "\n".join(losses)
