"""FR-1124: an authored top-level llm node without on_error defaults to fail.

Resolution order: node on_error -> defaults.on_error -> "fail", applied only
at the top-level llm compile seam; router, race and map sub-nodes keep their
current policies.
"""

from __future__ import annotations

import contextlib
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.compile.graph_loader import load_and_compile
from yamlgraph.constants import ErrorHandler
from yamlgraph.node_factory import llm_execution
from yamlgraph.node_factory.llm_nodes import create_node_function


class RankError(RuntimeError):
    pass


BOOM = RankError("rank provider exploded")


def _write(tmp_path: Path, nodes: str, defaults: str = "") -> Path:
    prompts = tmp_path / "prompts"
    prompts.mkdir(exist_ok=True)
    for name in ("rank", "fmt"):
        (prompts / f"{name}.yaml").write_text(
            f'system: {name}\nuser: "{name} {{items}}"\n', encoding="utf-8"
        )
    path = tmp_path / "graph.yaml"
    path.write_text(
        textwrap.dedent(
            """\
            version: "1.0"
            name: fr1124
            prompts_relative: true
            prompts_dir: prompts
            {defaults}
            state:
              items: str
            nodes:
            {nodes}
            edges:
              - from: START
                to: rank
              - from: rank
                to: fmt
              - from: fmt
                to: END
            """
        ).format(defaults=defaults, nodes=textwrap.indent(nodes, "  ")),
        encoding="utf-8",
    )
    return path


def _two_llm(rank_extra: str = "") -> str:
    return (
        "rank:\n  type: llm\n  prompt: rank\n  state_key: ranked\n"
        + textwrap.indent(rank_extra, "  ")
        + "fmt:\n  type: llm\n  prompt: fmt\n  state_key: formatted\n"
    )


@pytest.fixture
def calls():
    seen: list[str] = []

    def fake(prompt_name, **_kw):
        seen.append(prompt_name)
        if prompt_name == "rank":
            raise BOOM
        return "ok"

    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake):
        yield seen


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _invoke(path: Path) -> dict:
    return load_and_compile(path).compile().invoke({"items": "x"})


def _captured_on_error(path: Path, target: str) -> dict[str, object]:
    """Compile and return the on_error each factory call received, by node name."""
    seen: dict[str, object] = {}
    real = {
        "yamlgraph.compile.node_compiler.create_node_function": create_node_function,
        "yamlgraph.compile.map_compiler.create_node_function": create_node_function,
    }
    real_target = real.get(target)
    if real_target is None:
        from yamlgraph.compile import node_compiler

        real_target = getattr(node_compiler, target.rsplit(".", 1)[1])

    def spy(name, config, *args, **kwargs):
        seen[name] = config.get("on_error")
        return real_target(name, config, *args, **kwargs)

    with patch(target, side_effect=spy):
        load_and_compile(path)
    return seen


# AC-01 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-715")
def test_ac01_undeclared_llm_failure_propagates_original_exception(
    tmp_path, calls
) -> None:
    path = _write(tmp_path, _two_llm())
    with pytest.raises(RankError) as excinfo:
        _invoke(path)
    assert excinfo.value is BOOM
    assert calls == ["rank"]


# AC-02 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize(
    ("node_value", "default_value", "expected"),
    [
        (None, None, "fail"),
        (None, "skip", "skip"),
        (None, "retry", "retry"),
        ("retry", "skip", "retry"),
        ("skip", None, "skip"),
        ("fail", "skip", "fail"),
    ],
)
def test_ac02_resolution_node_then_default_then_fail(
    tmp_path, node_value, default_value, expected
) -> None:
    extra = f"on_error: {node_value}\n" if node_value else ""
    defaults = f"defaults:\n  on_error: {default_value}" if default_value else ""
    path = _write(tmp_path, _two_llm(extra), defaults)
    seen = _captured_on_error(
        path, "yamlgraph.compile.node_compiler.create_node_function"
    )
    assert seen["rank"] == expected
    assert seen["rank"] in {h.value for h in ErrorHandler}
    assert seen["fmt"] == (default_value or "fail")


# AC-03 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize("value", ["skip", "retry", "fail", "fallback"])
def test_ac03_defaults_on_error_accepts_the_four_values(tmp_path, value) -> None:
    rank_extra = "fallback:\n  provider: mistral\n"
    fmt = "fmt:\n  type: llm\n  prompt: fmt\n  fallback:\n    provider: mistral\n"
    nodes = (
        "rank:\n  type: llm\n  prompt: rank\n  state_key: ranked\n"
        + textwrap.indent(rank_extra, "  ")
        + fmt
    )
    load_and_compile(_write(tmp_path, nodes, f"defaults:\n  on_error: {value}"))


@pytest.mark.req("REQ-YG-715")
def test_ac03_invalid_defaults_on_error_fails_load_naming_key_and_value(
    tmp_path,
) -> None:
    path = _write(tmp_path, _two_llm(), "defaults:\n  on_error: record")
    with pytest.raises(Exception, match=r"defaults\.on_error.*'record'"):
        load_and_compile(path)


@pytest.mark.req("REQ-YG-715")
def test_ac03_defaults_fallback_without_node_fallback_provider_refused(
    tmp_path,
) -> None:
    """A graph-wide fallback with no provider to fall back to has no executable
    strategy; refusing it keeps top-level llm nodes off handle_default (AC-05)."""
    path = _write(tmp_path, _two_llm(), "defaults:\n  on_error: fallback")
    with pytest.raises(Exception, match=r"defaults\.on_error.*fallback.*rank"):
        load_and_compile(path)


# AC-04 -----------------------------------------------------------------------


ROUTER_NODES = (
    "rank:\n  type: router\n  prompt: rank\n  route_field: intent\n"
    "  routes:\n    a: fmt\n"
    "  default_route: fmt\n"
    "fmt:\n  type: llm\n  prompt: fmt\n"
)
RACE_NODES = (
    "rank:\n  type: race\n  prompt: rank\n  candidates:\n"
    "    - provider: mistral\n    - provider: openai\n"
    "fmt:\n  type: llm\n  prompt: fmt\n"
)


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize("defaults", ["", "defaults:\n  on_error: skip"])
def test_ac04_router_policy_unchanged(tmp_path, defaults) -> None:
    path = _write(tmp_path, ROUTER_NODES, defaults)
    seen = _captured_on_error(
        path, "yamlgraph.compile.node_compiler.create_node_function"
    )
    assert seen["rank"] is None


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize("defaults", ["", "defaults:\n  on_error: skip"])
def test_ac04_race_policy_unchanged(tmp_path, defaults) -> None:
    path = _write(tmp_path, RACE_NODES, defaults)
    seen = _captured_on_error(path, "yamlgraph.compile.node_compiler.create_race_node")
    assert seen["rank"] is None


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize("defaults", ["", "defaults:\n  on_error: skip"])
def test_ac04_map_llm_subnode_policy_unchanged(tmp_path, defaults) -> None:
    nodes = (
        "rank:\n  type: map\n  over: '{state.items_list}'\n  as: item\n"
        "  collect: ranked\n  node:\n    type: llm\n    prompt: rank\n"
        "    state_key: one\n"
        "fmt:\n  type: llm\n  prompt: fmt\n"
    )
    path = _write(tmp_path, nodes, defaults)
    seen = _captured_on_error(
        path, "yamlgraph.compile.map_compiler.create_node_function"
    )
    assert seen and all(v is None for v in seen.values())


# AC-05 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize(
    ("extra", "defaults"),
    [
        ("", ""),
        ("", "defaults:\n  on_error: skip"),
        ("on_error: retry\nmax_retries: 0\n", ""),
    ],
)
def test_ac05_top_level_llm_never_reaches_handle_default(
    tmp_path, calls, extra, defaults
) -> None:
    path = _write(tmp_path, _two_llm(extra), defaults)
    with (
        patch.object(
            llm_execution, "handle_default", wraps=llm_execution.handle_default
        ) as spy,
        contextlib.suppress(RankError),
    ):
        _invoke(path)
    assert spy.call_count == 0


@pytest.mark.req("REQ-YG-715")
def test_ac05_excluded_caller_still_reaches_handle_default(calls) -> None:
    """Map sub-nodes build through create_node_function with their own config."""
    node_fn = create_node_function(
        "rank", {"prompt": "rank", "state_key": "ranked"}, {}
    )
    with patch.object(
        llm_execution, "handle_default", wraps=llm_execution.handle_default
    ) as spy:
        result = node_fn({"items": "x"})
    assert spy.call_count == 1
    assert result["errors"] and not result["errors"][0].tolerated


# AC-06 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-715")
def test_ac06_defaults_skip_tolerates_and_continues(tmp_path, calls) -> None:
    path = _write(tmp_path, _two_llm(), "defaults:\n  on_error: skip")
    captured: list[dict] = []
    real = llm_execution.handle_error

    def spy(*args, **kwargs):
        update = real(*args, **kwargs)
        captured.append(update)
        return update

    with patch("yamlgraph.node_factory.llm_nodes._handle_error", side_effect=spy):
        final = _invoke(path)
    assert calls == ["rank", "fmt"]
    errors = final["errors"]
    assert len(errors) == 1 and errors[0].tolerated is True
    assert captured[0]["_skipped"] is True
    assert captured[0]["_skip_reason"] == "error"


@pytest.mark.req("REQ-YG-715")
def test_ac06_node_fail_overrides_defaults_skip(tmp_path, calls) -> None:
    path = _write(tmp_path, _two_llm("on_error: fail\n"), "defaults:\n  on_error: skip")
    with pytest.raises(RankError) as excinfo:
        _invoke(path)
    assert excinfo.value is BOOM
    assert calls == ["rank"]
