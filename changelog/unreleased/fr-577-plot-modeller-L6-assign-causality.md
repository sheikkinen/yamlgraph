---
type: feat
scope: examples
---
- **FR-577 L6 assign causality spike**: LLM-validator-retry graph assigns
  causal structure (`enables`, `motivation`, `threatens`) to classified beats.
  `validate_causality` enforces forward-only `enables` links (J:C2: a beat may
  only enable a later beat; a backward or self link is a validation failure that
  forces retry), referential integrity, orphan/missing id coverage, and
  `motivation`/`threatens` shape + agent membership via the `Motivation` schema
  (J:C3, informational). Enables recall is the gate; precision is reported as an
  over-link detector. Denominators are computed mechanically (J:C1).
