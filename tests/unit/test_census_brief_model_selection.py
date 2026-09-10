"""FR-1034 RED: independent model selection for the census synthesis call.

The two LLM stages of a census have opposite shapes — many tiny classifications
versus one long structured synthesis — and until now shared one provider/model
pair. These witnesses cover the resolver's independent fallback and the
provenance rule that a brief must name the model that actually wrote it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.demos.corpus_census.brief_model_selection import (
    effective_pair,
    resolve_brief_llm,
)

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

DEMO = Path("examples/demos/corpus_census")
BASE = {"provider": "inception", "model": "mercury-2.5"}


def _ledger(tmp_path: Path) -> Path:
    """A minimal reduced-ledger JSONL for render_brief to cite against."""
    path = tmp_path / "ledger.jsonl"
    row = {"item_ref": "doc-1", "label": "invariant-store", "count": 1}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return path


def _state(tmp_path: Path, brief_model: str, *, accepted: bool) -> dict:
    """render_brief input. `accepted` picks the brief vs REJECTED artifact."""
    rows = [{"item_ref": "doc-1", "label": "invariant-store", "count": 1}]
    claims = (
        [{"text": "Most files record invariants.", "citations": ["row:doc-1"]}]
        if accepted
        else []
    )
    return {
        **BASE,
        "brief_llm": {"provider": "anthropic", "model": brief_model},
        "brief_path": str(tmp_path / "brief.md"),
        "claims": {"claims": claims},
        "brief_input": rows,
        "ledger": {"jsonl_path": str(_ledger(tmp_path))},
    }


# --- AC-01..04: independent fallback -------------------------------------


@pytest.mark.req("REQ-YG-675")
def test_no_override_returns_the_base_pair():
    assert effective_pair(dict(BASE)) == {
        "provider": "inception",
        "model": "mercury-2.5",
    }


@pytest.mark.req("REQ-YG-675")
def test_both_overrides_are_used():
    state = {**BASE, "brief_provider": "anthropic", "brief_model": "claude-sonnet-5"}
    assert effective_pair(state) == {
        "provider": "anthropic",
        "model": "claude-sonnet-5",
    }


@pytest.mark.req("REQ-YG-675")
def test_model_only_override_keeps_base_provider():
    state = {**BASE, "brief_model": "claude-sonnet-5"}
    assert effective_pair(state) == {
        "provider": "inception",
        "model": "claude-sonnet-5",
    }


@pytest.mark.req("REQ-YG-675")
def test_provider_only_override_keeps_base_model():
    state = {**BASE, "brief_provider": "anthropic"}
    assert effective_pair(state) == {
        "provider": "anthropic",
        "model": "mercury-2.5",
    }


@pytest.mark.req("REQ-YG-675")
@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_override_counts_as_absent(blank):
    """A blank value must not become a model literally named empty."""
    state = {**BASE, "brief_provider": blank, "brief_model": blank}
    assert effective_pair(state) == dict(BASE)


@pytest.mark.req("REQ-YG-675")
def test_override_values_are_trimmed():
    state = {**BASE, "brief_model": "  claude-sonnet-5  "}
    assert effective_pair(state)["model"] == "claude-sonnet-5"


@pytest.mark.req("REQ-YG-675")
@pytest.mark.parametrize("missing", ["provider", "model"])
def test_missing_base_value_raises(missing):
    state = {k: v for k, v in BASE.items() if k != missing}
    with pytest.raises(ValueError, match=missing):
        effective_pair(state)


@pytest.mark.req("REQ-YG-675")
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_base_value_raises(blank):
    with pytest.raises(ValueError, match="provider"):
        effective_pair({**BASE, "provider": blank})


@pytest.mark.req("REQ-YG-675")
def test_tool_entry_returns_the_update_keyed_by_state_key():
    """Census python tools return {state_key: value}.

    Returning the bare pair left brief_llm unset and synthesize silently fell
    back to the graph defaults — a run that looked successful and used the
    wrong model. Caught only by a live run, so it is pinned here.
    """
    assert resolve_brief_llm(dict(BASE)) == {
        "brief_llm": {"provider": "inception", "model": "mercury-2.5"}
    }


# --- AC-05: the compiled graph, not the YAML text ------------------------


@pytest.mark.req("REQ-YG-675")
def test_compiled_graph_routes_the_two_stages_separately():
    from yamlgraph.compile.graph_loader import load_graph_config

    # The graph declares two slots; loading requires them bound, as the CLI does.
    config = load_graph_config(
        str(DEMO / "graph.yaml"),
        tool_bindings={
            "discover": str(DEMO / "adapters/md-discover.tool.yaml"),
            "extract": str(DEMO / "adapters/md-extract.tool.yaml"),
        },
    )
    nodes = config.nodes

    assert nodes["synthesize"]["provider"] == "{state.brief_llm.provider}"
    assert nodes["synthesize"]["model"] == "{state.brief_llm.model}"

    judge = nodes["judge_items"]["node"]
    assert judge["provider"] == "{state.provider}"
    assert judge["model"] == "{state.model}"

    assert "resolve_brief_llm" in nodes, "the resolver node must exist"
    assert nodes["resolve_brief_llm"]["state_key"] == "brief_llm"


# --- AC-07..10: truthful provenance --------------------------------------


@pytest.mark.req("REQ-YG-675")
def test_provenance_names_the_effective_brief_model(tmp_path):
    """An overridden brief must not be stamped with the map model."""
    from examples.demos.corpus_census.tools import render_brief

    result = render_brief(_state(tmp_path, "claude-sonnet-5", accepted=True))["brief"]
    assert result["accepted"], result.get("errors")
    artifact = Path(result["artifact"]).read_text(encoding="utf-8")
    assert "claude-sonnet-5" in artifact
    assert "mercury-2.5" not in artifact, "the map model must not be stamped"


@pytest.mark.req("REQ-YG-675")
def test_rejected_artifact_also_names_the_effective_brief_model(tmp_path):
    """The REJECTED artifact renders the same metadata and must be truthful."""
    from examples.demos.corpus_census.tools import render_brief

    result = render_brief(_state(tmp_path, "claude-sonnet-5", accepted=False))["brief"]
    assert not result["accepted"]
    assert result["artifact"].endswith(".REJECTED.md")
    artifact = Path(result["artifact"]).read_text(encoding="utf-8")
    assert "claude-sonnet-5" in artifact
    assert "mercury-2.5" not in artifact


@pytest.mark.req("REQ-YG-675")
def test_provenance_unchanged_without_override(tmp_path):
    from examples.demos.corpus_census.tools import render_brief

    result = render_brief(_state(tmp_path, "mercury-2.5", accepted=True))["brief"]
    assert "mercury-2.5" in Path(result["artifact"]).read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-675")
@pytest.mark.parametrize(
    "brief_llm", [None, {}, {"provider": "anthropic"}, {"model": "  "}]
)
def test_render_brief_fails_loudly_on_unresolved_model(tmp_path, brief_llm):
    """Never silently revert to the map model after resolution."""
    from examples.demos.corpus_census.tools import render_brief

    state = {
        **BASE,
        "brief_path": str(tmp_path / "brief.md"),
        "claims": {"claims": []},
        "brief_input": [],
        "ledger": {"jsonl_path": str(_ledger(tmp_path))},
    }
    if brief_llm is not None:
        state["brief_llm"] = brief_llm
    with pytest.raises(ValueError, match="brief_llm"):
        render_brief(state)


# --- AC-11..12: the governed documents no longer make the false claim ----


@pytest.mark.req("REQ-YG-675")
@pytest.mark.parametrize(
    "path",
    [
        DEMO / "README.md",
        Path("capabilities/CAP-250-census-synthesize-tail.yaml"),
    ],
)
def test_governed_docs_do_not_call_the_synthesis_model_pinned(path):
    text = path.read_text(encoding="utf-8").lower()
    assert "pinned" not in text, f"{path} still calls the synthesis model pinned"


@pytest.mark.req("REQ-YG-675")
def test_capability_owns_the_new_requirement():
    text = Path("capabilities/CAP-250-census-synthesize-tail.yaml").read_text(
        encoding="utf-8"
    )
    assert "REQ-YG-675" in text
    assert "FR-1034" in text
