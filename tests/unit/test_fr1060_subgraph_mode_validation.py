"""FR-1060: subgraph `mode` must be validated at the graph-schema boundary.

`SubgraphNodeConfig` owns the `Literal["invoke", "direct"]` contract and the
direct-mode mapping rule, but `GraphConfigSchema.nodes` is typed
`dict[str, NodeConfig]` (mode: `str | None`), so neither rule ever reached a
real graph. An unknown mode validated, ran, and silently took the invoke path.

Every witness here drives the CLI command functions argparse dispatches to
(C-3). Constructing `SubgraphNodeConfig` directly cannot observe whether it is
wired — that is the mirror_test trap this FR exists to close.
"""

import contextlib
import re
import shutil
from argparse import Namespace
from pathlib import Path

import pytest
import yaml

FIXTURES = Path(__file__).parent.parent / "fixtures" / "subgraph_direct_fr1058"
REFERENCE = Path(__file__).parent.parent.parent / "reference" / "graph-yaml.md"


def _graph(tmp_path: Path, **child_overrides) -> str:
    """Write a parent graph whose only subgraph node carries the overrides."""
    for src in FIXTURES.glob("*.yaml"):
        shutil.copy(src, tmp_path)
    config = yaml.safe_load((FIXTURES / "fr-1058-test.yaml").read_text())
    node = config["nodes"]["child"]
    node.pop("mode", None)
    node.update(child_overrides)
    target = tmp_path / "parent.yaml"
    target.write_text(yaml.safe_dump(config))
    return str(target)


def _validate(graph_path: str):
    """Invoke the `graph validate` CLI command; return (exit_code, output)."""
    from yamlgraph.cli.graph_validate import cmd_graph_validate

    try:
        cmd_graph_validate(Namespace(graph_path=graph_path))
    except SystemExit as exc:
        return int(exc.code or 0), None
    return 0, None


def _validate_captured(graph_path: str, capsys):
    code, _ = _validate(graph_path)
    return code, capsys.readouterr().out


def _lint_codes(graph_path: str, capsys) -> set[str]:
    """Invoke the `graph lint` CLI command; return the issue codes emitted."""
    from yamlgraph.cli.graph_validate import cmd_graph_lint

    with contextlib.suppress(SystemExit):
        cmd_graph_lint(Namespace(graph_path=[graph_path], json=False, strict=False))
    return set(re.findall(r"\[([EW]\d{3})\]", capsys.readouterr().out))


class TestUnsupportedModeIsRejected:
    """AC-01: an unsupported mode fails validation instead of degrading."""

    @pytest.mark.req("REQ-YG-685")
    @pytest.mark.parametrize("mode", ["stream", "bogus-typo"])
    def test_unsupported_mode_exits_nonzero(self, tmp_path, capsys, mode):
        code, out = _validate_captured(_graph(tmp_path, mode=mode), capsys)
        assert code != 0, f"mode={mode!r} was accepted; it silently runs as invoke"
        assert "invoke" in out and "direct" in out, (
            f"diagnostic must name the supported modes, got: {out!r}"
        )


class TestDirectModeRejectsMappings:
    """AC-02: direct mode shares the schema; mappings are a contradiction."""

    @pytest.mark.req("REQ-YG-685")
    @pytest.mark.parametrize("field", ["input_mapping", "output_mapping"])
    def test_direct_with_mapping_exits_nonzero(self, tmp_path, capsys, field):
        graph = _graph(tmp_path, mode="direct", **{field: {"phase": "phase"}})
        code, out = _validate_captured(graph, capsys)
        assert code != 0, f"mode=direct with {field} was accepted"
        assert field in out, f"diagnostic must name {field}, got: {out!r}"


class TestSupportedModesStillValidate:
    """AC-03: the wiring must not narrow what already works."""

    @pytest.mark.req("REQ-YG-685")
    @pytest.mark.parametrize("overrides", [{}, {"mode": "invoke"}, {"mode": "direct"}])
    def test_supported_mode_validates(self, tmp_path, overrides):
        code, _ = _validate(_graph(tmp_path, **overrides))
        assert code == 0, f"{overrides or 'omitted mode'} must keep validating"

    @pytest.mark.req("REQ-YG-685")
    def test_committed_fixtures_still_validate(self):
        for fixture in sorted(FIXTURES.glob("*.yaml")):
            code, _ = _validate(str(fixture))
            assert code == 0, f"{fixture.name} must remain valid"


class TestLintIsModeAware:
    """AC-04: stop advising mappings that direct mode rejects."""

    @pytest.mark.req("REQ-YG-685")
    def test_direct_mode_emits_no_mapping_warnings(self, tmp_path, capsys):
        codes = _lint_codes(_graph(tmp_path, mode="direct"), capsys)
        assert not {"W501", "W502"} & codes, (
            "lint recommends the mappings the schema rejects"
        )

    @pytest.mark.req("REQ-YG-685")
    def test_invoke_mode_still_emits_mapping_warnings(self, tmp_path, capsys):
        codes = _lint_codes(_graph(tmp_path, mode="invoke"), capsys)
        assert {"W501", "W502"} <= codes, "invoke mode still needs the advice"


def _documented_modes() -> set[str]:
    """Extract the mode values from the `type: subgraph` property table row."""
    section = REFERENCE.read_text().split("### `type: subgraph`")[1]
    row = next(
        line for line in section.splitlines() if re.match(r"\|\s*`mode`\s*\|", line)
    )
    return set(re.findall(r"`([a-z]+)`", row.split("|")[4]))


class TestReferenceMatchesSchema:
    """AC-05/AC-06: the reference row and the schema cannot drift apart."""

    @pytest.mark.req("REQ-YG-685")
    def test_documented_modes_equal_schema_literal(self):
        from typing import get_args

        from yamlgraph.models.node_schema import SubgraphNodeConfig

        schema_modes = set(get_args(SubgraphNodeConfig.model_fields["mode"].annotation))
        assert _documented_modes() == schema_modes

    @pytest.mark.req("REQ-YG-685")
    def test_direct_mode_semantics_are_documented(self):
        section = REFERENCE.read_text().split("### `type: subgraph`")[1].split("###")[0]
        assert "default" in section, "the default mode must be identified"
        for owed in ("input_mapping", "output_mapping"):
            assert owed in section
        assert re.search(r"direct.{0,200}(shares?|shared)", section, re.S | re.I), (
            "direct mode's shared-state-schema semantics must be explained"
        )
