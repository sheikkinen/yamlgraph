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

Let that settle. The trap was *named* in Audit IV. Documented in the Knowledge Graph. Written into the Scripture. And it was repeated in Audit V anyway. Naming a trap does not disarm it.

Why? Because by the time you have fixed the one you found, the reward circuit has already fired. The work *feels* done. The commit message is drafted. The mind has already moved on. The remaining occurrence exists in the codebase but not in your attention. And that is the essence of partial remediation: it is not a knowledge failure. It is an attention failure that *masquerades* as completion.

---

## II. Three Varieties of Incomplete

The diary reveals partial remediation in at least three distinct forms, each wearing its own disguise.

### The Sibling Copy

Two files contain the same logic. One breaks. You fix it. The other persists, carrying the original defect forward.

FR-255 found identical `_invoke_graph` code in the MCP server and the A2A server. The diary's diagnosis was blunt:

> "identical code in two places (mcp_server and a2a_server) that would diverge on any future fix."

The cure — extracting the shared logic to `graph_loader.py` — eliminated the *category* of partial remediation. But the cure only came after someone noticed the asymmetry.

### The Cleanup Contract

On March 19th, five bugs emerged from a single root cause: a singleton session object reused across telephone calls, whose cleanup between calls was incomplete at every layer.

> "Each cleanup path (call_cleanup, call_abort, session.reset) cleared *some* state but not all. The cleanup code grew organically: guards added for one bug, data keys for another, transport fields for a third. No single author saw the full picture because each layer was fixed in isolation."

Every mutable field set during a call creates an obligation to clear it on cleanup. The obligation is implicit — no simple grep will find it — and each fix addressed one obligation while leaving others unmet. The diary proposed a heuristic:

> "can you grep for every `context[key] = ` and find a matching `context.pop(key` or `del context[key]` in a cleanup path?"

This transforms an implicit contract into a mechanical check.

### The Renumber Cascade

When requirement IDs were renumbered, the operation touched the architecture file and the test files. It did not touch the changelog fragments:

> "Merge commit `be7ea746` ('renumber REQ-YG-238→241') updated ARCHITECTURE.md and `test_state_builder_reducers.py` to REQ-YG-241, but `changelog/unreleased/fr-238-pipeline-accumulated-state.md` still says `req: REQ-YG-238`."

The developer updated the artifacts that came to mind. The changelog fragments — a different file type, in a different directory — were outside the mental boundary of "things that reference requirement IDs." A post-renumber `grep -r 'REQ-YG-238'` would have caught it in seconds. The cost of preventing partial remediation is measured in seconds.

---

## III. The Cure: Three Reads

The Scripture prescribes `three_reads` as the antidote:

> "surface → deep against code → mechanical simulation"

**The first read is surface.** You read the change you made. This is what every developer does naturally. It is necessary but insufficient.

**The second read is deep, against the code.** You search for other locations where the same concept appears. You grep. You trace references. This is the read that catches the sibling copy, the module table, the changelog fragment. It is the read that most developers skip.

The diary entry for FR-190 demonstrates this:

> "After adding the new trap, FR-189's `test_no_other_traps_changed` also needed updating to include `infrastructure_self_exempt` in its expected set. Fixing only the new file would have left the guard incomplete."

The developer caught this during the second read — reading the change against the code, discovering that an existing test enumerated the trap list and needed updating.

**The third read is mechanical simulation.** You simulate the system as a machine, following every reference chain to its terminus. You don't read for understanding — you read for *completeness*.

The cure works because each read changes the question:

- Read 1: "Is the fix correct?" *(Confirm)*
- Read 2: "Where else does this pattern exist?" *(Discover)*
- Read 3: "Does the fix apply to each occurrence?" *(Discriminate)*

Expand, then contract. First, cast the net wider than you think necessary. Then, for each catch, verify it belongs. The partial remediator does neither.

The Inquisitor's heuristic from Audit XLV encodes the cure operationally:

> "When creating a remediation FR for missing artifacts, grep the full audit history for all instances of the violation class, not just the ones cited in the most recent audit. Scoping remediation to 'the ones I remember' is `partial_remediation` — the audit trail is the authoritative inventory."

Memory is selective. Grep is not. The cure replaces memory with mechanism.

---

## IV. The Concept as Boundary

The Scripture's One Law states:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

Where is the boundary in partial remediation? It is a *conceptual* boundary: the point where a fact enters the codebase.

When the project added its eighth provider, the fact "we have 8 providers" was expressed in multiple locations: line 219, line 1115, the ASCII diagram, the capability table. Each location is a *downstream manifestation* of the same fact. Fixing one location normalizes the fact at one manifestation point. But the boundary — the place where the fact should have been normalized — is the concept itself.

The renumber cascade illustrates this perfectly. The concept "REQ-YG-238 means pipeline accumulated state" was expressed in ARCHITECTURE.md, in test decorators, in changelog fragments, and in capability YAML. Renumbering the architecture file normalized the concept at one physical location. But the boundary of the concept was all four artifact types. The normalization was partial because the boundary was misidentified.

The multi-call cleanup bugs show the same pattern. The concept was "mutable state set during a call." The boundary was "the cleanup function." But the cleanup function only cleared the fields its author knew about. The boundary was defined by the author's knowledge of the concept, not by the concept itself. When knowledge is incomplete, the boundary is drawn too narrowly.

The One Law demands that boundaries be drawn by the *concept*, not by the *developer's awareness*. This is why mechanical tools — grep, cross-reference scripts — are not optional aids. They are the only reliable way to draw a boundary that matches the concept's actual extent.

---

## V. Why It Persists

Partial remediation appears in the diary in March, April, and May. It is named, defined, and graduated to the Knowledge Graph. It is the subject of automated tooling designed to prevent it. And it keeps happening.

Why?

Because partial remediation is not a knowledge problem. The developers who fell into this trap *knew about it*. They had read the Knowledge Graph. They had written diary entries about it. They had built tools to catch it. And still, when the next fix came along, they fixed the one that was cited and stopped looking.

This suggests that the trap operates below the level of knowledge, at the level of *attention*. Knowledge says "check for other occurrences." Attention says "this is done — move to the next task." And attention, in the moment of closure, is stronger than knowledge.

The cure — three reads — is not a knowledge intervention. It is an *attention* intervention. It forces the mind to stay with the fix after the reward circuit has fired. To keep looking after the click of closure.

The one you didn't fix is always the one you were certain you didn't need to look for. And that certainty — that warm, satisfied feeling that the job is done — is the trap's only weapon.

---

*The Knowledge Graph's entry for partial_remediation is eight words: "Fix all occurrences, not just cited one." The gap between naming a trap and preventing it is the space where partial remediation lives. It is a trap not of ignorance but of premature satisfaction — the feeling of completion arriving before completeness does, and being mistaken for it.*
