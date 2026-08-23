"""Race node factory — FR-232, FR-267, FR-271.

Creates LangGraph nodes that fire the same prompt to N provider/model
candidates concurrently and return the first successful result.

FR-271: Rewritten to asyncio so losing candidates are cooperatively
cancelled at await points after a winner is found, eliminating orphan
HTTP connections and interpreter-exit delays.

FR-713: the sync→async bridge substrate lives in yamlgraph.utils.bridge
(one persistent loop thread); this module keeps race semantics only.
"""

import asyncio
import functools
import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from yamlgraph.constants import ErrorHandler
from yamlgraph.executor_base import build_schema_hint, prepare_messages
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.utils.bridge import run_coro_sync_safe
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


_LS_CLIENT: Any = None


def _get_langsmith_client() -> Any:
    """Lazy singleton langsmith client (FR-720 AC-05: no module import)."""
    global _LS_CLIENT
    if _LS_CLIENT is None:
        from langsmith import Client

        _LS_CLIENT = Client()
    return _LS_CLIENT


def _tracing_enabled() -> bool:
    return (
        os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
        or os.getenv("LANGSMITH_TRACING", "").lower() == "true"
    )


def _close_cancelled_run(run_id: UUID, race_ctx: dict) -> None:
    """Close a cancelled loser's LangSmith span (FR-720).

    Tracing is ambient (no callback handle exists — Judgement F1); the
    run_id the wrapper passed to ainvoke is the handle. Enqueue-only:
    update_run is dispatched to the default executor so the teardown path
    never awaits (FR-707 discipline). Skipped cleanly when tracing is off.
    """
    if not _tracing_enabled():
        return
    try:
        client = _get_langsmith_client()
        winner = race_ctx.get("winner")
        if winner is not None:
            winner_id = f"{winner.get('provider', '?')}/{winner.get('model', '?')}"
            error = f"cancelled: lost race to {winner_id}"
            metadata = {"race_outcome": "lost", "race_winner": winner_id}
        else:
            error = "cancelled: race timed out"
            metadata = {"race_outcome": "lost"}
        asyncio.get_running_loop().run_in_executor(
            None,
            functools.partial(
                client.update_run,
                run_id=run_id,
                end_time=datetime.now(UTC),
                error=error,
                extra={"metadata": metadata},
            ),
        )
    except Exception:
        logger.warning(
            "FR-720: span closure enqueue failed for run %s", run_id, exc_info=True
        )


async def _invoke_candidate_async(
    candidate: dict,
    llm: Any,
    messages: list,
    output_model: type | None,
    parse_json: bool,
    race_ctx: dict | None = None,
) -> tuple[dict, Any]:
    """Invoke a single LLM candidate asynchronously (FR-271).

    Uses llm.ainvoke() for native cooperative cancellation at await points.
    The client is constructed OFF-loop by the caller (FR-713 F6): sync
    construction on the shared bridge loop would head-of-line block every
    concurrent race.

    FR-720: each ainvoke attempt carries a pre-generated run_id
    (config={"run_id": ...}) so a cancelled loser's LangSmith span can be
    closed — the retry is a second invocation with its own id, last
    retained (Judgement F1).
    """
    run_id = uuid4()
    try:
        if output_model:
            try:
                structured_llm = llm.with_structured_output(output_model)
                result = await structured_llm.ainvoke(
                    messages, config={"run_id": run_id}
                )
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
                    run_id = uuid4()
                    response = await llm.ainvoke(retry_msgs, config={"run_id": run_id})
                    content = normalize_content(response.content)
                    parsed = extract_json(content)
                    if isinstance(parsed, dict):
                        return candidate, output_model.model_validate(parsed)
                raise
        else:
            response = await llm.ainvoke(messages, config={"run_id": run_id})
            content = normalize_content(response.content)
            parsed = extract_json(content) if parse_json else content
            return candidate, parsed
    except asyncio.CancelledError:
        _close_cancelled_run(run_id, race_ctx or {})
        raise


def _build_candidate_llms(
    candidates: list[dict], temperature: float
) -> tuple[list[tuple[dict, Any]], list[tuple[dict, Exception]]]:
    """Construct candidate clients on the CALLER thread (FR-713 F6).

    Sync construction (including the vertex construct lock) must never run
    on the shared bridge loop. A candidate whose construction fails is a
    pre-failed entry in the race's error accounting, not a node failure —
    the race can still be won by the remaining candidates.
    """
    armed: list[tuple[dict, Any]] = []
    pre_errors: list[tuple[dict, Exception]] = []
    for candidate in candidates:
        try:
            llm = create_llm(
                temperature=temperature,
                provider=candidate.get("provider"),
                model=candidate.get("model"),
            )
        except Exception as exc:
            logger.warning(
                "Race candidate %s/%s failed to construct: %s",
                candidate.get("provider", "?"),
                candidate.get("model", "?"),
                exc,
            )
            pre_errors.append((candidate, exc))
            continue
        armed.append((candidate, llm))
    return armed, pre_errors


async def _race_async(
    armed: list[tuple[dict, Any]],
    messages: list,
    output_model: type | None,
    parse_json: bool,
    timeout: float | None,
    pre_errors: list[tuple[dict, Exception]] | None = None,
) -> tuple[dict, Any]:
    """Return first successful candidate result; cancel remaining tasks (FR-271).

    Deadline is computed once before the loop and decremented on each
    asyncio.wait() call so it applies to the full race window, not per attempt.
    """
    loop = asyncio.get_running_loop()
    # FR-720: shared context read by cancelled losers' closure handlers —
    # winner set BEFORE loser.cancel() so terminal payloads name the winner.
    race_ctx: dict[str, Any] = {"winner": None}
    tasks: dict[asyncio.Task, dict] = {
        asyncio.create_task(
            _invoke_candidate_async(
                c, llm, messages, output_model, parse_json, race_ctx
            ),
            name=f"race-{c.get('provider', '?')}-{c.get('model', '?')}",
        ): c
        for c, llm in armed
    }
    errors: list[tuple[dict, Exception]] = list(pre_errors or [])
    deadline = None if timeout is None else (loop.time() + timeout)

    if not tasks:
        raise AllCandidatesFailedError(errors)

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
                race_ctx["winner"] = winner_candidate
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
    """Race-scoped bridge entry — substrate lives in yamlgraph.utils.bridge
    (FR-713: one persistent loop thread; verdict-first contract unchanged).

    CLEANUP_GRACE is read at call time so tests may pin the drain bound.
    """
    return run_coro_sync_safe(
        coro, verdict_budget=verdict_budget, cleanup_grace=CLEANUP_GRACE
    )


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
            # FR-713 F6: construct clients on the caller thread, never on
            # the shared bridge loop.
            armed, pre_errors = _build_candidate_llms(candidates, temperature)
            winner_candidate, result = _run_coro_sync_safe(
                _race_async(
                    armed,
                    messages,
                    output_model,
                    parse_json,
                    timeout,
                    pre_errors,
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

        logger.info(f"Node {node_name} completed successfully")
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
