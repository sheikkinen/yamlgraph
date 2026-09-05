# Judgement: FR-1005 Research route demotes a failed persona to a recorded row instead of killing the run

**Prior art:** dispositioned in the parent FR header ([FR-1005](FR-1005-research-route-row-failed-demotion.md) — FR-890, FR-896, FR-926, FR-938, FR-990, FR-962); the judge additionally cited FR-943 (census row-failure containment) as the attributable-vs-structural precedent, folded into R-1.

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`) on lane commit `982ad57e`, 2026-09-05 21:0x UTC, this Windows host. Folded verbatim below; R-1…R-5 incorporated into the FR (closed attribution taxonomy, typed `FailedPersona` by canonical slot, head-split removed, JSON accounting with conserved invariants, atomicity), and the FR's acceptance criteria replaced by the revised AC-01…AC-15.


**Verdict:** APPROVED WITH REVISIONS — one attributable model-output failure may be contained at the existing gather/reduce boundary, but authority activates only after the FR preserves structural failures as fatal, carries canonical persona identity through reduction, removes the unevidenced delimiter-repair grammar, and makes short-run accounting mechanically substantive.

**Reviewed against:** `feature-requests/FR-1005-research-route-row-failed-demotion.md`; `feature-requests/evidence/FR-1005-research-route-run-failures.md`; `feature-requests/research-briefs/pi-agent-runtime-brief.md`; `docs/2026-09-05-research-pi-agent-runtime.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-896-research-route-precedent-traceability.judgement.md`; `feature-requests/FR-926-research-failure-cites-recorded-cause.md`; `feature-requests/FR-926-research-failure-cites-recorded-cause.judgement.md`; `feature-requests/FR-938-prior-art-retrieval-in-research-route.md`; `feature-requests/FR-938-prior-art-retrieval-in-research-route.judgement.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-990-cap-journey-census.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `examples/demos/research-route/nodes/research_tools.py`; `scripts/research.sh`; `scripts/research_preflight.py`; `yamlgraph/schema_loader.py`; `capabilities/CAP-248-research-sole-route.yaml`; `tests/unit/test_fr890_research_route.py`; `tests/unit/test_fr896_precedent_traceability.py`; `tests/unit/test_fr926_recorded_cause_witness.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real, repeated, and read at the raw boundary. Run 1 lost five completed findings because one `solution_class` contained a valid enum followed by prose; runs 2 and 3 lost four completed findings because the fifth persona's 471-character `candidate` failed structured-output validation identically after retry (`feature-requests/evidence/FR-1005-research-route-run-failures.md:11-36,38-75,78-115`). This is not a forecast from aggregate metrics: the evidence includes the rejected completion, names its 471-character field, and records concrete surprising precedent and effort details (`feature-requests/evidence/FR-1005-research-route-run-failures.md:78-115`). The in-body research record therefore satisfies the prospective research gate and `read_raw_output_first` in substance (`feature-requests/FR-1005-research-route-row-failed-demotion.md:8-10,143-154`; `.github/skills/judge-fr/doctrine.md:114-130`).

The central change is minimal and aligned with an existing seam. `gather_findings` currently requires every `PERSONA_KEYS` entry and raises before reduction, while `_validate_findings` turns any `PersonaFinding` validation error into a run-level failure (`examples/demos/research-route/nodes/research_tools.py:27-33,377-387,479-495`). The artifact verifier already permits four rows, requires at least three grounded rows, and requires a librarian (`scripts/research_preflight.py:245-298`). Allowing exactly one attributable non-librarian model-output failure to become recorded run metadata therefore composes with the existing floor instead of inventing a new orchestration path.

The FR also preserves the important fail-closed boundaries. It keeps the 400-character cap and reject-never-truncate rule, leaves fabricated precedent and librarian URL reconciliation fatal, and does not alter graph topology, prompts, or retry behavior (`feature-requests/FR-1005-research-route-row-failed-demotion.md:10,91-100,133-141`). That respects FR-896's bounded-field witness and FR-938's rule that invalid precedent must not become the cheaper path (`feature-requests/FR-896-research-route-precedent-traceability.judgement.md:71,84`; `feature-requests/FR-938-prior-art-retrieval-in-research-route.judgement.md:25-29`).

Strategic classification: **contrib/example bug fix**. The generic framework already records retry errors; this proposal changes only the research-route example's consumer-specific reduction and artifact contract. It has one concrete route and one repeated failure class, so it is neither a framework primitive nor pattern documentation.

## Required revisions

### R-1: Contain only attributable model-owned failures

Replace the blanket missing-key demotion and `no recorded cause` success path (`feature-requests/FR-1005-research-route-row-failed-demotion.md:71-80,129-130`) with a closed failure taxonomy.

A missing persona key may become a failed-persona record only when exactly one recorded error is deterministically attributable to that key through an explicit key-to-node mapping and the record proves a model-owned structured-output/schema validation failure. A missing key with no matching error, only malformed error entries, ambiguous matching errors, or a non-model failure such as authentication, provider, tool, graph-state, or infrastructure failure remains run-fatal with all available diagnostics. A failed librarian remains run-fatal. A present candidate whose `PersonaFinding` validation fails may be contained because every validated field is model-authored, but non-dict inputs, identity/order defects, precedent failures, URL-reconciliation failures, and reducer invariants remain fatal.

This boundary is required because the proposal's ideal is specifically a cell-shape failure (`feature-requests/FR-1005-research-route-row-failed-demotion.md:55-64`), while `no recorded cause` cannot distinguish model misbehavior from broken graph wiring. The cited row-containment precedent makes exactly this distinction: attributable model-owned failures are rows, structural impossibilities are batch-fatal (`feature-requests/FR-943-census-row-failure-containment.md:54-59,92-132`).

### R-2: Preserve canonical persona identity with a typed failure record

Define a Pydantic failed-persona record with a discriminator, canonical `state_key`, and non-empty `cause`; do not introduce the untyped `{"row_failed": ..., "cause": ...}` marker proposed at lines 71-80. `gather_findings` must emit exactly one entry per `PERSONA_KEYS` slot in canonical order, placing a failure record in the missing key's slot rather than appending markers after present rows. The reducer must attribute validation failures by that canonical slot, never by the model-authored `persona` cell and never by a fallback such as `"finding N"`.

This makes AC-07's promise to name every failed persona key implementable even when the `persona` cell itself is absent or invalid (`feature-requests/FR-1005-research-route-row-failed-demotion.md:91-92,135`). It also obeys the repository's Pydantic boundary and prohibition on wandering untyped dicts (`.github/copilot-instructions.md:47,192`). The all-five success payload may remain byte-for-byte unchanged; the positional identity contract belongs to the containing list and reducer.

### R-3: Remove enum head-splitting from this bug fix

Delete the delimiter-based `solution_class`/`verdict` repair, reducer notes, `notes` return value, and current AC-06 (`feature-requests/FR-1005-research-route-row-failed-demotion.md:83-90,101-103,134`). Run 1 already succeeds under the core proposal by containing its invalid row and retaining the other four. Parsing six punctuation forms and dropping an 80-character tail is a second, unevidenced normalization policy, is unnecessary to stop whole-run loss, and conflicts with the repository warning that a fourth regex special case requires a real parser (`.github/copilot-instructions.md:66`).

An invalid closed-enum value must therefore follow the same row-failure path as another `PersonaFinding` validation error. No model-authored field is truncated or repaired by this FR. A future proposal may seek enum-prefix recovery with its own evidence and semantics.

### R-4: Make short-run accounting machine-readable and conserved

Replace the semicolon-delimited `<key>: <cause>` header grammar and presence-only verifier check (`feature-requests/FR-1005-research-route-row-failed-demotion.md:101-110,137`) with deterministic structured metadata. Use JSON values on dedicated header lines, for example:

```text
- persona keys executed: ["os_infra_finding", ...]
- personas failed: {"yamlgraph_native_finding": "<cause>"}
```

The reducer and verifier must enforce all of these invariants: executed and failed keys are unique members of `PERSONA_KEYS`; their sets are disjoint; their union equals `PERSONA_KEYS`; table row count equals executed-key count; a failed cause is non-empty; at most one persona failed; the librarian key is executed; and a five-row artifact has no failed entries. Normalize embedded line breaks for the header while preserving the complete cause text as a JSON string. The verifier must reject malformed JSON, unknown/duplicate keys, count mismatches, empty causes, missing accounting on a short run, and failure metadata on a full run.

This is the substantive check required by the FR's own stated doctrine. Merely accepting any line with a `key: cause` shape repeats the presence-only failure the proposal says it cures (`feature-requests/FR-1005-research-route-row-failed-demotion.md:105-110`; `.github/copilot-instructions.md:102`).

### R-5: Reconcile the delivery surface and preserve failure atomicity

Replace "All changes in ... and tests" with the complete delivery surface: the FR amendment, `research_tools.py`, `research_preflight.py`, focused tests, `CAP-248`, changelog fragment, diary entry, generated `research-runs.jsonl` stamp, and the live promoted record appended to `docs/2026-09-05-research-pi-agent-runtime.md` (`feature-requests/FR-1005-research-route-row-failed-demotion.md:66-69,121-125,139-140`). State that every fatal condition is resolved before opening/writing `tmp/draft-alternatives.md`; `scripts/research.sh` already removes the prior draft before execution, so a failed run cannot verify stale output (`scripts/research.sh:49,67-69`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1005-research-route-row-failed-demotion.md`: fold R-1 through R-5 and record implementation status. |
| D-2 | `examples/demos/research-route/nodes/research_tools.py`: typed failed-persona record, explicit attribution taxonomy, canonical slot handling, row containment, fatal floors, and structured persona-outcome header. |
| D-3 | `scripts/research_preflight.py`: mirrored persona-count constant and exact structured short-run accounting invariants from R-4. |
| D-4 | `tests/unit/test_fr1005_research_row_failed.py` plus the minimum witness updates in `tests/unit/test_fr926_recorded_cause_witness.py`; existing FR-896/FR-938 tests remain unchanged unless an assertion must be strengthened without weakening its prior contract. |
| D-5 | `capabilities/CAP-248-research-sole-route.yaml`, one FR-1005 changelog fragment, and one diary reflection with a Seed. |
| D-6 | Live rerun evidence: `feature-requests/research-runs.jsonl` and `docs/2026-09-05-research-pi-agent-runtime.md` section 9. |

Not authorized: edits to `examples/demos/research-route/graph.yaml` or its prompts; retry-count or retry-feedback changes; schema-cap changes; truncation or repair of model-authored fields; delimiter-based enum parsing; generic YAMLGraph framework changes; demotion of missing/unverifiable precedent, fabricated citations, librarian failures, authentication/provider/tool failures, malformed state, or unexplained missing persona keys; changes to judge/review/author doctrine, hooks, or CI.

## Revised acceptance criteria

- [ ] AC-01: A direct unit test supplies one missing non-librarian `PERSONA_KEYS` entry and one matching real `PipelineError` proving a structured-output/schema validation failure; `gather_findings` returns five canonically ordered entries, with a typed failed-persona record in that key's slot containing the canonical key, node, category, exception type, and message.
- [ ] AC-02: Missing-key cases with an absent/empty error channel, malformed error entries, no matching node, ambiguous matching errors, or a non-model failure remain fatal and name the missing key plus all usable recorded diagnostics; errors for other persona nodes are never attributed to the missing key.
- [ ] AC-03: The key-to-node attribution map covers every `PERSONA_KEYS` member explicitly and has a mirror test; no prefix heuristic is inferred dynamically from the key string.
- [ ] AC-04: With all five keys present, `gather_findings` returns the existing `{"findings": [...]}` shape with five normalized findings in `PERSONA_KEYS` order and no added metadata inside successful finding dicts.
- [ ] AC-05: `reduce_findings` given four valid findings and one attributable failed-persona record writes four rows, structured executed/failed metadata satisfying R-4, lists only successful persona keys as executed, returns `failed == 1`, and is accepted by `verify_artifact`.
- [ ] AC-06: A present finding whose `candidate` is 471 characters, or whose `solution_class`/`verdict` is outside the closed enum, becomes a failed-persona outcome whose cause names the canonical state key, field, and Pydantic error type; no field is truncated, prefix-repaired, or written as a table row.
- [ ] AC-07: Two failed persona outcomes, any failed librarian, fewer than four valid rows, fewer than three grounded rows, or any structural/non-model failure raises before artifact creation and reports every accumulated attributable row failure plus the fatal cause.
- [ ] AC-08: Precedent validation and librarian URL reconciliation remain run-fatal; existing FR-938 fabricated-precedent and FR-896 librarian fail-closed tests pass unchanged, including fabricated `CAP-628`.
- [ ] AC-09: `verify_artifact` rejects malformed persona-accounting JSON, unknown or duplicate keys, overlapping executed/failed keys, incomplete union with `PERSONA_KEYS`, row/executed-count mismatch, empty causes, more than one failed key, a failed librarian, missing accounting on a short run, and failure metadata on a five-row run; it accepts a valid four-row/one-failure artifact.
- [ ] AC-10: A mirror test asserts `research_preflight.PERSONA_COUNT == len(research_tools.PERSONA_KEYS)` and the verifier's allowed key set equals the reducer's canonical key set.
- [ ] AC-11: Every FR-926 diagnostic witness has an equal or stronger replacement at the new location; the real `PipelineError` fields survive into the failed-persona record and artifact, dict-form compatibility remains covered, and `test_wrapper_surfaces_enriched_failure_text` remains unchanged.
- [ ] AC-12: A deterministic failure-atomicity test starts with no draft artifact, triggers each fatal class, and proves no artifact is created; the wrapper test proves a failed graph cannot pass by stale output.
- [ ] AC-13: A live `scripts/research.sh feature-requests/research-briefs/pi-agent-runtime-brief.md` run on the fixed code completes with a verified four- or five-row artifact, appends a matching `research-runs.jsonl` stamp, and appends the promoted table to `docs/2026-09-05-research-pi-agent-runtime.md` section 9 with structured failed-persona metadata quoted when present.
- [ ] AC-14: `CAP-248` carries `FR-1005` and `REQ-YG-665`; every new test carries `@pytest.mark.req("REQ-YG-665")`; `python scripts/req_coverage.py --strict` passes; the changelog fragment, implementation record, and diary reflection are present.
- [ ] AC-15: `git diff main -- examples/demos/research-route/graph.yaml examples/demos/research-route/prompts` is empty.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 are folded into FR-1005 and its acceptance criteria are replaced by the revised set above. | GATE |
| C-2 | Only an explicitly attributable model-owned `PersonaFinding`/structured-output validation failure may be contained; unknown, ambiguous, structural, provider, authentication, tool, and graph-state failures remain fatal. | GATE |
| C-3 | At most one non-librarian persona may fail; four valid rows, at least three grounded rows, and a valid librarian row remain mandatory. | GATE |
| C-4 | Canonical state-key identity must survive independently of model-authored persona text, and failed-persona data must cross the gather/reduce boundary through a Pydantic model. | GATE |
| C-5 | No model-authored cell may be truncated, head-split, prefix-repaired, or otherwise rewritten by this FR. | GATE |
| C-6 | Fabricated/unverifiable precedent and librarian reconciliation failures remain run-fatal exactly as governed by FR-896/FR-938. | GATE |
| C-7 | All fatal checks must complete before artifact writing; no failed run may leave a newly written partial artifact. | GATE |
| C-8 | No graph, prompt, retry, generic framework, judge/review/author doctrine, hook, or CI change is authorized. | GATE |

Authority granted: after R-1 through R-5 are folded into FR-1005, the enforcer may implement typed, attributable one-row failure containment and mechanically conserved short-run metadata solely on the frozen research-route Python, verifier, test, traceability, and live-evidence surfaces above.
