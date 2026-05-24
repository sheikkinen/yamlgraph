---
type: fix
scope: agent
---
- **FR-459 Judge JSON output instruction**: Added explicit JSON output instruction to judge prompt so DeepSeek (and other models without `response_format` support) embed structured verdicts in their final message, enabling the `extract_json` cheap path.
