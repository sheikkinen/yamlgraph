---
type: fix
scope: scripts
---
- **FR-739 altimeter phantom witness**: a cancelled zero-token turn was
  recorded as a compaction witness, poisoning min(peaks) → ETA≈0 for
  all sessions. post=0 turns are excluded; phantom purged from the
  calibration file; surviving witnesses agree within 0.5%.
