---
type: fix
scope: examples
req: REQ-YG-531
---
- **FR-930 Code-Owned FR-Reference Reconciliation**: the recap demo's anti-hallucination invariant moved from a prompt instruction plus one sampled live test into `finalize_recap` — model-authored `(FR|NC)-N` tokens are reconciled against the model-visible deterministic universe (commits/referenced, churn, fr_changes, fragments; never fr_statuses), stripped when unverified, and recorded in `recap["unverified_refs"]` before the status join. The 13–283s live bare-repo witness is retired, replaced by millisecond unit witnesses of the enforcing code. (REQ-YG-531)
