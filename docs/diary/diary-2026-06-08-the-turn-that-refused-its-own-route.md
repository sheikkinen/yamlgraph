# The Turn That Refused Its Own Route

**Date:** 2026-06-08
**FR:** FR-477 — DM v2 turn operation (private intents → consolidated recap)
**Arc:** Judge → Enforce, in one sitting, with the Judgement folded into the plan.

## What happened

FR-477 planned a play loop: every principal privately reasons (THINKING) and
commits (INTENT) each turn, then the intents consolidate into one authoritative
"Turn N" recap. The plan was sound but left two load-bearing decisions
unspecified. At Judge I resolved them as binding rulings and folded them inline.
At Enforce the rulings did the work — implementation was almost mechanical
because the hard thinking had already happened.

The plan's §6 anticipated a new `POST /story/turn` route. I did not build it.
The judged J3 design reuses the turn's `{text, reviewed}` recap entry, so turns
ride the existing stage-agnostic `weave`/`edit`/`accept`/`nav` endpoints
unchanged. The fifth route would have been dead weight. The plan named a file;
the judgement made it unnecessary.

## The trap I named at Judge and it paid off at Enforce

**`structured_result_through_str_str_seam`.** `_invoke_stage` is `str → str` and
the entire weave/edit/accept/`_entry`/`_view` chain assumes one `{text,
reviewed}` entry per stage. A turn returns *N intents + 1 recap* — it does not
fit that seam. The cheap move would have been to widen `_invoke_stage` to return
a structured blob and special-case every caller. Instead J3 isolated the
structured result to a dedicated `_invoke_turn` that writes `intents` as a *side
effect* and returns only the recap string, so the shared `str → str` contract
stayed honest. Every existing test of the preplan stayed green without a touch.
The seam held because I refused to widen it.

## The over-assertion that caught my own design drift

`test_iterate_rerolls` first asserted the DM's "make it grim" instruction would
appear in the *intents*. It failed — and the failure was correct. The frozen
spec routes `instruction` to `turn_recap` only; `character_intent`'s inputs are
`char`/`scene`/`turn_n`. The intents *re-roll* (regenerate fresh each pass, so
they can never drift from the recap they fed) but they are not *steered* by the
DM. My test had quietly assumed a capability the Judge never granted. The RED
condemned the test, not the code. I fixed the assertion to match the ruling
(`name_the_seam` cure: assert what J2 actually says — co-generation, not
steering). Respect the RED; it was the color of understanding that the test, not
the implementation, had wandered off-spec.

## Boundary honored

`turn_recap` names characters from the session-supplied `cast` list by index,
not from an LLM-echoed `name` field. Had I trusted the model to echo each name
back, a hallucinated or dropped name would have mislabeled the recap — the
`plausible_wrong_answer` trap, where output passes a shape check but is
semantically wrong. The authoritative names live on our side of the boundary;
the model only writes prose. The live Gemini run confirmed it: the recap named
Kara, Tarek, *and* Naru (who was only in the scene text) without ever being
handed a name to echo.

## Seed

When a planned artifact (a route, a table, a flag) becomes unnecessary *because
of a judgement made after the plan was written*, the plan and the judgement
disagree about what must exist. I caught this one by hand and wrote a deviation
note. **Could a mechanical check compare a judged FR's "anticipated files" table
against the actual diff and flag every planned-but-unbuilt artifact, forcing
each into either "built" or an explicit "deviation: superseded by J-N"?** A plan
that still lists a file the judgement killed is a small lie the next reader
inherits.
