# Development Diary

Metacognitive reflections on development process.

---

## 2026-02-17: FR-030 — Completionism Bias

**Context:** Needed to confirm `mode=invoke` subgraphs stream tokens with `subgraphs=True`.
**What I did:** Spent hours reading LangGraph source (`StreamMessagesHandler`, namespace filtering, callback propagation). Built a mental model. Concluded async conversion was needed. Drafted implementation plan.
**What I should have done:** Run a 10-line test. Would have taken 2 minutes.
**Root cause:** Encountered unfamiliar code → triggered "must understand everything" instinct → skipped empirical validation. This is **completionism bias** — the urge to build complete mental models before acting.
**The trap:** When asking "does X work?", the answer is a test, not source code. Source diving is for "why doesn't X work?" *after* the test fails. I confused investigation types.
**Correction:** The test passed. `subgraphs=True` already works. Phase 2 marked "Not Needed." Research was intellectually satisfying but operationally wasteful.
**Heuristic:** Before reading source, write the question as a test. If the test passes, stop. If it fails, *then* investigate.
