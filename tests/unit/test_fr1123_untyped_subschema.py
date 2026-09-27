"""FR-1123: refuse untyped prompt-schema fields before constrained decoding.

Anthropic's SDK strict transform raises ``Schema must have a 'type', 'anyOf',
'oneOf', or 'allOf' field.`` for an empty subschema (``Any``, ``list[Any]``)
before any request, naming neither prompt nor field. The daily digest ran
green for nine days on exactly that (FR-1121). The framework now names the
prompt and path at lint (E016/W028), compile, and bind.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import patch

import langchain_anthropic
import pytest
from yamlgraph.utils.schema_walk import (
    UnconstrainableSchemaError,
    find_untyped_subschemas,
    resolve_static_provider,
)

from yamlgraph.schema_loader import build_pydantic_model
from yamlgraph.utils.structured_output import bind_structured_output

REQ = "REQ-YG-712"


def _model(field_type: str) -> type:
    return build_pydantic_model(
        {
            "name": "RankedStories",
            "fields": {"stories": {"type": field_type, "description": "d"}},
        }
    )


# AC-01 -----------------------------------------------------------------------


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("field_type", "paths"),
    [
        ("Any", ["stories"]),
        ("list[Any]", ["stories.items"]),
        ("dict", []),
        ("list[dict]", []),
        ("list[str]", []),
    ],
)
def test_ac01_five_type_rows(field_type: str, paths: list[str]) -> None:
    assert find_untyped_subschemas(_model(field_type).model_json_schema()) == paths


# AC-02 -----------------------------------------------------------------------
# Traversal mirrors the SDK transform: it descends `properties` only under
# type object, `items` only under type array, the first of anyOf/oneOf/allOf,
# and `$defs`; `$ref` ends the walk; `prefixItems` and `additionalProperties`
# are folded into the description by the SDK, never validated.

_OBJ = "object"


def _obj(**props: Any) -> dict:
    return {"type": _OBJ, "properties": props}


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("schema", "paths"),
    [
        (_obj(a=_obj(b={})), ["a.b"]),
        (
            _obj(xs={"type": "array", "items": {"type": "array", "items": {}}}),
            ["xs.items.items"],
        ),
        (_obj(c={"anyOf": [{}, {"type": "null"}]}), ["c.anyOf[0]"]),
        (_obj(c={"oneOf": [{"type": "string"}, {}]}), ["c.oneOf[1]"]),
        (_obj(c={"allOf": [{}]}), ["c.allOf[0]"]),
        (_obj(c={"anyOf": [{"type": "string"}], "oneOf": [{}]}), []),
        (
            {
                "$defs": {"Item": _obj(v={})},
                **_obj(i={"$ref": "#/$defs/Item"}),
            },
            ["$defs.Item.v"],
        ),
        (_obj(r={"$ref": "#/$defs/X"}), []),
        (_obj(p={"type": "array", "prefixItems": [{}, {"type": "integer"}]}), []),
        (
            _obj(
                d={"type": _OBJ, "additionalProperties": {"type": "array", "items": {}}}
            ),
            [],
        ),
        (
            _obj(first={}, second={"type": "array", "items": {}}),
            ["first", "second.items"],
        ),
        ({"description": "no type at root"}, ["(root)"]),
    ],
)
def test_ac02_nested_traversal_exact_paths(schema: dict, paths: list[str]) -> None:
    assert find_untyped_subschemas(schema) == paths


# AC-03 -----------------------------------------------------------------------


class _Fake:
    model = "other-model"

    def __init__(self) -> None:
        self.bind_calls: list[dict] = []

    def with_structured_output(self, output_model: type, **kwargs: Any) -> str:
        self.bind_calls.append(dict(kwargs))
        return "bound"


class _FakeAnthropic(_Fake):
    model = "claude-fake-4-5"


@pytest.fixture
def anthropic_is_fake(monkeypatch):
    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", _FakeAnthropic)


@pytest.mark.req(REQ)
def test_ac03_binder_refuses_anthropic_json_schema(anthropic_is_fake) -> None:
    llm = _FakeAnthropic()
    with pytest.raises(UnconstrainableSchemaError) as exc:
        bind_structured_output(llm, _model("list[Any]"))
    assert "claude-fake-4-5" in str(exc.value)
    assert "stories.items" in str(exc.value)
    assert llm.bind_calls == []


@pytest.mark.req(REQ)
def test_ac03_binder_typed_anthropic_binds(anthropic_is_fake) -> None:
    llm = _FakeAnthropic()
    assert bind_structured_output(llm, _model("list[dict]")) == "bound"
    assert llm.bind_calls == [{"method": "json_schema"}]


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("llm_cls", "method"),
    [(_Fake, None), (_Fake, "json_schema"), (_FakeAnthropic, "function_calling")],
)
def test_ac03_walker_not_called_off_anthropic_json_schema(
    anthropic_is_fake, llm_cls: type, method: str | None
) -> None:
    llm = llm_cls()
    with patch("yamlgraph.utils.structured_output.find_untyped_subschemas") as walker:
        assert (
            bind_structured_output(llm, _model("list[Any]"), method=method) == "bound"
        )
    walker.assert_not_called()


# AC-04 -----------------------------------------------------------------------


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("node", "default", "env", "expected"),
    [
        ("mistral", "openai", "xai", "mistral"),
        (None, "openai", "xai", "openai"),
        (None, None, "xai", "xai"),
        (None, None, None, "anthropic"),
        ("{state.provider}", "openai", None, None),
        (None, "{state.provider}", None, None),
    ],
)
def test_ac04_static_provider_precedence(
    monkeypatch, node, default, env, expected
) -> None:
    if env is None:
        monkeypatch.delenv("PROVIDER", raising=False)
    else:
        monkeypatch.setenv("PROVIDER", env)
    assert resolve_static_provider(node, default) == expected


@pytest.mark.req(REQ)
def test_ac04_create_llm_uses_the_shared_resolver(monkeypatch) -> None:
    from yamlgraph.utils import llm_factory

    seen: list[tuple] = []

    def spy(*args: Any) -> str:
        seen.append(args)
        return "not-a-provider"

    monkeypatch.setattr(llm_factory, "resolve_static_provider", spy)
    with pytest.raises(ValueError, match="not-a-provider"):
        llm_factory.create_llm(provider="mistral")
    assert seen == [("mistral", None)]


# Graph fixtures ----------------------------------------------------------------

TOOLS_SRC = textwrap.dedent(
    """
    import os


    def mark(state):
        open(os.environ["FR1123_MARK"], "w").close()
        return 1
    """
)


def _graph(tmp_path: Path, provider_line: str, field_type: str = "list[Any]") -> Path:
    (tmp_path / "prompts").mkdir(exist_ok=True)
    (tmp_path / "prompts" / "rank.yaml").write_text(
        textwrap.dedent(
            f"""\
            schema:
              name: RankedStories
              fields:
                stories:
                  type: {field_type}
                  description: top stories
            system: rank
            user: "rank {{items}}"
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "tools_fr1123.py").write_text(TOOLS_SRC, encoding="utf-8")
    text = textwrap.dedent(
        f"""\
        version: "1.0"
        name: fr1123
        prompts_relative: true
        prompts_dir: prompts
        state:
          items: str
          provider: str
          marked: int
        tools:
          mark:
            type: python
            path: tools_fr1123.py
            function: mark
        nodes:
          first:
            type: python
            tool: mark
            state_key: marked
          rank_stories:
            type: llm
            prompt: rank
            {provider_line}
            variables:
              items: "{{state.items}}"
            state_key: ranked
        edges:
          - from: START
            to: first
          - from: first
            to: rank_stories
          - from: rank_stories
            to: END
        """
    )
    path = tmp_path / "fr1123.yaml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.setenv("FR1123_MARK", str(tmp_path / "first-ran"))


STATIC = "provider: anthropic\n            model: claude-fr1123"
STATE = 'provider: "{state.provider}"'


# AC-05 -----------------------------------------------------------------------


@pytest.mark.req(REQ)
def test_ac05_compile_refuses_static_anthropic(tmp_path) -> None:
    from yamlgraph.compile.graph_loader import load_and_compile

    with pytest.raises(UnconstrainableSchemaError) as exc:
        load_and_compile(_graph(tmp_path, STATIC))
    msg = str(exc.value)
    for part in ("rank_stories", "'rank'", "claude-fr1123", "stories.items"):
        assert part in msg
    assert not (tmp_path / "first-ran").exists()


@pytest.mark.req(REQ)
def test_ac05_compile_uses_env_and_default_provider(tmp_path, monkeypatch) -> None:
    from yamlgraph.compile.graph_loader import load_and_compile

    monkeypatch.setenv("PROVIDER", "mistral")
    load_and_compile(_graph(tmp_path, "temperature: 0.1"))
    monkeypatch.setenv("PROVIDER", "anthropic")
    with pytest.raises(UnconstrainableSchemaError):
        load_and_compile(_graph(tmp_path, "temperature: 0.1"))


@pytest.mark.req(REQ)
def test_ac05_state_provider_compiles_then_binder_refuses(
    tmp_path, anthropic_is_fake
) -> None:
    from yamlgraph.compile.graph_loader import load_and_compile

    load_and_compile(_graph(tmp_path, STATE))
    with pytest.raises(UnconstrainableSchemaError, match="stories.items"):
        bind_structured_output(_FakeAnthropic(), _model("list[Any]"))


@pytest.mark.req(REQ)
def test_ac05_typed_schema_compiles(tmp_path) -> None:
    from yamlgraph.compile.graph_loader import load_and_compile

    load_and_compile(_graph(tmp_path, STATIC, field_type="list[dict]"))


# AC-06 -----------------------------------------------------------------------


def _codes(path: Path) -> list[tuple[str, str]]:
    from yamlgraph.linter import lint_graph

    return [
        (i.code, i.message)
        for i in lint_graph(path).issues
        if i.code in {"E016", "W028"}
    ]


@pytest.mark.req(REQ)
def test_ac06_lint_e016_static_anthropic(tmp_path) -> None:
    issues = _codes(_graph(tmp_path, STATIC))
    assert [c for c, _ in issues] == ["E016"]
    assert "rank_stories" in issues[0][1] and "stories.items" in issues[0][1]


@pytest.mark.req(REQ)
def test_ac06_lint_w028_unresolved_provider(tmp_path) -> None:
    issues = _codes(_graph(tmp_path, STATE))
    assert [c for c, _ in issues] == ["W028"]
    assert "stories.items" in issues[0][1]


@pytest.mark.req(REQ)
@pytest.mark.parametrize(
    ("provider_line", "field_type"),
    [
        ("provider: mistral", "list[Any]"),
        ("provider: openai", "Any"),
        (STATIC, "list[dict]"),
    ],
)
def test_ac06_lint_silent(tmp_path, provider_line: str, field_type: str) -> None:
    assert _codes(_graph(tmp_path, provider_line, field_type)) == []


@pytest.mark.req(REQ)
def test_ac06_lint_serializes_through_issue_shape(tmp_path) -> None:
    from yamlgraph.linter import lint_graph

    result = lint_graph(_graph(tmp_path, STATIC))
    issue = next(i for i in result.issues if i.code == "E016")
    assert issue.severity == "error" and issue.fix
    assert result.valid is False


# AC-10 -----------------------------------------------------------------------


@pytest.mark.req(REQ)
def test_ac10_graph_run_exits_nonzero_before_any_node(tmp_path, capsys) -> None:
    from yamlgraph.cli import create_parser
    from yamlgraph.cli.graph_commands import cmd_graph_run

    graph = _graph(tmp_path, STATIC)
    args = create_parser().parse_args(["graph", "run", str(graph), "--var", "items=x"])
    code = 0
    try:
        cmd_graph_run(args)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    err = capsys.readouterr().err
    assert code != 0
    assert "stories.items" in err
    assert not (tmp_path / "first-ran").exists()
