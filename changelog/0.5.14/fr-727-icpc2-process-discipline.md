---
type: fix
scope: examples
req: REQ-YG-555
---
- **FR-727 ICPC-2 Process-Code Discipline & Combined Codes**: meta-process rubrics (`-43, -46, -48, -69` — encounter-form descriptors and junk drawers, pinned from a full read of all 40 process titles) are verdict-capped in the reducer (demote match→partial, evidence preserved, capped entries rank behind genuine partials); process primaries gain a mechanically composed `combined_code` (K86 context + `-50` → K50, chapter A when contextless) per ICPC-2's biaxial design. Cures the FR-725-measured regression where `-48` ate symptom transcripts with perfect agreement: definitive harness baseline 22/30 from 11/30, zero residual failures involving capped codes. classify.sh runner made reinstall-proof (venv-interpreter `python -c`); crosscheck treats failed runs as data. (REQ-YG-555)
