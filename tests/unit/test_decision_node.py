"""FR-1155 decision node: typed decision questions against a decision provider.

RED-first suite (Commandment 7). Covers AC-03..AC-07 of
feature-requests/FR-1155-decision-node-calibration-audit.md:
question-config validation, Pydantic normalization at the provider
boundary, sync/async execution parity, confidence branching, and
factory import isolation.
"""

import asyncio

import pytest

# =============================================================================
# Question config validation (AC-03)
# =============================================================================


@pytest.mark.req("REQ-YG-726")
class TestQuestionConfig:
    def test_valid_noul_config(self):
        from yamlgraph.models.decision_schema import parse_question_config

        q = parse_question_config({"kind": "noul", "instructions": "Is it urgent?"})
        assert q.kind == "noul"

    def test_valid_choice_config(self):
        from yamlgraph.models.decision_schema import parse_question_config

        q = parse_question_config(
            {
                "kind": "choice",
                "instructions": "Category?",
                "options": {"billing": "Money", "bug": None},
            }
        )
        assert q.kind == "choice"
        assert set(q.options) == {"billing", "bug"}

    def test_valid_score_config(self):
        from yamlgraph.models.decision_schema import parse_question_config

        q = parse_question_config(
            {"kind": "score", "instructions": "Severity?", "levels": ["low", "high"]}
        )
        assert q.kind == "score"
        assert q.levels == ["low", "high"]

    def test_unknown_kind_rejected(self):
        from yamlgraph.models.decision_schema import parse_question_config

        with pytest.raises(ValueError, match="kind"):
            parse_question_config({"kind": "box", "instructions": "Where?"})

    def test_noul_missing_instructions_rejected(self):
        from yamlgraph.models.decision_schema import parse_question_config

        with pytest.raises(ValueError):
            parse_question_config({"kind": "noul"})

    def test_choice_empty_options_rejected(self):
        from yamlgraph.models.decision_schema import parse_question_config

        with pytest.raises(ValueError):
            parse_question_config({"kind": "choice", "options": {}})

    def test_choice_cardinality_above_255_rejected(self):
        from yamlgraph.models.decision_schema import parse_question_config

        options = {f"label_{i}": None for i in range(256)}
        with pytest.raises(ValueError, match="255"):
            parse_question_config({"kind": "choice", "options": options})

    def test_score_empty_levels_rejected(self):
        from yamlgraph.models.decision_schema import parse_question_config

        with pytest.raises(ValueError):
            parse_question_config({"kind": "score", "levels": []})


# =============================================================================
# Provider boundary normalization (AC-04) and factory isolation (AC-07)
# =============================================================================


@pytest.mark.req("REQ-YG-726")
class TestDecisionFactory:
    def test_unknown_provider_rejected(self):
        from yamlgraph.utils.decision_factory import create_decision_client

        with pytest.raises(ValueError, match="provider"):
            create_decision_client("no_such_provider")

    def test_factory_module_does_not_import_vendor_sdk(self):
        """Provider-specific imports stay lazy inside the backend branch."""
        import sys

        from yamlgraph.utils import decision_factory

        assert decision_factory is not None
        assert "system_one_adapter" not in sys.modules

    def test_mock_provider_returns_pydantic_answers(self):
        from yamlgraph.models.decision_schema import (
            ChoiceDecision,
            NoulDecision,
            ScoreDecision,
        )
        from yamlgraph.utils.decision_factory import create_decision_client

        client = create_decision_client(
            "mock",
            mock_responses=[
                {
                    "match": "invoice",
                    "answers": {
                        "urgent": {"kind": "noul", "noul": 0.9},
                        "category": {
                            "kind": "choice",
                            "choice": "billing",
                            "confidence": 0.7,
                            "probabilities": {"billing": 0.8, "bug": 0.2},
                        },
                        "severity": {
                            "kind": "score",
                            "score": 1.4,
                            "confidence": 0.5,
                            "legend": {0: "low", 1: "medium", 2: "high"},
                            "probabilities": {0: 0.1, 1: 0.5, 2: 0.4},
                        },
                    },
                }
            ],
        )
        answers = client.decide(
            state="Customer cannot export an invoice",
            questions={
                "urgent": {"kind": "noul", "instructions": "Urgent?"},
                "category": {
                    "kind": "choice",
                    "instructions": "Category?",
                    "options": {"billing": None, "bug": None},
                },
                "severity": {
                    "kind": "score",
                    "instructions": "Severity?",
                    "levels": ["low", "medium", "high"],
                },
            },
        )
        assert isinstance(answers["urgent"], NoulDecision)
        assert answers["urgent"].noul == 0.9
        assert isinstance(answers["category"], ChoiceDecision)
        assert answers["category"].choice == "billing"
        assert answers["category"].confidence == 0.7
        assert isinstance(answers["severity"], ScoreDecision)
        assert answers["severity"].score == 1.4
        assert answers["severity"].probabilities == {0: 0.1, 1: 0.5, 2: 0.4}

    def test_mock_provider_unmatched_state_raises(self):
        """No silent fallback (Commandment 6): an unmatched state raises."""
        from yamlgraph.utils.decision_factory import create_decision_client

        client = create_decision_client(
            "mock",
            mock_responses=[{"match": "never-present", "answers": {}}],
        )
        with pytest.raises(ValueError, match="[Nn]o mock response"):
            client.decide(
                state="unrelated text",
                questions={"q": {"kind": "noul", "instructions": "?"}},
            )

    def test_mock_choice_answer_outside_options_rejected(self):
        """Label membership is validated at the boundary (contract table R-2)."""
        from yamlgraph.utils.decision_factory import create_decision_client

        client = create_decision_client(
            "mock",
            mock_responses=[
                {
                    "match": "",
                    "answers": {
                        "category": {
                            "kind": "choice",
                            "choice": "unlisted",
                            "confidence": 0.9,
                            "probabilities": {"unlisted": 1.0},
                        }
                    },
                }
            ],
        )
        with pytest.raises(ValueError, match="option"):
            client.decide(
                state="anything",
                questions={
                    "category": {
                        "kind": "choice",
                        "instructions": "?",
                        "options": {"billing": None, "bug": None},
                    }
                },
            )


# =============================================================================
# Graph execution: sync/async parity (AC-05), typed state (AC-04),
# confidence branching (AC-06)
# =============================================================================

DECISION_GRAPH_YAML = """
version: "1.0"
name: decision_test
description: FR-1155 decision node unit graph

state:
  ticket: str

nodes:
  triage:
    type: decision
    provider: mock
    state_template: "{state.ticket}"
    questions:
      urgent:
        kind: noul
        instructions: "The ticket is urgent."
      category:
        kind: choice
        instructions: "Primary category of the ticket."
        options:
          billing: "Invoicing and exports"
          bug: "A defect"
    mock_responses:
      - match: "invoice"
        answers:
          urgent: {kind: noul, noul: 0.9}
          category:
            kind: choice
            choice: billing
            confidence: 0.7
            probabilities: {billing: 0.8, bug: 0.2}
      - match: "crash"
        answers:
          urgent: {kind: noul, noul: 0.4}
          category:
            kind: choice
            choice: bug
            confidence: 0.3
            probabilities: {bug: 0.55, billing: 0.45}
    state_key: triage

edges:
  - from: START
    to: triage
  - from: triage
    to: END
"""

BRANCHING_GRAPH_YAML = """
version: "1.0"
name: decision_branch_test
description: FR-1155 confidence branching unit graph

state:
  ticket: str
  outcome: str

nodes:
  triage:
    type: decision
    provider: mock
    state_template: "{state.ticket}"
    questions:
      category:
        kind: choice
        instructions: "Primary category of the ticket."
        options:
          billing: null
          bug: null
    mock_responses:
      - match: "invoice"
        answers:
          category:
            kind: choice
            choice: billing
            confidence: 0.7
            probabilities: {billing: 0.8, bug: 0.2}
      - match: "crash"
        answers:
          category:
            kind: choice
            choice: bug
            confidence: 0.3
            probabilities: {bug: 0.55, billing: 0.45}
    state_key: triage
  auto_route:
    type: passthrough
    output:
      outcome: "auto"
  human_review:
    type: passthrough
    output:
      outcome: "review"

edges:
  - from: START
    to: triage
  - from: triage
    to: auto_route
    condition: triage.category.confidence >= 0.6
  - from: triage
    to: human_review
    condition: triage.category.confidence < 0.6
  - from: auto_route
    to: END
  - from: human_review
    to: END
"""


@pytest.fixture
def decision_graph_file(tmp_path):
    f = tmp_path / "decision_test.yaml"
    f.write_text(DECISION_GRAPH_YAML, encoding="utf-8")
    return f


@pytest.fixture
def branching_graph_file(tmp_path):
    f = tmp_path / "decision_branch_test.yaml"
    f.write_text(BRANCHING_GRAPH_YAML, encoding="utf-8")
    return f


@pytest.mark.req("REQ-YG-726")
class TestDecisionNodeExecution:
    def test_sync_execution_typed_state(self, decision_graph_file):
        from yamlgraph.compile.graph_loader import load_and_compile
        from yamlgraph.models.decision_schema import ChoiceDecision, NoulDecision

        compiled = load_and_compile(decision_graph_file).compile()
        result = compiled.invoke(
            {"thread_id": "t", "ticket": "Cannot export invoice since 4.2"}
        )
        triage = result["triage"]
        assert isinstance(triage["urgent"], NoulDecision)
        assert triage["urgent"].noul == 0.9
        assert isinstance(triage["category"], ChoiceDecision)
        assert triage["category"].choice == "billing"

    def test_async_execution_matches_sync(self, decision_graph_file):
        from yamlgraph.compile.graph_loader import load_and_compile

        compiled = load_and_compile(decision_graph_file).compile()
        state = {"thread_id": "t", "ticket": "Cannot export invoice since 4.2"}
        sync_result = compiled.invoke(dict(state))
        async_result = asyncio.run(compiled.ainvoke(dict(state)))
        assert (
            sync_result["triage"]["category"].model_dump()
            == async_result["triage"]["category"].model_dump()
        )
        assert (
            sync_result["triage"]["urgent"].model_dump()
            == async_result["triage"]["urgent"].model_dump()
        )

    def test_raw_dicts_do_not_enter_state(self, decision_graph_file):
        from pydantic import BaseModel

        from yamlgraph.compile.graph_loader import load_and_compile

        compiled = load_and_compile(decision_graph_file).compile()
        result = compiled.invoke(
            {"thread_id": "t", "ticket": "Cannot export invoice since 4.2"}
        )
        for answer in result["triage"].values():
            assert isinstance(answer, BaseModel)

    def test_condition_branches_on_high_confidence(self, branching_graph_file):
        from yamlgraph.compile.graph_loader import load_and_compile

        compiled = load_and_compile(branching_graph_file).compile()
        result = compiled.invoke(
            {"thread_id": "t", "ticket": "Cannot export invoice since 4.2"}
        )
        assert result["outcome"] == "auto"

    def test_condition_branches_on_low_confidence(self, branching_graph_file):
        from yamlgraph.compile.graph_loader import load_and_compile

        compiled = load_and_compile(branching_graph_file).compile()
        result = compiled.invoke({"thread_id": "t", "ticket": "App crash on login"})
        assert result["outcome"] == "review"


# =============================================================================
# Node config validation through the graph loader (AC-03)
# =============================================================================


@pytest.mark.req("REQ-YG-726")
class TestDecisionNodeConfigValidation:
    def _load(self, tmp_path, nodes_yaml: str):
        from yamlgraph.compile.graph_loader import load_and_compile

        content = f"""
version: "1.0"
name: invalid_decision
nodes:
{nodes_yaml}
edges:
  - from: START
    to: bad
  - from: bad
    to: END
"""
        f = tmp_path / "invalid.yaml"
        f.write_text(content, encoding="utf-8")
        return load_and_compile(f)

    def test_decision_without_questions_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="question"):
            self._load(
                tmp_path,
                """
  bad:
    type: decision
    provider: mock
    state_template: "x"
    state_key: out
""",
            )

    def test_decision_without_state_key_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="state_key"):
            self._load(
                tmp_path,
                """
  bad:
    type: decision
    provider: mock
    state_template: "x"
    questions:
      q: {kind: noul, instructions: "?"}
""",
            )

    def test_decision_unknown_question_kind_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="kind"):
            self._load(
                tmp_path,
                """
  bad:
    type: decision
    provider: mock
    state_template: "x"
    questions:
      q: {kind: oracle, instructions: "?"}
    state_key: out
""",
            )
