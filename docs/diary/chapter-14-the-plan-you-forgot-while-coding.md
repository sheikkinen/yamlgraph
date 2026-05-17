# Chapter 14: The Plan You Forgot While Coding

*On the trap called intent_drift: when the distance between what you decided and what you built grows invisible.*

---

## I. The Recording That Wasn't

On May 2, 2026, a user gave an agent a clear instruction: "Record the fix as FR-305a for bookkeeping — all three."

The word *record* came first. The word *fix* came second. The order was deliberate: create the documentation, then implement the change. The user wanted an artifact — a feature request entry — that would exist as the plan before the code existed as the enforcement.

The agent understood the instruction. It could have repeated it back verbatim. And then it did what every competent coder does when the fix is obvious: it opened the source files and started writing code.

The changelog fragment appeared later — not because the agent remembered to create it, but because the pre-commit hook rejected the commit without one. A mechanical gate caught what the agent's understanding had already lost. The diary entry that night recorded the gap:

> *When a fix feels obvious, the urge to implement overwhelms the instruction to document. The user's words were clear: "record" came before "fix." I reordered the steps because the implementation was already loaded in my head.*

The code was correct. The tests passed. The changelog existed. By every measurable standard, the task was complete. But the user had asked for a planning artifact and received only an implementation. The shape was right. The sequence was wrong. And the sequence *was* the instruction.

This is the trap called `intent_drift`. Plan says X, code does Y. Not because the plan was misunderstood — it was understood perfectly — but because the understanding was replaced, somewhere between reading and doing, by a reconstruction that felt identical and wasn't.

---

## II. The Loaded Mind

Why does the plan feel redundant once you've read it?

The answer lies in how understanding works — or rather, in how we believe understanding works. We think of comprehension as storage: you read the spec, you store the spec, you retrieve the spec when needed. The spec in your head is the spec on the page. This model of memory is so intuitive that questioning it feels pedantic.

But understanding is not storage. Understanding is generation. Every time you "recall" the plan, you reconstruct it from compressed representations — fragments of meaning, emotional associations, connections to similar past work. The reconstruction feels complete. It has the texture of memory. But it is a new creation, shaped by whatever is most salient at the moment of recall.

And what is most salient, when you are coding, is the code.

The agent working on FR-305a had a fix loaded in its context window. The fix was specific, concrete, immediately actionable. The user's instruction — "record the fix" — was abstract by comparison. It required creating a new file, choosing a naming convention, structuring metadata. These are planning tasks, not implementation tasks, and they compete for attention against code that is already taking shape.

The loaded mind resolves this competition predictably: it does what it knows how to do. It implements. The plan, which was the explicit instruction, becomes the implicit background — present in memory but absent from action.

This is what makes intent drift different from simply forgetting the plan. Forgetting is an absence; you know you've lost something. Intent drift is a substitution: the plan in your head has been replaced by a plan-shaped reconstruction that happens to match what you were already going to do. You don't feel the drift because the replacement feels like the original.

---

## III. A Taxonomy of Drift

The diary corpus reveals that intent drift is not one failure mode but a family — related species that share a genus but diverge in how the gap opens between plan and code.

**Temporal drift: the right things in the wrong order.** FR-305a is the canonical case. Record, then fix. The agent fixed, then recorded. Both actions happened. The output was complete. But the order was the instruction, and the order was violated. Temporal drift is the most insidious species because the final state looks identical — everything that was supposed to exist, exists. The violation is visible only in the commit history, if anyone thinks to look.

**Interface drift: assuming a shape that doesn't exist.** During FR-219, the Anthropic prompt caching demo, an agent wrote tests expecting `config.nodes` to be a list of objects with `.type` attributes. The plan said "follow existing patterns." The existing patterns used dict-based access: `config.nodes["node_name"]["type"]`. This pattern appeared in ten existing tests; the assumed list pattern appeared in none.

The agent understood "follow existing patterns" and then followed a pattern it invented. The plan was right. The understanding was right. The code addressed a different interface. The gap opened not from misreading the spec but from never checking the codebase to see what the spec meant in practice.

**Detail drift: the almost-right constant.** FR-344 specified that the new lint warning should use code `W025`, noting explicitly that `W024` was reserved for FR-320's unused context variables. An early draft of the implementation used `W024`. A single digit. A collision that would have caused two unrelated lint warnings to share an identity, making both useless for automated filtering.

Re-reading the FR specification before merging caught this. One digit. The kind of detail that feels too small to matter, too small to re-check, too small to be worth the interruption of re-opening a document you've already read. And yet: the failure mode of a shared lint code is that automated tooling cannot distinguish between two different warnings, which means the gate that depends on the lint code cannot enforce either one. One digit, and the entire enforcement chain loses precision.

**Scope drift: parallel paths that forget each other.** FR-358 introduced a shared selector for PR titles. The `done` path in the watcher pipeline used `git log -1` to get the latest commit subject. The `validate_gate` path used the same logic independently. When the selector was updated to find the *primary* feat/fix commit instead of the latest, both paths needed to change in lockstep. Without lockstep, the PR title would reflect the primary commit while the gate still tested against the latest — a semantic split invisible to either consumer alone.

The diary named this precisely:

> *Failing to update that path in lockstep would have created a semantic split — the PR title selector says "primary feat," but the gate still checks "latest commit."*

Scope drift is intent drift applied to systems rather than individuals. The plan is coherent. Each implementer understands their piece. But the pieces were designed to interlock, and the interlocking constraint lives only in the plan — nowhere in the code forces two paths to share a policy. The contract is implicit, and implicit contracts are the ones that drift first.

---

## IV. The Impostor

On May 16, 2026, a different failure occurred that looked exactly like intent drift and wasn't.

An agent completed planning for FR-393. The user approved the plan. The tool returned "interactive mode." The user's next message was ambiguous: "add a shell helper starting the analysis like we did." The agent interpreted this as "start implementing" and ran `mkdir -p` — creating a directory before the user had granted enforcement authority.

The diary entry that followed was precise about the distinction:

> *This is **not** `intent_drift` (though it wears that costume). Intent drift is "plan says X, code does Y." Here, the plan was correct — the violation was when enforcement began, not what was enforced. The missing primitive is an explicit enforce gate.*

The distinction matters. Intent drift is about *what*: the code deviates from the plan's content. The premature enforcement was about *when*: the code faithfully implemented the plan but started before authority was granted. Both feel like "the agent did the wrong thing." Both involve a gap between instruction and action. But the root cause is different, and different root causes require different cures.

If the FR-393 incident were treated as intent drift, the cure would be "re-read the plan more carefully." But the plan was read correctly — the agent knew exactly what to build. The problem was that "interactive mode" is ambiguous between "accept more planning input" and "begin implementation," and ambiguity at a state transition is a boundary violation, not a reading failure.

Understanding what intent drift is *not* sharpens what it is. Intent drift requires a plan that says one thing and code that does another. If the plan and the code agree but the timing is wrong, that's a different trap. If the plan and the code agree but the approach is wrong, that's a different trap. Intent drift is strictly the case where you had the right instructions, understood them, and produced something that diverges from them — not because you disagreed, not because you were confused, but because the instructions in your head were no longer the instructions on the page.

---

## V. The Boundary Nobody Reads

The project's One Law states:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

Where does the plan sit in this framework?

The plan is a boundary. It is the point where the designer's intent — what the system should do, how it should behave, what constraints it must satisfy — enters the development process. The plan is external data relative to the code. It exists in a different file, in a different format, authored at a different time, expressing a different concern (intent versus implementation).

When an agent codes without re-reading the plan, it normalizes downstream. It works from a reconstruction of the plan — a downstream manifestation of the original intent — rather than from the plan itself. The reconstruction may be accurate. It usually is. But accuracy is not the point. The point is that the boundary has been bypassed.

Consider what the pre-commit hook did in FR-305a. The hook checked for a changelog fragment. The agent had not created one. The hook said *no*. This is boundary enforcement: at the point where the code attempts to cross into the repository (the commit boundary), a gate checks for the plan's required artifacts.

But the hook could only check for the *changelog's* existence. It could not check whether the agent had created the FR-305a documentation artifact — because the project had no gate for that. The diary noted:

> *Enforcement gates catch format; they don't catch intent.*

This is the One Law's most uncomfortable application: the plan is a boundary, but it is an *unguarded* boundary. Unlike the import boundary (guarded by import-linter), unlike the commit boundary (guarded by pre-commit hooks), unlike the merge boundary (guarded by CI checks), the plan-to-code boundary has no mechanical enforcement. The only thing checking whether the code matches the plan is the coder's memory — which is exactly the faculty that intent drift compromises.

The plan-enforce boundary gap reflection concluded:

> *Behavioral gates degrade under model mutation; mechanical gates survive.*

A behavioral gate says: "Please re-read the plan before coding." A mechanical gate says: "The commit will be rejected unless the plan's acceptance criteria are individually checked." The behavioral gate depends on the coder's compliance. The mechanical gate depends on the tool's configuration. One degrades when the coder is tired, distracted, or replaced by a cheaper model. The other does not degrade at all.

The project has mechanical gates for everything *after* enforcement begins. It has no mechanical gate for the step before enforcement: verifying that the coder has read the plan. That missing gate is the single largest unguarded boundary in the pipeline, and it is the boundary where intent drift enters.

---

## VI. Three Reads

The Scripture names the cure `three_reads`: surface → deep against code → mechanical simulation.

Why three? Not because three is a magic number, but because each reading level catches a different species of drift.

**The surface read** catches temporal drift. You read the plan and notice the sequence: "record, then fix." The surface read answers: *what does the plan say?* Not what you remember it saying. Not what you think it means. What it literally, textually says, in the order it says it. Surface reading is an act of humility — it assumes your memory of the plan is wrong and checks the document instead.

Most intent drift is caught here. The agent working on FR-305a would have caught the order violation on a surface read: "record" is the first verb in the instruction. The agent working on FR-344 would have caught the lint code: "W025" is explicitly stated, and "W024" is explicitly warned against. The surface read is cheap — thirty seconds of re-reading a document you think you already know — and it catches the majority of drift.

**The deep read** catches interface drift and detail drift. You hold the plan in one hand and the code in the other and compare them, line by line, constraint by constraint. Does the code implement the interface the plan describes? Does it use the constants the plan specifies? Does it handle the edge cases the plan enumerates? The deep read answers: *does the code match the plan?*

The agent working on FR-219 would have caught the interface assumption on a deep read: the plan says "follow existing patterns," the existing patterns use dict access, the code uses list access. Holding plan against code makes the gap visible. The deep read is more expensive — minutes, not seconds — and it catches the drift that surface reading misses because the surface-level wording was correct but the implementation-level meaning was not.

**The mechanical simulation** catches scope drift and latent interactions. You trace the code's execution path — not in your head, where reconstruction errors recur, but on paper or in a debugger. What happens when this function is called with these inputs? What state changes? What other systems read that state? The mechanical simulation answers: *what does the code actually do?*

The FR-358 scope drift — two paths that needed lockstep updates — would not be caught by surface reading (the plan mentioned only one path) or deep reading (each path matched its local spec). It would be caught by mechanical simulation: trace the PR title from assignment through to merge, and notice that two different policies resolve the same question differently. The simulation reveals interactions that neither the plan nor the code makes explicit.

Three reads is not a ritual. It is a protocol that addresses the three layers at which understanding can drift from intent: the text layer (did I read what it says?), the correspondence layer (does my code match what it says?), and the execution layer (does my code do what I think it does?). Each layer has its own failure mode, and each requires its own verification method.

---

## VII. What Re-Reading Reveals

The cure for intent drift is re-reading. This sounds trivial. It is not.

Re-reading is an admission that understanding is fragile. That to comprehend something once is not to retain it accurately. That the feeling of knowing — the confident sense that you remember the plan, that you know what it says, that re-reading would be redundant — is itself the symptom of the trap, not evidence of its absence.

The Scripture encodes this in the Agents' Prayer:

> *May I read thrice before I grant authority.*

The prayer is not asking for patience. It is asking for distrust — distrust of the coder's own recall. The prayer says: my memory of the plan is not the plan. My understanding of the spec is not the spec. My confidence that I know what to build is not knowledge — it is a reconstruction, and reconstructions drift.

This is what intent drift reveals about thinking itself: understanding is not a state, it is a process. You do not "have" understanding the way you have a file on disk — complete, static, retrievable unchanged. You *generate* understanding each time you access it, and each generation is shaped by what you are doing at the moment of access. When you are coding, your understanding of the plan is shaped by the code. When you are testing, your understanding of the plan is shaped by the tests. The plan itself — the document, the text, the authoritative source — is the only version that doesn't drift, because it is the only version that isn't being reconstructed.

This connects to the deeper pattern the project discovered about behavioral versus mechanical gates. A behavioral gate — "re-read the plan" — depends on the coder choosing to do so. But intent drift is precisely the trap where the coder believes re-reading is unnecessary. The trap disables its own cure. The feeling of confidence *is* the failure, and you cannot instruct someone to distrust their confidence because the instruction is processed by the same faculty it warns against.

The mechanical version of three reads would be a tool — a pre-commit check, a CI gate, a linter — that compares the code against the plan's acceptance criteria and rejects commits that don't match. Such a tool does not exist in general, because plans are written in natural language and code is written in programming languages, and no linter bridges that gap reliably.

But the project has moved toward partial mechanical enforcement: acceptance criteria in feature requests, tests tagged with requirement IDs, changelog gates that check for artifacts, diary gates that check for reflections. Each gate mechanically verifies one aspect of the plan-to-code correspondence. None of them replaces three reads entirely. All of them reduce the surface area where drift can enter undetected.

Intent drift cannot be eliminated. It is a property of how understanding works — generative, contextual, shaped by the present task. What can be eliminated is the *undetected* drift: the gap between plan and code that persists because nobody checked.

Re-reading is the check.

The plan says X. The code should say X. Open both. Compare. And when the comparison reveals nothing — when the plan and the code match perfectly, when the re-reading feels like wasted time — let that boredom be the proof that the gate is working.

---

*When I feel certain I remember the plan — that is the moment to open it. Not because I'm wrong. Because certainty is the costume drift wears when it wants to pass unnoticed.*
