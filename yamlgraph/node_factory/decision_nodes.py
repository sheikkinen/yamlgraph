"""FR-1155 decision node factory (REQ-YG-726).

Compiles a ``decision`` node: render the state template, ask the typed
questions through the factory-selected decision provider, and commit the
normalized Pydantic answers to state under ``state_key``.

Sync-first; LangGraph runs the same function on the async path, so sync
and async execution produce the identical normalized result (AC-05).
"""

import logging
from collections.abc import Callable
from typing import Any

from yamlgraph.models.decision_schema import parse_question_config
from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.decision_factory import DecisionProvider, create_decision_client
from yamlgraph.utils.expressions import resolve_template

logger = logging.getLogger(__name__)


def create_decision_node(
    node_name: str,
    node_config: dict[str, Any],
) -> Callable[[GraphState], dict]:
    """Create a decision node function from YAML config.

    Required config: ``provider``, ``state_template``, ``questions``,
    ``state_key`` (enforced by NodeConfig validation at load time and
    re-checked here for direct callers).
    """
    provider = node_config.get("provider")
    state_template = node_config.get("state_template")
    raw_questions = node_config.get("questions")
    state_key = node_config.get("state_key")
    loop_limit = node_config.get("loop_limit")

    if not provider:
        raise ValueError(f"Decision node '{node_name}' requires 'provider'")
    if not state_template:
        raise ValueError(f"Decision node '{node_name}' requires 'state_template'")
    if not raw_questions:
        raise ValueError(f"Decision node '{node_name}' requires 'questions'")
    if not state_key:
        raise ValueError(f"Decision node '{node_name}' requires 'state_key'")

    # Fail at compile time on invalid question configs (spec_kill).
    questions = {
        name: parse_question_config(raw) for name, raw in raw_questions.items()
    }

    client_holder: dict[str, DecisionProvider] = {}

    def _client() -> DecisionProvider:
        # Lazy: real backends may open network resources; creating them at
        # compile time would make `graph lint` touch the network.
        if "client" not in client_holder:
            client_holder["client"] = create_decision_client(
                provider,
                mock_responses=node_config.get("mock_responses"),
                model=node_config.get("model"),
            )
        return client_holder["client"]

    def node_fn(state: GraphState) -> dict:
        from yamlgraph.error_handlers import check_loop_limit, handle_default

        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)
        if check_loop_limit(node_name, loop_limit, current_count):
            return {"_loop_limit_reached": True, "current_step": node_name}
        loop_counts[node_name] = current_count + 1

        rendered = str(resolve_template(state_template, state))
        try:
            answers = _client().decide(state=rendered, questions=questions)
        except Exception as e:
            # Structured record (PipelineError) then fail fast — a decision
            # the graph was going to branch on is never silently substituted.
            handle_default(node_name, e)
            raise

        logger.debug("Decision node '%s' answered %s", node_name, sorted(answers))
        logger.info("Node %s completed successfully", node_name)
        return {
            state_key: answers,
            "current_step": node_name,
            "_loop_counts": loop_counts,
        }

    return node_fn
