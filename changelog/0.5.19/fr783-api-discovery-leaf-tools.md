---
type: feat
scope: examples
req: REQ-YG-585
---
- **FR-783 API Discovery Leaf Tool Manifests**: Shared tool manifests
  (`curl_probe`, `fetch_page`, `gh_code_search`, `parse_openapi`) under
  `examples/api-discovery/tools/` — the foundation layer for the API
  discovery pipeline. `curl_probe` uses a Python wrapper (curl `-w`
  braces conflict with shell runtime `str.format()`); `parse_openapi`
  provides deterministic OpenAPI spec parsing. (REQ-YG-585)
