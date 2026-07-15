# Feature Request: FR-736 WebLLM Demo Trace Capture — record the stimulus

**Priority:** LOW
**Type:** Enhancement
**Status:** In Progress — GREEN landed; merged F5 witness pending a real browser session
**Effort:** 0.5 day
**Requested:** 2026-07-15
**Judged:** 2026-07-15 — scope frozen; restart ruling granted with a wire-fidelity witness attached
**Parent:** FR-731 (spike instrument); sibling of FR-735 (evidence ergonomics)
**Spawned by:** FR-731 evidence review (2026-07-15): the instrument records
outcomes, not stimuli. The flood diagnosis required reading compiler source
because the evidence never showed what was *sent*; the 10-run protocol
demands distinct inputs but evidence.md has no input column — the artifact
cannot prove its own protocol was followed
(`gate_checks_shape_not_substance`, `assert_path_not_destination` one
layer up).

## Summary

Capture the full request/response pair per run: the exact `messages` array
(system + hydrated user), `response_format` schema, generation params, and
the reply (content, usage, finish_reason). Per-run `run-NN-trace.json`
download; evidence.md gains a stimulus column so input distinctness is
verifiable from the artifact alone. **Completely standalone — no LangSmith,
no upload, no network** (explicit product decision: the demo stays
zero-key, zero-server, zero-telemetry; observability integrations are a
different product with a different premise).

## Problem

1. **Outgoing prompt invisible.** The spike's claim is about the compile
   path, yet no artifact shows the compiled prompt as actually sent
   (post-hydration, post-directive). The run-1 flood could not have been
   diagnosed from the evidence alone — the one-read `cat` that ends an
   investigation must include the request.
2. **Input distinctness unprovable.** The kill-criterion tally requires 10
   distinct inputs; the evidence records none of them. The protocol's own
   precondition is unverifiable from its artifact.
3. **Reply metadata discarded.** `finish_reason` (did the flood hit the
   token cap or stop naturally?) and the full usage object are diagnostic
   and currently dropped.

## Proposed Solution (page-only; no framework surface)

### 1. Per-run trace object

Built alongside the existing run record:

```json
{
  "run": 1, "session": "<SESSION_ID>", "model": "<MODEL_ID>",
  "params": {"temperature": 0, "max_tokens": 512},
  "request": {"messages": [...], "response_format_schema": {...}},
  "response": {"content": "...", "finish_reason": "...", "usage": {...}},
  "timing": {"ms": 1326}
}
```

- `messages` verbatim as passed to `chat.completions.create` — the
  hydrated user message included (single source: build the array once,
  pass the same identifier to the API call and the trace; the FR-735 F3
  single-identifier discipline applied to the request side).
- `Save trace` link per run: `run-NN-trace.json` (Blob, same mechanism
  as `run-NN-raw.txt`).
- Trace object logged to console in the `webllm-run` record (replaces
  nothing; extends).

### 2. Evidence.md stimulus column + request section

- Tally table gains `input_chars` and `input_head` (first ~40 chars,
  pipe-escaped) — distinctness readable from the table.
- Each per-run section embeds the hydrated user message and
  `finish_reason` alongside the existing verbatim raw; the system prompt
  (identical across runs) is printed once in the header section.

### 3. Tally-restart ruling (for the judge to pin)

Trace capture does not alter request semantics — same messages, same
params, same model. The FR-731 amendment precedent (restart on semantic
change) should NOT apply; pin explicitly so the 10-run tally can run on
the traced instrument without a second restart debate.

### Out of scope (purge list)

- **LangSmith / any trace upload / any network channel** — standalone
  demo is the product decision; even a local uploader script is purged
  until a real consumer exists.
- Request replay UI, trace diffing, streaming capture.
- Persistence (localStorage/IndexedDB) — FR-735 F2 labeling stance
  unchanged.

## Acceptance Criteria

- [ ] AC-01 RED — lexical page tests (FR-735 weight class): trace object
      keys present (`request`, `response`, `finish_reason`); `Save trace`
      download link; messages array built once and the same identifier
      passed to both the API call and the trace; `input_chars`/
      `input_head` in the tally header; system prompt printed once in
      the evidence header.
- [ ] AC-02 — evidence.md from a real session shows: stimulus column
      filled, hydrated user message per run, finish_reason per run;
      committed as an updated format witness (F5 file, regenerated).
- [ ] AC-03 — README evidence section updated (trace file described).
- [ ] AC-04 — changelog fragment (feat, examples; REQ claim stays with
      FR-731 per cross-wiring gate — note in fragment body only); diary.

## Alternatives Considered

- **LangSmith via local uploader script (key stays out of browser):**
  designed, then killed by product decision — the demo's value is its
  standalone-ness; an uploader is a second system to maintain for zero
  current consumers.
- **Embedding full traces in evidence.md:** bloats the tally artifact;
  the per-run trace.json carries the full pair, evidence.md carries the
  human-readable stimulus. Split by reader.
- **Recording only an input hash:** proves distinctness but not content;
  a 40-char head plus char count is one line and human-checkable.

## Related

- FR-731 (kill-criterion protocol consumer), FR-735 (instrument sibling)
- docs/demos/webllm/index.html, examples/webllm-demo/README.md
- tests/unit/test_fr735_webllm_evidence.py (test conventions)

## Judgement (2026-07-15)

**Verdict: APPROVED — with 5 findings.** The LangSmith purge is
correctly recorded as designed-then-killed with rationale, so it cannot
be re-proposed without new facts; the restart ruling is granted but
earns a witness obligation.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Restart ruling GRANTED, with teeth**: trace capture is semantics-neutral (same messages, params, model), so the FR-731 restart precedent does not apply — but "semantics-neutral" is a claim, and claims get witnesses | The evidence header must print the system prompt **from the same `prompt` object the request uses** (one identifier, fetched prompt.json → both the create call and the evidence renderer). Artifact-to-wire fidelity becomes readable: the header's system prompt IS what was sent, byte-for-byte, including the JSON directive. A tally run on the traced instrument then self-proves it ran the amended artifact |
| F2 | `input_head` in a markdown table breaks on `\|` **and newlines** — the FR says pipe-escaped only | Escape both: pipes → `/`, newlines → `⏎` (or space). Pin follows the `_esc` precedent in mermaid_export. One lexical test |
| F3 | "Same identifier to API call and trace" needs a mechanical form | Pin: `const messages = […]` built once; the create call uses the `messages,` shorthand; the trace object references the same `messages` identifier. Lexical tests: exactly one `role: "system"` literal in the script (array built once), shorthand present |
| F4 | `finish_reason` is the flood-vs-natural-stop discriminator and must appear in BOTH surfaces | In the tally table as a column (not just the per-run section) — a `length` row in a 10-run table is the one-glance signal the kill-criterion review needs. Table becomes: `\| run \| schema_valid \| score \| finish \| ms \| tok/s \| input_chars \| input_head \| raw_chars \|` |
| F5 | FR-735's F5 format witness is still open (needed ≥2 real runs); AC-02 here demands another real-session witness — two obligations, one browser session | **Merged**: one real ≥2-run session on the traced instrument produces `format-witness-evidence.md` satisfying FR-735 F5 and FR-736 AC-02 simultaneously. The file carries the "format witness, not spike evidence" header per FR-735 F5 |

**Scope frozen.** Purge list stands — LangSmith stays dead until a real
consumer exists; no persistence; no replay UI. Enforce order: AC-01 RED
(lexical tests in test_fr735_webllm_evidence.py or sibling) → page GREEN
→ merged real-session witness (closes FR-735 F5 too) → README →
paperwork. Then the FR-731 10-run tally runs on the traced instrument —
no further instrument FRs before the tally; the instrument is done
improving until the protocol it serves has actually run.

## Implementation (2026-07-15)

RED 103d05f3 (9 condemning across a sibling module + the FR-735 header
test updated in place per F4); GREEN this commit.

- `messages` built once (F3): create call uses shorthand, trace
  references the same identifier; one `role: "system"` literal in the
  script.
- Trace object per run: `{run, session, model, params, request:
  {messages, response_format_schema}, response: {content,
  finish_reason, usage}, timing}` — `Save trace` → `run-NN-trace.json`;
  also carried in the `webllm-run` console record.
- Evidence.md: `## system prompt (as sent)` header printed from the
  same `prompt` object the request uses (F1 wire fidelity); tally
  header now `finish | … | input_chars | input_head`; per-run sections
  embed the hydrated user message and finish_reason; `escCell` handles
  pipes and newlines (F2).
- One test-side alignment during GREEN: the trace-keys probe looked for
  JSON-quoted keys; JS object literals are unquoted — probe reworded to
  `request: {`/`response: {`, same substance.

**Open:** merged F5 witness (≥2-run real session on the traced
instrument → `format-witness-evidence.md`), then the FR-731 tally.
