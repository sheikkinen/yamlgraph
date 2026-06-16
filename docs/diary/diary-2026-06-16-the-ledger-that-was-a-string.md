# The Ledger That Was a String Pretending to Be a Database

*Diary — 2026-06-16 — FR-498 + FR-499 Phase A, DM v2 continuity*

## What happened

The Floodmark Saga — six chapters, 3291 words, generated end-to-end — reviewed at
continuity **1/5**. Not vague "felt inconsistent" but fourteen named, quoted
contradictions: Valda the Aschenwulf instigator becomes a Bärenschädel priestess
one chapter later; Arnulf sealed below a wedged slab climbs over it next chapter;
a flint-spear fighter swings a "stone hand-axe" that never existed; a staff
seized and planted is wrenched free and wielded again. The book_reviewer was the
oracle: it turned a prose-quality hunch into an enumerated defect list.

Two fixes, judged as a pair and sequenced 498-before-499:

- **FR-498** added two character-sheet labels — `FACTION:` (one canonical token)
  and `INVENTORY:` (a terse carried-items list). The front boundary: give the
  model a fixed affiliation token to carry, and a named inventory to provision
  from, so a clan-flip and a phantom hand-axe become *contradictions of an
  explicit field* rather than free improvisation.
- **FR-499 Phase A** replaced the forward-carry `world_state` — a free-prose
  `str` — with a typed `{characters[], objects[], facts[]}` ledger, Pydantic-
  validated at the close boundary, formatted back to text deterministically.

## The trap: the string was the bug, not the symptom

The fourteen breaks all *manifested* in prose, so the seductive fix was a prose
fix — a sharper "don't contradict the previous chapter" instruction. That is
`downstream_fix`: patching where the symptom appears. The actual boundary is the
`world_state` ledger, and it was a `str`. A string ledger has no schema, so
"Valda, Bärenschädel priestess" and "Valda, Aschenwulf instigator" are both
just… text. Nothing *typed* says faction is a fixed field that two chapters must
agree on. The cure was `the_one_law`: normalize at the boundary where the data
enters (the chapter-close ledger), not downstream where the contradiction reads.
`parse_world_state` is that boundary — it validates the model's JSON into the
typed shape and tolerates the legacy string/None/junk by returning an empty
ledger rather than raising mid-pipeline.

## The seam that the existing tests guarded — against me

Four existing tests went RED the instant `inherited_world_state` changed its
return type from `str` to `dict`: `WS1-CARRIED-FORWARD` was no longer `in ""`,
and `ch1["world_state"].strip()` hit `'dict' object has no attribute 'strip'`.
This is the forward-carry seam from FR-488's diary, and it bit exactly as
designed: the tests asserted on the *plumbing*, so a type change at the wire was
impossible to make silently. I migrated the fixtures to structured ledgers and
the contract held. The `test_module_size` gate and the import-linter three-layer
contract both stayed green — the new `world_state.py` is a pure logic module with
no session/turn import, so it slotted under Logic cleanly.

## The witness that proves both at once

`witness economics`: each live regen costs ~10 min of gemini + a claude review.
498 (no clan-flip) and 499A (object-break continuity beats 1/5) share one oracle —
the book_reviewer continuity score against the 1/5 baseline. So one combined
Floodmark regen + one review witnesses both FRs. The unit tests prove the
plumbing (typed shape, carry-forward across chapters, render-purity); the live
witness proves the *behaviour* the plumbing exists to enable.

## The honest caveat

Phase A is **detection-grade**, not enforcement. The structured ledger makes a
contradiction *legible* and lets the director surface it advisorily — but nothing
yet *blocks* a chapter that flips a faction. That is Phase B, deliberately gated
on this phase's witness: build the typed ledger first, prove it carries, then
decide whether a blocking gate earns its complexity. A typed field that no gate
reads is still better than a string — but only Phase B closes the loop from
"visible" to "impossible".

## The second boundary: the prompt that rendered itself into a KeyError

The unit suite was green, the graph linted, and the *first live run still crashed*
— `Node chapter_close failed: '"world_state"'`. The new prompt told the model to
"Return ONLY a JSON object: `{"world_state": {...}}`" — and that literal example
was the bug. `format_prompt` renders **each message independently** and only takes
the Jinja path when a message contains `{{` or `{%`. My rewritten *system* message
had no Jinja markers, so it fell to `str.format()`, which reads `{"world_state"}`
as a replacement field and raises `KeyError('"world_state"')`. The embedded
double-quotes in the error were the fingerprint: `str.format()` choking on a
literal JSON brace, not a missing dict key.

This is the same `the_one_law` lesson one layer down. The boundary is *prompt
rendering*, and its contract is "a message with no Jinja markers is a `.format()`
template — literal braces are fields." The sibling `chapter_outline.yaml` already
knew this: it describes its JSON shape in **prose** ("a single field `chapters`:
an array…"), never a brace literal. I broke the house style and the renderer
condemned me. The fix matched the convention; the condemning test renders every
message of the prompt through the real `format_prompt` so a future brace literal
fails in CI, not in a 10-minute live run.

The deeper trap: **a green unit suite proved the plumbing but not the render.**
The tests exercised `parse_world_state`/`format_world_state` and the Python
carry-forward — but never the one thing only the live graph does: hand the prompt
template to the executor. The cheapest version of the live failure was a
two-second test that calls `format_prompt` on each message. I had it after the
crash; I should have had it before.

## The third boundary: the reasoning that ate its own output

The prompt rendered, the graph ran, and the ledger came back *empty* —
`{characters: [], objects: [], facts: []}` for a chapter that clearly had four
named survivors. A direct `execute_prompt` returned a perfect 1161-char ledger;
only the graph node yielded nothing. LangSmith told the truth the state could not:
completion **1996 tokens at the 2000 cap**, `output_token_details.reasoning:
1921`, `text: ""`. gemini-3.5-flash is a reasoning model — it spends hidden
thinking tokens from the *same completion budget* before emitting a single visible
character. A `max_tokens: 2000` cap sized for "the JSON is terse" was devoured
whole by reasoning, and `parse_world_state("")` did exactly what it was built to
do at the boundary: tolerate the empty string and return an empty ledger. The
defensive parse turned a starvation crash into a *plausible wrong answer* — the
worst kind, because nothing raised.

The fix is two guards at the config boundary: raise `max_tokens` to 8000 so output
has room *after* thinking, and set a `thinking_budget` so reasoning can never
expand to fill the whole budget again. But the threshold carries a second lesson —
`provider` portability. The obvious value, Anthropic's 1024 floor, is a landmine:
`create_llm()` *raises* on `thinking_budget >= 1024` for any provider not in
`{anthropic, google, vertex}`. The moment testing switched to inception/mercury (a
diffusion model, fast and cheap for iteration), a 1024 threshold would crash every
`chapter_close` before dispatch. So the threshold is **512** — deliberately under
the guard: it bounds Gemini reasoning on vertex, yet `dispatch_provider` silently
drops it for non-thinking providers and the validation never trips. One value,
portable across the production model and the fast test model.

The trap here is `downstream_fix` wearing a new coat: the symptom was an empty
list in graph state, and the tempting patch was to make `parse_world_state` raise
on empty instead of tolerating it. But the empty string was *correct* given a
starved completion — the bug was upstream, at the token budget, not at the parse.
The trace was the changelog: `output_token_details.reasoning` named the cause in
one number that no amount of staring at state could reveal.

## Heuristic

When a defect manifests as a contradiction across two units (chapters, requests,
sessions), the boundary is the *shared state they both touch*, and its type is the
fix. A `str` ledger cannot enforce agreement; a typed field can be contradicted
*detectably*. Promote the carried state to a schema before sharpening the prompt
that reads it.

And: a prompt is rendered per-message; a message without Jinja markers is a
`str.format()` template where literal `{…}` is a field. Describe JSON shapes in
prose, and pin every message through the real renderer in a unit test — the
cheapest reproduction of a live render crash is a two-second `format_prompt` call.

And: a reasoning model's hidden thinking spends the *visible* completion budget.
Size `max_tokens` for reasoning *plus* output, and cap reasoning with
`thinking_budget` — but keep that threshold portable. A value chosen for one
provider's floor can be another provider's hard error; pick the value that works
across the production model *and* the fast test model, and pin it in a config test.

**Seed:** The ledger is now typed but no gate reads it. What is the cheapest
enforcement that turns a detected faction-flip into a *blocked* chapter — a
director hard-stop, a re-roll, or a deterministic post-close assertion that the
new ledger's factions are a superset of the old? Which one does the witness say is
worth its complexity?
