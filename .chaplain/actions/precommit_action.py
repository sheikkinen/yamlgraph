"""PrecommitAction — Run pre-commit with retry counter.

Runs ruff + pre-commit hooks, auto-staging fixes. Retries up to max_attempts
before returning 'failed'. Tracks attempt count in context['precommit_attempt'].

Config keys:
  max_attempts: Maximum retry attempts (default: 5)
  success:      Event on clean pass
  retry:        Event when auto-fix applied and retry needed
  cwd:          Working directory (default: context['wt_dir'])
"""

import logging
import subprocess
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class PrecommitAction(BaseAction):
    """Run pre-commit hooks with retry counter."""

    async def execute(self, context: dict[str, Any]) -> str:
        max_attempts = self.get_config_value("max_attempts", 5)
        success_event = self.get_config_value("success", "finalize_done")
        retry_event = self.get_config_value("retry", "precommit_retry")
        cwd = self.get_config_value("cwd") or context.get("wt_dir", ".")
        machine_name = self.get_machine_name(context)

        attempt = context.get("precommit_attempt", 0)

        if attempt >= max_attempts:
            logger.error(
                f"[{machine_name}] Pre-commit exceeded {max_attempts} attempts"
            )
            return "error"

        # Increment attempt counter
        context["precommit_attempt"] = attempt + 1
        logger.info(f"[{machine_name}] Pre-commit attempt {attempt + 1}/{max_attempts}")

        # FR-320: Stage tracked + untracked files before running pre-commit.
        prestage = subprocess.run(  # noqa: S603
            ["git", "add", "-A"],  # noqa: S607
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if prestage.returncode != 0:
            logger.error(
                f"[{machine_name}] Failed to stage files before pre-commit:\n"
                f"{prestage.stderr.strip() or prestage.stdout.strip()}"
            )
            return "error"

        # Run pre-commit
        result = subprocess.run(  # noqa: S603
            ["pre-commit", "run", "--all-files"],  # noqa: S607
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode == 0:
            logger.info(f"[{machine_name}] Pre-commit passed")
            if result.stdout.strip():
                logger.debug(
                    f"[{machine_name}] pre-commit output:\n{result.stdout.strip()}"
                )
            return success_event

        # Pre-commit failed — log full output for debugging
        logger.warning(
            f"[{machine_name}] Pre-commit failed (attempt {attempt + 1}):\n"
            f"{result.stdout.strip()}"
        )

        # FR-310: Store failure output in context for validate-step remediation
        context["precommit_output"] = result.stdout.strip()

        # FR-320: Restage all changes so untracked auto-fixes are not dropped.
        restage = subprocess.run(  # noqa: S603
            ["git", "add", "-A"],  # noqa: S607
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if restage.returncode != 0:
            logger.error(
                f"[{machine_name}] Failed to restage files after pre-commit failure:\n"
                f"{restage.stderr.strip() or restage.stdout.strip()}"
            )
            return "error"

        return retry_event
