---
type: feat
scope: llm
req: REQ-YG-230
---
- **FR-230 Google/Vertex Thinking Budget**: Extended `thinking_budget` support to `google` and `vertex` providers. `ChatGoogleGenerativeAI` receives `thinking_budget` as a constructor kwarg when set. Temperature is not overridden for non-Anthropic providers. Schema validator now accepts `-1` (Google automatic mode) and any positive integer; rejects only values `< -1`. Linter checks W071-1, W071-2, W071-4 scoped to Anthropic only; W071-3 extended with `gemini-2.5` and `gemini-3` as thinking-capable model substrings. (REQ-YG-230)
