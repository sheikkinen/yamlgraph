---
type: feat
scope: examples
req: REQ-YG-548
---
- **FR-722 ICPC-2 RFE Classifier**: map/reason/reduce example classifying freeform encounter transcripts into ICPC-2 Reason-for-Encounter codes. Cluster fan-out (17 chapters × components 1/7, 33 clusters) over a catalog generated locally from the Tier-1 ICPC-2e-v7.0 source — the repo ships the sha256-pinned builder, never the Wonca-copyrighted data; per-cluster LLM verdicts validate at a fully deterministic python reducer (evidence spans must quote the transcript character-for-character, codes must exist in the catalog, per-code dedup, explicit low-confidence path). Classification runs at temperature 0.1 with a contiguous-substring evidence bound (field run 6: HP-36 Finnish transcript exposed span editing-by-omission). (REQ-YG-548, REQ-YG-549, REQ-YG-550)
