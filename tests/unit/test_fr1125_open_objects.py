"""FR-1125 — refuse unconstrained (open) objects on Anthropic-bound nodes.

RED before GREEN. Anthropic constrained decoding cannot express an object
with unknown keys: the API rejects ``additionalProperties: true`` and the
SDK's transform rewrites an object with no declared ``properties`` into
``{"type": "object", "properties": {}, "additionalProperties": false}`` — a
grammar whose only instance is ``{}``. ``dict``, ``dict[str, Any]`` and
``list[dict]`` produce exactly that object; the framework sent it without
comment and the digest's ranker answered ``[]`` (spike
``docs/spikes/constrained-object-2026-09-27/``).

Witnesses per the judgement's AC-02..AC-06 and AC-13: the unified walker's
typed findings and canonical paths, kind-specific messages, the binder
refusal (Anthropic + json_schema only), the compile refusal, the E017/W029
lint codes with E016/W028 unchanged, and the linter extraction's import
boundary. The SDK content-parity oracle (AC-07) lives in
``test_fr1123_sdk_parity.py``, the only module allowed the private import.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import langchain_anthropic
import pytest

from tests.unit.test_fr1123_untyped_subschema import (
    STATE,
    STATIC,
    _Fake,
    _FakeAnthropic,
    _graph,
    _model,
)
from yamlgraph.schema_loader import build_pydantic_model_from_json_schema
from yamlgraph.utils.schema_walk import (
    UnconstrainableSchemaError,
    find_untyped_subschemas,
)
from yamlgraph.utils.structured_output import bind_structured_output

REQ = "REQ-YG-712"


@pytest.fixture
def anthropic_is_fake(monkeypatch):
    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", _FakeAnthropic)


RANKER_PROPS = {
    "title": {"type": "string"},
    "url": {"type": "string"},
    "summary": {"type": "string"},
    "relevance": {"type": "number"},
    "reason": {"type": "string"},
}


def _ranker_output_schema() -> type:
    return build_pydantic_model_from_json_schema(
        {
            "type": "object",
            "properties": {
                "stories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": RANKER_PROPS,
                        "required": sorted(RANKER_PROPS),
                    },
                }
            },
            "required": ["stories"],
        },
        "RankedStories",
    )


def _findings(schema: dict) -> list[tuple[str, str]]:
    # RED fails on behaviour (nothing flagged), not on an ImportError (judgement AC-02).
    from yamlgraph.utils import schema_walk as sw

    find = getattr(sw, "find_unconstrainable", lambda s: [])
    return [(f.path, f.kind) for f in find(schema)]


# AC-02 / AC-03 — walker -------------------------------------------------------


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        ("dict", [("stories", "open_object")]),
        ("dict[str, Any]", [("stories", "open_object")]),
        ("list[dict]", [("stories.items", "open_object")]),
        ("list[Any]", [("stories.items", "untyped")]),
        ("list[str]", []),
    ],
)
def test_ac02_fields_form_findings(field_type: str, expected) -> None:
    assert _findings(_model(field_type).model_json_schema()) == expected


@pytest.mark.req(REQ)
def test_ac02_declared_properties_are_not_open() -> None:
    schema = _ranker_output_schema().model_json_schema()
    assert _findings(schema) == []


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        # absent vs empty properties, both open; additionalProperties irrelevant
        (
            {"type": "object", "properties": {"a": {"type": "object"}}},
            [("a", "open_object")],
        ),
        (
            {
                "type": "object",
                "properties": {"a": {"type": "object", "properties": {}}},
            },
            [("a", "open_object")],
        ),
        (
            {
                "type": "object",
                "properties": {"a": {"type": "object", "additionalProperties": True}},
            },
            [("a", "open_object")],
        ),
        (
            {
                "type": "object",
                "properties": {
                    "a": {"type": "object", "additionalProperties": {"type": "string"}}
                },
            },
            [("a", "open_object")],
        ),
        # one declared property: not open
        (
            {
                "type": "object",
                "properties": {
                    "a": {"type": "object", "properties": {"k": {"type": "string"}}}
                },
            },
            [],
        ),
        # root open object
        ({"type": "object"}, [("(root)", "open_object")]),
        # nested inside array items and composition branches
        (
            {
                "type": "object",
                "properties": {"a": {"type": "array", "items": {"type": "object"}}},
            },
            [("a.items", "open_object")],
        ),
        (
            {
                "type": "object",
                "properties": {"a": {"anyOf": [{"type": "object"}, {"type": "null"}]}},
            },
            [("a.anyOf[0]", "open_object")],
        ),
        # $defs entry open, referenced once: one finding at the definition, $ref is a stop
        (
            {
                "$defs": {"Item": {"type": "object"}},
                "type": "object",
                "properties": {
                    "a": {"$ref": "#/$defs/Item"},
                    "b": {"type": "array", "items": {"$ref": "#/$defs/Item"}},
                },
            },
            [("$defs.Item", "open_object")],
        ),
        # both kinds in one schema, walk order
        (
            {"type": "object", "properties": {"a": {}, "b": {"type": "object"}}},
            [("a", "untyped"), ("b", "open_object")],
        ),
    ],
)
def test_ac02_raw_schema_findings_canonical_paths(schema: dict, expected) -> None:
    assert _findings(schema) == expected


@pytest.mark.req(REQ)
def test_ac03_findings_are_typed_deterministic_and_unique() -> None:
    from yamlgraph.utils import schema_walk as sw

    find = getattr(sw, "find_unconstrainable", lambda s: [])
    schema = {
        "type": "object",
        "properties": {"a": {"type": "object"}, "b": {}, "c": {"type": "object"}},
    }
    first = find(schema)
    assert len(first) == 3, "open objects and the untyped field must all be found"
    assert first == find(schema)
    assert all(type(f).__name__ == "SchemaFinding" for f in first)
    assert len({f.path for f in first}) == len(first)
    assert {f.kind for f in first} <= {"untyped", "open_object"}


@pytest.mark.req(REQ)
def test_ac03_projections_preserve_fr1123_paths() -> None:
    from yamlgraph.utils import schema_walk as sw

    both = {
        "type": "object",
        "properties": {
            "a": {},
            "b": {"type": "object"},
            "c": {"type": "array", "items": {}},
        },
    }
    assert find_untyped_subschemas(both) == ["a", "c.items"]
    assert getattr(sw, "find_open_objects", lambda s: [])(both) == ["b"]


@pytest.mark.req(REQ)
def test_ac03_messages_per_kind() -> None:
    from yamlgraph.utils import schema_walk as sw

    refusal_message = sw.refusal_message
    SchemaFinding = getattr(sw, "SchemaFinding", None) or (lambda path, kind: path)
    untyped = refusal_message("Prompt 'p'", [SchemaFinding("stories.items", "untyped")])
    assert "stories.items" in untyped
    assert "list[dict]" not in untyped and "dict" not in untyped.replace("dict.", "")
    opened = refusal_message(
        "Prompt 'p'", [SchemaFinding("stories.items", "open_object")]
    )
    assert "stories.items" in opened
    assert "{}" in opened and "output_schema" in opened and "provider" in opened
    both = refusal_message(
        "Prompt 'p'", [SchemaFinding("a", "untyped"), SchemaFinding("b", "open_object")]
    )
    assert "'a'" in both and "'b'" in both and "output_schema" in both


# AC-04 — binder ---------------------------------------------------------------


@pytest.mark.req(REQ)
@pytest.mark.parametrize("field_type", ["list[dict]", "dict"])
def test_ac04_binder_refuses_open_object_on_anthropic_json_schema(
    anthropic_is_fake, field_type
) -> None:
    llm = _FakeAnthropic()
    with pytest.raises(UnconstrainableSchemaError) as exc:
        bind_structured_output(llm, _model(field_type))
    assert "claude-fake-4-5" in str(exc.value)
    assert ("stories.items" if "list" in field_type else "'stories'") in str(exc.value)
    assert "output_schema" in str(exc.value)
    assert llm.bind_calls == []


@pytest.mark.req(REQ)
def test_ac04_binder_binds_declared_properties(anthropic_is_fake) -> None:
    llm = _FakeAnthropic()
    assert bind_structured_output(llm, _ranker_output_schema()) == "bound"
    assert llm.bind_calls == [{"method": "json_schema"}]


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("cls", "method"),
    [(_Fake, None), (_Fake, "json_schema"), (_FakeAnthropic, "function_calling")],
)
def test_ac04_walker_not_called_off_anthropic_json_schema(
    anthropic_is_fake, monkeypatch, cls, method
) -> None:
    import yamlgraph.utils.structured_output as so

    calls: list[Any] = []
    monkeypatch.setattr(
        so, "find_unconstrainable", lambda s: calls.append(s) or [], raising=False
    )
    monkeypatch.setattr(
        so, "find_untyped_subschemas", lambda s: calls.append(s) or [], raising=False
    )
    llm = cls()
    assert bind_structured_output(llm, _model("list[dict]"), method=method) == "bound"
    assert calls == []


# AC-05 — compile --------------------------------------------------------------


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.setenv("FR1123_MARK", str(tmp_path / "first-ran"))


def _compile(path: Path):
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    return compile_graph(load_graph_config(path))


@pytest.mark.req(REQ)
def test_ac05_compile_refuses_static_anthropic_open_object(tmp_path) -> None:
    with pytest.raises(UnconstrainableSchemaError) as exc:
        _compile(_graph(tmp_path, STATIC, "list[dict]"))
    text = str(exc.value)
    assert "rank_stories" in text and "rank" in text and "claude-fr1123" in text
    assert "stories.items" in text and "open" in text.lower()
    assert not (tmp_path / "first-ran").exists(), "a node executed before the refusal"


def _graph_output_schema(tmp_path: Path, provider_line: str) -> Path:
    path = _graph(tmp_path, provider_line, "list[str]")
    (tmp_path / "prompts" / "rank.yaml").write_text(
        textwrap.dedent(
            """\
            output_schema:
              type: object
              properties:
                stories:
                  type: array
                  items:
                    type: object
                    properties:
                      title: {type: string}
                      url: {type: string}
                    required: [title, url]
              required: [stories]
            system: rank
            user: "rank {{items}}"
            """
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.req(REQ)
def test_ac05_declared_properties_compile(tmp_path) -> None:
    _compile(_graph_output_schema(tmp_path, STATIC))


@pytest.mark.req(REQ)
def test_ac05_state_provider_compiles_then_binder_refuses(
    tmp_path, anthropic_is_fake
) -> None:
    _compile(_graph(tmp_path, STATE, "list[dict]"))
    with pytest.raises(UnconstrainableSchemaError):
        bind_structured_output(_FakeAnthropic(), _model("list[dict]"))


# AC-06 — lint -----------------------------------------------------------------

CODES = {"E016", "W028", "E017", "W029"}


def _codes(path: Path) -> list[tuple[str, str]]:
    from yamlgraph.linter import lint_graph

    return [(i.code, i.message) for i in lint_graph(path).issues if i.code in CODES]


@pytest.mark.req(REQ)
def test_ac06_lint_e017_static_anthropic(tmp_path) -> None:
    issues = _codes(_graph(tmp_path, STATIC, "list[dict]"))
    assert [c for c, _ in issues] == ["E017"]
    assert "rank_stories" in issues[0][1] and "stories.items" in issues[0][1]


@pytest.mark.req(REQ)
def test_ac06_lint_w029_unresolved_provider(tmp_path) -> None:
    issues = _codes(_graph(tmp_path, STATE, "list[dict]"))
    assert [c for c, _ in issues] == ["W029"]


@pytest.mark.req(REQ)
def test_ac06_lint_silent_for_mistral_and_declared(tmp_path) -> None:
    assert _codes(_graph(tmp_path, "provider: mistral", "list[dict]")) == []
    assert _codes(_graph_output_schema(tmp_path, STATIC)) == []


@pytest.mark.req(REQ)
def test_ac06_lint_both_kinds_in_one_schema(tmp_path) -> None:
    path = _graph(tmp_path, STATIC, "list[dict]")
    prompt = tmp_path / "prompts" / "rank.yaml"
    prompt.write_text(
        prompt.read_text(encoding="utf-8").replace(
            "system: rank",
            "    extra:\n      type: Any\n      description: d\nsystem: rank",
        ),
        encoding="utf-8",
    )
    codes = sorted(c for c, _ in _codes(path))
    assert codes == ["E016", "E017"]


@pytest.mark.req(REQ)
def test_ac06_e016_unchanged_for_untyped(tmp_path) -> None:
    issues = _codes(_graph(tmp_path, STATIC, "list[Any]"))
    assert [c for c, _ in issues] == ["E016"]
    assert "list[dict]" not in issues[0][1]


@pytest.mark.req(REQ)
def test_ac06_lint_sees_map_sub_nodes(tmp_path) -> None:
    """Compile refuses a map sub-node's open object; lint must report the same node."""
    path = _graph(tmp_path, STATIC, "list[dict]")
    text = path.read_text(encoding="utf-8").replace(
        """  rank_stories:
    type: llm
    prompt: rank
""",
        """  rank_stories:
    type: map
    over: "{state.items}"
    as: item
    collect: ranked_all
    node:
      type: llm
      prompt: rank
""",
    )
    path.write_text(text, encoding="utf-8")
    issues = _codes(path)
    assert [c for c, _ in issues] == ["E017"]
    assert "rank_stories/node" in issues[0][1]


# AC-13 — linter extraction ----------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req(REQ)
def test_ac13_linter_check_lives_in_checks_schema_and_is_wired() -> None:
    from yamlgraph.linter import checks_schema, graph_linter

    assert callable(checks_schema.check_unconstrainable_schemas)
    assert (
        graph_linter.check_unconstrainable_schemas
        is checks_schema.check_unconstrainable_schemas
    )
    prompts_src = (ROOT / "yamlgraph" / "linter" / "checks_prompts.py").read_text(
        encoding="utf-8"
    )
    assert "def check_untyped_subschemas" not in prompts_src
    assert len(prompts_src.splitlines()) < 400


@pytest.mark.req(REQ)
def test_ac13_no_production_import_of_private_sdk_transform() -> None:
    needle = ".".join(
        ("anthropic", "lib", "_parse")
    )  # assembled: this file must not carry it
    hits = [
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "yamlgraph").rglob("*.py")
        if needle in p.read_text(encoding="utf-8")
    ]
    assert hits == []
