"""Stub: yamlgraph_async — instant return, no LLM call.

Creates a placeholder file in the worktree (so git_commit has content)
and returns the success event. Supports _intent_sequence for injecting
specific verdict sequences in tests.

FR-303: Follows ninchat_voice _intent_sequence pattern.
"""

import logging
import os
from datetime import UTC, datetime

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class YamlgraphAsyncAction(BaseAction):
    """Returns the success event synchronously. No LLM call, no asyncio task."""

    async def execute(self, context):
        current_state = context.get("current_state", "unknown")
        machine_name = self.get_machine_name(context)

        # Hold support (same as ninchat_voice)
        if context.get(f"_hold_yamlgraph_async_{current_state}"):
            return None

        # Intent sequence override: pop next intent if available
        intent_seq = context.get("_intent_sequence")
        if intent_seq and isinstance(intent_seq, list) and len(intent_seq) > 0:
            event = intent_seq.pop(0)
            logger.info(
                f"[{machine_name}] stub yamlgraph_async: _intent_sequence → {event}"
            )
            return event

        # Create placeholder file in worktree (stub content for git_commit)
        wt_dir = context.get("wt_dir", ".")
        if os.path.isdir(wt_dir):
            docs_dir = os.path.join(wt_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            stub_file = os.path.join(docs_dir, "watcher-integration.md")
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            # Write (not append) — ensures single trailing newline for end-of-file-fixer
            with open(stub_file, "w") as f:
                f.write(f"## {ts} — {current_state}\n")

        success_event = self.get_config_value("success", "done")
        logger.info(
            f"[{machine_name}] stub yamlgraph_async [{current_state}] → {success_event}"
        )
        return success_event
