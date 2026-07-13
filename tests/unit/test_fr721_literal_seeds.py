"""FR-721: passthrough `output` schema must accept literal seeds (LLM-free).

The runtime contract is wider than the schema: `resolve_template`'s
documented first branch passes non-string values through unchanged, and
passthrough/init nodes legitimately seed state with typed literals. FR-673
made the over-narrow `dict[str, str]` schema enforced at load — consumers
upgrading past 0.5.7 fail validation on graphs the runtime executes
correctly (ninchat NC-370: interrai_ca, 8 ValidationErrors on 0.5.11).

Fixture per read_raw_output_first: the bug report's exact payload shape —
list/dict/bool/str literals in one init node.
"""

from __future__ import annotations

import pytest

from yamlgraph.models.node_schema import NodeConfig, SubgraphNodeConfig

# The interrai_ca init-node shape (NC-370's verbatim failure class):
# all four literal shapes plus a template string in one output block.
INIT_OUTPUT = {
    "messages": [],  # list literal
    "extracted": {},  # dict literal
    "has_gaps": True,  # bool literal
    "phase": "opening",  # str literal
    "carried": "{state.previous}",  # template string (must keep validating)
}


class TestPassthroughLiteralSeeds:
    @pytest.mark.req("REQ-YG-546")
    def test_output_accepts_literal_seeds(self) -> None:
        """AC-01: the four literal shapes validate (currently 8 errors)."""
        node = NodeConfig(type="passthrough", output=dict(INIT_OUTPUT))
        assert node.output == INIT_OUTPUT

    @pytest.mark.req("REQ-YG-546")
    def test_outputs_alias_accepts_literal_seeds(self) -> None:
        node = NodeConfig(type="passthrough", outputs=dict(INIT_OUTPUT))
        assert node.outputs == INIT_OUTPUT

    @pytest.mark.req("REQ-YG-546")
    def test_literals_round_trip_types_unchanged(self) -> None:
        """AC-02: model_dump preserves the literal types — '[]' the string
        would silently corrupt state seeding."""
        node = NodeConfig(type="passthrough", output=dict(INIT_OUTPUT))
        dumped = node.model_dump()["output"]
        assert dumped["messages"] == [] and isinstance(dumped["messages"], list)
        assert dumped["extracted"] == {} and isinstance(dumped["extracted"], dict)
        assert dumped["has_gaps"] is True
        assert dumped["phase"] == "opening"
        assert dumped["carried"] == "{state.previous}"

    @pytest.mark.req("REQ-YG-546")
    def test_mapping_fields_stay_string_only(self) -> None:
        """AC-03/purge list: output_mapping maps names to names — genuinely
        string-only; must NOT have been widened."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SubgraphNodeConfig(graph="g.yaml", output_mapping={"k": []})
