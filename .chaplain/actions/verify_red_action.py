"""VerifyRed — run pytest and expect failure (RED state in TDD).

Config keys:
  success:  Event when tests fail as expected (default: "red_verified")
  error:    Event when tests pass unexpectedly or crash (default: "error")
"""

import asyncio
import logging

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class VerifyRedAction(BaseAction):
    """Run pytest in the worktree and expect failure (RED = success)."""

    async def execute(self, context):
        wt_dir = context.get("wt_dir", ".")
        success_event = self.get_config_value("success", "red_verified")
        error_event = self.get_config_value("error", "error")
        machine_name = self.get_machine_name(context)

        cmd = (
            f"cd {wt_dir} && python -m pytest tests/ --no-cov -x 2>&1 | tail -5; "
            f"test ${{PIPESTATUS[0]}} -ne 0"
        )
        logger.info(
            f"[{machine_name}] verify_red: expecting pytest failure in {wt_dir}"
        )

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] verify_red crashed: {exc}")
            return error_event

        if proc.returncode == 0:
            logger.info(f"[{machine_name}] verify_red: RED confirmed (tests failed)")
            return success_event

        logger.warning(f"[{machine_name}] verify_red: tests passed — RED not confirmed")
        return error_event
