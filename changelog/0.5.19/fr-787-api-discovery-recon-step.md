---
type: feat
scope: examples
req: REQ-YG-592
---
- **FR-787 API Discovery Recon Step**: single-agent recon graph under `examples/api-discovery/steps/recon/` mines GitHub code search (FR-783 `gh_code_search`) for prior-art evidence — candidate URLs, auth patterns, schema hints — returning `ReconResult` (four required `list[str]` fields; empty lists valid; evidence strings carry repo/path/URL identity). Exposed to the orchestrator as an optional graph-runtime manifest `recon.tool.yaml`. Live smoke reproduced the THL Sotkanet case: `sotkanet.fi/rest/1.1` endpoints, no-auth pattern, JSON/CSV hints. (REQ-YG-592)
