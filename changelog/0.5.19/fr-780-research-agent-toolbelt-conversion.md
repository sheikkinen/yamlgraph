---
type: feat
scope: examples
req: REQ-YG-579
---
- **FR-780 Research-Agent Toolbelt Conversion**: research-agent becomes the fourth shell-manifest consumer — inline truncating variants (`head -80` reads, py-only capped grep/find) replaced by the canonical `examples/shared/toolbelt/` manifests (`read_file`, `search`, `list_dir`) plus `git_log`; `count_lines` stays inline per the fit boundary. Prompts teach canonical tool names/args and scope-to-glob translation. Grounded witness: the converted agent found all 12 LLM providers with high confidence where the truncated tools previously confirmed 2. (REQ-YG-579)
