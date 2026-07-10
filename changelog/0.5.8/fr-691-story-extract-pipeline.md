---
type: feat
scope: examples
req: REQ-YG-530
---
- **FR-691 story extraction pipeline**: `story_extract.yaml` wires the derived
  story layer end to end — reload canon → 1a threads-from-synopsis → 1b reconcile
  against canon (union, cap ≤8, latent mining with justification) → 1c
  per-character throughlines, persisting `story/` artifacts before each gate
  verdict. Two gate defects the real Floodmark canon exposed were fixed under
  condemning tests: the ledger walk now allows one raise to open a thread that
  de-escalates over several releases, and distinctness keys on `(kind, carriers)`
  so a feud and a survival crisis between the same two people stay distinct.
  (REQ-YG-530)
