# Judgement: FR-1162 Upgrade the sole-route adapter model pins to gpt-6.1-sol

**Verdict:** REJECTED — returned to plan without implementation authority: the mandatory committed research record is absent, and the acceptance criteria do not prove the stated four-route result.

**Prior art:** FR-1162-adapter-model-pin-gpt61sol.md is the FR under judgement, not prior art.
**Reviewed against:** Committed `HEAD` versions of `feature-requests/FR-1162-adapter-model-pin-gpt61sol.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (authoring, research, enforcement, TDD, submission and reflection clauses); `feature-requests/FR-931-judge-review-model-pin-gpt56sol.md`; `feature-requests/FR-931-judge-review-model-pin-gpt56sol.judgement.md`; `feature-requests/FR-995-outsider-reader.md`; the status and relevant route/model passages of `feature-requests/FR-765-graph-authoring-workflow-skill.md`, `feature-requests/FR-767-graph-authoring-sole-route.md`, and `feature-requests/FR-960-claude-judge-variant.md`; `tests/unit/test_fr931_sole_route_model_pin.py`; model-related assertions in `tests/unit/test_fr960_claude_judge_variant.py`, `tests/unit/test_fr1049_opencode_judge_variant.py`, and `tests/unit/test_fr995_outsider_wrapper.py`; `.github/skills/graph-authoring/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/graph.yaml`; model-pin passages of `.github/skills/review-pr/adapters/graph.yaml`, `.github/skills/outsider-view/adapters/graph.yaml`, and `scripts/outsider.sh`. Source line references below refer to these committed versions. No author transcript, working notes, external availability probe, or new judge execution was used as evidence.

## What is sound

The strongest case for rejection of the solution itself is that a model migration could become a configuration framework or an indiscriminate rewrite of historic evidence. This proposal avoids both: it retains literal node-local pins, updates the outsider observation marker, and excludes historical records and the Claude pin (FR-1162:50-67). A bounded replacement of unavailable pins is a credible maintenance concern, although the probe table alone does not establish that every old-model failure is caused by retirement: `Execution failed` is not a model-unavailable diagnostic (FR-1162:28-40).

| Criterion | Finding and evidence |
|---|---|
| 1. Scope | Four Copilot-CLI node pins, one matching wrapper marker, existing assertions and current-contract documentation are a coherent minimal migration (FR-1162:21-24, 50-64). AC-01 must name that surface rather than every adapter/wrapper on the branch (:71-72). |
| 2. Consistency | Keeping authoring outside the *twin-route invariant* is compatible with updating its pin, but that distinction needs to be explicit (:14-15, 50-55). The implementation record also says "Not started" (:80-82), although the committed four adapters and wrapper already contain the new value. |
| 3. Measurability | RED/GREEN history and CI success are measurable (:73-78). Absence of two old strings does not prove presence of the intended pin, and a judgement of this FR does not prove an expected substantive outcome (:71-77). |
| 4. Feasibility | The existing YAML node flags and wrapper marker already support the proposed literal, with no new dependency or abstraction (judge adapter:24-32; authoring adapter:18-25; outsider wrapper:24). The authoring bootstrap and live evidence remain unspecified. |
| 5. Architecture alignment | Literal pins and preservation of non-Copilot backends follow the existing contract (FR-931:88-110; judge adapter:39-65). Governed graph edits still require the authoring route and artifact evidence; a model-only edit does not establish an exemption (project instructions:13; FR-767:341). |
| 6. Single responsibility | One maintenance concern across its four consumers; no SPLIT is warranted. Shared configuration, selection logic or backend changes would be separate concerns (FR-1162:50-67). |
| 7. Strategic classification | Pattern documentation/configuration maintenance using existing abstractions, not a framework primitive or a new example. The proposal's four consumers do not justify introducing a new abstraction (FR-1162:37-51). |
| 8. Testability | Existing PyYAML/pytest witnesses support direct assertion changes, without missing implementation imports (FR-931 test:13-23, 26-43, 66-71). That witness covers judge/review only; authoring lacks the proposed exact-pin witness, and AC-03 omits the first consumer, review (FR-1162:7-8, 73-77). |

Prior-art dispositions are useful: FR-931 is an implemented literal-pin migration; FR-995 supplies the outsider adapter/marker contract; FR-765/767 establish the governed authoring route; FR-960 separates the Claude backend. The cited precedent also demonstrates that missing research is substantive, not clerical: FR-931:125-132 deliberately tests withholding authority from a research-less FR, and its judgement:15 documents the research substance required for its own approval.

## Required revisions

### R-1: Supply committed research and disposition alternatives

Add a `**Research:**` field pointing to a committed record or equivalent in-body alternatives table. Disposition four to six genuine solution classes, preserve disagreement, cite the relevant precedent, and answer `is_this_a_graph`. Distinguish the prior research for FR-931 from evidence that the present replacement is available and appropriate. Include the CLI version, dated commands and actual outputs for the availability claims; narrow the `gpt-5.5` claim unless its generic failure is diagnosed. The FR currently has neither the field nor a dispositioned alternatives record (FR-1162:3-87). Judge doctrine:118-130 explicitly denies authority on this basis; updating a pin does not waive it.

### R-2: Replace the negative-only criterion with exact scoped assertions

Name the four Copilot-CLI nodes and the outsider marker. Require each to equal `gpt-6.1-sol`, while preserving the existing judge/review equality witness and adding an authoring exact-pin assertion in an existing test module. Keep authoring outside the *two-route equality invariant*, not outside verification. Preserve `claude-opus-5` and `deepseek/deepseek-v4-pro`, backend selection, permissions, timeouts, prompts, state and edges. FR-1162:71-74 otherwise permits an unpinned or differently pinned authoring route; the existing FR-931 test:19-22 does not inspect it.

### R-3: Specify artifact-based validation for all changed routes

Retain the outsider live report, add the omitted real review run for this PR, and require a recorded authoring-route smoke and graph lint results. For judge model validation, use the known missing-research fixture already specified by FR-931:118-132 and require a no-authority verdict, not merely a verdict-shaped file. A judgement of FR-1162 may be recorded separately but is not a golden outcome. Record commands, code identity, artifact/log paths and substantive outcomes in the FR. Do not prescribe rerunning a judge inside an active judge execution.

### R-4: Resolve governed-authoring bootstrap and reconcile implementation status

State how the four governed graph edits are produced through the existing authoring route, with its draft report, lint and smoke evidence. If the route is unavailable, state the blocker and seek separately judged remediation rather than authorize direct graph edits or hook bypasses (project instructions:13). Replace "Not started" with an accurate record of already committed pin/assertion changes and their provenance: judge adapter:28, review adapter:23, outsider adapter:44, authoring adapter:23, outsider wrapper:24 and FR-931 test:23 already use the target literal. Cite actual RED/GREEN commits or explicitly record missing proof; do not fabricate historical RED evidence or rewrite it to satisfy AC-02.

### R-5: Record human gates and required maintenance artifacts

Add an explicit human-review gate for enforcement-infrastructure changes (judge doctrine:98-101), retain review as advisory, and enumerate a valid fix changelog fragment and one diary reflection with a `Seed:`. Historical entries remain unchanged; a new reflection is not a rewrite (project instructions:26-27, 204, 213-214). Surface this human decision explicitly: **Does the operator approve `gpt-6.1-sol` for these four routes, including its spend implications and the reviewed enforcement diff?** The directive recorded at FR-1162:5 selects the model but is not evidence that the eventual diff or this draft has received human review.

## Scope is frozen

This table bounds a revised proposal; rejection grants no implementation permission.

| Deliverable | Surface |
|---|---|
| D-1 | Four Copilot-CLI `cli_flags.model` literals in `.github/skills/{judge-fr,review-pr,outsider-view,graph-authoring}/adapters/graph.yaml` |
| D-2 | Matching `MODEL` literal in `scripts/outsider.sh`; no wrapper behavior change |
| D-3 | The four existing test modules named in FR-1162:54-57, including a focused authoring-pin witness in an existing module |
| D-4 | Current-pin statements in the precise documentation/registry surfaces named at FR-1162:60-64; no semantic doctrine changes |
| D-5 | FR implementation/validation record, committed research or in-body equivalent, and any required authoring brief/report evidence |
| D-6 | One `type: fix` changelog fragment and one new diary reflection with `Seed:` |

Not authorized: changing Claude/OpenCode pins or backend defaults; shared pin configuration; model-selection or fallback logic; dependency changes; prompt, permission, timeout, state or edge changes; hook/CI relaxation; edits to historical evidence; automatic promotion, approval or merge. Adjacent availability-monitoring work belongs in a separate FR.

## Revised acceptance criteria

These are requirements for a revised submission, not an authority grant.

- [ ] AC-01: A committed `**Research:**` reference resolves to substantive alternatives, precedent dispositions, preserved dissent and an `is_this_a_graph` answer; availability claims cite dated command/output evidence.
- [ ] AC-02: Parsed YAML assertions prove all four named Copilot-CLI nodes equal `gpt-6.1-sol`; the outsider wrapper marker equals the same literal. Exact-pin tests fail against the old values and pass against the new ones, with actual RED/GREEN commit references recorded.
- [ ] AC-03: Judge/review retain the FR-931 equality invariant; authoring receives a focused exact-pin assertion without extending that two-route invariant. Existing Claude/OpenCode pins and all non-model graph behavior remain unchanged.
- [ ] AC-04: The required authoring-route report identifies the governed graph edits and records lint results for all four graphs plus an actual smoke attempt/outcome. Any bootstrap blocker is resolved under existing doctrine, not bypassed.
- [ ] AC-05: An external, non-recursive judge validation on the known missing-research fixture produces a contract-valid no-authority judgement. Live review and outsider runs for this PR produce contract-valid reports; the FR cites their commands, code identity, logs, artifacts and outcomes.
- [ ] AC-06: The four existing affected unit modules pass; the unit suite passes in the CI-mirror container and CI, with exact commands/results and CI run references recorded.
- [ ] AC-07: The named current-contract documentation matches the target literal; historical evidence and model-pass-through fixtures remain unchanged. A valid fix fragment and a new diary reflection with `Seed:` exist.
- [ ] AC-08: The FR accurately records implementation status, provenance, decisions and deviations; a human has reviewed the enforcement diff and explicitly resolved the model/spend decision before authority can activate.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority is granted by this rejected draft. Commit the revised FR/research and obtain a fresh independent judgement before enforcement. | GATE |
| C-2 | A human must review the enforcement-infrastructure diff and resolve the explicit model/spend question; an agent must not infer that approval from this verdict. | GATE |
| C-3 | Preserve governed authoring and artifact-validation boundaries; no direct-edit exception, recursive judge execution, weakened report validator or exit-code-only success claim. | GATE |
| C-4 | Preserve the frozen non-model surfaces and disclose already completed work and missing historical proof rather than manufacturing compliance. | GATE |

Authority granted: none; this proposal is returned to plan, and completing the listed revisions alone does not activate implementation authority.
