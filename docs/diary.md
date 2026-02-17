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

---

## 2026-02-17: Building the Diary — Meta on Meta

**Context:** Created this diary file and the "Distill" step in the Sermon.
**What I did:** First draft was verbose (full narrative). Revised to structured format (context/did/should/cause/trap/correction/heuristic). Changed "Reflect" to "Distill" after noticing "reflect" is overloaded AI-speak.
**Insight:** Naming instructions matters. A unique verb ("Distill") signals intent better than a generic one ("Reflect"). The word should name the *posture*, not describe the action.
**Trap avoided:** Almost made the diary performative (writing for the diary, not for insight). The friction test helps: if it's tedious to document *during* work, question whether it's worth capturing.
**Heuristic:** When naming workflow steps, prefer uncommon verbs. Generic instructions get ignored; distinct ones get remembered.

---

## 2026-02-17: FR-038 — Analysis Momentum

**Context:** Reviewed QA architecture (pre-commit, CI, Scripture). Identified gaps between doctrine and practice.
**What happened:** After listing gaps (no security scanning, CI triggers late, docs/adr/ unused), immediately proposed solutions. Then caught myself: *I had just violated the Plan-Judge-Enforce sequence while analyzing the system designed to enforce it.*
**The trap:** **Analysis momentum** — once gaps are identified, the urge to "fix them" bypasses deliberation. The gap list becomes a to-do list by inertia, not by judgment.
**Correction:** Stopped. Labeled proposals as "observation, not prescription." Created FR-038 only after explicit prompt to do so. Followed Plan → Judge → Enforce properly for the commit hook.
**Second insight:** Doctrine contained dead references (`docs/adr/`, `docs/epics/`, `purgatory/`). 31 feature requests exist; 2 ADRs. Practice had diverged. Updated Scripture to match practice, not aspirations.
**Heuristic:** Gap identification is observation, not prescription. Stop after analysis. Let the gap sit. If it matters, it will return as a real problem — and then follow the rite.
