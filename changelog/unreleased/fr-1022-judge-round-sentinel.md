---
type: feat
scope: judge
req: REQ-YG-668
---
- **FR-1022 Judge round sentinel**: `scripts/judge.sh` now counts
`**Verdict:**` lines in the FR's adjacent `.judgement.md` after the backend and
re-entry checks and before the lock. Rounds 1 and 2 run the judge graph as
before; from the third run on, the wrapper never launches the graph or takes the
lock — it writes the fixed verdict `REJECTED — Operator: Rethink and rewrite the
FR. It's getting too complicated as a planning document.` to the per-backend
draft and exits 77. No argument or environment variable bypasses it; the human
exits are marking the FR Rejected or re-filing a shorter plan as a new FR file.
Witness: FR-1013 (four model rounds on a 20-line docs sweep, closed unmerged,
re-filed as FR-1019). (REQ-YG-668)
