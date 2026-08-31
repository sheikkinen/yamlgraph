---
type: fix
scope: demos
req: REQ-YG-633
---
- **FR-940 Census Judgement Normalization**: `reduce_ledger` now normalizes judgement labels at the ledger boundary with a deterministic LLM-free algorithm (prefix strip, separator cut, grammar gate, optional caller `labels` vocabulary with canonical spelling). Non-conforming values are demoted to abstain with a frozen reason — never dropped; `raw_judgement`/`repaired` audit fields and a frozen normalization summary line record every reconciliation. The census judge/synthesis model is caller-selectable via the `model` variable with provenance carrying the effective model. (REQ-YG-633)
