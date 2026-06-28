---
type: feat
scope: examples
---
- **FR-571 Plot Modeller schema + validators**: Typed core for the Plot Modeller
  — 17-kind FunctionKind enum, 6-kind AffectKind enum, relational `toward`,
  `held: bool | str` beliefs, `extra="forbid"` on all models. Validators for
  monotonic lifecycle, belief grounding, affect closure (policy-aware). Deliberate
  fork from DM schema. 30 tests, all 4 ground-truth fixtures parse cleanly.
