"""YamlGraphAsyncAction — Run a yamlgraph graph and route via event_map.

Executes `yamlgraph graph run <graph>` as a subprocess, optionally mapping
the LLM output to FSM events via an event_map dict.

Config keys:
  graph:      Path to graph YAML (resolved relative to context['main_dir'])
  vars:       Dict of --var key=value pairs to pass
  success:    Default success event
  error:      Error event (default: "error")
  event_map:  Dict mapping LLM output substrings to FSM events
  timeout:    Command timeout in seconds (default: 300)
"""

import asyncio
import logging
import re
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


def _is_placeholder(value: str) -> bool:
    return bool(re.fullmatch(r"\{[A-Za-z_][A-Za-z0-9_]*\}", value))


_NORMALIZE_EMPTY_ON_UNRESOLVED = {"precommit_output", "validate_gate_output"}


class YamlgraphAsyncAction(BaseAction):
    """Execute yamlgraph graph run and route output via event_map."""

    async def execute(self, context: dict[str, Any]) -> str:
        graph = self.get_config_value("graph", "")
        var_dict = self.get_config_value("vars", {})
        success_event = self.get_config_value("success", "done")
        error_event = self.get_config_value("error", "error")
        event_map = self.get_config_value("event_map", {})
        timeout = self.get_config_value("timeout", 300)
        machine_name = self.get_machine_name(context)

        # Resolve graph path relative to main_dir
        main_dir = context.get("main_dir", ".")
        graph_path = f"{main_dir}/{graph}" if not graph.startswith("/") else graph

        # Build command
        cmd_parts = ["yamlgraph", "graph", "run", graph_path, "--full"]

        # Add --var pairs (substitute {placeholders} from context)
        for key, value in var_dict.items():
            resolved = str(value)
            for ctx_key, ctx_val in context.items():
                resolved = resolved.replace(f"{{{ctx_key}}}", str(ctx_val))
            if key in _NORMALIZE_EMPTY_ON_UNRESOLVED and _is_placeholder(resolved):
                resolved = ""
            cmd_parts.extend(["--var", f"{key}={resolved}"])
        logger.info(f"[{machine_name}] yamlgraph argv={cmd_parts[:20]}")

        # FR-314: Run in worktree dir so relative paths (fr_path etc.) resolve
        # correctly against the feature branch, not main.
        wt_dir = context.get("wt_dir")
        cwd = f"{main_dir}/{wt_dir}" if wt_dir else main_dir
        logger.debug(f"[{machine_name}] cwd={cwd}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except TimeoutError:
            logger.error(f"[{machine_name}] yamlgraph timed out after {timeout}s")
            return error_event
        except Exception as exc:
            logger.error(f"[{machine_name}] yamlgraph failed: {exc}")
            return error_event

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()

        # FR-307 AC-03: Always log exit code, stdout/stderr lengths
        logger.info(
            f"[{machine_name}] yamlgraph exit={process.returncode}, "
            f"stdout={len(stdout_text)} chars, stderr={len(stderr_text)} chars"
        )

        # FR-307 AC-01: Always log stderr when non-empty
        if stderr_text:
            logger.warning(f"[{machine_name}] yamlgraph stderr: {stderr_text[:2000]}")

        if process.returncode != 0:
            logger.error(
                f"[{machine_name}] yamlgraph exit {process.returncode}: "
                f"{stderr_text[:300]}"
            )
            return error_event

        # Route via event_map if configured
        if event_map:
            for pattern, event in event_map.items():
                if pattern in stdout_text:
                    logger.info(
                        f"[{machine_name}] event_map matched '{pattern}' → {event}"
                    )
                    logger.debug(
                        f"[{machine_name}] yamlgraph stdout: {stdout_text[:2000]}"
                    )
                    return event
            # FR-307 AC-02: Log full stdout on event_map miss
            logger.warning(
                f"[{machine_name}] No event_map match in output: {stdout_text[:2000]}"
            )

        logger.debug(f"[{machine_name}] yamlgraph stdout: {stdout_text[:2000]}")
        return success_event
