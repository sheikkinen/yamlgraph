---
type: feat
scope: tests
req: REQ-YG-591
---
- **FR-801 Provider Readiness Preflight**: live-provider integration tests gate on a session-memoized readiness probe (one minimal completion per provider per session, `LLM_REQUEST_TIMEOUT` bracketed by `clear_cache()`); unhealthy providers surface as one legible fixture-setup skip (`provider openai not ready: RateLimitError/429`) instead of N misleading product-failure reds. (REQ-YG-591)
