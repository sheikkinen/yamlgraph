"""FailureCleanup — move topic to failed/ directory.

Config keys:
  success:  Event on completion (default: "analyze")
  error:    Event on failure (default: "error")
"""

import asyncio
import logging

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class FailureCleanupAction(BaseAction):
    """Move failed topic to .chaplain/failed/ for forensic analysis."""

    async def execute(self, context):
        success_event = self.get_config_value("success", "analyze")
        machine_name = self.get_machine_name(context)
        topic_file = context.get("topic_file", "")

        cmd = "mkdir -p .chaplain/failed"
        if topic_file:
            cmd += f'\nif [ -n "{topic_file}" ] && [ -f "{topic_file}" ]; then\n'
            cmd += f'  mv "{topic_file}" .chaplain/failed/\n'
            cmd += "fi"

        logger.info(f"[{machine_name}] failure_cleanup: moving {topic_file} to failed/")

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] failure_cleanup crashed: {exc}")

        return success_event
