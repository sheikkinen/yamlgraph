"""Stub: failure_cleanup — full integration cleanup (worktree, branch, PR, topic)."""

import asyncio
import logging

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class FailureCleanupAction(BaseAction):
    async def execute(self, context):
        machine_name = self.get_machine_name(context)
        wt_dir = context.get("wt_dir", "")
        wt_branch = context.get("wt_branch", "")
        pr_number = context.get("pr_number", "")
        topic_file = context.get("topic_file", "")

        cmds = []
        if wt_dir:
            cmds.append(
                f"bash .chaplain/lib/watcher/worktree_teardown.sh --dir {wt_dir} || true"
            )
        if wt_branch:
            cmds.append(f"git push origin --delete {wt_branch} 2>/dev/null || true")
        if pr_number:
            cmds.append(f"gh pr close {pr_number} 2>/dev/null || true")
        cmds.append("mkdir -p .chaplain/failed")
        if topic_file:
            cmds.append(
                f'[ -f "{topic_file}" ] && mv "{topic_file}" .chaplain/failed/ || true'
            )

        cmd = " && ".join(cmds)
        logger.info(f"[{machine_name}] stub failure_cleanup: full integration cleanup")

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] stub failure_cleanup crashed: {exc}")

        return self.get_config_value("success", "analyze")
