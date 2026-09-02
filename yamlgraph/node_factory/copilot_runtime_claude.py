"""Claude Code CLI backend for the copilot node (FR-959).

``backend: claude`` spawns ``claude -p <prompt> --output-format json`` and
maps the JSON envelope into the existing ``CopilotResult``. Three boundaries
are enforced here, all derived from the committed raw probe
``feature-requests/evidence/FR-959-claude-auth-probe.md``:

* **Payer environment** (REQ-YG-641): the child never inherits the observed
  API-key, bearer, base-URL, or cloud-provider switches.
* **Per-invocation preflight** (REQ-YG-641): exact CLI version, then a
  fail-closed ``claude auth status`` that must report a subscription method.
  No cache — a cached pass would outlive ``claude logout`` (judgement R-2).
* **Typed envelope** (REQ-YG-639): stdout crosses ``_ClaudeEnvelope`` before
  any state update; ``is_error`` is the only failure signal in the envelope
  (``subtype`` reads ``"success"`` even on a failed run — evidence §5).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from yamlgraph.models.schemas import ClaudeCliFlags, CopilotResult
from yamlgraph.node_factory.copilot_runtime import _resolve_resume

logger = logging.getLogger(__name__)

# Pinned from `claude --version` on the probed host (evidence §1). Widening
# this set requires a new evidence capture on the new version.
CLAUDE_SUPPORTED_VERSIONS: frozenset[str] = frozenset({"2.1.255"})

# `authMethod` values that bill the Claude subscription, each pinned to a raw
# capture in the evidence file: `claude.ai` is the browser login (§2.3,
# subscriptionType reported alongside); `oauth_token` is the setup-token method
# ("requires Claude subscription", §2.7). Observed refusals: `none`, `api_key`,
# `third_party`.
CLAUDE_SUBSCRIPTION_AUTH_METHODS: frozenset[str] = frozenset(
    {"claude.ai", "oauth_token"}
)

# Stripped from the child environment for every subprocess (evidence §7).
CLAUDE_STRIPPED_ENV_VARS: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)

_PROBE_TIMEOUT_S = 30
_HEAD = 200


class _ClaudeAuthStatus(BaseModel):
    """Shape of `claude auth status` JSON (evidence §2; extra keys ignored)."""

    loggedIn: bool  # noqa: N815 - vendor field name
    authMethod: str  # noqa: N815 - vendor field name
    apiProvider: str  # noqa: N815 - vendor field name


class _ClaudeEnvelope(BaseModel):
    """Shape of the `--output-format json` result object (evidence §5)."""

    model_config = ConfigDict(strict=True)

    result: str
    session_id: str
    is_error: bool = False


def validate_claude_cli_flags(
    node_name: str, cli_flags: Any, backend: str = "claude"
) -> ClaudeCliFlags | None:
    """Compile-time shape check (judgement R-4); raises ValueError, never a probe.

    A no-op for every other backend: the Copilot and API backends keep their
    untyped ``cli_flags`` (AC-13).
    """
    if backend != "claude":
        return None
    try:
        return ClaudeCliFlags.model_validate(cli_flags or {})
    except ValidationError as e:
        raise ValueError(
            f"Copilot node '{node_name}': invalid cli_flags for backend 'claude': {e}"
        ) from e


def _build_claude_env(node_name: str) -> dict[str, str]:
    """Child environment: os.environ minus payer switches, plus FR-363 OTel."""
    env = {k: v for k, v in os.environ.items() if k not in CLAUDE_STRIPPED_ENV_VARS}
    if otel_dir := env.get("YAMLGRAPH_OTEL_DIR"):
        env["COPILOT_OTEL_FILE_EXPORTER_PATH"] = str(
            Path(otel_dir) / f"{node_name}.otel.jsonl"
        )
    return env


def _run_probe(node_name: str, argv: list[str], env: dict[str, str]):
    try:
        return subprocess.run(  # noqa: S603
            argv, capture_output=True, text=True, timeout=_PROBE_TIMEOUT_S, env=env
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[{node_name}] claude binary not found. Is Claude Code installed "
            f"and on PATH? Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"[{node_name}] `{' '.join(argv)}` timed out after {_PROBE_TIMEOUT_S}s"
        ) from e


def _check_version(node_name: str, env: dict[str, str]) -> str:
    proc = _run_probe(node_name, ["claude", "--version"], env)
    observed = (proc.stdout or "").strip()
    version = observed.split(" ", 1)[0] if observed else ""
    if proc.returncode != 0 or version not in CLAUDE_SUPPORTED_VERSIONS:
        raise RuntimeError(
            f"[{node_name}] unsupported Claude Code version {observed!r} "
            f"(exit {proc.returncode}); accepted: "
            f"{sorted(CLAUDE_SUPPORTED_VERSIONS)}. Widening the set needs a new "
            "evidence capture (FR-959 §4)."
        )
    return version


def _check_auth(node_name: str, env: dict[str, str]) -> str:
    proc = _run_probe(node_name, ["claude", "auth", "status"], env)
    stdout = proc.stdout or ""
    try:
        status = _ClaudeAuthStatus.model_validate(json.loads(stdout))
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise RuntimeError(
            f"[{node_name}] claude auth status returned no parseable JSON "
            f"(exit {proc.returncode}): {stdout[:_HEAD]!r}"
        ) from e
    if proc.returncode != 0:
        raise RuntimeError(
            f"[{node_name}] claude auth status exit {proc.returncode}; "
            f"authMethod={status.authMethod!r} apiProvider={status.apiProvider!r}"
        )
    if (
        not status.loggedIn
        or status.apiProvider != "firstParty"
        or status.authMethod not in CLAUDE_SUBSCRIPTION_AUTH_METHODS
    ):
        raise RuntimeError(
            f"[{node_name}] refusing to run: authMethod={status.authMethod!r} "
            f"apiProvider={status.apiProvider!r} is not a subscription login "
            f"(accepted: {sorted(CLAUDE_SUBSCRIPTION_AUTH_METHODS)})"
        )
    return status.authMethod


def _preflight_claude(node_name: str, env: dict[str, str]) -> tuple[str, str]:
    """Version then auth, every invocation. Returns (version, auth_method)."""
    version = _check_version(node_name, env)
    auth_method = _check_auth(node_name, env)
    return version, auth_method


def _build_claude_argv(
    prompt: str, flags: ClaudeCliFlags, resume: str | None
) -> list[str]:
    """Frozen argv order (FR-959 §3; byte-for-byte tested)."""
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if flags.model:
        cmd.extend(["--model", flags.model])
    if resume:
        cmd.extend(["--resume", str(resume)])
    elif flags.continue_session:
        cmd.append("--continue")
    if flags.tools is not None:
        cmd.extend(["--tools", ",".join(flags.tools)])
    if flags.allow_all_tools:
        cmd.append("--dangerously-skip-permissions")
    elif flags.allowed_tools:
        cmd.extend(["--allowedTools", ",".join(flags.allowed_tools)])
    if flags.allow_all_paths:
        cmd.extend(["--add-dir", str(Path.cwd())])
    if flags.max_turns:
        cmd.extend(["--max-turns", str(flags.max_turns)])
    return cmd


def _parse_envelope(node_name: str, proc) -> _ClaudeEnvelope:
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    parsed: Any = None
    try:
        parsed = json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        parsed = None

    if proc.returncode != 0:
        head = (
            parsed["result"]
            if isinstance(parsed, dict) and isinstance(parsed.get("result"), str)
            else stderr
        )
        raise RuntimeError(
            f"Claude Code CLI exit {proc.returncode} in node '{node_name}': "
            f"{head[:_HEAD]}"
        )
    if not isinstance(parsed, dict):
        raise RuntimeError(
            f"Claude Code CLI exit 0 but no JSON envelope in node '{node_name}': "
            f"{stdout[:_HEAD]!r}"
        )
    try:
        envelope = _ClaudeEnvelope.model_validate(parsed)
    except ValidationError as e:
        raise RuntimeError(
            f"Claude Code CLI exit 0 but malformed envelope in node '{node_name}': {e}"
        ) from e
    if envelope.is_error:
        raise RuntimeError(
            f"Claude Code CLI reported is_error in node '{node_name}': "
            f"{envelope.result[:_HEAD]}"
        )
    logger.debug(
        "[%s] total_cost_usd (notional under subscription): %s",
        node_name,
        parsed.get("total_cost_usd"),
    )
    return envelope


def _execute_claude(
    node_name: str,
    prompt: str,
    state_key: str,
    cli_flags: dict[str, Any],
    timeout: int,
    state: dict[str, Any] | None = None,
) -> dict:
    """Execute the copilot node via the Claude Code CLI (print mode)."""
    flags = ClaudeCliFlags.model_validate(cli_flags or {})
    env = _build_claude_env(node_name)
    version, auth_method = _preflight_claude(node_name, env)
    logger.info(
        "[%s] Claude Code %s authenticated via %s; executing with timeout=%ss",
        node_name,
        version,
        auth_method,
        timeout,
    )

    resume = _resolve_resume(node_name, flags.resume, state)
    cmd = _build_claude_argv(prompt, flags, resume)
    try:
        proc = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[{node_name}] claude binary not found. Is Claude Code installed "
            f"and on PATH? Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Claude Code CLI timed out after {timeout}s in node '{node_name}'. "
            "Consider increasing 'timeout' or simplifying the prompt."
        ) from e

    envelope = _parse_envelope(node_name, proc)
    result = CopilotResult(
        output=envelope.result,
        exit_code=0,
        model=flags.model,
        backend="claude",
        session_id=envelope.session_id,
    )
    return {state_key: result, "current_step": node_name}


__all__ = [
    "CLAUDE_STRIPPED_ENV_VARS",
    "CLAUDE_SUBSCRIPTION_AUTH_METHODS",
    "CLAUDE_SUPPORTED_VERSIONS",
    "_execute_claude",
    "validate_claude_cli_flags",
]
