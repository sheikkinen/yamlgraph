"""FR-1156: the walker follows anthropic 2.8's literal rule.

From 2.8.0 the SDK transform accepts a subschema with no type/composition when
it carries a primitive ``const`` or a non-empty all-primitive ``enum``; pydantic
emits that shape for a mixed-type ``Literal``. A literal makes the SDK drop
``type``, so nothing below it is visited; compositions and ``$defs`` still are.
"""

from __future__ import annotations

from typing import Any, Literal

import langchain_anthropic
import pytest
from pydantic import create_model

from yamlgraph.utils.schema_walk import (
    UnconstrainableSchemaError,
    find_open_objects,
    find_untyped_subschemas,
)
from yamlgraph.utils.structured_output import bind_structured_output

REQ = "REQ-YG-712"
_DEFS_UNTYPED = {"D": {"type": "object", "properties": {"v": {}}}}

# Each row is mirrored in test_fr1123_sdk_parity._NESTED against the real SDK.
LITERAL_ROWS: list[tuple[dict, list[str]]] = [
    # eligible: every primitive category
    ({"enum": ["a", "b"]}, []),
    ({"enum": [None, "s", 1, 2.5, True]}, []),
    ({"const": "x"}, []),
    ({"const": None}, []),
    ({"const": False}, []),
    # not eligible: empty or non-primitive
    ({"enum": []}, ["(root)"]),
    ({"enum": [{"a": 1}]}, ["(root)"]),
    ({"enum": ["a", ["b"]]}, ["(root)"]),
    ({"const": {"a": 1}}, ["(root)"]),
    # const and enum are eligible independently
    ({"const": "x", "enum": ["a"]}, []),
    ({"const": "x", "enum": [{"a": 1}]}, []),
    ({"const": {"a": 1}, "enum": ["a"]}, []),
    # a literal stops type-driven descent
    ({"type": "array", "const": "x", "items": {}}, []),
    ({"type": "object", "enum": ["a"], "properties": {"u": {}}}, []),
    # compositions and $defs under a literal are still walked; $ref still stops
    ({"anyOf": [{}], "enum": ["a"]}, ["anyOf[0]"]),
    ({"oneOf": [{}], "const": 1}, ["oneOf[0]"]),
    ({"allOf": [{}], "const": True}, ["allOf[0]"]),
    ({"enum": ["a"], "$defs": _DEFS_UNTYPED}, ["$defs.D.v"]),
    ({"enum": ["a"], "$ref": "#/$defs/X"}, []),
]


@pytest.mark.req(REQ)
@pytest.mark.parametrize(("schema", "paths"), LITERAL_ROWS)
def test_literal_untyped_paths(schema: dict, paths: list[str]) -> None:
    assert find_untyped_subschemas(schema) == paths


@pytest.mark.req(REQ)
def test_literal_nested_beside_untyped_sibling() -> None:
    schema = {"type": "object", "properties": {"k": {"enum": ["a", 1]}, "u": {}}}
    assert find_untyped_subschemas(schema) == ["u"]


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "enum": ["a"]},
        {"type": "object", "properties": {"o": {"type": "object", "const": "x"}}},
    ],
)
def test_literal_object_is_not_open(schema: dict) -> None:
    assert find_open_objects(schema) == []


def _mixed(**extra: Any) -> type:
    return create_model("M", f=(Literal["a", 1], ...), **extra)


class _FakeAnthropic:
    model = "claude-fake-4-5"

    def __init__(self) -> None:
        self.bind_calls: list[dict] = []

    def with_structured_output(self, output_model: type, **kwargs: Any) -> str:
        self.bind_calls.append(dict(kwargs))
        return "bound"


@pytest.fixture
def llm(monkeypatch) -> _FakeAnthropic:
    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", _FakeAnthropic)
    return _FakeAnthropic()


@pytest.mark.req(REQ)
def test_mixed_literal_model_has_no_finding() -> None:
    schema = _mixed().model_json_schema()
    assert schema["properties"]["f"] == {"enum": ["a", 1], "title": "F"}
    assert find_untyped_subschemas(schema) == []


@pytest.mark.req(REQ)
def test_binder_binds_mixed_literal(llm: _FakeAnthropic) -> None:
    assert bind_structured_output(llm, _mixed()) == "bound"
    assert llm.bind_calls == [{"method": "json_schema"}]


@pytest.mark.req(REQ)
def test_binder_still_refuses_neighbouring_any(llm: _FakeAnthropic) -> None:
    with pytest.raises(UnconstrainableSchemaError) as exc:
        bind_structured_output(llm, _mixed(g=(Any, ...)))
    assert "field 'g' has no type" in str(exc.value)
    assert "'f'" not in str(exc.value)
    assert llm.bind_calls == []
