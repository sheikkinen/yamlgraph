"""BashContextAction — Run bash, parse JSON stdout, merge into FSM context.

Extends BashAction pattern: runs a command, but captures the last JSON line
from stdout and merges specified keys into the FSM context dict.

Config keys:
  command:      Shell command to execute (supports {var} substitution)
  capture_keys: List of keys to extract from JSON stdout
  success:      Event name on exit 0 + valid JSON
  error:        Event name on non-zero exit or invalid JSON
  timeout:      Command timeout in seconds (default: 60)
"""

import asyncio
import json
import logging
import re
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class BashContextAction(BaseAction):
    """Execute bash command, capture JSON stdout, merge into context."""

    async def execute(self, context: dict[str, Any]) -> str:
        command = self.get_config_value("command", "")
        capture_keys = self.get_config_value("capture_keys", [])
        success_event = self.get_config_value("success", "done")
        error_event = self.get_config_value("error", "error")
        timeout = self.get_config_value("timeout", 60)
        machine_name = self.get_machine_name(context)

        # Substitute {var} placeholders from context
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))

        # Warn about unsubstituted placeholders — match {identifier} only,
        # not shell group syntax ({ cmd; }) or JSON literals ({"key": ...})
        remaining = re.findall(r"\{[a-zA-Z_]\w*\}", command)
        if remaining:
            logger.warning(f"[{machine_name}] Unsubstituted placeholders: {remaining}")

        logger.info(f"[{machine_name}] bash_context: {command[:80]}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except TimeoutError:
            logger.error(f"[{machine_name}] Command timed out after {timeout}s")
            return error_event
        except Exception as exc:
            logger.error(f"[{machine_name}] Command failed: {exc}")
            return error_event

        if process.returncode != 0:
            logger.error(
                f"[{machine_name}] exit {process.returncode}: "
                f"{stderr.decode().strip()[:200]}"
            )
            return error_event

        # Parse last non-empty line as JSON
        stdout_text = stdout.decode().strip()
        lines = [ln for ln in stdout_text.splitlines() if ln.strip()]
        if not lines:
            logger.error(f"[{machine_name}] No stdout to parse")
            return error_event

        last_line = lines[-1]
        try:
            data = json.loads(last_line)
        except json.JSONDecodeError:
            logger.error(
                f"[{machine_name}] Invalid JSON on last stdout line: {last_line[:120]}"
            )
            return error_event

        # Merge captured keys into context
        for key in capture_keys:
            if key in data:
                context[key] = data[key]
                logger.debug(f"[{machine_name}] Captured {key}={data[key]}")
            else:
                logger.warning(f"[{machine_name}] Key '{key}' not in JSON output")

        return success_event
