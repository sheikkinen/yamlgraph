---
type: feat
scope: tools
req: REQ-YG-576
---
- **FR-772 tool_call Inline Dict Args**: `tool_call.args` accepts an inline
  YAML mapping resolved per value (FR-252 semantics) — mixed literal and
  templated kwargs without a Python wrapper. Resolved values still containing
  `{state.` raise `ValueError`; empty mappings dispatch no kwargs; the string
  form is unchanged. (REQ-YG-576)
