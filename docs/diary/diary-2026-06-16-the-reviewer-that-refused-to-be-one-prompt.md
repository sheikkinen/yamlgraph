# The reviewer that refused to be one prompt

*FR-497 — a stand-alone book-reviewer example, built as map → reduce*

## What happened

The ask started small: give the Dungeon Master a way to evaluate the prose it had
just rendered. The obvious shape was one prompt — paste the book, ask for a 1–5 and
a paragraph. I planned exactly that, and it was judged. Then the user named the
flaw before I did: *the almighty prompt*. A single call that ingests a whole book
and emits a number is unauditable, hits every long-context failure mode, and hides
its reasoning behind one digit.

So we stopped, researched how books are actually evaluated, and replanned. The
literature pointed one way every time: decompose. **Lost in the Middle** says the
middle of a long context is where evidence goes to die — so one chapter per prompt.
**BooookScore** says book-length judgement is incremental, not one-shot — so map,
then reduce. **FActScore** says reliability comes from atomic, independently
checkable claims — so pairwise continuity and per-beat synopsis delivery. **HANNA**
gives the axes. The re-judgment froze two invariants that turned out to be the
whole design: **no LLM call sees the whole book**, and **no LLM emits a number** —
every score is computed by a deterministic reduce; the model writes only prose.

The build itself was boring, which is the sign the judgment was good. Pure
parse/lint/reduce under TDD, then the prompts, then the graph, then a mocked graph
test plus a *tested* prompt-scope gate. The K4 gate is the interesting artefact: it
asserts, per prompt, exactly what the stage is allowed to see — one body for
chapter review, two for continuity, summaries-only for synopsis, findings-only for
the verdict. The anti-almighty-prompt rule is not a comment; it fails CI if
violated.

## The trap: green mocks, red reality — twice, at the same boundary

Thirty tests passed with a fake executor. Then the first live run died, and the
second live run died, both at the *same* seam: the LLM boundary.

1. **The provider named the key, not me.** The continuity schema required
   `{detail: str}`; the model returned `{issue: ...}`. Structured output is a
   request, not a guarantee. The fix was to stop having a key at all — `breaks`
   became `list[str]`. No nested key means no key to get wrong.
2. **The schema class was a lie of a name.** `compute_node` did
   `SynopsisBeats.model_validate(state["synopsis_beats"])` and pydantic rejected
   its own input: *"Input should be an instance of SynopsisBeats"* — while the input
   *was* a SynopsisBeats. It was the executor's *dynamically built* class, distinct
   from mine despite the identical name (FR-059's exact signature). The mock
   returned a dict and sailed through; the real node returned a foreign instance.

Both are the same lesson the Scripture already carries: *normalize at the boundary,
trust no provider's type.* The mock had quietly papered over the boundary by
returning the one shape — a plain dict — that the real system never produces for a
plain `llm` node. The fake was too kind.

## The cure that held

`_as_dict` coerces model-or-dict to a dict at the compute boundary, and a witness
test feeds `compute_node` a model *instance* (not a dict) so the foreign-class path
can never silently regress again. The continuity boundary went flat. The live run
then produced a real, defensible review — and caught three genuine continuity
contradictions across the single chapter seam that no shape check would ever find.

The deeper note: a mock's job is to stand in for the boundary, but a mock that
returns the *convenient* shape instead of the *actual* shape isn't testing the
boundary — it's testing my hope about the boundary. The two live failures were both
invisible to thirty green tests because the fake spoke dict and the provider spoke
model.

## Heuristic

- **A mock that returns the convenient shape hides the boundary it claims to
  cover.** When a node's real output is a provider/framework object, the fake must
  return that object's *shape* (a foreign model instance), not the dict you wish it
  returned. Otherwise green mocks guarantee nothing about the live seam.
- **The cheapest anti-almighty-prompt enforcement is a render-and-count test.**
  Don't trust the prompt's intent; render it and assert exactly which inputs appear.

**Seed:** Could the framework offer a "boundary mock" mode that, for any `llm` node
with a schema, returns a *dynamically built* instance (not a dict) by default — so
that the foreign-class coercion path is exercised by every mocked graph test,
making FR-059-class bugs impossible to mock away?
