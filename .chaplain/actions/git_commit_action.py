"""GitCommitAction — Stage, diff-check, commit, optionally capture fr_path.

Config keys:
  add_paths:       List of paths to `git add` (default: ["."])
  message:         Commit message (supports {var} substitution)
  success:         Event on successful commit
  error:           Event on failure (default: "error")
  nothing_event:   Event when nothing to commit (default: success event)
  capture_fr_path: If true, capture FR path from staged files into context['fr_path']
  cwd:             Working directory (default: context['wt_dir'])
  max_attempts:    Max commit attempts after hook auto-fixes (default: 3, FR-311)
"""

import asyncio
import logging
import os
import re
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class GitCommitAction(BaseAction):
    """Stage files, check diff, commit, optionally capture fr_path."""

    BLOCKED_AUTHOR_NAME = "Test"
    BLOCKED_AUTHOR_EMAIL = "test@test.com"

    async def execute(self, context: dict[str, Any]) -> str:
        add_paths = self.get_config_value("add_paths", ["."])
        message = self.get_config_value("message", "chore: automated commit")
        success_event = self.get_config_value("success", "committed")
        error_event = self.get_config_value("error", "error")
        nothing_event = self.get_config_value("nothing_event", success_event)
        capture_fr = self.get_config_value("capture_fr_path", False)
        cwd = self.get_config_value("cwd") or context.get("wt_dir", ".")
        max_attempts = int(self.get_config_value("max_attempts", 3))
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
                match = re.match(r"feature-requests/(FR-\d+)", line)
                if match:
                    context["fr_path"] = line.strip()
                    fr_id = match.group(1)
                    logger.info(f"[{machine_name}] Captured fr_path={line.strip()}")
                    # Rewrite message to include FR number
                    if fr_id not in message:
                        message = f"{message} — {fr_id}"
                        logger.info(
                            f"[{machine_name}] Rewrote commit message: {message[:80]}"
                        )
                    break

        # Resolve and validate commit identity from repository git config.
        commit_env = await self._build_commit_env(cwd, machine_name)
        if commit_env is None:
            return error_event

        # Commit with retry on hook auto-fixes (FR-311)
        for attempt in range(1, max_attempts + 1):
            proc = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                message,
                cwd=cwd,
                env=commit_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            combined = (stdout.decode() + stderr.decode()).strip()

            if proc.returncode == 0:
                logger.info(f"[{machine_name}] Committed: {message[:60]}")
                if combined:
                    logger.debug(f"[{machine_name}] pre-commit output:\n{combined}")
                return success_event

            # Check if hooks modified files (recoverable)
            diff_proc = await asyncio.create_subprocess_exec(
                "git",
                "diff",
                "--name-only",
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            diff_stdout, _ = await diff_proc.communicate()
            modified_files = diff_stdout.decode().strip()

            if not modified_files:
                # Genuine failure — no hook-modified files to re-stage
                logger.error(
                    f"[{machine_name}] git commit failed (rc={proc.returncode}):"
                    f"\n{combined}"
                )
                return error_event

            if attempt < max_attempts:
                logger.info(
                    f"[{machine_name}] Hook modified files (attempt {attempt}/"
                    f"{max_attempts}), re-staging and retrying: {modified_files}"
                )
                restage_proc = await asyncio.create_subprocess_exec(
                    "git",
                    "add",
                    "-u",
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await restage_proc.communicate()
            else:
                logger.error(
                    f"[{machine_name}] git commit failed after {max_attempts}"
                    f" attempts (rc={proc.returncode}):\n{combined}"
                )

        return error_event

    async def _resolve_identity(self, cwd: str) -> tuple[str, str]:
        name = await self._git_config_get(cwd, "user.name")
        email = await self._git_config_get(cwd, "user.email")
        return name, email

    async def _build_commit_env(self, cwd: str, machine_name: str) -> dict | None:
        author_name, author_email = await self._resolve_identity(cwd)
        if not author_name:
            logger.error(
                f"[{machine_name}] Missing git user.name in {cwd}. "
                'Run: git config user.name "Your Name"'
            )
            return None
        if not author_email:
            logger.error(
                f"[{machine_name}] Missing git user.email in {cwd}. "
                'Run: git config user.email "you@example.com"'
            )
            return None
        if (
            author_name == self.BLOCKED_AUTHOR_NAME
            or author_email == self.BLOCKED_AUTHOR_EMAIL
        ):
            logger.error(
                f"[{machine_name}] Blocked git identity detected: "
                f"{author_name} <{author_email}>. "
                'Run: git config user.name "Your Name" && '
                'git config user.email "you@example.com"'
            )
            return None

        commit_env = os.environ.copy()
        commit_env.update(
            {
                "GIT_AUTHOR_NAME": author_name,
                "GIT_AUTHOR_EMAIL": author_email,
                "GIT_COMMITTER_NAME": author_name,
                "GIT_COMMITTER_EMAIL": author_email,
            }
        )
        return commit_env

    async def _git_config_get(self, cwd: str, key: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "config",
            "--get",
            key,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return ""
        return stdout.decode().strip()
