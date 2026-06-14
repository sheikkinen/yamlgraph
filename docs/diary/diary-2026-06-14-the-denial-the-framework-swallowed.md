# The denial that the framework swallowed and htmx threw away

*2026-06-14 — DM v2 LLM failure/denial UI feedback*

## What happened

The user, running the DM app with an explicit premise on Vertex/Gemini, asked me
to "check the UI feedback in case of llm failure / denial." I expected to find a
crude-but-present error card. I found that there was, in practice, *no feedback at
all* — and that the absence was assembled from two independent, individually
plausible decisions.

## The trap: feedback that exists in code but never reaches the eye

Three layers each did something locally reasonable, and their composition produced
silence:

1. **The provider** declines an explicit scene by returning an *empty* completion,
   not by raising. `clean_text(None)` → `""`. No exception to catch.
2. **The framework** (yamlgraph's node error handler) *swallowed* the cases that
   did raise — `on_error` default skipped the node and recorded the error in
   `state["errors"]`, returning empty output. So even a real `RuntimeError` reached
   the adapter as a blank string, indistinguishable from #1.
3. **The transport** (htmx 2.x) swaps only 2xx responses. The error card was
   returned as `status_code=400` — so the one place that *did* try to show the
   failure had its body dropped on the floor. The busy spinner cleared, the card
   sat unchanged, and the DM saw nothing.

Every layer had a defensible reason. The empty-on-block is the provider's contract.
The swallow-and-record is the framework's resilience policy. The 2xx-only swap is
htmx's safety default. The bug lived in *none* of them and in *all* of them — a
`composition_bug`, where each component passes its own test and the system still
fails. The only way to see it was to trace the full chain end to end: provider →
clean_text → node error handler → adapter → route status → htmx swap rule.

## The cure

Normalize at the boundary where the failure becomes legible, not where it
originates. The adapter (`weave` / `_invoke_stage`) is the seam where "empty
output" and "recorded error" both first carry meaning, so that is where I raised:
empty-with-no-error → a DM-facing "declined" message; recorded-error → its real
reason. And the transport truth — htmx swaps only 2xx — is not negotiable from the
server's intent, so the error must ride a 200 with a banner, not a semantically
"correct" 400 that the client discards. Honesty about the *channel's* contract beat
purity about HTTP status.

The witness that mattered: the provider-error test passed *before* I touched the
status code, because the framework had already swallowed the exception into empty
output — proving the 400 path was dead code I'd have "fixed" blind. The RED told me
the real shape of the failure, not the one I'd assumed.

## Heuristic

When a user reports "no feedback," do not look for the missing handler — look for
the handler whose output is silently discarded one layer downstream. Feedback is a
*pipeline* property: surface at the first legible boundary, and honor the
transport's swap contract, or the message dies in transit no matter how correct it
is at the source.

## Seed

The framework's `on_error: skip` default converts raises into empty outputs that
the application cannot distinguish from a content block. Should YAMLGraph offer the
adapter a structured "why is this empty?" signal at the graph boundary — a typed
result that carries `(output, errors, finish_reason)` together — so applications
stop reverse-engineering denials from blank strings?
