---
type: feat
scope: chaplain
req: REQ-YG-564
---
- **FR-745 FR Triage Graph**: `.chaplain/graphs/fr_triage/` runs the checklist tier of judgement (canon answers, pre-mortem witnesses, value-prop check) with a small model and appends dispositionable claims inside the FR — never a verdict. `triage-gate` pre-commit hook blocks Judged+ FRs carrying undispositioned `- [pending]` claims; FR-creation hook gains a reminder-only line. Kill criterion bound: review at 10th judged FR. (REQ-YG-564)
