# Diary — 2026-08-06 — The Provider Was Innocent

**Context:** FR-777 enforcement — shared shell toolbelt manifests for the
planner/enforcer/judge demos. RED committed cleanly; GREEN blocked for an
hour on regenerating live-agent demo witnesses.

## The trap sequence

Three "provider timeouts" in a row: deepseek twice, anthropic once. The
frame hardened immediately — *providers can't handle the planner's
context* — and I spent the next attempts rotating providers instead of
reading the evidence. The google run then "failed" with a
`JSONDecodeError` and a broken pipe, and only reading the full log
end-to-end (`read_raw_output_first`, again) exposed that the agent had
**completed all 15 iterations successfully**. The failure was mine: a
heredoc piped program text into the same stdin the JSON was supposed to
arrive on, so the extractor read empty input and yamlgraph got EPIPE.

Two distinct defects, one symptom bucket. The deepseek/anthropic timeouts
were real (ARCHITECTURE.md grew ~263KB since the 2026-05-29 witness and
the planner prompt mandates reading it in full); the google failure was a
wrapper bug wearing the same "❌ Error" costume. `composition_bug` in
miniature: every component was fine, the shell plumbing connecting them
was the defect — and the shared symptom string laundered a plumbing bug
into a provider indictment.

## Second trap: `.env` defeats env defaults

The demo scripts `source .env` *after* the caller's environment, so
`PROVIDER=x ./demo.sh` silently loses to the pinned `PROVIDER=deepseek`.
The cure was a wrapper that never sources `.env` — but that wrapper is
where the heredoc bug lived. Normalizing at the boundary and then
introducing a new defect *at the normalization layer* is a known shape:
`infrastructure_self_exempt` — the guard/wrapper gets less scrutiny than
what it guards.

## Heuristic

When N runs fail with the same user-facing error string, do not assume N
instances of one defect. Diff the *full* logs pairwise before rotating
variables: the google log showed 15 completed tool calls where the
anthropic log showed client retries — structurally different failures
that the tail-line similarity concealed.

## Standing observation (seed candidate, second occurrence)

Live-agent demo runs as merge witnesses are expensive and flaky: minutes
per run, provider-sensitive, context-growth-sensitive. The planner witness
rotted silently as ARCHITECTURE.md grew — nothing re-runs committed demos,
so the witness only fails when someone next touches the demo.

**Seed:** should agent-graph demos carry a *deterministic* witness tier
(recorded tool-call transcripts replayed against the graph's tool wiring)
alongside the live log, so the wiring is testable in CI without an LLM —
and witness rot is detected when it happens, not when it's inherited?
