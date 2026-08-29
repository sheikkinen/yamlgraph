# 2026-08-29 — The Partial Read of an Event Log Is a Plausible Wrong Answer

## What happened

A session that began as "plan a pair of hooks" ended having: discovered a
live `.env` leak (implicit context attached the focused editor file — API
keys sent to the model in three requests), closed the vector with one
settings key, authored FR-898 and FR-899, and prototyped
`scripts/vscode/session_report.py`. The forensic instrument and the
incident it found were the same file: the session store documented its own
leak (`generatedTitle: "Attached .env on three occasions during prompts"`).

## The trap, enacted three times in one hour

The chatSessions store is an event-sourced patch log (kind 0 snapshot,
kind 1 set-at-path, kind 2 array-insert). I read it three ways:

1. **grep** — found nothing (escaped quotes); concluded "no attachments."
2. **recursive scan of raw records** — found a plausible ledger: 18
   requests, 560 credits, some "(no titles)" rows. Shipped it as a report.
3. **full replay** — 22 requests, **1800 credits**, every title present.

The scan's output was `plausible_wrong_answer` in its purest form: correct
shape, correct field names, internally consistent, off by 3.2x. Nothing in
the output signaled the error. What exposed it was the operator's
three-word question — "was 1 fixable" — which forced me to distinguish
*missing data* from *my shortcut*. The data was never missing.

## The insight: the_one_law has a read side

The Scripture says normalize at the boundary where external data enters.
I had internalized that as a write-side rule. But an event-sourced store
makes *reading* a boundary operation: the only faithful read is a replay
of the writes. Grepping an event log is normalizing downstream — you get
whichever intermediate state your regex happens to land on. `copilotCredits`
is patched repeatedly during a turn; a non-replay read samples a random
draft of the truth.

Corollary for FR-898: replay is not an implementation detail, it is the
correctness boundary. An AC now must assert totals against a hand-verified
session, or the ledger will be confidently wrong forever.

## Second insight: the platform already did this

`does_the_platform_already_do_this` fired twice, late both times:

- FR-898's planned LLM intent classification: `generatedTitle` already
  narrates every turn, pre-computed, free. The classification map-node
  demotes from core AC to optional refinement.
- The hooks originally proposed for prompt capture: the store already
  captures prompts verbatim, with model, credits, timestamps, and even
  implicit-attachment provenance (`vscode.implicit.selection` — which is
  how the .env leak was provable request-by-request, months later).

The session's opening proposal (build capture hooks) was largely a request
to build what the vendor already persists. The reporting-first pivot
(request #4, "consider hook vs reporting based on existing logs") was the
operator applying the question before I did.

## Third insight: self-referential probes are cheap and decisive

The operator switched models on the *exact request* that asked "how is
model change reflected" — turning the question into its own test fixture.
One switch produced: `requests[].modelId` (historical truth, per request),
`inputState.selectedModel` (current selection only, with pricing/effort/
context config), and the negative result that `modelState` is lifecycle,
not identity. No archaeology across old sessions needed; the probe
manufactured its own witness. Same pattern as the setting verification:
"is the setting active" was answerable from within the very request that
asked it (the request arrived without the attachment).

## Traps confirmed

- `plausible_wrong_answer` — the 560-credit ledger. Assertion beyond shape:
  replay totals vs. known session.
- `downstream_fix` (read-side variant) — grep/scan of an event log instead
  of replay at the boundary.
- `does_the_platform_already_do_this` — twice; the store is richer than the
  instrumentation we planned to add.

## Heuristic extracted

**Event-sourced stores have no random access.** If the artifact is a patch
log, the ONLY reads are (a) full replay or (b) provably replay-equivalent.
Any direct scan must be treated as sampling a draft — usable for schema
discovery, never for totals or final values. Second witness will graduate
this; first witness is today's 3.2x.

**Seed:** The store self-documented its own incident — the leak was
queryable *from the artifact that leaked*. What else in the workspace is a
self-witnessing record we treat as write-only? (Candidates: hooks
audit.jsonl, LangSmith runs, git reflog.) Could FR-898's monthly report
include a standing "anomaly section" — implicit attachments of dotfiles,
cancelled-turn clusters, cost outliers — turning the ledger from
accounting into an incident detector?
