"""SyncingInboxAction — sync inbox, dispatch topic, and apply audit cadence routing."""

import asyncio
import json
import logging
import time
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)

_DEFAULT_CAPTURE_KEYS = [
    "topic_file",
    "project",
    "branch_prefix",
    "work_dir",
    "test_cmd",
    "precommit_config",
    "fr_template",
    "architecture_doc",
]


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_last_json_line(stdout_text: str) -> dict[str, Any] | None:
    lines = [line for line in stdout_text.splitlines() if line.strip()]
    if not lines:
        return None
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


class SyncingInboxAction(BaseAction):
    """Run inbox sync + dispatch topic and emit cadence-aware events."""

    async def execute(self, context: dict[str, Any]) -> str:
        success_event = self.get_config_value("success", "topic_found")
        no_topics_event = self.get_config_value("error", "no_topics")
        audit_needed_event = self.get_config_value("audit_needed", "audit_needed")
        capture_keys = self.get_config_value("capture_keys", _DEFAULT_CAPTURE_KEYS)
        cadence_seconds = _coerce_int(self.get_config_value("cadence_seconds", 86400))
        machine_name = self.get_machine_name(context)

        if not isinstance(capture_keys, list):
            capture_keys = _DEFAULT_CAPTURE_KEYS

        inbox_dir = str(context.get("inbox_dir", ".chaplain/inbox"))
        processing_dir = str(
            self.get_config_value("processing_dir", ".chaplain/processing")
        )
        cwd = str(context.get("main_dir", "."))

        try:
            sync_process = await asyncio.create_subprocess_exec(
                "bash",
                ".chaplain/lib/watcher/inbox_sync.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            _, sync_stderr = await sync_process.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] inbox sync invocation failed: {exc}")
            return no_topics_event

        if sync_process.returncode != 0:
            logger.warning(
                f"[{machine_name}] inbox sync exited {sync_process.returncode}: "
                f"{sync_stderr.decode().strip()[:200]}"
            )

        try:
            dispatch_process = await asyncio.create_subprocess_exec(
                "python",
                ".chaplain/lib/watcher/dispatch_topic.py",
                "--inbox-dir",
                inbox_dir,
                "--processing-dir",
                processing_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            dispatch_stdout, dispatch_stderr = await dispatch_process.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] dispatch invocation failed: {exc}")
            return no_topics_event

        payload = _parse_last_json_line(dispatch_stdout.decode().strip())
        if payload:
            for key in capture_keys:
                if key in payload:
                    context[key] = payload[key]

        if dispatch_process.returncode == 0:
            return success_event

        stderr_text = dispatch_stderr.decode().strip()
        if stderr_text:
            logger.info(
                f"[{machine_name}] dispatch no-topic stderr: {stderr_text[:200]}"
            )

        last_audit_ts = _coerce_int(context.get("last_audit_ts", 0))
        elapsed = time.time() - last_audit_ts
        if elapsed >= cadence_seconds:
            return audit_needed_event
        return no_topics_event
