---
type: feat
scope: examples
req: REQ-YG-621
---
- **FR-878 Reversible Amnesia & Tiered Approval**: memory-curation apply now archives `forget` targets and stashes `redact` originals under an op-id shelf with schema tombstone rows in a protected `_tombstones.md`; `restore` is conflict-safe and idempotent-when-recorded; approval tier is computed from disposition content (`premise_kind` enum fails closed to tier 3) — delegated tier 1 with audit trail, human-named tier 2 for forgets, non-delegable tier 3 for export; collect emits a re-derivation advisory against forget-tombstones only. Amends FR-875 C-6. (REQ-YG-621)
