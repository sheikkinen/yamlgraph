---
type: feat
scope: llm
req: REQ-YG-541
---
- **FR-713 Persistent Bridge Loop (Part B)**: the LLM client cache is uniform again — the FR-712 `_UNCACHED_PROVIDERS` carve-out (google/vertex constructed fresh per call) is deleted, its justifying cause retired by Part A's persistent loop. Entropy removed: one caching rule for every provider, and the vertex Express `_masked_env` global-`os.environ` mutation window collapses from once-per-race-call to once-per-cache-key. Cache keys now embed an env fingerprint (FR-227: construction is env-sensitive) — a common set (`LLM_REQUEST_TIMEOUT`) plus a declarative per-provider var list; changing a fingerprinted var yields a new client, unchanged env is a cache hit. Witnessed by a uniform cache-identity gate, a staleness gate across providers, and a warm-cached zero-errors-over-10 google integration run on the bridge loop. (REQ-YG-541)
