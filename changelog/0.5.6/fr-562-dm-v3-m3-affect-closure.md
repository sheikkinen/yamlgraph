---
type: feat
scope: examples
---
- **FR-562 DM v3 M3 -- affect closure**: the fourth and final hand-written narrative check. A pure,
  engine-free `validate._check_affect_closure(plan, order)` flags every opened affect unit
  (`AffectDelta(op="open", char, kind)`) with no later `close` of the same `(char, kind)` as a new
  `unclosed_affect` flaw localized to the opening beat -- the dropped-confrontation class. A typed
  per-unit `PlotPlan.intentional_open` allowlist exempts deliberately unresolved endings (a global
  flag would gut the check). The check is an ordered pop-walk, not a symmetric count, so a
  close-then-reopen of the same unit is residual debt on the reopening beat. The report gains an
  affect-ledger column (opened-at / closed-at / debt). Completes the four-check narrative validator
  half (lifecycle, grounding, antecedent, closure); `unreachable`/`causal_threat` remain planner-owned.
