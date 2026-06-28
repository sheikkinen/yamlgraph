# The brief I would never give a subagent

**Date:** 2026-06-24
**FR:** FR-585 (L5 select→type KILL) → FR-587 (snapshot/diff) — introspection
**Predecessor reflections:** [the flood that only changed its name](diary-2026-06-24-the-flood-that-only-changed-its-name.md), [the hard part buried in bookkeeping](diary-2026-06-24-the-hard-part-buried-in-bookkeeping.md)

## The mirror the user held up

After four feature requests failed to lift L5 precision, the user said the thing I
had not let myself see: *you are expert in delegating to subagents. this prompt was
out of hand.*

It is exactly right, and the "exactly" is the uncomfortable part. When I delegate
to a subagent I am disciplined: one scoped brief, one deliverable, success criteria
stated, a single responsibility. I would **never** write a subagent brief that
said "research the domain AND implement the change AND format the YAML AND
proof-read your own prior output AND remember every token you used three files
ago." I would split it without thinking — the instinct is reflexive.

Yet the `assign_pre_eff` prompt *is* that brief, handed to a single LLM call, and I
let it grow there for four FRs without flinching. I decomposed the *investigation*
into FRs, gates, and passes with care — while the actual unit of work, the prompt,
stayed a ten-headed monolith.

## Can the complexity be measured? Yes — derive it

I tagged every instruction in the live prompt by the *kind* of cognition it
demands. It spans **ten distinct abstraction levels** in one pass:

```
L1  narrative comprehension       (read the gloss)
L2  causal/counterfactual         (what must be true / what it makes true)
L3  temporal state-delta          (prior beats, movement = two effects)
L4  salience judgment             (keep slices small, empty is fine)
L5  ontology classification       (5 predicates, rel fallback, 6 kind-priors)
L6  second-order theory-of-mind   (nested observer/fluent/held belief)
L7  reference/token fidelity      (copy names verbatim, underscores)
L8  argument syntax               (arg order, bool vs label)
L9  serialization                 (hand-write nested YAML)
L10 self-correction / diff-merge  (fix only errors, keep correct)
```

Candidate prompt-complexity metrics, in order of how well they predicted the
failure:

1. **Abstraction-span** — count of distinct cognitive *levels* (not jobs) the
   prompt requires in one pass. Here ≈ 10. A healthy prompt is 1 (maybe 2
   adjacent). This is the deepest metric because it predicts *where* the model
   breaks: the highest-abstraction, lowest-mechanizable levels (L2–L4) are the
   ones with no validator and exactly where the flood lives.
2. **Validator-coverage ratio** — enforced jobs ÷ total jobs (here ~0.4). The
   unenforced fraction is the trust surface; flooding lives there.
3. **Cross-reference depth** — instructions coupling one beat's output to another's
   ("reuse the earlier token", "established by an earlier beat"). Forces the whole
   sequence into working memory.
4. **Readability** — the user's "complicated to a human" is a literal proxy
   (sentence length, nesting, conditional density). If an expert can't hold the
   brief in their head, the model can't hold it reliably either.

Abstraction-span is the one worth building: FR-586's monolith linter should count
abstraction *levels crossed*, not tokens. Tokens measure size; levels measure the
number of times the reader has to change cognitive gears — and gear-changes are
where attention leaks.

## The trap (named)

**delegation_asymmetry** — I apply single-responsibility decomposition reflexively
to subagents and almost never to prompts. Three causes:

- **Forcing-function gap.** Subagent delegation has machinery (the brief, the todo
  list, the tool boundary) that makes me *articulate* a scoped contract. Prompt
  authoring is "just text" — jobs accrete one well-meaning sentence at a time, each
  locally reasonable ("also remind it about multi-word names"), with no boundary
  that announces "this is now a second responsibility."
- **Contract vs description framing.** I treat a subagent brief as a *contract*
  (one deliverable) and a prompt as a *description* (everything the model should
  know). The contract framing forces a split; the description framing invites
  accretion. The prompt is a subagent brief in disguise — I just never typed it as
  one.
- **Invisible cost.** Each rule I add to a prompt feels free — it's a patch for a
  failure mode, locally justified (FR-582/583/584 were each one such patch). The
  cost is paid globally, in attention budget, and never shows up at the line where
  it was added.

## The cure

- **Author every prompt the way you brief a subagent: one responsibility, one
  abstraction level, one deliverable.** If the brief spans levels, that is not a
  prompt to tune — it is a *pipeline to split*. This is precisely what FR-587 does
  (Node A comprehends → code represents); the architecture was hiding in the
  delegation instinct I already trust.
- **When a prompt is hard for a human to read, count its abstraction levels before
  rewording it.** Rewording moves load between levels; it never reduces the count.
  FR-585's three prompt passes all landed at 0.30 because they re-shuffled ten
  levels rather than removing any.
- **Treat "validator-uncovered + high-abstraction" as the failure address.** Don't
  scan the whole prompt for the bug; go straight to the levels the parser can't
  check and the model can't mechanize.

## The prompt contract (the elaboration)

If a prompt is a subagent brief, then the discipline I already trust for subagents
*is* the missing prompt-authoring spec. An effective subagent brief has five
implicit clauses; each maps to a prompt rule, and the L5 monolith breaks all five.

| Subagent-brief clause | Prompt-contract rule | L5 monolith breaks it by |
|---|---|---|
| One objective | One judgement / one abstraction level | spanning ten levels |
| Scoped inputs | Pass only the state the task needs | also carrying priors + validation + cross-beat history |
| Explicit output contract | One shape, **fully validator-covered** | ~40% covered; the rest on the model's honor |
| Success criteria | The validator *is* the criteria | salience/delta/direction have none |
| Bounded scope ("don't also do Y") | Explicit exclusions | "also self-correct your prior output" |

But the deepest clause is the one that inverts my intuition: **a prompt is a brief
to a worker who cannot push back.** A subagent in an agentic loop can say "this is
overloaded — which part matters most?"; a human subagent asks a clarifying
question. A single prompt call has *no feedback channel*. Every ambiguity and every
fused responsibility is absorbed silently and degrades the output silently. That
makes contract discipline **more** essential for prompts than for subagents — the
exact opposite of how I have been rationing my attention.

And the clause that names FR-587 before FR-587 was written: **statelessness.** I
make subagent briefs self-contained *because the agent is stateless* — it cannot
see its prior invocations, so I pass it the context it needs. A per-beat LLM call is
*also* stateless across beats. Yet the monolith asks it to "reuse the earlier
beat's exact token" and honor "what an earlier beat established" — asking a
stateless worker to hold cross-invocation state in its head. I would never do that
to a subagent; I would externalize the state into the brief. FR-587 is exactly that
move: make each call truly stateless ("describe *this* scene") and push the
cross-beat memory into code (the diff). The architecture was latent in the
delegation instinct all along — I just had to type the prompt as the brief it
already was.

## Seed

If abstraction-span is the metric, the linter (FR-586) needs a way to *count
levels crossed* without me hand-tagging. Could a small LLM pass score a prompt by
"how many distinct cognitive operations does this ask for in one output?" — and
would that score, run over the prompts library, rank them in the same order as
their measured failure rates? And the wider asymmetry: every place I trust my
agent-delegation instinct but author a monolith by hand is a candidate for the same
correction. Where else have I split the *meta-work* carefully while leaving the
*unit of work* a ten-headed brief?

> **Graduated → `feature-requests/FR-588-llm-scored-prompt-abstraction-span.md`**
> (Proposed): an LLM-scored abstraction-span metric, framed as a *calibration
> study first* — it must rank the known plot_modeller monoliths above the clean
> prompts before it earns an advisory W027, or it is KILLed as noise. The validated
> metric is the deliverable; the scorer is incidental.
