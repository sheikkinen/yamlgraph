## 2026-05-20: FR-424 — Changelog req frontmatter enforcement retrospective

**Context:** FR-424 improved enforcement around changelog requirement frontmatter, but the merged change did not include its canonical FR-numbered reflection. The governance signal was asymmetric: we tightened gates for documentation quality while leaving our own retrospective witness missing.

**Trap:** *working_system_inertia* with *downstream_fix*. Because the pipeline was already passing, it was tempting to treat reflection as optional and rely on later audits to catch omissions. That pushes correction downstream and normalizes small process debt until it becomes recurring audit noise.

**Heuristic:** Enforcement infrastructure changes must satisfy the same evidence contract they impose on product changes. If a gate is worthy of adding, the reflection proving why and what was learned is also worthy of shipping in the same FR.

**Seed:** Can the changelog/diary gates share a single witness manifest so FR IDs are checked once and both artifacts are required atomically at merge time?
