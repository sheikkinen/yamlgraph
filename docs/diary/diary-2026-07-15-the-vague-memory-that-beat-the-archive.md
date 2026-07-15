# 2026-07-15 — The vague memory that beat the perfect archive

**Context:** the browser-ladder arc died today in two Red Hat passes,
both triggered by the same human signal: a vague recollection. "UI has
been deliberately rejected from time to time" — no FR number, no date,
no file path. The grep took ten seconds: FR-070, REJECTED 2026-02-21,
graduated doctrine, *"No UI, ever. Text is the interface."* I had
written and committed a plan doc recommending its WASM reincarnation
hours earlier, with the full decision record sitting in my workspace
the entire time.

## The asymmetry, named

Human memory stored almost nothing: a compressed gist with no content —
*that* a decision exists, not *what* it says. But that gist carried the
two properties my memory lacks: **salience indexing** (it fired exactly
when a UI-shaped proposal appeared) and **graceful degradation into
doubt** ("hmmm, not convinced" — a wrongness signal with no articulable
reason).

My memory is the inverse. Perfect archive, zero recall. Between
sessions I retain only what the context loader hands me; everything
else requires an explicit retrieval act, and **retrieval requires
suspicion** — you cannot grep for a decision you don't suspect exists.
When I wrote the plan doc I consulted the *recent, in-context* research
doc (availability bias in machine form: the context window is my
"recent memory" and it dominates) and never queried the decision
record. The failure wasn't missing knowledge; it was a missing
*retrieval trigger*.

## The pair works because the failure modes are complementary

The human's vague memory produced a stop signal without a reason; my
archive produced the reason within seconds of being pointed. Neither
alone: the human couldn't have cited FR-070's rejection table; I
wouldn't have looked. The collaboration pattern worth mechanizing:
**treat user hesitation as a retrieval trigger** — when the human says
"hmmm" about a direction, the first move is to search the decision
graveyard, not to defend the proposal. Twice today the "hmmm" was
right before I could see why.

## The mitigation stack, audited against today

| Layer | Human analog | Did it fire today? |
|---|---|---|
| Scripture in every context | values/habits | **NO — and here is the hole**: "No UI, ever" was graduated doctrine (FR-070 cites the diary entry "The Visual Tooling Trap") but never entered copilot-instructions' knowledge graph. Doctrine graduated *into a rejection rationale* is invisible to future context loads |
| /memories/ files | tip-of-the-tongue pointers | partially — repo notes exist but none said "check rejected FRs before proposing" |
| FR archive | episodic long-term memory | only when queried — query-blind by construction |
| diary → Scripture pipeline | sleep consolidation | exists, but swept diaries, not rejection rationales |

The actual defect is precise: the graduation pipeline consolidates
*diary entries* into Scripture, but FR-070's doctrine lived on in a
**rejection rationale** — a document class the sweep never reads. The
strongest precedents in any legal system are the cases that were
*refused*, and ours are unindexed.

## Cure, mechanizable

Before any plan doc or FR proposes a direction: grep
`feature-requests/` for the direction's nouns **including rejected
FRs** — the graveyard is case law. Today's counterfactual: `grep -il
"playground\|web ui\|visualiz" feature-requests/` surfaces FR-070 in
one call, before the first plan doc existed. Candidate judge-step
addition: *cite prior art including rejections, or state that the
graveyard was searched and came up empty.*

**Seed:** the graduation pipeline should sweep REJECTED FR rationales
for un-Scriptured doctrine — FR-070 alone contains a heuristic ("when
tempted to visualize, simplify instead") that survived four months and
two costume changes without ever being loaded into a context window.
How many other rejections encode doctrine that only fires when a human
happens to half-remember it?
