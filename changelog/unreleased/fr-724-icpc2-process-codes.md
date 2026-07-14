---
type: feat
scope: examples
req: REQ-YG-551
---
- **FR-724 ICPC-2 Process Codes (Phase 2)**: components 2–6 process rubrics (medication renewal, exams, results, administrative, referrals — 40 rubrics, 5 `PROC-C<n>` clusters, fan-out 38) join the RFE catalog. Reducer pins process-over-chapter primacy as an explicit witnessed rule (the stated reason for a renewal/admin call IS the process) and attaches `chapter_context` — the best non-process candidate — to process primaries in code. HP-36 renewal fixture flips from low_confidence to `-50 Medication/prescription/renewal` primary. Dropped-sigil repair ("48" → "-48") added at the catalog-membership boundary. (REQ-YG-551)
