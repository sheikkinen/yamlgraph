"""Copilot runtime helpers for CLI execution and prompt rendering."""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from yamlgraph.executor_base import format_prompt
from yamlgraph.models.schemas import COPILOT_BACKENDS, CopilotResult
from yamlgraph.utils.expressions import resolve_state_expression
from yamlgraph.utils.prompts import load_prompt

logger = logging.getLogger(__name__)

# FR-274: Regex to extract session ID from --share file content
# Matches: **Session ID:** `d0137402-936d-4e5c-a3fe-27e924ef5dd2`
SHARE_FILE_SESSION_PATTERN = re.compile(
    r"\*\*Session ID:\*\*\s*`([a-f0-9-]+)`", re.IGNORECASE
)


def _extract_session_id_from_share_file(share_path: Path) -> str | None:
    """Extract session ID from Copilot CLI --share file."""
    if not share_path.exists():
        logger.debug("[session] Share file not found: %s", share_path)
        return None

    try:
        content = share_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("[session] Failed to read share file: %s", e)
        return None

    match = SHARE_FILE_SESSION_PATTERN.search(content)
    if match:
        session_id = match.group(1)
        logger.debug("[session] Extracted session ID: %s", session_id)
        return session_id

    logger.debug("[session] No session ID found in share file")
    return None


def _load_and_render_prompt(
    prompt_path: str | Path,
    variables: dict[str, Any],
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
    load_prompt_fn=load_prompt,
) -> str:
    """Load a prompt YAML file and render it with variables."""
    path_obj = Path(prompt_path)
    if path_obj.is_absolute() and path_obj.exists():
        import yaml

        with open(path_obj, encoding="utf-8") as f:
            prompt_config = yaml.safe_load(f)
    else:
        prompt_config = load_prompt_fn(
            str(prompt_path),
            prompts_dir=prompts_dir,
            graph_path=graph_path,
            prompts_relative=prompts_relative,
        )

    parts = []
    if system := prompt_config.get("system"):
        rendered_system = format_prompt(system, variables, state=variables)
        parts.append(f"System: {rendered_system}")

    if user := prompt_config.get("user"):
        rendered_user = format_prompt(user, variables, state=variables)
        parts.append(f"User: {rendered_user}")

    return "\n\n".join(parts)


def unknown_backend_message(node_name: str, value: Any) -> str:
    return (
        f"Copilot node '{node_name}': unknown backend {value!r}; "
        f"expected one of {', '.join(COPILOT_BACKENDS)}"
    )


def normalize_backend(node_name: str, value: Any) -> str:
    """Closed backend set (FR-959 REQ-YG-640): None → cli; anything else exact.

    Unknown strings, the empty string, other casings, and non-strings raise
    before any node function exists — a typo never falls through to the
    Copilot CLI. Exact match, as the schema `Literal` does (review P4).
    """
    if value is None:
        return "cli"
    if isinstance(value, str) and value in COPILOT_BACKENDS:
        return value
    raise ValueError(unknown_backend_message(node_name, value))


def _resolve_resume(node_name: str, resume: Any, state: dict[str, Any] | None) -> Any:
    """Resolve a ``cli_flags.resume`` value, expanding ``{state.…}`` (FR-105).

    Shared by the Copilot and Claude backends; behaviour unchanged from the
    original inline block (warn and drop on unresolvable expressions).
    """
    if isinstance(resume, str) and "{state." in resume:
        if state is None:
            logger.warning(
                f"[{node_name}] Cannot resolve resume expression without state"
            )
            return resume
        try:
            return resolve_state_expression(resume, state)
        except (KeyError, AttributeError) as e:
            logger.warning(f"[{node_name}] Failed to resolve resume: {e}")
            return None
    return resume


def _execute_cli(
    node_name: str,
    prompt: str,
    state_key: str,
    cli_flags: dict[str, Any],
    timeout: int,
    state: dict[str, Any] | None = None,
) -> dict:
    """Execute copilot via CLI backend."""
    cmd = ["copilot", "--silent"]

    if cli_flags.get("allow_all_paths"):
        cmd.append("--allow-all-paths")
    if cli_flags.get("allow_all_tools"):
        cmd.append("--allow-all-tools")
    if model := cli_flags.get("model"):
        cmd.extend(["--model", model])

    if cli_flags.get("resume"):
        resume = _resolve_resume(node_name, cli_flags.get("resume"), state)
        if resume:
            cmd.extend(["--resume", str(resume)])
    elif cli_flags.get("continue_session"):
        cmd.append("--continue")

    share_tmpdir = Path(tempfile.mkdtemp(prefix="yamlgraph-copilot-"))
    share_path = share_tmpdir / "session.md"
    cmd.extend(["--share", str(share_path)])
    cmd.extend(["-p", prompt])

    logger.info(f"[{node_name}] Executing copilot CLI with timeout={timeout}s")
    logger.debug(f"[{node_name}] Command: {' '.join(cmd[:5])}...")

    otel_dir = os.environ.get("YAMLGRAPH_OTEL_DIR")
    node_env = None
    if otel_dir:
        node_otel_path = Path(otel_dir) / f"{node_name}.otel.jsonl"
        node_env = {
            **os.environ,
            "COPILOT_OTEL_FILE_EXPORTER_PATH": str(node_otel_path),
        }

    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=node_env,
        )

        session_id = _extract_session_id_from_share_file(share_path)
        stdout_clean = (
            result.stdout.encode("utf-8", errors="replace").decode("utf-8")
            if result.stdout
            else ""
        )
        stderr_text = result.stderr or ""
        if (
            result.returncode == 0
            and not stdout_clean.strip()
            and "error" in stderr_text.lower()
        ):
            logger.error(
                f"[{node_name}] Copilot CLI returned exit 0 but produced no output. "
                f"stderr: {stderr_text[:500]}"
            )
            raise RuntimeError(
                f"Copilot CLI silent failure (exit 0, empty output): {stderr_text[:200]}"
            )

        copilot_result = CopilotResult(
            output=stdout_clean,
            exit_code=result.returncode,
            model=cli_flags.get("model"),
            backend="cli",
            session_id=session_id,
        )
        logger.info(
            f"[{node_name}] Copilot CLI completed with exit code {result.returncode}"
        )
        return {
            state_key: copilot_result,
            "current_step": node_name,
        }
    except FileNotFoundError as e:
        raise RuntimeError(
            f"copilot binary not found. Is GitHub Copilot CLI installed and in PATH? "
            f"Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Copilot CLI timed out after {timeout}s in node '{node_name}'. "
            f"Consider increasing 'timeout' or simplifying the prompt."
        ) from e
    finally:
        shutil.rmtree(share_tmpdir, ignore_errors=True)


__all__ = [
    "_load_and_render_prompt",
    "_execute_cli",
    "_resolve_resume",
    "normalize_backend",
    "unknown_backend_message",
]
