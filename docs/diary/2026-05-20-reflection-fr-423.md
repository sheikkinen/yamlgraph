## 2026-05-20: FR-423 — Watcher plan/judge convergence retrospective

**Context:** FR-423 strengthened watcher plan/judge convergence and judgement persistence, but the merge landed without a numbered diary witness. This left a traceability hole: implementation evidence existed in code and tests, yet the metacognitive record required by Distill was missing for future audits.

**Trap:** *partial_remediation* and *audit_as_ritual*. The team fixed the functional gap in watcher behavior, but skipped the final doctrinal artifact. That created the same failure mode we claim to prevent: audits could detect drift, but without the reflection file the remediation story stayed incomplete.

**Heuristic:** Treat diary reflection as part of the definition of done, not as post-merge documentation. If an FR is merged without its reflection witness, the system has delivered behavior but not institutional learning.

**Seed:** Should watcher2 fail enforce-phase completion when an FR-numbered diary file is absent, rather than waiting for inquisitor to discover the omission later?
