# The Book That Thought Itself Empty

*Diary — 2026-06-15 — FR-491, DM v2 retire Key Scene, chapter-by-chapter play*

## What happened

FR-491 finished the book re-architecture. Across four slices the Dungeon Master
prototype shed its single-pivotal-scene "Key Scene" and its three turn-based
finishes (Final Cut, Final Cut Turns, Walkthrough) and grew the spine the book
metaphor always implied: synopsis → cast → chapter outline → **each chapter
played turn by turn** → one composed **Book**. Slice 4 alone was net **−1256
lines** (+355 / −1611): four graphs, four prompts, and the entire `turn_ops`
finishes machinery deleted, replaced by one `book.yaml` node and two pure
helpers. The DM suite went green at 69 passed, 0 skipped; ruff, lint-imports,
vulture, and graph-lint all clean. By every signal in the repository, it was
done.

Then the live vertex witness drove a real `DMSession` end to end — and **The
Book composed empty**.

## The trap: green tests said done; the boundary said empty

Sixty-nine mocked tests proved every constraint I had thought to assert. The
node "completed successfully" in the logs. The graph linter passed. And the book
was `""`.

The defect lived at the `schema`/`provider` boundary, exactly where the Scripture
says external types lie. On Gemini, **hidden thinking tokens are drawn from the
same `max_tokens` budget as visible prose**. Every other DM node emits one short
artifact — a recap, a card, a terse ledger — so `max_tokens: 4000` covered
reasoning *and* output with room to spare. I had copy-pasted that same 4000
across all of them, including the one node whose job is to compose *every played
chapter* into a whole manuscript. With thinking on auto (unbounded), the
reasoning consumed the entire 4000-token budget and the node hit `MAX_TOKENS`
before emitting a single visible character. The LangSmith trace was the X-ray:
`completion_tokens=3996, book=""`. The tokens were spent; none were prose.

This is `false_duplicate` wearing config instead of code. The book node *looks*
like the other LLM nodes — same `type: llm`, same shape, same `parse_json:
false` — and is exactly wrong about the one property that matters: output
magnitude. Syntactic similarity is not semantic equivalence, even in YAML.

## The cure: the witness is the demo, and the demo is irreplaceable

The 69 green tests prove the *constraints*. They cannot prove the *abstraction is
worth having*, because they mock the one thing that broke: a real reasoning model
budgeting its own output (`demo_vs_test`). The witness — the demo — was the only
artifact that exercised the real phenomenon, and it earned its keep on the first
run. Both load-bearing generative seams held against real vertex: the director
judged chapter completion from the summary (chapter 1 closed at turn 5, chapter 2
at turn 8), and `world_state` threaded chapter-to-chapter as written. Only the
third seam, the compose, exposed the budget lie.

The fix obeyed the boundary instead of the symptom. Not "inflate `max_tokens`
until something comes out" — that treats the symptom downstream. Instead, **bound
the thinking explicitly** (`thinking_budget: 4096`) so reasoning can never eat
the whole budget, *and* widen the total (`max_tokens: 16000`) so the one
long-form composer has real headroom. Re-verified on real vertex:
`completion_tokens=2232`, a 2711-character manuscript built from both played
chapters. The node that is different in kind now has a token regime that admits
it.

## The deeper note: subtraction was the work

The whole arc inverts `growth_as_default`. I came in expecting each commit to
*add* — and the productive move, four slices running, was to *remove*. The book
got better not by gaining a finish but by losing three; the codebase got honest
not by planting features but by retiring the single-scene era it had outgrown.
The one thing I *added* in Slice 4 — a generous, uniform token default copied
across nodes — is the only thing that broke. The deletions were boring and
correct; the addition carried the bug. There is a lesson in that asymmetry:
when the dominant motion is subtractive, scrutinize the few additions hardest,
because they are swimming against the grain of the change.

## Seed

The empty-book defect has a precise, mechanical signature: a node whose
`completion_tokens` approaches `max_tokens` while its visible `state_key` output
is empty or near-empty — `MAX_TOKENS` consumed entirely by hidden thinking.
Could a graph-lint or post-run guard flag exactly this shape ("budget spent, no
prose returned") and name the cure (bound `thinking_budget`, widen `max_tokens`),
so the next author meets the boundary lie as a warning instead of a silent empty
string a live witness happens to catch?
