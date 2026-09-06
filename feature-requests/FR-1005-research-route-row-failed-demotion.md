# Feature Request: Research route demotes a failed persona to a recorded row instead of killing the run

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced 2026-09-06 — judged 2026-09-05 APPROVED WITH REVISIONS ([judgement](FR-1005-research-route-row-failed-demotion.judgement.md), Copilot route on `982ad57e`), R-1…R-5 folded; RED `91f1e214` → GREEN `d53cae3f` + `4bc34a82` (loader seam found by the live witness); AC-13 live run verified and stamped 2026-09-05T21:19:01Z. [Implementation record](#implementation-record-2026-09-06)
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

A research run whose one non-librarian persona fails on a defect the
model owns (a cell over 400 characters, an enum value outside the closed
set, an empty required cell) still writes `tmp/draft-alternatives.md` with
the other four rows and two machine-readable header lines: the persona
keys that landed, and the one that did not with the cause FR-926 already
records. The run is stamped in `research-runs.jsonl`. A run that loses two
personas, the librarian, a persona for a cause that is not attributable to
a model-output defect (auth, provider, tool, graph wiring, no recorded
error, two candidate errors), or any row to a fabricated citation, still
fails closed before any artifact is written, naming every accumulated
failure and the fatal cause. No model-authored cell is ever truncated,
head-split, or repaired.

## Proposed Solution

Delivery surface (R-5): this FR amendment; `examples/demos/research-route/nodes/research_tools.py`;
`scripts/research_preflight.py`; `tests/unit/test_fr1005_research_row_failed.py`
plus the minimum witness updates in `tests/unit/test_fr926_recorded_cause_witness.py`
and `tests/unit/test_fr890_research_route.py`; `capabilities/CAP-248-research-sole-route.yaml`;
one changelog fragment; one diary reflection; the live `research-runs.jsonl`
stamp and the promoted record appended to `docs/2026-09-05-research-pi-agent-runtime.md` §9.
No graph or prompt edits (AC-15).

### S-1: `gather_findings` contains exactly one attributable model-output failure (R-1, R-2)

A typed `FailedPersona` Pydantic record (`outcome: Literal["row_failed"]`
discriminator, `state_key` constrained to `PERSONA_KEYS`, non-empty
`cause`) crosses the gather/reduce boundary as its `model_dump()` inside
the existing `findings: list` state key, so the graph's typed state does
not change. `gather_findings` emits exactly one entry per `PERSONA_KEYS`
slot in canonical order: the normalised finding when the key is present,
the failure record in that slot when it is not.

A missing key is contained only when **all** of these hold, else the run
is fatal with FR-926's exact message (`missing persona findings: <keys>` +
`recorded node errors:` block listing every usable recorded diagnostic):

- the key is not `librarian_finding` (C-3);
- exactly one recorded error's `node` is in the explicit
  `PERSONA_NODES[key]` set (a static map covering every key, mirrored by a
  test against the graph's node names; no prefix heuristic, AC-03);
- that error is model-owned: `type == validation_error` or
  `details.exception_type ∈ {"ValidationError", "OutputParserException"}`.

Zero matching errors, malformed-only entries, two or more matching errors
(ambiguous), or a matching non-model error (auth, provider, tool,
graph-state) remain fatal. The all-five success path is byte-for-byte
unchanged (AC-04). The FR-926 formatter is kept for the fatal path and the
cause text of the contained record uses the same fields.

### S-2: `reduce_findings` contains one invalid row by canonical slot (R-1, R-2, R-3)

- The reducer walks `findings` by index; index `i` **is** `PERSONA_KEYS[i]`.
  More entries than slots, a non-dict entry, or a failure record whose
  `state_key` is not its slot's key is a structural defect: fatal.
- A `FailedPersona` dump is re-validated through the model.
- A present finding that fails `PersonaFinding` validation (over-length,
  closed-enum miss, empty cell) becomes a failure attributed to its slot's
  key with cause `<field>: <message> [<pydantic type>]`. Nothing is
  truncated, head-split, or repaired (R-3, C-5); an enum value outside the
  set takes this same path.
- Precedent validation (FR-938) and librarian URL reconciliation stay
  fatal, unchanged (C-6).
- Floors, all checked **before** the artifact path is touched (R-5, C-7):
  more than one failure, a failed `librarian_finding`, fewer than four
  valid rows, fewer than three grounded rows → `ValueError` listing every
  accumulated failure and the fatal cause; no artifact exists afterwards.
- Header gains machine-readable accounting (R-4):

  ```text
  - persona keys executed: ["os_infra_finding", "data_process_finding", "subtractionist_finding", "librarian_finding"]
  - personas failed: {"yamlgraph_native_finding": "yamlgraph_native_planner: unknown_error (OutputParserException): …"}
  ```

  JSON values, line breaks in the cause normalised to spaces, full text
  preserved. The `personas failed` line is written only when one failed.
  The reducer asserts before writing: executed and failed keys are unique
  members of `PERSONA_KEYS`, disjoint, union equal to `PERSONA_KEYS`; row
  count equals executed count; cause non-empty; at most one failed;
  librarian executed. The human `personas executed:` names line stays.
  The return dict gains `failed`.

### S-3: `verify_artifact` enforces the same invariants (R-4)

`research_preflight.py` mirrors `PERSONA_KEYS` and `MIN_ROWS` (witnessed).
On an artifact with fewer than five rows both accounting lines are
required; malformed JSON, unknown or duplicate keys, overlapping sets,
incomplete union, row/executed-count mismatch, empty cause, more than one
failed key, a failed librarian, or missing accounting is a violation. On a
five-row artifact a `personas failed` line is a violation; an executed
line, when present, must equal the full key set (older promoted records
without the line stay verifiable).

### S-4: tests (RED first with `SKIP=pytest`, then GREEN)

New `tests/unit/test_fr1005_research_row_failed.py` (`REQ-YG-665`,
`pytestmark = pytest.mark.process`) covering AC-01…AC-12 including the
failure-atomicity test and the stale-artifact wrapper test. FR-926's
witnesses keep their exact fatal-path assertions (its fictional node
`yamlgraph_native_persona` is not in `PERSONA_NODES`, so it stays fatal by
R-1) and gain replacements showing the real node's fields survive into the
contained record and the artifact. Two FR-890 witnesses are re-homed to
canonical five-slot inputs: disagreement preserved as rows is shown with
two slots proposing the same candidate under opposite verdicts, and the
empty-cell witness asserts the row is contained with a cause naming the
field instead of the run dying.

### S-5: traceability and record

`CAP-248` gains `REQ-YG-665` and `FR-1005`; changelog fragment;
implementation record; diary reflection with a Seed.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: A direct unit test supplies one missing non-librarian `PERSONA_KEYS` entry and one matching real `PipelineError` proving a structured-output/schema validation failure; `gather_findings` returns five canonically ordered entries, with a typed failed-persona record in that key's slot containing the canonical key, node, category, exception type, and message.
- [x] AC-02: Missing-key cases with an absent/empty error channel, malformed error entries, no matching node, ambiguous matching errors, or a non-model failure remain fatal and name the missing key plus all usable recorded diagnostics; errors for other persona nodes are never attributed to the missing key.
- [x] AC-03: The key-to-node attribution map covers every `PERSONA_KEYS` member explicitly and has a mirror test; no prefix heuristic is inferred dynamically from the key string.
- [x] AC-04: With all five keys present, `gather_findings` returns the existing `{"findings": [...]}` shape with five normalized findings in `PERSONA_KEYS` order and no added metadata inside successful finding dicts.
- [x] AC-05: `reduce_findings` given four valid findings and one attributable failed-persona record writes four rows, structured executed/failed metadata satisfying R-4, lists only successful persona keys as executed, returns `failed == 1`, and is accepted by `verify_artifact`.
- [x] AC-06: A present finding whose `candidate` is 471 characters, or whose `solution_class`/`verdict` is outside the closed enum, becomes a failed-persona outcome whose cause names the canonical state key, field, and Pydantic error type; no field is truncated, prefix-repaired, or written as a table row.
- [x] AC-07: Two failed persona outcomes, any failed librarian, fewer than four valid rows, fewer than three grounded rows, or any structural/non-model failure raises before artifact creation and reports every accumulated attributable row failure plus the fatal cause.
- [x] AC-08: Precedent validation and librarian URL reconciliation remain run-fatal; existing FR-938 fabricated-precedent and FR-896 librarian fail-closed tests pass unchanged, including fabricated `CAP-628`.
- [x] AC-09: `verify_artifact` rejects malformed persona-accounting JSON, unknown or duplicate keys, overlapping executed/failed keys, incomplete union with `PERSONA_KEYS`, row/executed-count mismatch, empty causes, more than one failed key, a failed librarian, missing accounting on a short run, and failure metadata on a five-row run; it accepts a valid four-row/one-failure artifact.
- [x] AC-10: A mirror test asserts `research_preflight.PERSONA_COUNT == len(research_tools.PERSONA_KEYS)` and the verifier's allowed key set equals the reducer's canonical key set.
- [x] AC-11: Every FR-926 diagnostic witness has an equal or stronger replacement at the new location; the real `PipelineError` fields survive into the failed-persona record and artifact, dict-form compatibility remains covered, and `test_wrapper_surfaces_enriched_failure_text` remains unchanged.
- [x] AC-12: A deterministic failure-atomicity test starts with no draft artifact, triggers each fatal class, and proves no artifact is created; the wrapper test proves a failed graph cannot pass by stale output.
- [x] AC-13: A live `scripts/research.sh feature-requests/research-briefs/pi-agent-runtime-brief.md` run on the fixed code completes with a verified four- or five-row artifact, appends a matching `research-runs.jsonl` stamp, and appends the promoted table to `docs/2026-09-05-research-pi-agent-runtime.md` section 9 with structured failed-persona metadata quoted when present.
- [x] AC-14: `CAP-248` carries `FR-1005` and `REQ-YG-665`; every new test carries `@pytest.mark.req("REQ-YG-665")`; `python scripts/req_coverage.py --strict` passes; the changelog fragment, implementation record, and diary reflection are present.
- [x] AC-15: `git diff main -- examples/demos/research-route/graph.yaml examples/demos/research-route/prompts` is empty.

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
| Accept an exact enum head followed by prose (`process-boundary. The four …`) and record the dropped tail | REJECTED by judgement R-3 — a second, unevidenced normalisation policy; run 1 already survives by containing the row; a fourth delimiter special case wants a parser, not a regex (`regex_fourth_exclusion`) | The run-1 row had a valid head and four other valid cells; containment loses a real finding a five-character split would have kept. Recorded for a future FR with its own evidence. |
| **Chosen**: one attributable model-output failure becomes a typed `FailedPersona` record in its canonical slot at gather or reduce; the artifact carries JSON persona accounting with conserved invariants; everything structural, ambiguous, or librarian stays fatal; floor of four rows plus librarian unchanged | PURSUE | — |

## Related

- Evidence: [evidence/FR-1005-research-route-run-failures.md](evidence/FR-1005-research-route-run-failures.md)
- The brief that killed three runs: [research-briefs/pi-agent-runtime-brief.md](research-briefs/pi-agent-runtime-brief.md); its research document [docs/2026-09-05-research-pi-agent-runtime.md](../docs/2026-09-05-research-pi-agent-runtime.md) §9 records the runs and receives the AC-11 witness.
- Scripture: `two_strike_split`, `junk_drawer_cap` (enum leak → cap in code), `substance_over_presence`, `read_raw_output_first`.

## Implementation record (2026-09-06)

Enforced within the frozen scope of the judgement (D-1…D-6). Commits, in
order: FR + evidence `982ad57e`; judgement folded `35443c5d`; RED
`91f1e214` (13 of 21 new witnesses failing on the unchanged route);
GREEN `d53cae3f`; GREEN follow-up `4bc34a82`.

- **D-2** `research_tools.py`: `FailedPersona` (validated `outcome`
  discriminator, `state_key` constrained to `PERSONA_KEYS`, whitespace-
  squashed non-empty `cause`); `PERSONA_NODES` explicit map;
  `MODEL_OUTPUT_ERROR_TYPE` / `MODEL_OUTPUT_EXCEPTIONS`; `gather_findings`
  emits one entry per slot and stays fatal with FR-926's exact message for
  every non-attributable case; `_contain_findings` walks by slot (structural
  → fatal, librarian → fatal, two failures → fatal); the `MIN_VALID_ROWS`
  floor is applied by the reducer *after* FR-896's grounding check so that
  check keeps its message; `_assert_accounting` enforces R-4 before the
  artifact path is touched; header gains `- persona keys executed:` and
  `- personas failed:` (JSON); return gains `failed`.
- **D-3** `research_preflight.py`: mirrored `PERSONA_KEYS`, `PERSONA_COUNT`,
  `MIN_ROWS`, `LIBRARIAN_KEY`; `_check_persona_accounting` re-derives every
  R-4 invariant; module trimmed to 439 lines to stay under the 450-line
  gate (docstrings compacted, no behaviour change).
- **D-4** `tests/unit/test_fr1005_research_row_failed.py` (22 witnesses,
  `REQ-YG-665`, `pytest.mark.process`). FR-926 witnesses unchanged (their
  fictional node is not in `PERSONA_NODES`, so they stay on the fatal path
  by R-1) plus two replacements for the contained path. **Deviation,
  recorded:** three pre-existing witnesses were re-homed to the judged
  contract rather than left unchanged — FR-896
  `test_over_length_cell_rejected_not_truncated` (AC-06 makes the
  over-length row a contained outcome; the test now asserts the row is
  never written, never truncated, and the named violation carries `400`
  and `string_too_long` in the accounting) and FR-890
  `test_reduce_preserves_conflicting_rows` (six inputs → five canonical
  slots, disagreement still two rows) and `test_reduce_fails_closed_on_empty_cell`
  (empty cell → contained row, cause names the field). No witnessed
  behaviour was deleted without a replacement.
- **D-5** `CAP-248` (`FR-1005`, `REQ-YG-665`), `ARCHITECTURE.md`
  regenerated, `changelog/unreleased/fr-1005-research-route-row-failed.md`,
  diary `docs/diary/diary-2026-09-06-reflection-fr-1005-the-loader-that-kept-no-name.md`.
- **D-6 / AC-13** live witness: run 4 on `d53cae3f` died in
  `gather_findings` with "`FailedPersona` is not fully defined" — the
  runtime tool loader keeps no `sys.modules` entry, so a deferred `Literal`
  annotation could not resolve; the unit loader had registered the module
  and hidden it. Fixed in `4bc34a82` (validated `str` discriminator) with a
  witness that loads the module exactly as the runtime does. Run 5 on
  `4bc34a82`: verified artifact, four rows, `personas failed` naming
  `yamlgraph_native_finding` with the recorded `OutputParserException`
  cause; stamped in `research-runs.jsonl` at 2026-09-05T21:19:01Z; promoted
  to `docs/2026-09-05-research-pi-agent-runtime.md` §9 and §11.

**Host limitations, stated:** the ten bash-wrapper tests across the FR-890,
FR-896, FR-926 and FR-1005 suites cannot run on this Windows host
(`subprocess.run(["bash", …])` resolves to the WSL stub, FR-953); they run
in CI. `pre-commit` hooks are not installed here; the gates were run by
hand (`ruff`, `size_gate`, `req_coverage --strict`, `validate_capabilities`,
`aggregate_capabilities`, `check_changelog_req --strict --skip-llm`,
route suites 84 passing).

**Observed, not acted on (out of frozen scope):** `research_tools.py` is
now 830 lines, over the repository's module-size standard, though outside
the size gate's scan roots; a split FR is owed. Two personas in run 5 wrote
a paragraph into the `persona` cell, which the canonical key line makes
harmless but which the FR-896 brevity contract did not anticipate. The
temperature-0 `on_error: retry` on persona nodes is a witnessed no-op six
times over; FR-926's deferred retry-with-feedback now has two witnesses
(diary Seed).
