---
type: fix
scope: llm
req: REQ-YG-729
---
- **FR-1164 Report replies cut off by the output-token limit**: plain, structured, FR-464 fallback and race-candidate LLM calls whose provider reports `stop_reason=max_tokens` / `finish_reason=length|MAX_TOKENS` now raise `OutputTruncatedError` naming the output and thinking token counts and visible characters, instead of returning empty text, cut text or a parser-repaired structured model. Never retried. Docs state that thinking shares `max_tokens` on providers that count it. (REQ-YG-729)
