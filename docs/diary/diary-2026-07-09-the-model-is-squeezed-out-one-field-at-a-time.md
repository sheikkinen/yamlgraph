# The Model Is Squeezed Out One Field at a Time (FR-703)

**Date:** 2026-07-09
**Context:** FR-703 enforce — status join moved from model to post-pass; third FR in the recap demo's 48-hour mechanization arc.

## The arc, compressed

FR-700 shipped a one-judgement prompt. Every field run since has removed a
piece of that judgement:

- FR-702/R2: orphan *detection* → regex pre-pass (model false-positived on
  mid-subject refs).
- FR-703: status *join* → arithmetic post-pass (model silently dropped joins
  at ~50 input lines; its fallback tag read as verified absence).
- Today's raw-output read of the *fixed* pipeline found the next one: the
  model corrupted an orphan hash in transit (`703b72e` for `703b72d`) — a
  one-character error in a "copy verbatim" step. Copying is the most
  mechanizable operation there is, and code already holds the list.

The pattern: each defect lived in the least-judgement-like part of the
model's job. Grouping (real judgement) has been correct in every field run.
What failed was always transport — detect, join, copy — work a for-loop does
perfectly. The prompt-contract memory predicted this from the start:
validator-uncovered, mechanizable levels break first.

## The trap named

Shipping a prompt whose output schema mixes judgement fields with transport
fields is deferred debugging: transport WILL corrupt at some input size, and
each corruption costs a field run + FR + fix cycle to find. The W026 linter
counts fields; it cannot yet see that `orphans` is transport wearing a
judgement's schema slot.

## Heuristic

At prompt-authoring time, label every output field **judgement** or
**transport**. Transport fields (copies, joins, lookups, counts of given
input) are pipeline bugs by construction — move them to code before the
first run, not after the field failure. The recap schema should have been 2
fields on day one; it took three FRs to discover that empirically.

**Seed:** FR-704 — orphans bypass the model entirely (`unreferenced` is
already in state; post-pass merges fragment-less graph/prompt changes),
schema drops to workstreams + hotspots. More generally: should W026 gain a
transport-field detector — flag any schema field whose description contains
"copy", "verbatim", "from the input"?
