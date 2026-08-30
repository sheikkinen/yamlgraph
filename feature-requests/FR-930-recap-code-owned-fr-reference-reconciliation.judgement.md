# Judgement: FR-930 Code-Owned FR-Reference Reconciliation in the Recap Demo

**Verdict:** APPROVED WITH REVISIONS -- the boundary-reconciliation direction is sound, but authority activates only after the FR repairs its FR-890 research evidence and closes the `fr_statuses` loophole that would let status-only hallucinations survive.

**Prior art:** the only nominal hit is `FR-930-recap-code-owned-fr-reference-reconciliation.md` — the FR under judgement itself, a self-reference, not competing precedent. Substantive prior art (FR-700, FR-702/703/704 eviction lineage, FR-922 gray-zone verdict, FR-923, FR-677) is dispositioned in the FR's own Prior art section and weighed in "What is sound" below.

**Reviewed against:** `feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md`; cited evidence files `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md`, `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.judgement.md`, `feature-requests/FR-700-timeframe-recap-example.md`, `feature-requests/FR-702-recap-disposition-axis.md`, `feature-requests/FR-703-recap-status-join-post-pass.md`, `feature-requests/FR-704-recap-orphans-bypass-model.md`, `feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md`, `feature-requests/FR-677-verification-first-class-dsl.md`, `yamlgraph/tools/python_tool.py`, `examples/demos/recap/graph.yaml`, `examples/demos/recap/prompts/recap.yaml`, `examples/demos/recap/nodes/partition.py`, `tests/unit/test_recap_demo.py`, `tests/integration/test_recap_demo_integration.py`, `capabilities/CAP-195-timeframe-recap-demo.yaml`, `ARCHITECTURE.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`; judgement-precedent files `feature-requests/FR-928-cloud-judge-github-actions.judgement.md`, `feature-requests/FR-899-org-repo-census-azure.judgement.md`.

## What is sound

The problem is real and correctly located at the model-to-code boundary. The prompt currently asks the model to "Never invent commit hashes, FR references, or file paths" (`examples/demos/recap/prompts/recap.yaml:21-22`), while the current live witness checks one sampled output for absent `FR-\d+` references (`tests/integration/test_recap_demo_integration.py:67-83`). That is weaker than runtime enforcement for every invocation, and repo doctrine says mechanizable instruction-following failures belong in code: `two_strike_split` says to treat model output as a claim reconciled against the source of truth (`.github/copilot-instructions.md:117`), and `the_one_law` says to normalize where external data enters (`.github/copilot-instructions.md:51-53`).

The chosen surface is feasible. Python nodes receive the full state dict and return a partial state update (`yamlgraph/tools/python_tool.py:236-240`, `yamlgraph/tools/python_tool.py:270-311`), and the existing graph already routes `synthesize -> finalize_recap -> END` (`examples/demos/recap/graph.yaml:101-116`). `finalize_recap` currently normalizes the recap through `attach_statuses`, then appends code-owned orphans (`examples/demos/recap/nodes/partition.py:132-149`), so it is the right deterministic post-model boundary for stripping and recording unverified FR/NC tokens before status decoration.

The proposal honors the recap-demo evolution. FR-702 moved reference partitioning into a deterministic python pre-pass after prompt-only orphan detection failed (`feature-requests/FR-702-recap-disposition-axis.md:52-54`, `feature-requests/FR-702-recap-disposition-axis.md:80-88`); FR-703 moved status joining into code (`examples/demos/recap/nodes/partition.py:68-105`; `capabilities/CAP-195-timeframe-recap-demo.yaml:49-60`); FR-704 moved orphan copying out of the model after repeated hash corruption (`feature-requests/FR-704-recap-orphans-bypass-model.md:14-16`, `feature-requests/FR-704-recap-orphans-bypass-model.md:29-32`). FR-930 is the same pattern applied to the remaining prompt-only anti-hallucination clause.

Retiring the specific live bare-repo hallucination witness is defensible after construction replaces sampling. FR-922 recorded the test as a gray-zone witness because its wall time ranged from 12.95s to 78.35s steady-state with a 283s observed outlier, it silently bound to Anthropic, and it tested live demo output quality rather than a deterministic regression boundary (`feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md:122-132`, `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md:191-210`, `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md:213-235`). FR-922's judgement forbade deleting the test in FR-922 only (`feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.judgement.md:51-62`); this FR supplies the missing replacement mechanism.

Strategic classification: **contrib/example bug fix**. This is not a framework primitive: FR-677 already provides graph-level verification, but this invariant is better enforced inside the recap demo's deterministic finalizer because the output can be repaired and recorded without halting the graph (`feature-requests/FR-677-verification-first-class-dsl.md:58-73`; `feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:144-152`). It is one concern: reconciling model-authored FR/NC reference claims in the recap demo.

## Required revisions

### R-1: Replace the research field with a committed or substantively equivalent FR-890 record

Revise the `**Research:**` field so it points at an exact committed research artifact or expands the FR body into an equivalent committed alternatives record. The record must include 4-6 genuine solution classes, precedent/evidence lines for each class, preserved disagreement, and an explicit `is_this_a_graph` answer for the chosen path.

Do not leave the current shorthand as the full research evidence. FR-930 currently says only "FR-922 investigation record" plus two factual checks (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:9`), and its alternatives table dispositions five options without the FR-890 columns or explicit `is_this_a_graph` answer (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:144-152`). Local judge doctrine requires newly created FRs to carry a committed research record or equivalent substantive alternatives table, and the judge must check substance rather than field presence (`.github/skills/judge-fr/doctrine.md:118-128`). Authority is inactive until this is folded in.

### R-2: Define the allowed universe as model-visible deterministic evidence, not `fr_statuses`

Replace the allowed-universe bullet in Proposed Solution section 1 so the reconciler admits FR/NC tokens only from deterministic fields the model was allowed to see or deterministic derivatives of those fields: `commits`/`referenced`, `churn`, `fr_changes`, and `fragments`. Explicitly exclude `fr_statuses` from the allowed universe. `fr_statuses` may be used only after reconciliation by `attach_statuses` to decorate IDs that survived reconciliation.

The current FR says the allowed universe includes `fr_statuses` (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:71-73`), but the graph does not pass `fr_statuses` into the LLM prompt (`examples/demos/recap/graph.yaml:101-108`). The `fr_statuses` tool greps every FR status at `HEAD`, not just the recap window (`examples/demos/recap/graph.yaml:34-39`). If an LLM invents a real but prompt-invisible FR ID that happens to exist in `fr_statuses`, the proposed universe would preserve it and `attach_statuses` could lend it a `[Status: ...]` tag. That contradicts the FR's own requirement that an invented ID never receive status credibility (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:79-81`).

### R-3: Freeze `unverified_refs` normalization and add the status-only negative witness

Revise the recording contract and tests to specify that `recap["unverified_refs"]` is a deterministic list of uppercase unique `FR-N`/`NC-N` tokens in first-seen order, with `[]` when nothing was stripped. Add a required unit witness where `fr_statuses` contains `FR-999` but `commits`/`referenced`, `churn`, `fr_changes`, and `fragments` do not; `finalize_recap` must strip `FR-999`, record `["FR-999"]`, and the final workstream must contain neither `[Status: ...]` nor `[no FR status]` for that ID.

The current ACs require recording and ordering generally (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:126-133`) but do not define duplicate/case behavior for the new field, and the listed ordering test does not cover the `fr_statuses` loophole created by the proposed universe (`feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md:91-99`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md`: fold R-1 through R-3, update implementation status/decisions, and record REQ-YG-531 coverage counts before/after. |
| D-2 | `examples/demos/recap/nodes/partition.py`: add the deterministic reconciler and call it inside `finalize_recap` before `attach_statuses`; preserve existing orphan assembly and status-join semantics for verified IDs. |
| D-3 | `tests/unit/test_recap_demo.py`: add RED/GREEN unit witnesses for stripped workstream refs, preserved legitimate refs, hotspot stripping, case handling, empty `unverified_refs`, and the status-only `fr_statuses` negative case from R-3. |
| D-4 | `tests/integration/test_recap_demo_integration.py`: delete only `TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions`; retain `TestRecapDispositionAxis::test_rejected_status_surfaces_verbatim`. |
| D-5 | `examples/demos/recap/demo-output.log`: refreshed demo-gate witness for the recap demo after the finalizer change. |
| D-6 | `changelog/unreleased/*.md` and `docs/diary/*.md`: changelog fragment with `req: REQ-YG-531` and a metacognitive reflection for this fix. |

Not authorized: changes to `examples/demos/recap/graph.yaml`, `examples/demos/recap/prompts/recap.yaml`, any `yamlgraph/` module, CI workflows, pytest configuration, provider/model selection, latency lanes owned by FR-923, graph-level `verify:` or guard edits, `#N` issue-reference reconciliation, reconciling fields not authored by the model, broad deletion or skipping of recap integration tests, or changing the judge/authoring/review doctrine. If a graph or prompt edit becomes necessary, stop and return to the graph-authoring route; this judgement does not authorize unsentineled graph-artifact edits.

## Revised acceptance criteria

- [ ] AC-01: FR-930 contains a `**Research:**` field pointing at a committed research artifact or an in-body equivalent that satisfies the FR-890 judge gate: 4-6 genuine solution classes, precedent/evidence line per class, preserved disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-02: The reconciler builds its allowed FR/NC universe only from model-visible deterministic evidence: `commits`/`referenced`, `churn`, `fr_changes`, and `fragments`; `fr_statuses` is excluded from that universe and used only by the later status join for IDs that survived reconciliation.
- [ ] AC-03: A RED commit adds failing `REQ-YG-531` unit tests for the reconciler behavior; a separate GREEN commit implements the fix and makes those tests pass.
- [ ] AC-04: `finalize_recap` normalizes dict/Pydantic recap values as today, reconciles only the model-authored `workstreams` and `hotspots` fields, strips every `_REF_PATTERN` `FR-N`/`NC-N` token absent from the allowed universe, and records stripped refs in `recap["unverified_refs"]`.
- [ ] AC-05: `recap["unverified_refs"]` is an uppercase unique first-seen list of stripped `FR-N`/`NC-N` refs, and is exactly `[]` when no refs were stripped.
- [ ] AC-06: Unit tests prove an invented workstream ref with an empty universe is stripped and recorded; a legitimate ref present in `commits` or `referenced` is preserved and receives the existing status behavior; an invented `hotspots` ref is stripped and recorded; lowercase model refs reconcile case-insensitively.
- [ ] AC-07: Unit tests prove a status-only ID present in `fr_statuses` but absent from `commits`/`referenced`, `churn`, `fr_changes`, and `fragments` is stripped before `attach_statuses` and receives no `[Status: ...]` or `[no FR status]` tag.
- [ ] AC-08: `TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions` is deleted; any orphan-hash assertion it uniquely carried is covered by a deterministic `finalize_recap` unit test; `TestRecapDispositionAxis::test_rejected_status_surfaces_verbatim` remains live.
- [ ] AC-09: `python scripts/req_coverage.py --detail` is run after the test move, and the FR records the before/after REQ-YG-531 coverage count separately from runtime live-witness status.
- [ ] AC-10: No changes are made to `examples/demos/recap/graph.yaml`, `examples/demos/recap/prompts/recap.yaml`, any `yamlgraph/` module, CI workflows, pytest configuration, provider/model settings, or graph-level verification/guard configuration.
- [ ] AC-11: `examples/demos/recap/demo-output.log` is regenerated for the changed demo surface and shows the final recap has no nonempty `unverified_refs` on the real run.
- [ ] AC-12: The targeted recap unit tests, `python scripts/req_coverage.py --detail`, and `pytest tests/unit/ -q --no-cov -m "not slow"` pass; a changelog fragment with `req: REQ-YG-531`, FR implementation notes, and a diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-3 are folded into FR-930. | GATE |
| C-2 | `fr_statuses` must not be part of the allowed universe for deciding whether a model-authored FR/NC token is verified; using it to rescue a prompt-invisible token is forbidden. | GATE |
| C-3 | Reconciliation must run before `attach_statuses`; a stripped token must never receive `[Status: ...]` or `[no FR status]`. | GATE |
| C-4 | No `graph.yaml` or `prompts/*.yaml` edit is authorized by this judgement. If such an edit becomes necessary, stop and re-enter graph authoring through the governed route. | GATE |
| C-5 | No CI, pytest-default, provider/model, or FR-923 latency-lane change is authorized by this FR. | GATE |
| C-6 | If preserving existing status-join behavior for verified IDs conflicts with the reconciler, stop and return to judgement; do not silently weaken FR-703/REQ-YG-535. | GATE |

Authority granted: after the required revisions are folded into FR-930, the enforcer may implement deterministic FR/NC reference reconciliation in the recap finalizer, replace the single live hallucination witness with direct unit witnesses, and update only the frozen supporting artifacts listed above.
