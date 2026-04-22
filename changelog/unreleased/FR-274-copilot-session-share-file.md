---
type: fix
scope: copilot
req: REQ-YG-105
---
- **FR-274 Copilot Session ID Extraction**: Replace broken stderr-based session ID extraction with `--share` file extraction. Copilot CLI never emitted `Session: <id>` in stderr — the regex was speculative (FR-105). Now uses `--share=<tmpfile>` and parses the share file's `**Session ID:** \`<uuid>\`` format. Also removes duplicate model resolution block in `create_copilot_node()`. (REQ-YG-105)
