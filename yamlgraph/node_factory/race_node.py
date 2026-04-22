"""Race node factory — FR-232, FR-267.

Creates LangGraph nodes that fire the same prompt to N provider/model
candidates concurrently and return the first successful result.
"""

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from yamlgraph.constants import ErrorHandler
from yamlgraph.executor_base import prepare_messages
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.utils.content import normalize_content
from yamlgraph.utils.expressions import resolve_node_variables
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.utils.llm_factory import create_llm

logger = logging.getLogger(__name__)


class AllCandidatesFailedError(Exception):
    """Raised when all race candidates fail."""

    def __init__(self, errors: list[tuple[dict, Exception]]):
        self.errors = errors
        messages = [
            f"{c.get('provider', '?')}/{c.get('model', '?')}: {e}" for c, e in errors
        ]
        super().__init__(
            f"All {len(errors)} race candidates failed:\n"
            + "\n".join(f"  - {m}" for m in messages)
        )


def _invoke_candidate(
    llm: Any,
    messages: list,
    output_model: type | None,
    parse_json: bool = False,
) -> Any:
    """Invoke a single LLM candidate.

    Args:
        llm: LLM instance
        messages: Prepared messages
        output_model: Optional Pydantic model for structured output
        parse_json: If True, extract JSON from response (FR-264)

    Returns:
        LLM response (parsed model, extracted JSON, or normalized string)
    """
    if output_model:
        structured_llm = llm.with_structured_output(output_model)
        return structured_llm.invoke(messages)
    else:
        response = llm.invoke(messages)
        content = normalize_content(response.content)
        if parse_json:
            return extract_json(content)
        return content


def create_race_node(
    node_name: str,
    node_config: dict,
    defaults: dict,
    graph_path: Path | None = None,
) -> Callable[[GraphState], dict]:
    """Create a race node function from YAML config.

    A race node fires the same prompt to N provider/model combinations
    concurrently and returns the first successful result.

    Args:
        node_name: Name of the node
        node_config: Node configuration from YAML
        defaults: Default configuration values
        graph_path: Path to graph YAML file

    Returns:
        Node function compatible with LangGraph
    """
    prompt_name = node_config.get("prompt")
    state_key = node_config.get("state_key", node_name)
    candidates = node_config.get("candidates", [])
    timeout = node_config.get("timeout", 30)
    temperature = node_config.get("temperature")
    if temperature is None:
        temperature = defaults.get("temperature", 0.7)
    on_error = node_config.get("on_error")
    variable_templates = node_config.get("variables", {})
    parse_json = node_config.get("parse_json", False)

    # Resolve prompt path config
    prompts_relative = defaults.get("prompts_relative", False)
    prompts_dir = defaults.get("prompts_dir")
    if prompts_dir:
        prompts_dir = Path(prompts_dir)

    # Resolve output model (skipped when parse_json is enabled)
    if parse_json:
        output_model = None
    else:
        output_model = get_output_model_for_node(
            node_config,
            prompts_dir=prompts_dir,
            graph_path=graph_path,
            prompts_relative=prompts_relative,
        )

    def node_fn(state: dict) -> dict:
        """Race node: fire prompt to all candidates, return first success."""
        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)
        loop_counts[node_name] = current_count + 1

        variables = resolve_node_variables(variable_templates, state)

        # Prepare messages once (shared across all candidates)
        messages, _resolved_provider, _resolved_model = prepare_messages(
            prompt_name=prompt_name,
            variables=variables,
            provider=None,
            model=None,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
            state=state,
        )

        # Create LLM instances for each candidate
        llms = []
        for candidate in candidates:
            llm = create_llm(
                temperature=temperature,
                provider=candidate.get("provider"),
                model=candidate.get("model"),
            )
            llms.append(llm)

        # Race all candidates concurrently.
        # Explicit pool lifecycle: shutdown(wait=False) in finally so the winner
        # is returned immediately; loser threads finish naturally and are discarded.
        errors: list[tuple[dict, Exception]] = []

        pool = ThreadPoolExecutor(max_workers=len(llms))
        try:
            futures = {
                pool.submit(
                    _invoke_candidate, llm, messages, output_model, parse_json
                ): candidate
                for llm, candidate in zip(llms, candidates, strict=True)
            }

            try:
                for future in as_completed(futures, timeout=timeout):
                    candidate = futures[future]
                    try:
                        result = future.result()
                        logger.info(
                            "Race node %s: winner %s/%s",
                            node_name,
                            candidate.get("provider", "?"),
                            candidate.get("model", "?"),
                        )
                        return {
                            state_key: result,
                            "_race_winner": {
                                "provider": candidate.get("provider"),
                                "model": candidate.get("model"),
                            },
                            "current_step": node_name,
                            "_loop_counts": loop_counts,
                        }
                    except Exception as e:
                        logger.warning(
                            "Race candidate %s/%s failed: %s",
                            candidate.get("provider", "?"),
                            candidate.get("model", "?"),
                            e,
                        )
                        errors.append((candidate, e))
            except TimeoutError:
                timeout_exc = TimeoutError(
                    f"Race {node_name} timed out after {timeout}s"
                )
                if on_error == ErrorHandler.SKIP:
                    return {
                        state_key: None,
                        "current_step": node_name,
                        "_loop_counts": loop_counts,
                        "errors": [
                            PipelineError.from_exception(
                                timeout_exc,
                                node=node_name,
                                error_type=ErrorType.TIMEOUT_ERROR,
                            )
                        ],
                    }
                raise AllCandidatesFailedError(
                    errors + [({}, timeout_exc)]
                ) from timeout_exc
        finally:
            # Race-to-first: abandon still-running losers without waiting.
            # Loser threads die naturally when their HTTP calls return; results discarded.
            pool.shutdown(wait=False, cancel_futures=True)

        # All candidates failed
        all_failed_error = AllCandidatesFailedError(errors)

        if on_error == ErrorHandler.SKIP:
            return {
                state_key: None,
                "current_step": node_name,
                "_loop_counts": loop_counts,
                "errors": [
                    PipelineError.from_exception(all_failed_error, node=node_name)
                ],
            }

        raise all_failed_error

    node_fn.__name__ = f"{node_name}_race_node"
    return node_fn


__all__ = ["AllCandidatesFailedError", "create_race_node"]
