"""Stub: changelog_gen — generates a minimal valid changelog fragment."""

import logging
import os

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class ChangelogGenAction(BaseAction):
    async def execute(self, context):
        machine_name = self.get_machine_name(context)
        wt_dir = context.get("wt_dir", ".")

        # Create minimal fragment so changelog-gate passes
        frag_dir = os.path.join(wt_dir, "changelog", "unreleased")
        os.makedirs(frag_dir, exist_ok=True)
        frag = os.path.join(frag_dir, "integration-stub.md")
        if not os.path.exists(frag):
            with open(frag, "w") as f:
                f.write("---\ntype: feat\nscope: integration\n---\n")
                f.write("- **Integration**: stub changelog fragment.\n")

        success_event = self.get_config_value("success", "changelog_done")
        logger.info(f"[{machine_name}] stub changelog_gen → {success_event}")
        return success_event
