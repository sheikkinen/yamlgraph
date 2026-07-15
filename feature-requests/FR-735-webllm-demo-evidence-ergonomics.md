# Feature Request: FR-735 WebLLM Demo Evidence Ergonomics — console + save links

**Priority:** LOW
**Type:** Enhancement
**Status:** In Progress — GREEN landed; F5 format witness pending a real browser session
**Effort:** 0.5 day
**Requested:** 2026-07-15
**Judged:** 2026-07-15 — scope frozen; session-mortality gap closed by protocol wording, not storage
**Parent:** FR-731 (the page under change; AC-04 is the consumer)
**Spawned by:** FR-731 run 1 (2026-07-15) — the whitespace-flood failure
exposed that the page is a good *demo* but a bad *instrument*: the raw
output (≈4 KB of grammar-legal whitespace) had to be rescued by manual
text selection, the console carried zero diagnostics, and the 10-run
tally F1 demands is hand-transcribed line by line.

## Summary

Make the demo page self-evidencing for the AC-04 protocol: structured
console records per run, per-run **Save raw output** download links, and
a session-accumulated **Download evidence.md** whose format *is* the
FR-731 F1 tally (one line per run + verbatim raws). The human runs 10
inputs and saves one file; transcription error disappears as a class.

## Problem

1. **Console is empty.** Engine load progress, load time, tokens/s
   (`reply.usage` is available and discarded), run timing, raw output,
   and schema verdict are all computed or computable but never logged.
   Debugging run 1 meant reading a DOM `<pre>` full of whitespace.
2. **No way to save files.** F1 requires verbatim raw outputs; verbatim
   means bytes, and copy-from-DOM mangles whitespace-degenerate outputs
   (the run-1 flood is *exactly* the case where fidelity matters most).
3. **Tally is manual.** 10 runs × (input id, schema-valid, score, time)
   hand-copied into spike-evidence.md — transcription at the boundary
   where the kill criterion is evaluated. `substance_over_presence`
   argues the tool should emit the evidence in its required shape.

## Proposed Solution (page + build only; no framework surface)

### 1. Console diagnostics (`console.log`, structured)

- On load: model id, cache hit/miss (from progress text), total load ms.
- Per run: one object
  `{run, ms, tokens_per_s, schema_valid, error, raw_chars, raw}` —
  `tokens_per_s` from `reply.usage`; `raw` verbatim (console clipping is
  the browser's concern; the download link is the fidelity channel).
- On schema failure: the parse error and failure position alongside the
  record, not instead of it.

### 2. Per-run save link

- After every completion: `Save raw output` anchor —
  `Blob` + `URL.createObjectURL`, `download="run-NN-raw.txt"`, bytes
  identical to `message.content`. No network, no storage beyond the
  in-memory session (FR-731 purge list intact: still no telemetry).

### 3. Session evidence bundle

- Every run appends to an in-memory array; a `Download evidence.md`
  link renders it as: header (model id, browser UA, GPU if
  `navigator.gpu` adapter info is available, load time), the **tally
  table** — `| run | schema_valid | score | ms | tok/s | raw_chars |`
  one line per run (F1 shape) — then each run's verbatim raw in a fenced
  block. Kill-criterion arithmetic (`failures: N/M`, M = session run
  count, with a "protocol requires 10" note when M < 10) printed under
  the table, computed, not asserted.
- Raw display in the DOM additionally shows `raw_chars` count and parse
  failure position (run-1 lesson: a whitespace flood *looks* empty;
  the count says otherwise).

### Out of scope (purge list)

- Any network transmission, localStorage/IndexedDB persistence,
  analytics — the FR-731 purge list stays binding.
- Model picker, streaming, retry/penalty knobs — protocol changes are
  a re-judgement of FR-731, not ergonomics.
- Automating the 10 runs (input corpus, auto-runner): the protocol is
  deliberately manual-distinct-inputs; automation would be a new
  judged protocol.

## Acceptance Criteria

- [ ] AC-01 RED — lexical page tests (same weight class as FR-731 F4):
      `console.log` of a per-run record present; `URL.createObjectURL`
      + `download=` attributes present; evidence renderer emits the
      tally-table header and `failures:` line.
- [ ] AC-02 — per-run save link produces bytes identical to
      `message.content` (witnessed by construction: single variable
      flows to both Blob and DOM; test asserts no reformatting call
      between).
- [ ] AC-03 — evidence.md format matches FR-731 F1: one tally line per
      run, the verbatim raws, kill-criterion arithmetic computed.
      A saved sample from a real 2-run session committed as the format
      witness (not the AC-04 evidence itself).
- [ ] AC-04 — FR-731's spike-evidence.md protocol section updated to
      say "save evidence.md from the page" instead of hand-transcribe;
      README run instructions updated.
- [ ] AC-05 — changelog fragment (feat, examples); tests under
      REQ-YG-562 (same instrument, same requirement) or new REQ if the
      judge rules the evidence path a separate concern; diary.

## Alternatives Considered

- **Copy-to-clipboard buttons instead of downloads:** clipboard loses
  the byte-fidelity guarantee for pathological outputs and cannot carry
  the whole bundle; rejected.
- **Auto-download after each run:** browsers throttle/inspect repeated
  programmatic downloads; explicit links are calmer and sufficient.
- **Send evidence to a collector endpoint:** violates the zero-server,
  zero-telemetry premise of the whole ladder; rejected.

## Related

- FR-731 (parent; AC-04 protocol is the consumer)
- docs/demos/webllm/index.html, examples/webllm-demo/README.md
- tests/unit/test_fr731_webllm_build.py (page-test conventions)

## Judgement (2026-07-15)

**Verdict: APPROVED — with 6 findings.** The proposal is honest about
its weight class (lexical tests, page-only); the findings close its
three soft spots: an unverified API claim, a session-mortality gap the
purge list itself creates, and an unenforceable AC.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | `reply.usage` tokens/s is asserted, not verified — WebLLM exposes usage on non-streaming completions but the `extra.decode_tokens_per_s` field varies by version | Defensive pin: prefer `usage.extra.decode_tokens_per_s` when present; else compute `completion_tokens / elapsed_s`; else leave the column blank. **Never fabricate** — a blank cell is honest, a computed proxy is labeled (`tok/s*`) |
| F2 | **Session mortality**: the in-memory run array dies on reload, and the purge list (correctly) forbids localStorage — a mid-protocol crash or accidental reload silently forks the tally | Evidence.md is **per-session** by design: header carries a session id (load timestamp); multi-session tallies are concatenated by hand; the `failures: N/M` line makes short sessions visible instead of deniable. No storage added — the cure is honest labeling, not persistence |
| F3 | AC-02's "test asserts no reformatting call between" is not mechanically checkable as worded | Pin: the page reads `.message.content` **exactly once**, into one identifier; both the Blob constructor and the DOM sink reference that identifier. Lexical test: one occurrence of `.message.content`, and `new Blob([` receives the same identifier. Crude, same weight class as FR-731 F4, sufficient |
| F4 | AC-05's REQ question (562 vs new) left to the judge | **REQ-YG-562 stands** — the requirement's subject is the spike instrument; amend its description in CAP-04 to name the evidence channel and regenerate ARCHITECTURE.md. No new REQ for example-local ergonomics; registry precision over registry growth |
| F5 | Format-witness path and identity unpinned — risks being mistaken for (or polluting) the AC-04 evidence | Pinned: `docs/demos/webllm/format-witness-evidence.md`, header line stating "format witness, not spike evidence", ≥2 real runs from one session. The FR-731 AC-04 artifact remains `spike-evidence.md`, distinct file |
| F6 | GPU info via `adapter.info` requires an async adapter request and is absent on some builds | Best-effort: populate when `navigator.gpu.requestAdapter()` resolves and `adapter.info` exists; omit the field otherwise; must never block or delay the consent flow. UA always recorded |

**Scope frozen.** Purge list stands (no storage, no telemetry, no
protocol knobs, no auto-runner). Enforce order: AC-01 RED (lexical
tests extended in test_fr731_webllm_build.py or a sibling module) →
page GREEN → real 2-run session for the F5 witness → AC-04 protocol
doc updates → AC-05 paperwork. FR-731's AC-04 tally should run
**after** this lands — runs 2–10 get the instrument they deserve.

## Implementation (2026-07-15)

RED 8537f824 (15 lexical tests, sibling module
tests/unit/test_fr735_webllm_evidence.py); GREEN this commit.

- Console: `webllm-load` (model, session, load_ms, gpu, ua) and
  `webllm-run` (full record incl. verbatim raw) structured logs.
- Save links: per-run `run-NN-raw.txt` Blob from the single `raw`
  identifier (F3 — one enforcement wrinkle: a *comment* mentioning
  the property name tripped the lexical counter; reworded, which is
  the guard working as designed); session `evidence.md` with header
  (SESSION_ID, model, UA, GPU, load_ms, temperature), F1 tally table,
  `failures: N/M` + "protocol requires 10" note when M<10, fenced
  verbatim raws with error annotations.
- F1 tok/s chain implemented: `usage.extra.decode_tokens_per_s` →
  computed proxy labeled `tok/s*` → blank.
- F6: `requestAdapter().then(...).catch(() => {})` — fire-and-forget,
  consent flow untouched. `raw-meta` char count beside the raw block.
- `renderParsed` now returns a verdict object consumed by the run
  record; DOM rendering behavior unchanged.

**Open:** F5 format witness (`format-witness-evidence.md` from a real
2-run session) — requires a browser with the cached model; then AC-03
closes.
