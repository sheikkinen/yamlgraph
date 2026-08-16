---
type: feat
scope: tool_call
req: REQ-YG-597
---
- **FR-810 Router-Visible Tool Call Outputs**: `parsed_key` on tool_call nodes exposes the parsed dict output of a graph-runtime tool as its own state key, routable by edge conditions. Dict outputs pass through, JSON-object strings parse, everything else fails closed per `on_error` (fail raises, skip returns the failure envelope without `parsed_key`); wrapper under `state_key` preserved unchanged. Graph tools now serialize dict/list outputs as JSON instead of Python repr. Lint `W703` warns on statically known non-graph misuse; `parse_result`/`result_key` aliases rejected by schema. (REQ-YG-597)
