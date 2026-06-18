---
type: feat
scope: examples
---
- **FR-514–518 World Ledger as Agent Memory**: The DM v2 forward-carry relationship
  ledger gains update-delta semantics. The chapter close emits grounded
  `operations` (add/reaffirm/update/invalidate) instead of regenerating the whole
  relationship web; deterministic code in `world_state.py` applies them to the
  inherited ledger with a carry-forward floor (FR-514), bi-temporal
  `valid_from`/`valid_to` reconciliation that closes-and-opens on a type change
  instead of overwriting (FR-515), mechanical active→dormant decay on a chapter
  schedule (FR-517), ranked top-K cast-relevant retrieval into turn context
  (FR-516), and a grounded consolidation merge primitive (FR-518). The FR-513
  per-relationship grounding gate is preserved per-operation.
