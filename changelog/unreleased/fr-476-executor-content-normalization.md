---
type: fix
scope: executor
req: REQ-YG-472
---
- **FR-476 Normalize Plain-Text LLM Content at the Executor Boundary**: The sync
  (`PromptExecutor._invoke_with_retry`) and async (`invoke_async`) plain-text
  invoke paths now normalize `response.content` via the shared
  `normalize_content()` utility. Providers that return content as a list of
  part-dicts — notably Google Gemini 2.5+/3.x on Vertex, which attaches
  thought-signature parts — no longer leak the raw Python list into graph state.
  Completes FR-264's boundary normalization for the executor. (REQ-YG-472)
