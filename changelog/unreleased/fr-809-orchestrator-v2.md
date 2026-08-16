---
type: feat
scope: examples
req: REQ-YG-599
---
- **FR-809 API Discovery Orchestrator v2**: `examples/api-discovery/graph.yaml`
  now composes the FR-787 recon and FR-789 browser-sniff steps as `tool_call`
  nodes. Recon is gated on a `use_recon` flag (default true; `use_recon=false`
  preserves the FR-791 v1 route exactly). Browser-sniff is entered only on
  parsed FR-810 ground truth (`page_findings.is_spa == true and
  page_findings.api_found != true`), never on candidate hints; its target URL
  is selected by a deterministic Python node, not an LLM. The terminal schema
  gains `manual_reason`; `steps_tried` copy-only discipline extends to both
  new wrappers. Boundary hardening found during live smokes: `fetch_page`
  output is byte-capped (unbounded HTML overflowed the 200k-token LLM
  context), `_parse_output` failures quote the raw offending output, and
  structured-output fallback tiers cover providers rejecting `response_format`
  and `tool_choice`. (REQ-YG-599)
