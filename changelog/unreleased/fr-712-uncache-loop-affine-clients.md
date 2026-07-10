---
type: fix
scope: llm
req: REQ-YG-540
---
- **FR-712 Loop-Affine Clients Uncached**: google and vertex clients are excluded from the LLM instance cache (`_UNCACHED_PROVIDERS`) — the google-genai wrapper's aiohttp session binds to the first event loop that runs it, and under the race bridge (fresh loop per call) a cached client errored on ~50% of *completed* calls (`Executor shutdown has been called` / `Timeout context manager should be used inside a task`), silently degrading the gemini race hedge. Fresh-per-call construction costs ~ms and collapses google's fresh-loop latency delta to +0.07 s (FR-711 instrument, post-fix run). Other providers keep the cache. (REQ-YG-540)
