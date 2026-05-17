# Chapter 5: Same Shape, Different Soul

*Part I — false_duplicate*

---

## I. Two Proposals Walk Into a Codebase

In April 2026, someone proposed an optimisation: run the LLM extraction on each interim speech-to-text result while the user is still talking, accumulate the extracted fields, and process the decision after the silence fires. It was a latency play — move the LLM off the critical path by prefetching during speech.

The developer reviewing the proposal felt a cold recognition. They had seen this before. Five months earlier, a feature called NC-220 had attempted something that looked identical: fire an LLM on partial inputs, then merge the results when the final input arrived. That feature had shipped, detonated with a four-bug cascade, and been rolled back in NC-227. The root cause — concurrent actors writing the same mutable state — was documented but never resolved.

The reviewer's instinct was to reject. *Too risky. Don't do it.* The shape was the same: both proposals fire an LLM on partial inputs. The history was catastrophic.

It was wrong.

The diary entry from that day records the moment of correction:

> "Syntactically the two look similar: both fire an LLM on partials. Semantically they are different universes."

NC-220 was *speculation*: fork the state, run the LLM, then commit or rollback the speculative branch into the real state. Correctness required consensus between two writers. Concurrency required locks or checkpoint isolation — neither of which existed.

NC-232 was *prefetch*: launch the LLM, write results to a scratch dictionary that nobody else reads during the launch window, and let the real task check the scratch *if* it's valid, else recompute from scratch. Cancellation is free — drop the scratch. Worst case is today's latency plus a wasted API call.

Same syntax. Different soul.

The reviewer almost killed a safe optimisation because it wore the costume of a dangerous one.

---

## II. The Trap: Syntactic Similarity ≠ Semantic Equivalence

The trap is called *false_duplicate*. Its definition is six words: **Syntactic similarity ≠ semantic equivalence.**

Pattern recognition works. A senior developer glances at a function signature and knows what it does. A code reviewer spots an anti-pattern in unfamiliar code. An architect recognises a distributed systems problem dressed as a microservice question. Matching by shape is fast, and being fast at shape-matching separates the experienced from the novice.

The trap exploits this strength. It says: *you recognise this shape, therefore you know this thing.* Because the recognition is genuine — the shapes *are* similar — the conclusion feels earned rather than assumed. There is no alarm. Just a quiet substitution: the thing in front of you is replaced, in working memory, by the thing you remember.

Consider the Chatterbox consolidation (FR-237). Two Python files, both called `tools.py`, both importing `torch`, both calling `model.generate()`. A developer consolidating directories would naturally ask: *are these the same?* The syntactic evidence says yes.

But one file wraps `ChatterboxMultilingualTTS` with a `language_id` keyword argument. The other wraps `ChatterboxTTS` with an `audio_prompt_path` parameter. One clones a voice from reference audio. The other synthesises speech in a specified language. Confusing them would ruin both.

The diary records the trap avoided:

> "The two `tools.py` files were syntactically similar (both import torch, both call `model.generate`), but semantically distinct. Merging required preserving both functions completely rather than collapsing them."

**The parts that match are not the parts that matter.**

---

## III. The Institutional Shape

In April 2026, a developer working on FR-301 needed to tag a changelog fragment with a requirement ID. The tests already used `@pytest.mark.req("REQ-YG-162")` — the watcher FSM capability area. The changelog fragment got `req: REQ-YG-162` too.

The CI gate rejected it.

The identifier was identical. The *validation pipelines* were not. `@pytest.mark.req` is checked against `ARCHITECTURE.md`. The changelog `req:` field is checked against capability YAML files. Same string, different contract, different source of truth.

The diary names it plainly:

> "Same identifier, different validation boundary. This is `false_duplicate`: syntactic similarity does not imply semantic equivalence."

The audit-178 case shows how far this propagates. `REQ-YG-235` (Chatterbox voice clone) was assigned to FR-234 (Parallel Fan-Out Edges) in a changelog fragment. The numbers are close. The capability areas are adjacent. The mistake survived *seven audit cycles* without correction — because a REQ ID that *looks right* is more dangerous than one that is obviously wrong. The obviously wrong one triggers investigation. The plausibly right one passes.

---

## IV. The Boundary Within the Boundary

Two features (FR-286 and FR-287) hit the same wall. Shell scripts containing brace-heavy constructs — regex quantifiers like `{0,250}`, bash functions with `{...}` blocks — were embedded in YAMLGraph tool commands. The YAMLGraph template engine saw the braces and interpreted them as variable placeholders. Runtime failure: `Missing variable: '0,250'`.

> "Shell snippets that looked valid were interpreted by YAMLGraph template substitution as variable placeholders. The syntax looked familiar, but semantics differed at the template boundary."

This is false_duplicate at the *character level*. The brace `{` is syntactically identical in bash and in Jinja2 templates. It is semantically opposite: in bash, it groups; in Jinja2, it substitutes. The template engine sees shape, not soul.

---

## V. Decompress Before Comparing

The NC-232 reviewer almost rejected a safe feature because the compressed representation — "fire LLM on partials" — matched a dangerous precedent. The Chatterbox developer could have collapsed two distinct functions because the compressed representation — "Python file that calls model.generate()" — was identical. The changelog author used an identifier that looked right because the compressed representation was true in one context and false in another.

In each case, the cure was the same: **decompress before comparing.** Look past the shape. Ask what contract each thing serves. Ask what state each thing writes. Ask what boundary each thing crosses. Ask what happens when each thing fails.

The FR-346 diary entry demonstrates this discipline:

> "Early drafts tried to unify the Chaplain subprocess action with the async task-based action under the same class hierarchy. These two actions share a name but not a contract: one is synchronous from FSM's perspective (fork + wait), the other is fire-and-forget (asyncio task + guard key). Recognising this as `false_duplicate` kept Phase 1 cleanly scoped."

"Share a name but not a contract." That is the normalisation rule. At the boundary where two things are being compared, the question is not *do they look the same?* but *do they promise the same things to the same consumers under the same failure modes?* If the answer requires investigation, they are not duplicates. They are homonyms.

The four invariants for prefetch — no shared durable state, overwrite never merge, debounce and cancel, validate before use — are not rules about concurrency. They are questions disguised as constraints. Each one asks: *is this really the same as the thing you remember?*

> "Violate any one and the feature becomes NC-220."

Four invariants separate a safe optimisation from a four-bug cascade. The shapes are identical. The souls are not. And the only way to know is to ask the questions that compression discards.

---

## VI. For the Practitioner

When you feel the flash of recognition — *I've seen this before* — that flash is valuable. It narrows the search space. It summons relevant experience. But it is not a conclusion.

Before you collapse two things into one, ask:

1. **What does each one promise?** Same interface, different postconditions means different things.

2. **What does each one write?** If they write to different state, they are different regardless of how similar they read.

3. **What does each one assume?** The Chatterbox files both call `model.generate()`. One assumes a language code. The other assumes a voice sample. Same verb, different object.

4. **What happens when each one fails?** The success path may be identical; the failure path may not.

Pattern recognition gives you candidates. Only investigation gives you identity.

---

*The cheapest duplicate is the one you didn't merge.*
