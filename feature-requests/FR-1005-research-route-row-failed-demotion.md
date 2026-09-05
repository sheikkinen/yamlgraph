# Feature Request: Research route demotes a failed persona to a recorded row instead of killing the run

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** the next operator whose `scripts/research.sh` run loses one persona to a cell-shape failure, at the moment the wrapper would today print `contract violated … missing or empty` and discard the four findings that succeeded. Concretely: the FR-1005 author, re-running `feature-requests/research-briefs/pi-agent-runtime-brief.md`, which killed three consecutive runs on 2026-09-05 (AC-11 is that re-run). Second consumer: the judge reading a promoted research record, who today cannot tell a five-persona run from a four-persona one because the four-persona one never exists.
**Research:** in-body. The sole route is the instrument under repair, and it failed three times on the brief that motivates this FR; those three runs, read raw in [evidence/FR-1005-research-route-run-failures.md](evidence/FR-1005-research-route-run-failures.md), are the research record, and the *Alternatives Considered* table below is the dispositioned design space with dissent preserved (FR-1004 and FR-959 precedent for the in-body route). `is_this_a_graph`: **no new LLM decision** is introduced and **no governed graph artifact changes** (`graph.yaml` and `prompts/*.yaml` of the route are untouched, AC-13); the change is in the LLM-free gather and reduce code and the artifact verifier.
**Prior art:** [FR-890](FR-890-research-sole-route-closed-input-alternatives.md) created the route and `gather_findings` with its all-five-keys raise; this FR keeps five personas running (FR-890 AC-03) and changes what happens when one of them returns nothing usable. [FR-896](FR-896-research-route-precedent-traceability.md) §4 set `max_length=400` with "the reducer rejects (not truncates) violations so the model contract, not post-processing, carries the constraint" (AC-07); this FR **preserves reject-never-truncate** at the row level and observes that the premise did not hold: the cap is checked after generation by Pydantic (`yamlgraph/schema_loader.py` passes `constraints` into `Field`), nothing upstream shortens the text, and FR-896's own implementation record lists three live runs that overflowed. FR-896's `on_error: retry` mechanization is inherited unchanged and recorded here as ritual for a temperature-0 call (runs 2 and 3 failed byte-identically); changing it is graph authoring and is out of scope. [FR-926](FR-926-research-failure-cites-recorded-cause.md) witnessed this exact class on 2026-08-30 (`rationale … string_too_long`, three runs), fixed the diagnostics, froze "no partial artifact" **for its own scope**, and deferred "retry-with-error-feedback … until recurrence (`graduation` rule)"; this FR is that recurrence, keeps FR-926's cause text and moves it into the artifact, and re-homes FR-926's witnesses rather than deleting them (AC-10). [FR-938](FR-938-prior-art-retrieval-in-research-route.md): fabricated precedent fails the whole run and **stays fatal** here, because a fabricated citation is adversarial-shaped and an over-length cell is not (its judgement's "counting the miss against the floor would make a fabricated citation the cheaper option" is honoured by leaving that path untouched). [FR-990](FR-990-cap-journey-census.md) and [FR-962](FR-962-person-profile-census-authored-prs.md): the `row_failed` and enum-leak-demotion reducer precedents this FR copies (`demote-never-drop`). No REJECTED FR governs research-route reducer semantics (`ls feature-requests | grep -i REJECTED` → one unrelated file).

## Summary

`examples/demos/research-route` fans a brief out to five personas and
reduces their findings into one table. Today one malformed cell from one
persona discards the whole run: an enum field carrying prose kills it in
the reducer (run 1), an over-length field kills it in the persona node and
then in `gather_findings` (runs 2 and 3). The artifact contract only needs
four rows, three of them grounded, and a librarian row. Make the failure
of one persona a **recorded row failure** in the artifact header, with the
cause FR-926 already formats, and keep the run fail-closed at the floor the
verifier already enforces.

## Value Statement

An operator who pays five persona calls gets four findings and one named
failure instead of nothing, three times in a row; a judge who reads the
promoted record sees exactly which persona did not speak and why.

## Problem

### Witnessed 2026-09-05 (evidence file, raw)

| Run | Where it died | Cell | What was lost |
|---|---|---|---|
| 1 | `reduce_findings` → `PersonaFinding._closed_class` | `solution_class` = `process-boundary. The four per-vendor concerns …` (valid enum head, rationale tail) | 5 findings incl. the one with a valid head |
| 2 | `yamlgraph_native_planner` structured-output parse, retried identically, then `gather_findings` | `candidate` 471 chars > 400 | 4 valid findings |
| 3 | same as run 2, byte-identical | same | 4 valid findings |

Prior witness: FR-926, 2026-08-30, three runs, `rationale` over-length,
same persona, "retried and re-failed identically".

### Why one cell kills the run

1. `gather_findings` raises when any of the five persona keys is absent
   (`research_tools.py`), although the artifact verifier accepts four rows.
2. `_validate_findings` wraps any `ValidationError` on any row into a
   run-level `ValueError`, although the reducer's own module docstring
   promises findings are "demoted (never dropped)".
3. The persona node's `max_length=400` is a post-generation Pydantic check;
   the retry re-sends the identical temperature-0 request. Six recorded
   failures (FR-926 ×3, this FR ×3) are all this shape. That retry is not
   changed here (graph authoring), only named.

## Ideal Result

A research run that loses one persona to a cell-shape defect still writes
`tmp/draft-alternatives.md` with the other four rows, a `personas failed:`
header line naming the persona, its state key and the recorded cause, and
is stamped in `research-runs.jsonl`. A run that loses two personas, or the
librarian, or any row to a fabricated citation, still fails closed with
every cause in one message. An enum cell whose head is exactly an enum
value and whose tail is prose is accepted on its head, and the split is
recorded in the artifact header. Nothing is ever truncated.

## Proposed Solution

All changes in `examples/demos/research-route/nodes/research_tools.py`,
`scripts/research_preflight.py`, and tests. No graph or prompt edits.

### S-1: `gather_findings` records instead of raising

For each `PERSONA_KEYS` entry absent from state, append a marker
`{"row_failed": "<state key>", "cause": "<text>"}` to `findings` instead of
raising. `<text>` is the FR-926 formatter output filtered to the recorded
error(s) whose `node` shares the key's prefix (`yamlgraph_native_` matches
`yamlgraph_native_planner`; `librarian_` matches `librarian_structure` and
`librarian_research`), or `no recorded cause` when the channel holds none.
The all-five success path is byte-for-byte unchanged (FR-926 AC-04). The
markers travel inside the existing `findings: list` state key, so the
graph's typed state does not change.

### S-2: `reduce_findings` demotes invalid rows and normalises enum heads

- Markers from S-1 are separated from candidate rows.
- Before validation, `solution_class` and `verdict` cells not in their
  enum are split at the first of `.`, `:`, `;`, `(`, newline, or ` — `; if
  and only if the head is an exact enum value, the head is used and a
  note `<persona>: <field> head-split, tail dropped: "<tail, first 80
  chars>"` is recorded. Free text with no enum head is not repaired.
- A row that fails `PersonaFinding` validation becomes a row failure with
  cause `<persona or "finding N">: <first validation line>`. Over-length
  cells are therefore rejected as rows, never truncated (FR-896 AC-07
  holds at row level).
- Precedent validation (FR-938) and librarian URL reconciliation keep
  their fatal behaviour unchanged.
- Floor, fail-closed, in the reducer where the causes are known: fewer
  than **4** valid rows (the verifier's existing minimum) or no librarian
  row → `ValueError` listing every failed persona with its cause and every
  note. The existing "fewer than 3 grounded findings" check stays.
- Header gains `- personas failed: <key>: <cause>; …` when any failed and
  `- reducer notes: …` when any head-split happened; `personas executed:`
  lists only the rows written. Return dict gains `failed` and `notes`.

### S-3: `verify_artifact` checks the substance of a short run

If the table has fewer than `PERSONA_COUNT` (5) rows, the artifact must
carry a `- personas failed:` line whose entries each have the `key: cause`
shape; a four-row artifact with no such line is a violation
(`substance_over_presence`). `PERSONA_COUNT` mirrors `len(PERSONA_KEYS)`
and a test witnesses the mirror, like the existing enum mirrors.

### S-4: tests (RED first with `SKIP=pytest`, then GREEN)

New `tests/unit/test_fr1005_research_row_failed.py` tagged
`REQ-YG-665`; FR-926's `test_fr926_recorded_cause_witness.py` re-homed:
the cause text is asserted in the S-1 marker and the artifact header
instead of a `gather_findings` raise; its wrapper-propagation witness
(AC-05 there) is unchanged.

### S-5: traceability and record

`capabilities/CAP-248-research-sole-route.yaml` gains `REQ-YG-665` and
`FR-1005` in `fr:`; `changelog/unreleased/fr-1005-…md`; implementation
record in this FR; diary reflection.

## Acceptance Criteria

- [ ] AC-01: `gather_findings` with one `PERSONA_KEYS` entry missing and a `PipelineError` for that node in `state["errors"]` returns `findings` holding the four present findings plus one `row_failed` marker whose `cause` contains the node, category, exception type and message (FR-926's fields); it does not raise.
- [ ] AC-02: The same call with an absent or empty error channel yields a marker with cause `no recorded cause`; recorded errors for *other* nodes are not attributed to the missing persona.
- [ ] AC-03: With all five keys present, `gather_findings` returns `{"findings": [...]}` with the five normalised findings in `PERSONA_KEYS` order, unchanged (FR-926 AC-04).
- [ ] AC-04: `reduce_findings` given four valid findings and one S-1 marker writes an artifact with four table rows, a `- personas failed:` line naming the key and the cause, `personas executed:` naming only the four, returns `failed == 1`, and `research_preflight.verify_artifact` accepts it.
- [ ] AC-05: A finding whose `candidate` is 471 characters becomes a row failure whose cause names the field and `string_too_long`; the artifact contains no truncated text from that finding; `rows == 4` when the other four are valid.
- [ ] AC-06: `solution_class` = `process-boundary. The four …` is accepted as `process-boundary` with a `- reducer notes:` line recording the split and the tail's first 80 characters; `solution_class` = `The four per-vendor concerns …` (no enum head) is a row failure; the same rule holds for `verdict`.
- [ ] AC-07: Two row failures among five findings, or a failed librarian, raise `ValueError` whose message names every failed persona key and its cause; no artifact is written.
- [ ] AC-08: Existing FR-938 fabricated-precedent tests and FR-896 librarian fail-closed tests pass unchanged; a fabricated `CAP-628` still fails the run.
- [ ] AC-09: `verify_artifact` rejects a four-row artifact without a `personas failed:` line and accepts one whose line has `key: cause` entries; a test asserts `research_preflight.PERSONA_COUNT == len(research_tools.PERSONA_KEYS)`.
- [ ] AC-10: Every FR-926 witness has a replacement asserting the same information in its new location; none is deleted without one; `test_wrapper_surfaces_enriched_failure_text` is unchanged.
- [ ] AC-11: Live witness: `scripts/research.sh feature-requests/research-briefs/pi-agent-runtime-brief.md` on the fixed code completes with a verified artifact (four or five rows), stamps `research-runs.jsonl`, and the promoted table is appended to `docs/2026-09-05-research-pi-agent-runtime.md` §9 with the `personas failed:` line quoted if present.
- [ ] AC-12: `CAP-248` carries `REQ-YG-665`; `req_coverage.py --strict` passes; changelog fragment; implementation record; diary reflection.
- [ ] AC-13: `git diff main -- examples/demos/research-route/graph.yaml examples/demos/research-route/prompts` is empty: no governed artifact changed, no authoring route needed.

## Alternatives Considered (with dissent preserved)

| Alternative | Disposition | Dissent (strongest case against the disposition) |
|---|---|---|
| Truncate over-length cells at 400 and keep the row | REJECTED — FR-896 AC-07 stands; a truncated candidate is a claim the persona never made | The first 400 characters of a real idea beat an empty row; the reader can see the ellipsis. |
| Raise or remove the 400 cap in the prompt schemas | REJECTED — governed artifact (authoring route); the cap keeps the table readable; every observed overflow was 430–480 chars, so a higher cap moves the cliff, not the behaviour | Six failures in two months on one persona is a design signal that 400 is too tight for `candidate` specifically. |
| Retry with error feedback: the persona sees the validation error and shortens | DEFERRED to its own FR — a framework `llm` node feature, second witness now recorded (FR-926 first); `graduation` rule fires | It is the only option that *recovers* the fifth row instead of recording its loss; this FR makes the loss visible, not smaller. |
| Remove `on_error: retry` on persona nodes (temperature-0 retry is ritual) | OUT OF SCOPE — graph authoring; recorded as a finding for the deferred FR above | Two identical calls per failure double the cost of every failed run for nothing. |
| Keep the hard failure, print every cause (FR-926, status quo) | REJECTED as insufficient — done; three runs today still lost four good findings each | A run that cannot field five personas is arguably not the run the judge asked for (FR-890 AC-03). Answer: five still *run*; the artifact says which did not *land*. |
| LangGraph `error_handler` node rewiring | REJECTED — FR-926 librarian row; topology change for information already in state | Structurally the "right" LangGraph answer. |
| Demote any invalid row, including fabricated precedent, to `row_failed` | REJECTED — FR-938 made fabrication fatal on purpose; adversarial-shaped failures must not become the cheaper option | One rule for all cells is simpler to explain than two. |
| **Chosen**: row failure recorded in the artifact header at gather and reduce; enum head-split with note; floor of 4 rows plus librarian kept fail-closed; verifier requires the failure line on short runs | PURSUE | — |

## Related

- Evidence: [evidence/FR-1005-research-route-run-failures.md](evidence/FR-1005-research-route-run-failures.md)
- The brief that killed three runs: [research-briefs/pi-agent-runtime-brief.md](research-briefs/pi-agent-runtime-brief.md); its research document [docs/2026-09-05-research-pi-agent-runtime.md](../docs/2026-09-05-research-pi-agent-runtime.md) §9 records the runs and receives the AC-11 witness.
- Scripture: `two_strike_split`, `junk_drawer_cap` (enum leak → cap in code), `substance_over_presence`, `read_raw_output_first`.
