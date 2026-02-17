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

---

## 2026-02-17: FR-039 — The Bug That Wasn't

**Context:** FR-039 claimed `__pregel_send` is "sync-only" and returns `None` under `astream()`. The fix options ranged from warning logs to async variants.

**What I did:** Instead of implementing Option B (the "safe" warning-only fix), I investigated. Wrote a test script, checked LangGraph 1.0.6 internals. Discovered:
1. `__pregel_send` is NOT `None` under async — empirically proven
2. The log `FR-006: Subgraph mapped state` fires, confirming `send()` IS called
3. The "missing state" is a stream mode issue: `stream_mode="updates"` excludes accumulated state; `stream_mode="values"` includes it.

**What the original FR author did wrong:** Observed symptom ("state missing after astream"), reasoned from documentation/memory ("pregel_send is sync-only"), concluded bug exists. Never wrote a test to verify the assumption.

**The trap:** **Armchair debugging** — using mental models instead of empirical tests. The symptom was real (state missing), but the diagnosis was wrong (assumed `send=None`). A 10-line test would have shown `send` is available.

**Second trap narrowly avoided:** I almost just implemented Option B. Had I added a warning log without investigating, the warning would NEVER fire (because `send` is never `None`). The "fix" would have been no-op code, creating false confidence.

**Why the bug report seemed plausible:** The FR cited the log line as evidence: "FR-006 log fires, but send IS None." In hindsight, this was a red flag — if the log fires, the code REACHED the send() call. The author confused "state not visible" with "state not sent."

**Correction:** FR-039 closed as "Not a Bug." The actual fix is consumer education: use `stream_mode="values"` or `ainvoke()` for interrupt workflows.

**Heuristic:** When a bug report includes technical claims about internals ("X is None under Y"), verify the claim with a test before designing fixes. The symptom might be real while the diagnosis is wrong.

**Meta-heuristic:** Bug reports that propose solutions are often wrong about root cause. The solution-space narrows prematurely around a false hypothesis. Start from symptoms, not proposed fixes.

---

## 2026-02-17: Vuosikello Slot Matching — The Boundary Between Code and LLM Output

**Context:** Psykologia PS1 lesson plans showed random semester assignments (Y1-Y3 syksy/kevät scattered across PS1 topics). User reported "timing seems random." Duration (75 min) and session types were correct.

**What happened:** `load_data.py` filtered vuosikello slots with exact match: `s.get("module","").upper() == module_upper`. But the LLM-generated vuosikello had full module names like `"PS1: Toimiva ja oppiva ihminen"` instead of bare `"PS1"`. Exact match returned 0 results → fallback to ALL slots → round-robin across all 6 semesters for PS1 topics.

**The trap:** **Schema-code impedance mismatch.** The extraction prompt's schema defines `module` as a string field with description "Module code". The code assumes bare codes (`PS1`). The LLM interprets "module code" as the full identifier. Neither is wrong in isolation — the bug lives in the gap between what the LLM produces and what the code expects.

**Why it wasn't caught earlier:** The fallback `if not module_slots: module_slots = slots` was designed as a safety net but silently masked the real failure. With 0 matches, all slots became candidates, producing plausible-looking but incorrect output. No error, no warning, just wrong data — the hardest bug class.

**Second insight:** Dead code detected. `_assign_vuosikello_slot()` function was never called — the logic had been inlined into `load_data()` during a refactor but the old function was left behind. The dead function still had the old `==` match, so even if someone called it, the bug would persist.

**Fix:** Changed to `.startswith(module_upper)` — tolerant of both `"PS1"` and `"PS1: Toimiva ja oppiva ihminen"`. Removed the dead function. Added test G18 that uses the LLM output format. 29/29 GREEN.

**Heuristic:** When code consumes LLM output, use tolerant matching (prefix, contains, regex) rather than exact equality. LLMs are creative with formatting even within structured schemas. The contract should be "starts with the expected code" not "equals the expected code."

**Meta-heuristic:** Silent fallbacks that produce plausible output are worse than loud failures. A `KeyError` would have surfaced this bug on first run. The "defensive" fallback hid it across 20 lessons.
