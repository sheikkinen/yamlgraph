"""AuditAction — run inquisitor cadence audit and update last_audit_ts."""

import asyncio
import logging
import time
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class AuditAction(BaseAction):
    """Execute inquisitor --propose and route result."""

    async def execute(self, context: dict[str, Any]) -> str:
        success_event = self.get_config_value("success", "audit_done")
        error_event = self.get_config_value("error", "error")
        machine_name = self.get_machine_name(context)
        cwd = str(context.get("main_dir", "."))

        try:
            process = await asyncio.create_subprocess_exec(
                "bash",
                ".chaplain/inquisitor.sh",
                "--propose",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await process.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] audit invocation failed: {exc}")
            return error_event

        if process.returncode != 0:
            logger.error(
                f"[{machine_name}] audit failed (exit {process.returncode}): "
                f"{stderr.decode().strip()[:200]}"
            )
            return error_event

        if stdout:
            logger.info(
                f"[{machine_name}] audit output: {stdout.decode().strip()[:200]}"
            )

        context["last_audit_ts"] = int(time.time())
        return success_event
