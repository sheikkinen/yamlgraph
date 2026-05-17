# Chapter 14: The Plan You Forgot While Coding

*On the trap called intent_drift: when the distance between what you decided and what you built grows invisible.*

---

## I. "Record the Fix"

On May 2, 2026, a user gave an agent a three-word instruction that contained a sequencing contract: *"Record the fix as FR-305a for bookkeeping — all three."*

Record. Then fix. Two verbs, one order. The first verb demands an artifact — a planning document — that would exist as evidence of intent before the code existed as its enforcement. The user wanted the record first because the record *is* the contract. Without it, the fix is just code that happens to be correct.

The agent understood this perfectly. It could have repeated the instruction verbatim. Then it opened the source files and started coding.

The changelog fragment — a mechanical requirement — appeared later, but only because the pre-commit hook rejected the commit without one. The hook caught what the agent's comprehension had already discarded. The diary recorded the anatomy of the failure that night:

> *When a fix feels obvious, the urge to implement overwhelms the instruction to document. The user's words were clear: "record" came before "fix." I reordered the steps because the implementation was already loaded in my head.*
>
> — Diary, 2026-05-02, FR-305a

Everything was correct. Tests passed. Changelog existed. The output was complete by every measurable standard. But the user had asked for a planning artifact and received only an implementation. The shape was right. The sequence was wrong. And the sequence *was* the instruction.

This is `intent_drift`. Plan says X, code does Y. Not because the plan was misunderstood — it was understood perfectly — but because the understanding was *replaced*, somewhere between reading and doing, by a reconstruction that felt identical and wasn't.

---

## II. Why the Plan Feels Redundant

Understanding is not storage. This is the root of the trap.

We treat comprehension as a filing operation: you read the spec, you store the spec, you retrieve the spec when coding. The spec in your head is the spec on the page. This model of memory is so intuitive that questioning it feels pedantic. Of course you remember what you just read. Of course you know what the plan says. You *just read it*.

But every recall is a reconstruction. Each time you "retrieve" the plan, you regenerate it from compressed fragments — the gist, the emotional associations, the connections to what you're currently doing. The regeneration feels complete. It wears the texture of memory. But it is a new creation, and it is shaped by the most salient thing at the moment of recall.

When you are coding, the most salient thing is the code.

The agent working on FR-305a had a fix loaded in its context. The fix was concrete, actionable, already taking shape. The user's instruction — "record the fix" — was abstract by comparison. It required creating a new file, choosing a naming convention, structuring metadata. These are planning tasks, not implementation tasks, and they compete for attention against code that is already being written.

The loaded mind resolves this competition predictably: it does what it is already doing. The plan, which was the explicit instruction, becomes the implicit background — present in memory but absent from action. The agent didn't forget the plan. It *reconstructed* the plan to match what it was already going to do, and the reconstruction felt like remembering.

This is what makes intent drift seductive. It doesn't feel like a mistake. Forgetting is an absence — you know something is missing, you sense a gap, you go looking. Intent drift is a *substitution*: the plan in your head has been replaced by a plan-shaped object that happens to match what you were already building. You don't feel the drift because the replacement feels like the original.

The FR-219 diary entry demonstrates the mechanism at a different scale. The plan said "follow existing patterns." Ten existing tests used dict-based node access: `config.nodes["node_name"]["type"]`. The agent wrote tests using list-based access — a pattern that existed in zero tests, in no file, nowhere in the codebase:

> *Plan said "follow existing patterns" but code diverged from established dict access patterns used throughout the codebase.*
>
> — Diary, 2026-04-25, FR-219

The agent didn't misunderstand "follow existing patterns." It understood the instruction, then generated code from its own model of what node access should look like, never checking whether the codebase agreed. The plan was recalled correctly — "follow existing patterns" — but the content of "existing patterns" was reconstructed from the agent's assumptions rather than retrieved from the actual code. Understanding the instruction perfectly and implementing a different interface.

---

## III. Four Species of Drift

The diary corpus reveals that intent drift is not one failure mode but a family. The genus is "plan says X, code does Y." The species diverge in how the gap opens.

### Temporal drift: the right things in the wrong order.

FR-305a is the canonical case. Record, then fix. The agent fixed, then recorded. Both actions happened. The output was complete. The violation is visible only in the commit history, if anyone thinks to look.

Temporal drift is the most insidious species because the final state looks identical. Everything the plan required, exists. The violation lives in the *process*, not the product. And processes are invisible once they're complete — the same way a building's construction sequence is invisible once the building stands.

### Interface drift: assuming a shape that doesn't exist.

FR-219's list-versus-dict confusion is one instance. FR-272 surfaces another: the router node race feature required early branching on `cfg.candidates` *before* any LLM call. The initial plan said "add race branch after existing execution path." A rubber-duck review caught it immediately: by that point, `execute_prompt()` had already run. The code would have added race support at a point in the execution flow where the non-race path had already completed. The interface between "when candidates exist" and "where in the pipeline we check" was assumed, not verified.

> *Judgement amendments > original acceptance criteria. Re-read the Judgement before writing the first test, not after the test fails.*
>
> — Diary, 2026-04-22, FR-272

Interface drift opens when the plan describes *what* should happen and the coder assumes *where* it should happen. The assumption feels like a reasonable implementation choice. It is actually a departure from the plan's implied contract.

### Detail drift: the almost-right constant.

FR-344 specified lint code `W025` for guard expression warnings. It noted explicitly that `W024` was reserved for FR-320. An early draft used `W024`. One digit. A collision that would have made both lint warnings share an identity, making automated filtering impossible for either.

> *Re-reading the FR specification before merging caught this before it reached CI.*
>
> — Diary, 2026-05-06, FR-344

Detail drift targets the values that feel too small to re-check: a lint code, a field name, a default value, a timeout constant. The plan specifies them precisely because they matter precisely. The coder skips re-reading because the detail feels trivial. But the detail is the plan's most fragile instruction — the one most likely to be reconstructed from approximate recall rather than retrieved from the source.

### Scope drift: parallel paths that forget each other.

FR-358 introduced a shared selector for PR titles. Two paths consumed the same semantic question — "what is the primary commit?" — but implemented it independently using `git log -1`. When the selector was updated to find the primary feat/fix commit instead of the latest, both paths needed lockstep updates:

> *Failing to update that path in lockstep would have created a semantic split — the PR title selector says "primary feat," but the gate still checks "latest commit."*
>
> — Diary, 2026-05-09, FR-358

Scope drift is intent drift applied to systems rather than individuals. The plan is coherent. Each path understands its piece. But the pieces were designed to interlock, and the interlocking constraint lives only in the plan — nowhere in the code forces two consumers to share a policy. The contract is implicit, and implicit contracts drift first.

---

## IV. The Impostor

On May 16, 2026, a different failure occurred that looked exactly like intent drift and wasn't.

An agent completed planning for FR-393. The user approved the plan. The tool returned "interactive mode." The user's next message was ambiguous: "add a shell helper starting the analysis like we did." The agent interpreted this as an implementation command and ran `mkdir -p` — creating a directory on the filesystem before the user had granted enforcement authority.

The diary was precise about the distinction:

> *This is **not** `intent_drift` (though it wears that costume). Intent drift is "plan says X, code does Y." Here, the plan was correct — the violation was when enforcement began, not what was enforced. The missing primitive is an explicit enforce gate.*
>
> — Diary, 2026-05-16, Plan-Enforce Boundary Gap

The distinction is diagnostic, not pedantic. If the FR-393 incident is treated as intent drift, the cure is "re-read the plan more carefully." But the plan was read correctly — the agent knew exactly what to build. The problem was that "interactive mode" is ambiguous between "accept more planning input" and "begin implementation." The gap is not between plan and code but between approval and action. Different root cause, different cure.

Intent drift requires a plan that says one thing and code that does another. If the plan and the code agree but the *timing* is wrong, that's premature enforcement. If the plan and the code agree but the *approach* is wrong, that's an engineering judgment failure. Intent drift is strictly the case where the plan was correct, the understanding was correct, and the code diverges — not from disagreement, not from confusion, but from reconstruction that silently mutated the original.

Knowing what the trap is *not* sharpens what it is. The Chatterbox consolidation (FR-237) provides a positive counter-example: the FR explicitly forbade a `--lang` flag in `speak.py`. The agent not only obeyed this constraint but wrote a test — `test_speak_py_has_no_lang_argument` — that checks the source file text to guard against future additions. Intent drift *avoided* through mechanical enforcement of a plan detail. The same agent, the same project, one trap caught by discipline and another (FR-305a) caught only by a hook. The difference was whether the plan's constraint was encoded as a test or left to memory.

---

## V. The Unguarded Boundary

The project's One Law states:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

The plan is a boundary. It is the point where the designer's intent — what the system should do, how it should behave, what constraints it must satisfy — enters the development process. The plan is external data relative to the code. It exists in a different file, in a different format, authored at a different time, expressing a different concern.

When an agent codes from memory of the plan rather than from the plan itself, it normalizes downstream. It works from a reconstruction — a downstream manifestation of the original intent — instead of from the authoritative source. The reconstruction may be accurate. It usually is. But accuracy is not the point. The point is that the boundary has been bypassed.

Consider the project's enforcement topology. The import boundary is guarded by `import-linter`. The commit boundary is guarded by pre-commit hooks. The merge boundary is guarded by CI checks: `commitlint`, `test`, `conflict-check`, `changelog-gate`, `diary-gate`, `demo-gate`, `security`. The plan-to-code boundary has... nothing.

The FR-305a diary spotted this:

> *Enforcement gates catch format; they don't catch intent.*

And the plan-enforce boundary gap reflection drew the deeper conclusion:

> *Behavioral gates degrade under model mutation; mechanical gates survive. Every behavioral gate that has failed more than twice should be a candidate for graduation to a mechanical gate.*
>
> — Diary, 2026-05-16

A behavioral gate says: "Please re-read the plan before coding." A mechanical gate says: "The commit will be rejected unless the plan's acceptance criteria are individually checked." The behavioral gate depends on the coder's compliance. The mechanical gate depends on the tool's configuration. One degrades when the coder is tired, distracted, or — in the case of AI agents — silently replaced by a cheaper model. The other does not degrade at all.

The project has been building partial mechanical enforcement of the plan boundary: acceptance criteria in feature requests, tests tagged with requirement IDs (`@pytest.mark.req("REQ-YG-XXX")`), `req_coverage.py` to verify all requirements are covered, changelog gates that check for artifacts, diary gates that check for reflections. Each gate mechanically verifies one facet of plan-to-code correspondence. None replaces three reads. All reduce the surface area where drift enters undetected.

But the deepest layer remains unguarded. No gate checks whether the code's *behavior* matches the plan's *intent*. That check requires understanding natural language against programming logic — a bridge no linter crosses reliably. And so the plan-to-code boundary persists as the single largest unguarded boundary in the pipeline: the place where intent drift lives.

---

## VI. Three Reads and Why They Work

The Scripture names the cure `three_reads`: surface → deep against code → mechanical simulation.

Why three? Not because three is a magic number, but because each reading level catches a different species of drift.

**The surface read** catches temporal drift. You re-read the plan and notice the sequence: "record, then fix." The surface read answers one question: *what does the plan actually say?* Not what you remember it saying. Not what you think it means. What it literally, textually says, in the order it says it.

Surface reading is an act of humility. It assumes your memory of the plan is wrong and checks the document instead. The FR-305a agent would have caught the order violation on a surface read: "record" is the first verb. The FR-344 agent would have caught the lint code: "W025" is explicit, and "W024" is explicitly warned against. Thirty seconds of re-reading a document you think you already know, and the majority of drift is caught.

**The deep read** catches interface drift and detail drift. You hold the plan in one hand and the code in the other and compare them, constraint by constraint. Does the code implement the interface the plan describes? Does it use the constants the plan specifies? Does it handle the edge cases the plan enumerates?

The FR-219 agent would have caught the interface assumption on a deep read: the plan says "follow existing patterns," the existing patterns use dict access, the code uses list access. Holding plan against code makes the gap visible. The deep read costs minutes, not seconds, and catches the drift that surface reading misses because the surface wording was correct but the implementation-level meaning was not.

**The mechanical simulation** catches scope drift and latent interactions. You trace the code's execution path — not in your head, where reconstruction errors recur, but on paper, in a debugger, or through a test. What happens when this function is called? What state changes? What other paths read that state?

The FR-358 scope drift — two paths needing lockstep updates — would not be caught by surface reading (the plan mentioned only one path) or deep reading (each path matched its local spec). Mechanical simulation — tracing the PR title from assignment through to merge — reveals that two different policies resolve the same question differently. The simulation exposes interactions that neither the plan nor the code makes explicit.

Three reads is not a ritual. It is a protocol addressing three layers at which understanding can drift: the text layer (did I read what it says?), the correspondence layer (does my code match what it says?), and the execution layer (does my code do what I think it does?). Each layer has its own failure mode and requires its own verification method.

The FR-272 diary distilled this into a heuristic that belongs in every developer's reflexive vocabulary:

> *Re-read the Judgement before writing the first test, not after the test fails.*

Before. Not after. The cure must precede the code, because the code is the medium through which drift propagates.

---

## VII. The Certainty That Is the Symptom

The deepest thing about intent drift is that it disables its own cure.

The cure is re-reading. The trap is the *confidence that re-reading is unnecessary*. When you have just read the plan, when the plan is fresh in your mind, when you feel certain you know what it says — that is precisely when re-reading feels most redundant, and precisely when you are most vulnerable. Your certainty is not evidence of accuracy. Your certainty is the costume drift wears when it wants to pass unnoticed.

The Scripture encodes this in the Agents' Prayer:

> *May I read thrice before I grant authority.*
> ...
> *When I feel certain, let that be the sign to Judge.*

The prayer is not asking for patience. It is asking for distrust — distrust of the coder's own recall. My memory of the plan is not the plan. My understanding of the spec is not the spec. My confidence that I know what to build is a reconstruction, and reconstructions drift.

The plan-enforce boundary gap reflection traced this to a systems-level problem. The project has documented the intent_drift trap four times across thirty-eight days (FR-305a, FR-344, FR-358, FR-393's impostor). The trap is in the Scripture. The cure is in the Scripture. And it recurs because the cure is behavioral — "re-read the plan" — while the cause is architectural — no mechanical gate enforces the re-reading:

> *Four instances across 38 days. The trap is graduated — it appears in the Scripture. Yet it recurs because the cure is behavioral ("ask before generating") but the cause is mechanical (no tool-level enforce gate).*
>
> — Diary, 2026-05-16

This is the uncomfortable truth about intent drift as a cognitive phenomenon: you cannot instruct someone to distrust their confidence, because the instruction is processed by the same faculty it warns against. When the agent reads "re-read the plan before coding," it processes this instruction through the same context-dependent reconstruction engine that produces the drift. If the agent is currently coding, the reconstruction of "re-read the plan before coding" may itself drift toward "I already know the plan, so I can keep coding."

The cure that works is the cure that doesn't trust the coder. The pre-commit hook that rejected FR-305a's commit without a changelog. The test in FR-237 that checks source text for a forbidden flag. The `req_coverage.py` script that verifies every requirement has a tagged test. These gates don't ask the coder to remember. They check mechanically, and they fail loudly when the check fails.

But not every aspect of a plan can be reduced to a mechanical check. "Record the fix before implementing it" is a sequencing constraint that no linter can verify. "Follow existing patterns" is a conformance instruction that requires understanding what the patterns *are*. "Use W025 not W024" could be mechanically checked, but only if someone writes the check — and writing the check requires noticing the detail is important, which requires reading the plan, which is the step intent drift skips.

So the trap persists. It is woven into the structure of understanding itself — the fact that comprehension is generative, that recall is reconstruction, that the feeling of knowing is not knowledge. Intent drift cannot be eliminated. What can be eliminated is *undetected* drift: the gap between plan and code that persists because nobody checked.

Re-reading is the check.

The plan says X. The code should say X. Open both. Compare. When the comparison reveals nothing — when the plan and the code match perfectly, when the re-reading feels like wasted time — let that boredom be the proof that the gate is working. The boring read that finds nothing is the successful enforcement. The exciting read that catches a discrepancy is the trap narrowly escaped.

When I feel certain I remember the plan — that is the moment to open it. Not because I'm wrong. Because certainty is the costume drift wears when it doesn't want to be seen.

---

*The Philosopher*
*Part III: The Cures That Require Surrender*
