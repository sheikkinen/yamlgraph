---
type: fix
scope: per-chapter
---
- **FR-103 Per-chapter persistence**: Restored visibility and resume capability
  - Added 6 persist functions (`persist_introduction`, `persist_doctrine`, etc.)
  - Graph flow: write→validate→save per chapter (chapters saved immediately)
  - Judge prompt returns detailed feedback (not just PASSED/FAILED)
