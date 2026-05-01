"""ChangelogGen — generate a changelog fragment from FR metadata.

Config keys:
  success:  Event on completion (default: "changelog_done")
  error:    Event on failure (default: "error")
"""

import asyncio
import logging

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class ChangelogGenAction(BaseAction):
    """Generate a changelog fragment from the FR path in context."""

    async def execute(self, context):
        success_event = self.get_config_value("success", "changelog_done")
        error_event = self.get_config_value("error", "error")
        machine_name = self.get_machine_name(context)
        fr_path = context.get("fr_path", "")

        cmd = f"""
FR_NUM=$(basename "{fr_path}" | grep -oE 'FR-[0-9]+' | sed 's/FR-//' || true)
FR_ID="FR-${{FR_NUM}}"
SLUG=$(basename "{fr_path}" .md | sed "s/FR-${{FR_NUM}}-//" | head -c 40)
SCOPE=$(echo "$SLUG" | cut -d- -f1)
FRAG="changelog/unreleased/fr-${{FR_NUM}}-${{SLUG}}.md"
if [ ! -f "$FRAG" ] && ! ls changelog/unreleased/fr-"${{FR_NUM}}"-*.md 1>/dev/null 2>&1; then
  REQ_ID=$(grep -l "fr: $FR_ID" capabilities/CAP-*.yaml 2>/dev/null | head -1 | xargs -I{{}} grep -oE 'REQ-YG-[0-9]+' {{}} 2>/dev/null | head -1 || true)
  mkdir -p "$(dirname "$FRAG")"
  echo "---" > "$FRAG"
  echo "type: feat" >> "$FRAG"
  echo "scope: $SCOPE" >> "$FRAG"
  [ -n "$REQ_ID" ] && echo "req: $REQ_ID" >> "$FRAG"
  echo "---" >> "$FRAG"
  echo "- **$FR_ID**: Generated changelog fragment. ($REQ_ID)" >> "$FRAG"
fi
"""

        logger.info(f"[{machine_name}] changelog_gen: generating for {fr_path}")

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        except Exception as exc:
            logger.error(f"[{machine_name}] changelog_gen crashed: {exc}")
            return error_event

        if proc.returncode != 0:
            logger.error(
                f"[{machine_name}] changelog_gen failed (exit {proc.returncode})"
            )
            return error_event

        return success_event
