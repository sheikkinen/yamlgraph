"""Race node factory — FR-232, FR-267, FR-271.

Creates LangGraph nodes that fire the same prompt to N provider/model
candidates concurrently and return the first successful result.

FR-271: Rewritten to asyncio so losing candidates are cooperatively
cancelled at await points after a winner is found, eliminating orphan
HTTP connections and interpreter-exit delays.
"""

import asyncio
import concurrent.futures
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from yamlgraph.constants import ErrorHandler
from yamlgraph.executor_base import build_schema_hint, prepare_messages
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.utils.content import normalize_content
from yamlgraph.utils.expressions import resolve_node_variables
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.utils.llm_factory import create_llm

logger = logging.getLogger(__name__)

# FR-707: post-verdict cleanup drain bound (module constant by Judgement F5 —
# no YAML knob until a real workload demands one) and the bridge budget margin.
CLEANUP_GRACE = 5.0
_BRIDGE_MARGIN = 1.0


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


async def _invoke_candidate_async(
    candidate: dict,
    messages: list,
    output_model: type | None,
    parse_json: bool,
    temperature: float,
) -> tuple[dict, Any]:
    """Invoke a single LLM candidate asynchronously (FR-271).

    Uses llm.ainvoke() for native cooperative cancellation at await points.
    create_llm() is called synchronously — it is pure object construction.
    """
    llm = create_llm(
        temperature=temperature,
        provider=candidate.get("provider"),
        model=candidate.get("model"),
    )
    if output_model:
        try:
            structured_llm = llm.with_structured_output(output_model)
            result = await structured_llm.ainvoke(messages)
            return candidate, result
        except Exception as struct_err:
            if "response_format" in str(struct_err):
                logger.info(
                    "Structured output rejected in race candidate %s/%s, "
                    "falling back to JSON extraction (FR-464)",
                    candidate.get("provider", "?"),
                    candidate.get("model", "?"),
                )
                from langchain_core.messages import HumanMessage

                schema_hint = build_schema_hint(output_model)
                retry_msgs = list(messages) + [HumanMessage(content=schema_hint)]
                response = await llm.ainvoke(retry_msgs)
                content = normalize_content(response.content)
                parsed = extract_json(content)
                if isinstance(parsed, dict):
                    return candidate, output_model.model_validate(parsed)
            raise
    else:
        response = await llm.ainvoke(messages)
        content = normalize_content(response.content)
        parsed = extract_json(content) if parse_json else content
        return candidate, parsed


async def _race_async(
    candidates: list[dict],
    messages: list,
    output_model: type | None,
    parse_json: bool,
    timeout: float | None,
    temperature: float,
) -> tuple[dict, Any]:
    """Return first successful candidate result; cancel remaining tasks (FR-271).

    Deadline is computed once before the loop and decremented on each
    asyncio.wait() call so it applies to the full race window, not per attempt.
    """
    loop = asyncio.get_running_loop()
    tasks: dict[asyncio.Task, dict] = {
        asyncio.create_task(
            _invoke_candidate_async(c, messages, output_model, parse_json, temperature),
            name=f"race-{c.get('provider', '?')}-{c.get('model', '?')}",
        ): c
        for c in candidates
    }
    errors: list[tuple[dict, Exception]] = []
    deadline = None if timeout is None else (loop.time() + timeout)

    try:
        while tasks:
            remaining = None if deadline is None else max(0.0, deadline - loop.time())
            done, _pending = await asyncio.wait(
                tasks.keys(),
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                # FR-705: raise where the context exists — already-failed
                # candidates keep their real exceptions; still-pending ones
                # are reported as timed out BY NAME (NC-361: forensics need
                # to know WHICH providers were pending at the deadline).
                timeout_exc = TimeoutError(f"race timed out after {timeout}s")
                raise AllCandidatesFailedError(
                    errors + [(c, timeout_exc) for c in tasks.values()]
                )

            for task in done:
                candidate = tasks.pop(task)
                try:
                    winner_candidate, winner_result = task.result()
                except Exception as exc:
                    logger.warning(
                        "Race candidate %s/%s failed: %s",
                        candidate.get("provider", "?"),
                        candidate.get("model", "?"),
                        exc,
                    )
                    errors.append((candidate, exc))
                    continue

                # Winner found — cancel all remaining losers.
                for loser in tasks:
                    loser.cancel()
                await asyncio.gather(*tasks.keys(), return_exceptions=True)
                logger.info(
                    "Race winner: %s/%s",
                    winner_candidate.get("provider", "?"),
                    winner_candidate.get("model", "?"),
                )
                return winner_candidate, winner_result

        raise AllCandidatesFailedError(errors)
    finally:
        # FR-707: cancel-only — the verdict must not wait for losers. The
        # bounded drain (and its WARNING) happens post-verdict in the bridge
        # wrapper; awaiting uncancellable losers here delayed the verdict by
        # their full lifetime (NC-361: 320–340 s).
        for task in tasks:
            task.cancel()


def _run_coro_sync_safe(coro: Any, verdict_budget: float | None = None) -> Any:
    """Run coroutine from a sync node; the caller waits for the VERDICT,
    never for cleanup (FR-707).

    The coroutine runs under asyncio.run() in a dedicated daemon thread on
    BOTH entry paths (a plain asyncio.run() in the caller would block at
    shutdown on cancellation-ignoring tasks — the NC-361 stall). Its result
    or exception is handed to the caller through a Future the moment the
    coroutine finishes; the loop's post-verdict drain (bounded by
    CLEANUP_GRACE, WARNING names what it abandons) is invisible to the
    caller.

    verdict_budget: None → wait indefinitely (a race with `timeout: null`
    has no deadline authority). On budget expiry raises RuntimeError — an
    invariant breach, deliberately NOT TimeoutError (FR-705 removed that
    handling; an anonymous bridge TimeoutError would bypass the
    on_error: skip contract).
    """
    verdict: concurrent.futures.Future[Any] = concurrent.futures.Future()

    async def _deliver() -> None:
        try:
            verdict.set_result(await coro)
        except BaseException as exc:  # noqa: BLE001 — verdict transport
            verdict.set_exception(exc)
        # Post-verdict drain: bounded, invisible to the caller.
        current = asyncio.current_task()
        pending = [t for t in asyncio.all_tasks() if t is not current]
        if pending:
            _done, still = await asyncio.wait(pending, timeout=CLEANUP_GRACE)
            if still:
                logger.warning(
                    "race cleanup abandoned %d task(s) still pending "
                    "after %.1fs: %s",
                    len(still),
                    CLEANUP_GRACE,
                    ", ".join(t.get_name() for t in still),
                )

    t = threading.Thread(
        target=lambda: asyncio.run(_deliver()), daemon=True, name="race-bridge"
    )
    t.start()
    try:
        return verdict.result(timeout=verdict_budget)
    except TimeoutError:
        if verdict.done():
            raise  # the TimeoutError IS the verdict — deliver it unrelabeled
        raise RuntimeError(
            f"race sync bridge abandoned after {verdict_budget:.1f}s — "
            "background loop failed to deliver a verdict within its "
            "guaranteed budget"
        ) from None


def create_race_node(
    node_name: str,
    node_config: dict,
    defaults: dict,
    graph_path: Path | None = None,
) -> Callable[[GraphState], dict]:
    """Create a race node function from YAML config.

    A race node fires the same prompt to N provider/model combinations
    concurrently and returns the first successful result. Losers are
    cooperatively cancelled via asyncio after the winner is found (FR-271).

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

        try:
            winner_candidate, result = _run_coro_sync_safe(
                _race_async(
                    candidates,
                    messages,
                    output_model,
                    parse_json,
                    timeout,
                    temperature,
                ),
                verdict_budget=(
                    None
                    if timeout is None
                    else timeout + CLEANUP_GRACE + _BRIDGE_MARGIN
                ),
            )
        except AllCandidatesFailedError as exc:
            if on_error == ErrorHandler.SKIP:
                # FR-705 F2: deadline expiry is what ended the race — when any
                # candidate error is a TimeoutError, preserve the skip
                # contract's TIMEOUT_ERROR classification (REQ-YG-266).
                timed_out = any(isinstance(e, TimeoutError) for _, e in exc.errors)
                return {
                    state_key: None,
                    "current_step": node_name,
                    "_loop_counts": loop_counts,
                    "errors": [
                        PipelineError.from_exception(
                            exc,
                            node=node_name,
                            error_type=(ErrorType.TIMEOUT_ERROR if timed_out else None),
                        )
                    ],
                }
            raise

        return {
            state_key: result,
            "_race_winner": {
                "provider": winner_candidate.get("provider"),
                "model": winner_candidate.get("model"),
            },
            "current_step": node_name,
            "_loop_counts": loop_counts,
        }

    node_fn.__name__ = f"{node_name}_race_node"
    return node_fn


__all__ = ["AllCandidatesFailedError", "create_race_node"]
