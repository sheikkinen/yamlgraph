---
type: feat
scope: scripts
req: REQ-YG-606
---
- **FR-851 Requirement-Witness Audit**: deterministic constructor
  (`scripts/req_audit_questions.py`) emits one frozen-schema question file
  per registry requirement with per-test resolution classes
  (coverage/ast/no-link-ran/no-link-unrecorded/doc-witness) and
  token-budgeted batches; boundary reconciliation + ranked report
  (`scripts/req_audit_report.py`) rejects hallucinated req_ids, keeps first
  duplicates, re-queues missing once then surfaces unaudited. (REQ-YG-606)
