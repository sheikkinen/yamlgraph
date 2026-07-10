# The Error Message Is Also an Artifact (FR-705)

**Date:** 2026-07-10
**Context:** FR-705 enforce — race timeout errors now enumerate every candidate by name; spawned by the NC-361 production incident in ninchat_voice.

## What happened

A production race timeout reported `All 1 race candidates failed: - ?/?:
race timed out` while two named providers were pending. Investigators had to
leave the error message and excavate LangSmith child runs to learn the one
fact that separates local starvation from provider failure: *which*
candidates were still pending. The context existed at the raise site —
`tasks` mapped every pending task to its candidate dict, `errors` held the
real failures — and was discarded twice: once by raising a bare
`TimeoutError`, once by the sync wrapper synthesizing `[({}, exc)]`.

## The trap, and its two echoes

`read_raw_output_first` teaches that the artifact answers what the metric
cannot. This incident is the inverse lesson: **the error message is itself
an artifact**, and one that miscounts its own evidence (`All 1` for a fleet
of 2) is a `plausible_wrong_answer` at the exact moment trust matters most —
mid-incident. Two findings at Judgement sharpened the fix:

- **F2**: the naive fix would have silently traded one fidelity bug for
  another — rerouting skip handling loses the `TIMEOUT_ERROR`
  classification an existing test asserts. The "no behavior change" claim
  in the proposal was false and only reading the existing contracts
  revealed it.
- **F3** (`partial_remediation`): the identical synthetic wrap sat in
  `router_race_node.py`; fixing only the cited site would have let the
  router path re-anonymize the now-enumerated error back to `?/?`.

## Heuristic

When raising across an abstraction boundary, raise **where the context
lives**, not where the failure is noticed. Every `except X: raise Y(...)`
re-wrap is a context funnel — audit what it discards. A grep for
`raise .*\(\[.*\{\}` (synthetic empty payloads) is a cheap smell detector
for forensic-fidelity holes.

**Seed:** NC-361-class incidents are found by reading error text against
the evidence it summarizes. Could the inquisitor audit error-construction
sites mechanically — flag any exception constructor receiving a literal
empty dict/list as payload, the way W026 flags fused prompt fields?
