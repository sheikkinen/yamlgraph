---
type: feat
scope: provider
req: REQ-YG-010
---
- **FR-766 RunPod Provider**: New `runpod` provider targeting RunPod's OpenAI-compatible endpoints (Public API and serverless vLLM workers) via the existing `ChatOpenAI + base_url` pattern — zero new dependencies. Configured by `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT` (full base URL), and `RUNPOD_MODEL` (no hard-coded default); all three fail fast at the provider boundary. Cache keys are env-fingerprinted on key + endpoint (REQ-YG-540). The unmaintained `langchain-runpod` package was rejected: simulated streaming and skipped structured-output tests (see `docs/plan-research-runpod.md`). (REQ-YG-010)
