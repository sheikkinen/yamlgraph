---
type: feat
scope: examples
req: REQ-YG-557
---
- **FR-733 CWE Vulnerability Classifier**: second instance of the
  coded-classification pattern (`examples/cwe-classifier/`). View-699
  category fan-out over a locally generated cwec_v4.20 catalog
  (versioned URL + sha256 pin; 944 live weaknesses, 345 candidates —
  54 Prohibited codes stripped from candidacy at build time, per
  MITRE's own Mapping_Notes); deterministic reducer with span-alignment
  boundary, CWE-prefix sigil repair, Discouraged demote-not-drop,
  Allowed-with-Review flagging, and a ChildOf lowest-abstraction guard;
  NVD-gold crosscheck harness partitioning disagreements by MITRE usage
  (our_miss / label_questionable / gold_unscoreable). (REQ-YG-557)
