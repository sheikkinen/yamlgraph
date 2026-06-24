---
type: feat
scope: examples
---
- **FR-578 L7 assign affects spike**: LLM-validator-retry graph assigns emotional
  affect operations (`eff_affect`: list of `AffectDelta`) to classified beats.
  `validate_affects` checks AffectDelta structure (closed `AffectKind` enum,
  binary `op`, `extra="forbid"`) and `char`/`toward` agent membership (J1
  write-on-success). C1: open/close balance is NOT enforced in the validator (it
  is a merge-node plan invariant, FR-579). C4: `kind` matching is exact (no
  tolerance). Affect recall is the gate; precision is reported as an
  over-emission detector (C2).
