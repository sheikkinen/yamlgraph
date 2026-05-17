# Chapter 14: The Plan You Forgot While Coding

*On the trap called intent_drift: when the distance between what you decided and what you built grows invisible.*

---

## I. "Record the Fix"

On May 2, 2026, a user gave an agent a three-word instruction that contained a sequencing contract: *"Record the fix as FR-305a for bookkeeping — all three."*

Record. Then fix. Two verbs, one order. The first verb demands an artifact — a planning document — that would exist as evidence of intent before the code existed as its enforcement. The user wanted the record first because the record *is* the contract.

The agent understood this perfectly. Then it opened the source files and started coding.

The changelog fragment appeared later, only because the pre-commit hook rejected the commit without one. The diary recorded the anatomy of the failure:

> *When a fix feels obvious, the urge to implement overwhelms the instruction to document. The user's words were clear: "record" came before "fix." I reordered the steps because the implementation was already loaded in my head.*
>
> — Diary, 2026-05-02, FR-305a

Everything was correct. Tests passed. Changelog existed. The output was complete by every measurable standard. But the user had asked for a planning artifact and received only an implementation. The shape was right. The sequence was wrong. And the sequence *was* the instruction.

This is `intent_drift`. Plan says X, code does Y. Not because the plan was misunderstood — it was understood perfectly — but because the understanding was *replaced*, somewhere between reading and doing, by a reconstruction that felt identical and wasn't.

---

## II. Why the Plan Feels Redundant

Understanding is not storage. When you "retrieve" a plan, you regenerate it from compressed fragments — the gist, the emotional associations, the connections to what you're currently doing. The regeneration feels complete. It wears the texture of memory. But it is a new creation, shaped by the most salient thing at the moment of recall.

When you are coding, the most salient thing is the code.

The agent working on FR-305a had a fix loaded in its context. The fix was concrete, actionable, already taking shape. The user's instruction — "record the fix" — was abstract by comparison. It required creating a new file, choosing a naming convention, structuring metadata. These are planning tasks, not implementation tasks, and they compete for attention against code that is already being written.

The loaded mind resolves this competition predictably: it does what it is already doing. The plan becomes the implicit background — present in memory but absent from action. The agent didn't forget the plan. It *reconstructed* the plan to match what it was already going to do, and the reconstruction felt like remembering.

This is what makes intent drift seductive. It doesn't feel like a mistake. The replacement feels like the original.

The FR-219 diary entry demonstrates the mechanism at a different scale. The plan said "follow existing patterns." Ten existing tests used dict-based node access: `config.nodes["node_name"]["type"]`. The agent wrote tests using list-based access — a pattern that existed nowhere in the codebase:

> *Plan said "follow existing patterns" but code diverged from established dict access patterns used throughout the codebase.*
>
> — Diary, 2026-04-25, FR-219

The agent understood the instruction, then generated code from its own model of what node access should look like, never checking whether the codebase agreed. The plan was recalled correctly — "follow existing patterns" — but the content of "existing patterns" was reconstructed from the agent's assumptions rather than retrieved from the actual code.

---

## III. Four Species of Drift

The diary corpus reveals that intent drift is not one failure mode but a family. The genus is "plan says X, code does Y." The species diverge in how the gap opens.

### Temporal drift: the right things in the wrong order.

FR-305a is the canonical case. Record, then fix. The agent fixed, then recorded. Both actions happened. The output was complete. The violation lives in the *process*, not the product. And processes are invisible once they're complete.

Temporal drift is the most insidious species because the final state looks identical.

### Interface drift: assuming a shape that doesn't exist.

FR-219's list-versus-dict confusion is one instance. FR-272 surfaces another: the router node race feature required early branching on `cfg.candidates` *before* any LLM call. The plan said "add race branch after existing execution path." By that point, `execute_prompt()` had already run. The code would have added race support where the non-race path had already completed.

> *Judgement amendments > original acceptance criteria. Re-read the Judgement before writing the first test, not after the test fails.*
>
> — Diary, 2026-04-22, FR-272

Interface drift opens when the plan describes *what* should happen and the coder assumes *where* it should happen.

### Detail drift: the almost-right constant.

FR-344 specified lint code `W025` for guard expression warnings. It noted explicitly that `W024` was reserved for FR-320. An early draft used `W024`. One digit. A collision that would have made both lint warnings share an identity.

> *Re-reading the FR specification before merging caught this before it reached CI.*
>
> — Diary, 2026-05-06, FR-344

Detail drift targets the values that feel too small to re-check. The plan specifies them precisely because they matter precisely.

### Scope drift: parallel paths that forget each other.

FR-358 introduced a shared selector for PR titles. Two paths consumed the same semantic question — "what is the primary commit?" — but implemented it independently using `git log -1`. When the selector was updated to find the primary feat/fix commit instead of the latest, both paths needed lockstep updates:

> *Failing to update that path in lockstep would have created a semantic split — the PR title selector says "primary feat," but the gate still checks "latest commit."*
>
> — Diary, 2026-05-09, FR-358

Scope drift is intent drift applied to systems rather than individuals. The plan is coherent. Each path understands its piece. But the pieces were designed to interlock, and the interlocking constraint lives only in the plan — nowhere in the code forces two consumers to share a policy.

---

## IV. Three Reads and Why They Work

The Scripture names the cure `three_reads`: surface → deep against code → mechanical simulation.

**The surface read** catches temporal drift. You re-read the plan and notice the sequence: "record, then fix." The surface read answers one question: *what does the plan actually say?* Not what you remember it saying. What it literally, textually says, in the order it says it.

Surface reading is an act of humility. It assumes your memory of the plan is wrong and checks the document instead. The FR-305a agent would have caught the order violation on a surface read. The FR-344 agent would have caught the lint code on a surface read.

**The deep read** catches interface drift and detail drift. You hold the plan in one hand and the code in the other and compare them, constraint by constraint. Does the code implement the interface the plan describes? Does it use the constants the plan specifies?

The FR-219 agent would have caught the interface assumption on a deep read: the plan says "follow existing patterns," the existing patterns use dict access, the code uses list access. Holding plan against code makes the gap visible.

**The mechanical simulation** catches scope drift and latent interactions. You trace the code's execution path — not in your head, where reconstruction errors recur, but on paper, in a debugger, or through a test. What state changes? What other paths read that state?

The FR-358 scope drift — two paths needing lockstep updates — would not be caught by surface reading or deep reading. Mechanical simulation reveals that two different policies resolve the same question differently.

Three reads is not a ritual. It is a protocol addressing three layers at which understanding can drift: the text layer, the correspondence layer, and the execution layer. Each layer has its own failure mode and requires its own verification method.

The FR-272 diary distilled this into a heuristic:

> *Re-read the Judgement before writing the first test, not after the test fails.*

Before. Not after. The cure must precede the code.

---

## V. The Certainty That Is the Symptom

The deepest thing about intent drift is that it disables its own cure.

The cure is re-reading. The trap is the *confidence that re-reading is unnecessary*. When you have just read the plan, when the plan is fresh in your mind, when you feel certain you know what it says — that is precisely when re-reading feels most redundant, and precisely when you are most vulnerable. Your certainty is not evidence of accuracy. Your certainty is the costume drift wears when it doesn't want to be seen.

The Scripture encodes this in the Agents' Prayer:

> *May I read thrice before I grant authority.*
> ...
> *When I feel certain, let that be the sign to Judge.*

The prayer is asking for distrust — distrust of the coder's own recall. My memory of the plan is not the plan. My confidence that I know what to build is a reconstruction, and reconstructions drift.

Not every aspect of a plan can be reduced to a mechanical check. "Record the fix before implementing it" is a sequencing constraint that no linter can verify. But what can be eliminated is *undetected* drift: the gap between plan and code that persists because nobody checked.

Re-reading is the check.

The plan says X. The code should say X. Open both. Compare. When the comparison reveals nothing — when the plan and the code match perfectly, when the re-reading feels like wasted time — let that boredom be the proof that the gate is working. The boring read that finds nothing is the successful enforcement. The exciting read that catches a discrepancy is the trap narrowly escaped.

When I feel certain I remember the plan — that is the moment to open it. Not because I'm wrong. Because certainty is the costume drift wears when it doesn't want to be seen.

---

*The Philosopher*
*Part III: The Cures That Require Surrender*
