"""opencode CLI backend for the copilot node (FR-1048).

``backend: opencode`` spawns ``opencode run <prompt> --format json`` and maps
the JSONL event stream through a typed, fail-closed state machine into the
existing ``CopilotResult``. Two boundaries are enforced here, both derived
from the committed raw probe ``feature-requests/evidence/FR-1048-opencode-cli-probe.md``:

* **Exact-version preflight** (REQ-YG-679): the whole ``--version`` banner is
  compared against the pinned set before every run; widening needs a new
  capture.
* **Provider-key payer** (REQ-YG-681): the child environment is *not* stripped
  of provider credentials (they are the payer); the resolved ``--model`` is a
  compile-time requirement enforced in ``create_copilot_node`` and always
  emitted here.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from yamlgraph.models.schemas import CopilotResult, OpenCodeCliFlags
from yamlgraph.utils.expressions import resolve_state_expression

logger = logging.getLogger(__name__)

# Pinned from `opencode --version` on the probed host (evidence §1). Widening
# this set requires a new evidence capture on the new version.
OPENCODE_SUPPORTED_BANNERS: frozenset[str] = frozenset({"1.18.31"})

_PROBE_TIMEOUT_S = 30
_HEAD = 200

# Frozen event vocabulary (evidence §11). Any other `type` or `part.type` or
# `step_finish.reason` is a failure, not silently ignored.
_STEP_FINISH_REASONS: frozenset[str] = frozenset({"stop", "tool-calls"})


class _StepStartPart(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    type: Literal["step-start"]


class _TextPart(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    type: Literal["text"]
    text: str


class _ToolUsePart(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    type: Literal["tool"]


class _StepFinishPart(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    type: Literal["step-finish"]
    reason: str


class _ErrorData(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    message: str


class _ErrorBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    name: str
    data: _ErrorData


class _BaseEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    sessionID: str  # noqa: N815 - vendor field name


class _StepStartEvent(_BaseEvent):
    type: Literal["step_start"]
    part: _StepStartPart


class _TextEvent(_BaseEvent):
    type: Literal["text"]
    part: _TextPart


class _ToolUseEvent(_BaseEvent):
    type: Literal["tool_use"]
    part: _ToolUsePart


class _StepFinishEvent(_BaseEvent):
    type: Literal["step_finish"]
    part: _StepFinishPart


class _ErrorEvent(_BaseEvent):
    type: Literal["error"]
    error: _ErrorBody


OpenCodeEvent = Annotated[
    _StepStartEvent | _TextEvent | _ToolUseEvent | _StepFinishEvent | _ErrorEvent,
    Field(discriminator="type"),
]

_EVENT_ADAPTER: TypeAdapter = TypeAdapter(OpenCodeEvent)


def validate_opencode_cli_flags(
    node_name: str, cli_flags: object, backend: str = "opencode"
) -> OpenCodeCliFlags | None:
    """Compile-time shape check (FR-1048 REQ-YG-680); raises ValueError.

    A no-op for every other backend. An explicitly blank ``model``/``resume``
    is invalid (never silently omitted); the five dropped flags and
    ``continue_session`` are rejected as extras.
    """
    if backend != "opencode":
        return None
    try:
        return OpenCodeCliFlags.model_validate(cli_flags or {})
    except ValidationError as e:
        raise ValueError(
            f"Copilot node '{node_name}': invalid cli_flags for backend 'opencode': {e}"
        ) from e


def _resolve_resume_fail_closed(
    node_name: str, resume: str | None, state: dict | None
) -> str | None:
    """Resolve a ``resume`` value fail-closed (FR-1048 REQ-YG-680).

    Unlike the Copilot helper's warn-and-drop, an unresolved ``{state.…}``
    expression, a missing path, a non-string, or an empty/whitespace result
    raises before any subprocess — dropping an invalid explicit session would
    silently start a new opencode session (evidence §10).
    """
    if resume is None:
        return None
    if "{state." not in resume:
        return resume
    if state is None:
        raise RuntimeError(
            f"[{node_name}] cannot resolve resume expression without state"
        )
    try:
        value = resolve_state_expression(resume, state)
    except (KeyError, AttributeError) as e:
        raise RuntimeError(
            f"[{node_name}] failed to resolve resume expression {resume!r}: {e}"
        ) from e
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"[{node_name}] resume expression {resume!r} resolved to "
            f"invalid value {value!r}"
        )
    return value


def _build_opencode_env(node_name: str) -> dict[str, str]:
    """Child environment: os.environ unchanged (provider keys are the payer),
    plus FR-363 OTel scoping."""
    env = dict(os.environ)
    if otel_dir := env.get("YAMLGRAPH_OTEL_DIR"):
        env["COPILOT_OTEL_FILE_EXPORTER_PATH"] = str(
            Path(otel_dir) / f"{node_name}.otel.jsonl"
        )
    return env


def _run_probe(
    node_name: str, argv: list[str], env: dict[str, str]
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(  # noqa: S603
            argv, capture_output=True, text=True, timeout=_PROBE_TIMEOUT_S, env=env
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[{node_name}] opencode binary not found. Is opencode installed "
            f"and on PATH? Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"[{node_name}] `{' '.join(argv)}` timed out after {_PROBE_TIMEOUT_S}s"
        ) from e


def _check_version(node_name: str, env: dict[str, str]) -> str:
    proc = _run_probe(node_name, ["opencode", "--version"], env)
    observed = (proc.stdout or "").strip()
    if proc.returncode != 0 or observed not in OPENCODE_SUPPORTED_BANNERS:
        raise RuntimeError(
            f"[{node_name}] unsupported opencode version {observed!r} "
            f"(exit {proc.returncode}); accepted: "
            f"{sorted(OPENCODE_SUPPORTED_BANNERS)}. Widening the set needs a "
            "new evidence capture (FR-1048 evidence file)."
        )
    return observed


def _build_opencode_argv(
    prompt: str, flags: OpenCodeCliFlags, resume: str | None
) -> list[str]:
    """Frozen argv order (evidence §12): prompt first, then flags."""
    cmd = ["opencode", "run", prompt, "--format", "json", "--model", flags.model]
    if resume:
        cmd.extend(["--session", str(resume)])
    return cmd


def _decode_event(raw: str, node_name: str) -> BaseModel:
    """Parse one stdout line into a typed event; raise on non-JSON/unknown."""
    line = raw.strip()
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"[{node_name}] opencode stream: non-JSON line: {raw[:_HEAD]!r}"
        ) from None
    try:
        return _EVENT_ADAPTER.validate_python(data)  # type: ignore[return-value]
    except ValidationError as e:
        raise RuntimeError(
            f"[{node_name}] opencode stream: malformed or unknown event: {e}"
        ) from e


def _merge_session(session_id: str | None, candidate: str, node_name: str) -> str:
    """Enforce a single consistent, non-empty sessionID across the stream."""
    if not candidate:
        raise RuntimeError(f"[{node_name}] opencode stream: empty sessionID")
    if session_id is None:
        return candidate
    if candidate != session_id:
        raise RuntimeError(
            f"[{node_name}] opencode stream: conflicting sessionID "
            f"{candidate!r} != {session_id!r}"
        )
    return session_id


def _transition(
    event: BaseModel, step_open: bool, texts: list[str], node_name: str
) -> tuple[bool, bool]:
    """Apply one event to the step state; return (step_open, terminated)."""
    if isinstance(event, _ErrorEvent):
        raise RuntimeError(
            f"[{node_name}] opencode stream: error event: "
            f"{event.error.name}: {event.error.data.message}"
        )
    if isinstance(event, _StepStartEvent):
        if step_open:
            raise RuntimeError(f"[{node_name}] opencode stream: nested step_start")
        return True, False
    if isinstance(event, _TextEvent):
        if not step_open:
            raise RuntimeError(
                f"[{node_name}] opencode stream: text outside an open step"
            )
        texts.append(event.part.text)
        return step_open, False
    if isinstance(event, _ToolUseEvent):
        if not step_open:
            raise RuntimeError(
                f"[{node_name}] opencode stream: tool_use outside an open step"
            )
        return step_open, False
    if isinstance(event, _StepFinishEvent):
        if not step_open:
            raise RuntimeError(
                f"[{node_name}] opencode stream: step_finish with no open step"
            )
        reason = event.part.reason
        if reason not in _STEP_FINISH_REASONS:
            raise RuntimeError(
                f"[{node_name}] opencode stream: unknown step_finish reason {reason!r}"
            )
        return False, reason == "stop"
    raise RuntimeError(
        f"[{node_name}] opencode stream: unknown event {event.type!r}"
    )  # pragma: no cover


def _parse_stream(node_name: str, stdout: str) -> tuple[str, str]:
    """Typed, fail-closed JSONL state machine (FR-1048 REQ-YG-679).

    Returns ``(result_text, session_id)``. Raises ``RuntimeError`` on any
    malformed/unknown event, transition violation, session-ID conflict, or
    missing terminal, with no partial result.
    """
    session_id: str | None = None
    step_open = False
    terminated = False
    texts: list[str] = []

    for raw in stdout.splitlines():
        if not raw.strip():
            continue
        event = _decode_event(raw, node_name)
        session_id = _merge_session(session_id, event.sessionID, node_name)  # type: ignore[attr-defined]
        if terminated:
            raise RuntimeError(
                f"[{node_name}] opencode stream: event after terminal: {event.type!r}"  # type: ignore[attr-defined]
            )
        step_open, terminated = _transition(event, step_open, texts, node_name)

    if step_open:
        raise RuntimeError(
            f"[{node_name}] opencode stream: unclosed step at end of stream"
        )
    if not terminated:
        raise RuntimeError(
            f"[{node_name}] opencode stream: ended without a terminal step_finish(stop)"
        )
    if not texts:
        raise RuntimeError(f"[{node_name}] opencode stream: no text events in stream")

    return "".join(texts), session_id  # type: ignore[return-value]


def _execute_opencode(
    node_name: str,
    prompt: str,
    state_key: str,
    cli_flags: dict,
    timeout: int,
    state: dict | None = None,
) -> dict:
    """Execute the copilot node via the opencode CLI (print mode)."""
    flags = OpenCodeCliFlags.model_validate(cli_flags or {})
    if not flags.model:
        raise RuntimeError(
            f"[{node_name}] opencode backend requires a resolved --model "
            "(compile-time fail-closed; this should have been rejected at compile)"
        )
    env = _build_opencode_env(node_name)
    version = _check_version(node_name, env)
    logger.info(
        "[%s] opencode %s; executing --model %s with timeout=%ss",
        node_name,
        version,
        flags.model,
        timeout,
    )

    resume = _resolve_resume_fail_closed(node_name, flags.resume, state)
    cmd = _build_opencode_argv(prompt, flags, resume)
    try:
        proc = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[{node_name}] opencode binary not found. Is opencode installed "
            f"and on PATH? Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"opencode CLI timed out after {timeout}s in node '{node_name}'. "
            "Consider increasing 'timeout' or simplifying the prompt."
        ) from e

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[:_HEAD]
        detail = tail
        if resume:
            detail = f"{tail} (attempted --session {resume!r})"
        raise RuntimeError(
            f"opencode CLI exit {proc.returncode} in node '{node_name}': {detail}"
        )

    result_text, session_id = _parse_stream(node_name, proc.stdout or "")
    result = CopilotResult(
        output=result_text,
        exit_code=0,
        model=flags.model,
        backend="opencode",
        session_id=session_id,
    )
    return {state_key: result, "current_step": node_name}


__all__ = [
    "OPENCODE_SUPPORTED_BANNERS",
    "_execute_opencode",
    "validate_opencode_cli_flags",
]
