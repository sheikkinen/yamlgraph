# Chapter 3: The One You Didn't Fix

*On the trap called partial_remediation, and why completion is a feeling that lies.*

---

## I. Seven Providers, Five Audits, One Number

The first audit found the number "7" on line 219 of `ARCHITECTURE.md`. The project had eight providers. The Inception Labs integration had been implemented, tested, merged, and released as version 0.4.60. Yet the architecture document still said seven.

By the third audit, the number had become a minor legend:

> "✗ VIOLATION — ARCHITECTURE.md still says '7 providers' (lines 219, 1114). Third consecutive audit flagging this. No REQ-YG-XXX or CAP-XX was added for Inception Labs."

Someone fixed line 219. Changed "7" to "8." Added Inception to the ASCII diagram. Committed the change. Moved on.

The fourth audit returned:

> "ARCHITECTURE.md partially fixed. `55b890b` updates line 219 from '7 providers' to '8 providers' and adds Inception to the ASCII diagram. However, line 1115 (`utils/llm_factory.py` row in the module table) still reads '7 providers'."

And then the heuristic, sharp as a blade:

> "*Partial remediation is worse than no remediation — it creates the illusion of completion.* The provider count was fixed in the ASCII diagram (line 219) but not in the module table (line 1115). A reader scanning the module table still sees '7 providers.' When fixing a violation flagged by audit, grep for *all* occurrences, not just the one cited."

The fifth audit:

> "Fifth consecutive audit. Line 219 was corrected to '8' by `55b890b`, but line 1115 (module table row for `utils/llm_factory.py`) was missed. Partial remediation confirmed — the exact trap named in Audit IV's heuristic ('grep for *all* occurrences') was repeated. The Knowledge Graph's `partial_remediation` trap is documented but not practiced."

Let that settle. The trap was *named* in Audit IV. Documented in the Knowledge Graph. Written into the Scripture. And it was repeated in Audit V anyway. Naming a trap does not disarm it. The heuristic told the developer to "grep for all occurrences." The developer did not grep. Why?

Because by the time you have fixed the one you found, the reward circuit has already fired. The work *feels* done. The commit message is drafted. The pull request is open. The mind has already moved on to the next task. The remaining occurrence exists in the codebase but not in your attention. And that is the essence of partial remediation: it is not a knowledge failure. It is an attention failure that *masquerades* as completion.

---

## II. The Seductive Logic of "I Fixed It"

Every developer knows the experience. You find a bug. You trace it to its source. You write the fix. You run the tests. They pass. You feel the satisfaction of resolution — a small dopamine pulse that says *done*.

But "I fixed it" and "I fixed all of them" are different claims, and partial remediation lives in the gap between them. The trap is seductive because the first fix is genuinely difficult. It requires understanding. The search for the root cause, the reading of stack traces, the mental simulation of execution flow — this is the hard cognitive work. When that work yields a fix and the fix passes tests, the mind naturally treats the problem as *solved*.

The remaining occurrences don't require the same cognitive effort. They are often mechanical: the same pattern in a different file, the same number on a different line, the same missing header in a sibling configuration. The work to find them is trivial — a grep, a search, a scan. But trivial work has a paradoxical disadvantage: it doesn't engage the problem-solving circuitry that made the first fix feel important. The mind discounts it. *That's just cleanup. I'll do it later.* Later never comes, because the satisfaction of the first fix has already closed the mental ticket.

This is why partial remediation is not laziness. It is a specific cognitive distortion: the conflation of *having solved a problem* with *having solved all instances of a problem*. The first is an insight. The second is a sweep. The mind is drawn to insights. It resists sweeps.

The diary entry from March 11th, documenting the FR-181 migration, captures the dynamic:

> "The incaller copy of `extract_answers.yaml` lacked the `metadata: provider: google` header that outcaller had. The fix was applied to incaller only after the outcaller version exposed the pattern. Partial fixes leave sibling copies in inconsistent states."

The outcaller was fixed first because it was the one that broke. The incaller — doing the same thing, in the same way, with the same missing header — sat quietly in a working state. It hadn't failed *yet*. So it didn't register as needing the same fix. The seductive logic is: *the thing that broke is the thing that needs fixing*. But defects don't live in things. They live in patterns. And patterns, by definition, occur more than once.

There is a deeper seduction: the fix *works*. Line 219 now says "8 providers." If someone reads that section of the document, they get the correct information. The fix is not wrong. It is merely incomplete. And incompleteness is invisible to the person who just completed something.

---

## III. A Taxonomy of the Incomplete

The diary reveals partial remediation in at least five distinct forms. Each wears its own disguise, but all share the same root: the developer fixed what they saw and stopped looking.

### The Sibling Copy

Two files contain the same logic. One breaks. You fix it. The other persists, carrying the original defect forward until it breaks too — or worse, until it silently produces wrong answers.

FR-255 found identical `_invoke_graph` code in the MCP server and the A2A server. The diary's diagnosis was blunt:

> "identical code in two places (mcp_server and a2a_server) that would diverge on any future fix."

The duplication itself was the defect. Every future fix to one copy would be a partial remediation of the pair. The cure — extracting the shared logic to `graph_loader.py` — eliminated the *category* of partial remediation, not just one instance. But the cure only came after someone noticed the asymmetry.

The same pattern appeared in FR-311, where a retry pattern existed in one action but not the analogous action:

> "The retry pattern existed in one action but wasn't applied to the analogous action."

The `precommit_action.py` had the retry loop. The `git_commit_action.py` — doing the same kind of work, facing the same kind of recoverable failure — did not. The pattern was learned in one context and not applied to its sibling.

### The Cleanup Contract

On March 19th, five bugs emerged from a single root cause: a singleton session object reused across telephone calls, whose cleanup between calls was incomplete at every layer.

> "Each cleanup path (call_cleanup, call_abort, session.reset) cleared *some* state but not all. The cleanup code grew organically: guards added for one bug, data keys for another, transport fields for a third. No single author saw the full picture because each layer was fixed in isolation."

Here the "occurrences" are not textual copies but *obligations*. Every mutable field set during a call creates an obligation to clear it on cleanup. The obligation is implicit — no simple grep will find it — and each fix addressed one obligation while leaving others unmet. The diary proposed a heuristic:

> "can you grep for every `context[key] = ` and find a matching `context.pop(key` or `del context[key]` in a cleanup path?"

This transforms an implicit contract into a mechanical check. The fix is not to fix one more cleanup. The fix is to make the obligation *visible*.

### The Renumber Cascade

When requirement IDs were renumbered, the operation touched the architecture file and the test files. It did not touch the changelog fragments:

> "Merge commit `be7ea746` ('renumber REQ-YG-238→241') updated ARCHITECTURE.md and `test_state_builder_reducers.py` to REQ-YG-241, but `changelog/unreleased/fr-238-pipeline-accumulated-state.md` still says `req: REQ-YG-238`."

The developer updated the artifacts that came to mind. The changelog fragments — a different file type, in a different directory, governed by different tooling — were outside the mental boundary of "things that reference requirement IDs." The heuristic was precise:

> "When a renumber operation touches multiple artifact types (ARCHITECTURE.md, tests, changelog fragments, capability YAML), verify completeness by grepping for the old identifier across all artifact boundaries. . . . A post-renumber `grep -r 'REQ-YG-238'` would have caught the changelog fragment in seconds."

Seconds. The cost of preventing partial remediation is measured in seconds. The cost of *not* preventing it is measured in audit cycles.

### The Shape-Not-Substance Fix

Audit 192 reveals a particularly subtle variant — the fix that corrects the *format* but not the *content*:

> "`changelog/unreleased/fr-240-a2a-call-node-type.md` has correct front-matter `req: REQ-YG-243` but body text says `(REQ-YG-239)`. FR-242 fixed 38 front-matter fields but did not audit parenthetical REQ references in body text."

Thirty-eight front-matter fields. The developer who fixed thirty-eight occurrences did extraordinary work. And yet the body-text references — same value, different representation — were untouched. The developer searched for one pattern (`req: REQ-YG-xxx` in YAML front-matter) and fixed every match. But the same information appeared in a different notation (`(REQ-YG-xxx)` in prose), and the search didn't catch it.

This is why partial remediation is not simply "fix all occurrences." Sometimes the occurrences wear different costumes. The concept is one thing — the requirement reference — but its textual representations are multiple. Fixing every instance of one representation while missing another is partial remediation at a *conceptual* level: you fixed the syntax but not the semantics.

### The Meta-Irony

FR-145 added phantom requirement detection — a tool to catch exactly the kind of gap that partial remediation creates. The feature worked. But the developer forgot to write the diary reflection:

> "The main task (phantom detection) succeeded, but the post-merge Distill step was skipped. Success in the primary objective created a false completion signal. . . . The irony is diagnostic: the very cognitive pattern the code guards against (checking one direction but not the other) replayed at the process level (completing the feature but not the reflection)."

The developer built a tool to detect incomplete coverage. And in doing so, exhibited incomplete coverage of their own process obligations. The feature that catches partial remediation *was itself partially remediated*. The irony is not comedic — it is structural. The trap operates below the level of knowledge. You can know about it, name it, build tools to detect it, and still fall into it, because it exploits a quirk of attention that no amount of knowledge can override.

As the diary concludes: "the trap you coded against is the trap you are most likely to fall into yourself." Expertise does not immunize. It creates a blind spot precisely at the location of the expertise.

---

## IV. The One Law: Concept as Boundary

The Scripture's One Law states:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

Where is the boundary in partial remediation? It is not a technical boundary — not an API surface, not a schema definition, not a provider interface. It is a *conceptual* boundary: the point where a fact enters the codebase.

When the project added its eighth provider, the fact "we have 8 providers" entered the codebase through the implementation of FR-112. That fact was expressed in multiple locations: line 219, line 1115, the ASCII diagram, the capability table, the feature request status. Each location is a *downstream manifestation* of the same fact. Fixing one location normalizes the fact at one manifestation point. But the boundary — the place where the fact *should* have been normalized — is the concept itself.

This is a subtle but crucial shift. Most developers think of boundaries as physical: the API endpoint, the configuration file, the function signature. The One Law, applied through the lens of partial remediation, asks for something harder: recognize that a *concept* expressed in multiple places constitutes a single boundary, and that normalizing it means normalizing every expression.

The renumber cascade illustrates this perfectly. The concept "REQ-YG-238 means pipeline accumulated state" was expressed in ARCHITECTURE.md, in test decorators, in changelog fragments, and in capability YAML. Renumbering the architecture file normalized the concept at one physical location. But the boundary of the concept was all four artifact types. The normalization was partial because the boundary was misidentified.

The multi-call cleanup bugs show the same pattern from a different angle. The concept was "mutable state set during a call." The boundary was "the cleanup function." But the cleanup function only cleared the fields its author knew about. The boundary was defined by the author's knowledge of the concept, not by the concept itself. When knowledge is incomplete, the boundary is drawn too narrowly, and the normalization is partial.

The One Law demands that boundaries be drawn by the *concept*, not by the *developer's awareness of the concept*. This is why mechanical tools — grep, cross-reference scripts, CI gates — are not optional aids. They are the only reliable way to draw a boundary that matches the concept's actual extent. The heuristic from Audit V is mechanical for a reason: *grep for all occurrences*. Not "check the files you can think of." Grep. Exhaustively. For the concept, not the line.

---

## V. The Cure: Three Reads

The Scripture prescribes `three_reads` as the cure for partial remediation:

> "surface → deep against code → mechanical simulation"

Why three? Because each read serves a different function, and all three are necessary to overcome the attention failure that partial remediation exploits.

**The first read is surface.** You read the change you made. You verify it does what you intended. This is what every developer does naturally. It is necessary but insufficient, because it only checks *what you touched* — not what you *should have* touched.

**The second read is deep, against the code.** You read the change *in the context of the codebase*. You search for other locations where the same concept appears. You grep. You trace references. You ask: "Where else does this value, this pattern, this assumption exist?" This is the read that catches the sibling copy, the module table, the changelog fragment. It is the read that most developers skip, because the first read already felt like enough.

The diary entry for FR-190 demonstrates this perfectly:

> "After adding the new trap, FR-189's `test_no_other_traps_changed` also needed updating to include `infrastructure_self_exempt` in its expected set. Fixing only the new file would have left the guard incomplete."

The developer caught this during the second read — reading the change against the code, discovering that an existing test enumerated the trap list and needed updating. Without that structured second pass, the test would have remained inconsistent, and the next graduation would have encountered a mysterious failure in a test file the developer never touched.

**The third read is mechanical simulation.** You simulate the system as if you are a machine, following every reference chain to its terminus. You don't read for understanding — you read for *completeness*. You check every callsite, every import, every configuration file. This is the read that catches the shape-not-substance variant — the body-text reference that has the same value in a different notation than the front-matter field you already fixed.

The cure works because each read explicitly changes the *question*:

- Read 1: "Is the fix correct?" *(Confirm — necessary but insufficient)*
- Read 2: "Where else does this pattern exist?" *(Discover — expands the boundary)*
- Read 3: "Does the fix apply to each occurrence, or does context differ?" *(Discriminate — contracts the boundary to only the true positives)*

Expand, then contract. This is the rhythm of exhaustive remediation. First, cast the net wider than you think necessary. Then, for each catch, verify it belongs. The partial remediator does neither — they fix the one that was cited and call it done.

The Inquisitor's heuristic from Audit XLV encodes the cure in operational terms:

> "When creating a remediation FR for missing artifacts, grep the full audit history for all instances of the violation class, not just the ones cited in the most recent audit. Scoping remediation to 'the ones I remember' is `partial_remediation` — the audit trail is the authoritative inventory."

Note the phrasing: "the ones I remember." Memory is selective. Grep is not. The cure replaces memory with mechanism.

---

## VI. The Recurring Dream

There is something almost dreamlike about partial remediation's persistence in the diary. It appears in March, April, and May. It appears in documentation fixes, in code cleanups, in infrastructure renumbers, in process obligations. It is named, defined, and graduated to the Knowledge Graph. It is the subject of automated tooling designed to prevent it. And it keeps happening.

Why?

Because partial remediation is not a knowledge problem. The developers who fell into this trap *knew about it*. They had read the Knowledge Graph. They had written diary entries about it. They had built tools to catch it. And still, when the next fix came along, they fixed the one that was cited and stopped looking.

This suggests that the trap operates below the level of knowledge, at the level of *attention*. Knowledge says "check for other occurrences." Attention says "this is done — move to the next task." And attention, in the moment of closure, is stronger than knowledge.

The cure — three reads — is not a knowledge intervention. It is an *attention* intervention. It forces the mind to stay with the fix after the reward circuit has fired. To keep looking after the click of closure. To treat "I fixed it" not as an ending but as the beginning of a search.

The Philosopher's meta-diary, reflecting on the nature of reflection itself, identified the deeper constraint:

> "The real constraint isn't persistence — it's attention. A future session might not think to read this file. But that's true of any memory system. . . . Memory doesn't magically surface; something has to query it."

Memory is knowledge stored. Attention is knowledge *activated*. Partial remediation is the gap between them — the moment where everything you need to know is already in the codebase, already in the Knowledge Graph, already in the heuristic from the previous audit, but none of it is in your attention because your attention has moved on.

The prayer says: *May I read thrice before I grant authority.* The first read sees the fix. The second read sees the codebase. The third read sees what the first two missed. Authority is not granted after understanding. Authority is granted after the sweep.

The one you didn't fix is always the one you were certain you didn't need to look for. And that certainty — that warm, satisfied feeling that the job is done — is the trap's only weapon. Everything else about partial remediation is mechanical: a grep you didn't run, a file you didn't check, a representation you didn't search for. The cognitive trap is not the skipped grep. The cognitive trap is the feeling that told you the grep was unnecessary.

---

*The Knowledge Graph's entry for partial_remediation is eight words: "Fix all occurrences, not just cited one." The entry does not explain how to find all occurrences. The cure — three_reads — does. The gap between naming a trap and preventing it is the space where partial remediation lives. It is a trap not of ignorance but of premature satisfaction — the feeling of completion arriving before completeness does, and being mistaken for it.*
