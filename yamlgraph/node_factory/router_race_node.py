"""Router-race node helper — FR-272.

Executes a router node using the race path: fires the same prompt to N
provider/model candidates concurrently and routes based on the first
valid result. Extracted from llm_nodes.py to keep that module < 450 lines.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from yamlgraph.constants import ErrorHandler
from yamlgraph.executor_base import prepare_messages
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType
from yamlgraph.node_factory.race_node import (
    AllCandidatesFailedError,
    _race_async,
    _run_coro_sync_safe,
)

if TYPE_CHECKING:
    from yamlgraph.node_factory.llm_nodes import LLMNodeConfig

logger = logging.getLogger(__name__)


def _execute_router_race(
    cfg: LLMNodeConfig,
    node_name: str,
    variables: dict,
    state: dict,
    loop_counts: dict,
    graph_path: Path | None,
) -> dict:
    """Execute a router node using the race path (FR-272).

    Fires the same prompt to all candidates concurrently, uses the first
    successful result for routing resolution. Losers are cancelled.

    on_error semantics:
    - fail:         raises AllCandidatesFailedError
    - fallback/unset: routes via default_route, records error
    """
    # Lazy import to avoid circular dependency (llm_nodes ↔ router_race_node)
    from yamlgraph.node_factory.llm_nodes import _resolve_route

    messages, _provider, _model = prepare_messages(
        prompt_name=cfg.prompt_name,
        variables=variables,
        provider=None,
        model=None,
        graph_path=graph_path,
        prompts_dir=cfg.prompts_dir,
        prompts_relative=cfg.prompts_relative,
        state=state,
    )

    try:
        winner_candidate, result = _run_coro_sync_safe(
            _race_async(
                cfg.candidates,  # type: ignore[arg-type]
                messages,
                output_model=None,  # parse_json path only for race-router
                parse_json=cfg.parse_json,
                timeout=cfg.timeout,
                temperature=cfg.temperature,
            )
        )
    except (TimeoutError, AllCandidatesFailedError) as exc:
        if cfg.on_error == ErrorHandler.FAIL:
            # FR-705 F3: AllCandidatesFailedError already enumerates every
            # candidate by name — re-raise as-is; wrapping it in a synthetic
            # [({}, exc)] entry would collapse it back to 'All 1 … ?/?'.
            raise
        route = cfg.default_route or (
            list(cfg.routes.values())[0] if cfg.routes else None
        )
        logger.warning(
            "Router %s race failed (%s), falling back to default_route: %s",
            node_name,
            exc,
            route,
        )
        update: dict[str, Any] = {
            cfg.state_key: None,
            "current_step": node_name,
            "_loop_counts": loop_counts,
            "errors": [
                PipelineError.from_exception(
                    exc,
                    node=node_name,
                    error_type=ErrorType.TIMEOUT_ERROR
                    if isinstance(exc, TimeoutError)
                    else None,
                )
            ],
        }
        if route is not None:
            update["_route"] = route
        return update

    logger.info(
        "Router %s race winner: %s/%s",
        node_name,
        winner_candidate.get("provider", "?"),
        winner_candidate.get("model", "?"),
    )

    route, route_key = _resolve_route(cfg, result)

    return_update: dict[str, Any] = {
        cfg.state_key: route_key if route_key is not None else result,
        "current_step": node_name,
        "_loop_counts": loop_counts,
        "_race_winner": {
            "provider": winner_candidate.get("provider"),
            "model": winner_candidate.get("model"),
        },
    }
    if route is not None:
        return_update["_route"] = route
        logger.info("Router %s routing to: %s", node_name, route)

    return return_update


__all__ = ["_execute_router_race"]
