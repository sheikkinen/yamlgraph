"""GitCommitAction — Stage, diff-check, commit, optionally capture fr_path.

Config keys:
  add_paths:       List of paths to `git add` (default: ["."])
  message:         Commit message (supports {var} substitution)
  success:         Event on successful commit
  error:           Event on failure (default: "error")
  nothing_event:   Event when nothing to commit (default: success event)
  capture_fr_path: If true, capture FR path from staged files into context['fr_path']
  cwd:             Working directory (default: context['wt_dir'])
"""

import asyncio
import logging
import re
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class GitCommitAction(BaseAction):
    """Stage files, check diff, commit, optionally capture fr_path."""

    async def execute(self, context: dict[str, Any]) -> str:
        add_paths = self.get_config_value("add_paths", ["."])
        message = self.get_config_value("message", "chore: automated commit")
        success_event = self.get_config_value("success", "committed")
        error_event = self.get_config_value("error", "error")
        nothing_event = self.get_config_value("nothing_event", success_event)
        capture_fr = self.get_config_value("capture_fr_path", False)
        cwd = self.get_config_value("cwd") or context.get("wt_dir", ".")
        machine_name = self.get_machine_name(context)

        # Substitute {var} in message
        for key, value in context.items():
            message = message.replace(f"{{{key}}}", str(value))

        # git add
        for path in add_paths:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "add",
                path,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        # Check if there's anything to commit
        proc = await asyncio.create_subprocess_exec(
            "git",
            "diff",
            "--cached",
            "--quiet",
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode == 0:
            logger.info(f"[{machine_name}] Nothing to commit")
            return nothing_event

        # Optionally capture FR path from staged files
        if capture_fr:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "diff",
                "--cached",
                "--name-only",
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                if re.match(r"feature-requests/FR-\d+", line):
                    context["fr_path"] = line.strip()
                    logger.info(f"[{machine_name}] Captured fr_path={line.strip()}")
                    break

        # Commit (write message to tmp file to avoid shell escaping issues)
        proc = await asyncio.create_subprocess_exec(
            "git",
            "commit",
            "-m",
            message,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        combined = (stdout.decode() + stderr.decode()).strip()
        if proc.returncode != 0:
            logger.error(
                f"[{machine_name}] git commit failed (rc={proc.returncode}):\n{combined}"
            )
            return error_event

        logger.info(f"[{machine_name}] Committed: {message[:60]}")
        if combined:
            logger.debug(f"[{machine_name}] pre-commit output:\n{combined}")
        return success_event
