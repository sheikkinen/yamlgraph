---
type: fix
scope: providers
req: REQ-YG-732
---
- **FR-1170 Azure thinking can be turned off**: `thinking_budget: 0` on an `azure` node or race candidate now sends `reasoning_effort: "none"` instead of being silently discarded, so Azure reasoning deployments (gpt-5.x, gpt-6) accept `temperature: 0`. Omitting the field keeps the deployment default, an accepted sub-1024 budget stays a logged no-op, and `≥1024` still raises. A deployment that does not support `reasoning_effort` returns a provider error; to keep an inherited `0` off one node, set `thinking_budget: 512` on it. (REQ-YG-732)
