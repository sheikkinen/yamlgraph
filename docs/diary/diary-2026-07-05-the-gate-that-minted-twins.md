# Diary — 2026-07-05 — The Gate That Minted Twins

## Context
Use-case review of FR-686 (novel_fandom agent-first rewrite) during its
judgement cycle. Scenario: synopsis implies an unnamed third character —
father of one protagonist, killed by the other. Both character creations
must reference him.

## What Happened
The judged design (Judgement v2, Findings 1–6) had a deterministic
existence check inside every `create_*` tool: "referenced ID must exist —
create it first." Walking the use case exposed the failure mode: the
error message *coerces* the agent into minting the unnamed entity
mid-create, from the local context of whichever character it is currently
building. Hilde's pass mints `hildes_father` ("my father, drowned").
Erik's pass doesn't recognize that ID and mints another ("the man I
killed"). Two IDs, one person, contradictory framings — both internally
coherent, both passing every deterministic gate.

Then checked git history: the deleted canon already contained the
evidence. `ulf`/`ulfs`. `arnulf_rescue`/`arnulf_rescued`. The
invented-relative stubs `hildes_father`, `gunnars_father`,
`reinmars_father`, `fridas_grandmother`. The failure predicted by the
thought experiment had already happened in production runs.

## The Trap
`gate_checks_shape_not_substance`, in a new costume. The gate answers
"does this ID exist" but the actual question is "does this *entity*
exist" — an identity question, which is semantic. A deterministic gate
placed on a semantic question does not remove the error; it **relocates
it to where no gate can see it**, and worse, it *coerces the LLM into
producing the invisible error* as the path of least resistance. The
enforcement mechanism was the bug's manufacturing process.

Second-order trap: the digest + ref-prefetch amendment (Finding 2) checks
internal consistency only. Both twins are internally coherent. Only the
origin document — the synopsis — reveals that the father and the victim
are the same man. A validator without ground truth validates plausibility,
not truth (`plausible_wrong_answer` at the pipeline level).

## The Cure (Finding 7, three parts)
- **(a)** Origin document into every semantic check: synopsis persisted
  to canon deterministically, self-loaded by check nodes. Fidelity to
  source, not just internal coherence.
- **(b)** Identity resolution is semantic → `dedup_check` in the genesis
  agent's tools, mandated before minting any entity not explicitly named
  in the synopsis.
- **(c)** Enumerate-then-create: agent's first obligation is the full
  entity checklist — named AND implied — with IDs minted once at
  global-context time. The "create it first" error demotes from design
  mechanism to safety net.

## Heuristic
When a deterministic gate guards a semantic question, ask what behavior
the gate's *error message* trains the agent into. A gate is also a
prompt. If compliance with the gate is cheaper than correctness, the
gate manufactures compliant errors.

**Seed:** Should entity-ID minting be a single-writer concern — a
`mint_entity` tool that owns ID assignment and consults dedup internally
— so that identity has one boundary instead of being re-decided inside
every `create_*` call? And: can the final gate diff canon against the
synopsis (LLM, origin-grounded) rather than only checking internal ref
closure?
