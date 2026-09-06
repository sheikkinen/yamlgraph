# Judgement: FR-1001 `yamlgraph-outsider` standalone demo repository

**Verdict:** APPROVED WITH REVISIONS — the standalone contrib/example remains a sound direction, but authority activates only after the FR stops treating the sample configuration's failed semantic calibration as success, restores the frozen `NO/NO/NO/YES` behavior gate, and folds the unplanned raw-reading capture into the contract.

**Prior art:** [FR-1001-yamlgraph-outsider-demo-repo.md](FR-1001-yamlgraph-outsider-demo-repo.md) — the subject; its `**Prior art:**` line dispositions FR-995, FR-865, FR-998, FR-1004. Third judgement (2026-09-06), after `scripts/review.sh` #603 P1: restores the frozen AC-13 gate, rejects the xfail oracle, folds raw-reading capture. Supersedes the two 2026-09-05 judgements of this FR. Operator merge decision recorded in the FR: ship with AC-13 openly NOT MET.

**Reviewed against:** `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.md`; the prior `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.judgement.md`; `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md` (application-layer and `projects/` versus `examples/` doctrine); `docs/2026-09-05-research-plan-cap-journey-census.md` sections 12–13; `docs/spikes/outsider-llm-2026-09-05/out/positive-claude-sonnet-4-5-20260905T080348Z.md`; `docs/spikes/outsider-llm-2026-09-05/out/positive-claude-sonnet-4-5-20260905T080409Z.md`; `docs/spikes/outsider-llm-2026-09-05/out/pr-591-claude-sonnet-4-5-20260905T080437Z.md`; `docs/spikes/outsider-llm-2026-09-05/out/plain-591-claude-sonnet-4-5-20260905T080503Z.md`; `docs/spikes/outsider-llm-2026-09-05/out/pr-591-v2-claude-sonnet-4-5-20260905T080533Z.md`; `docs/spikes/outsider-llm-2026-09-05/out/592-claude-sonnet-4-5-20260905T080708Z.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-995-outsider-reader.judgement.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-1004-retire-outsider-ledger.md`; and `feature-requests/FR-1004-retire-outsider-ledger.judgement.md`. The external repository implementation, mutable GitHub comments, and the author's chat narrative were not consumed.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | One public demo repository plus one discovery link is a bounded response to the stated first event. Framework changes, ramp installation, automation, and merge authority remain excluded (`FR-1001:8,12-22,46-63,83-84`). A plain Python program would not demonstrate the named YAMLGraph use case. |
| Consistency | The transport, three-layer ownership, typed boundary, reducer, and manual comment flow agree across Summary and Proposed Solution (`FR-1001:12-22,46-63`). The remaining contradiction is explicit and repairable: Ideal Result still requires `NO/NO/NO/YES` twice, while amended AC-13 calls `REJECTED/NO/YES/NO` acceptable (`FR-1001:40-42,81,106`). |
| Measurability | Prerequisites, subprocess argument lists, graph/report dual success, typed normalization, provenance, posting, and repository boundaries have direct commands or assertions (`FR-1001:67-80,82-84`). AC-13 is mechanically executable, but its amended oracle measures preservation of the observed defect rather than the stated result; R-1 replaces that oracle. |
| Feasibility | The provider-API spike proves the Python → `llm` → Python topology and records stable API execution (`research plan:629-694`; six spike reports). The current Haiku sample did not prove the required discrimination, but that is a calibration failure inside an otherwise feasible implementation, not an architectural impossibility (`FR-1001:90-113`). |
| Architecture alignment | The wrapper owns presentation, the graph owns orchestration, and Python tools own GitHub/file side effects (`FR-1001:47-48`), matching the repository's three-layer application pattern (`ARCHITECTURE.md:25-57`). The separate Git root and committed authoring brief preserve the graph-authoring and workspace boundaries (`FR-1001:46,67-68`; authoring brief:1-40). |
| Single responsibility | Repository packaging, fixtures, evidence, README, and the adapter link all serve one event: obtaining an advisory outsider reading before review (`FR-1001:8,12-22,46-63`). No orthogonal framework or enforcement concern is bundled. |
| Strategic classification | **Contrib/example.** The proposal packages one demonstrated workflow using existing YAMLGraph abstractions and local calibration. It is not a framework primitive; FR-998 separately owns the provider structured-output boundary (`FR-1001:9-10,46-63`; `FR-998:8-18`). |
| Testability | Failing tests derive directly for every deterministic seam and for the live semantic gate (`FR-1001:67-84`). A strict xfail of the desired behavior is the inverse of such a witness: it makes the known failure green and makes future success red (`FR-1001:81,106`). |

The research requirement is satisfied in substance. The cited record preserves the disagreement between a discriminating but flickering Copilot route and a stable but over-flagging provider route, and it reads the raw reports rather than relying on aggregate counts (`FR-1001:9,30-38`; `research plan:629-694`). Prior art is dispositioned: FR-995 supplies the reader contract, FR-998 owns framework normalization, FR-865 owns distribution, and FR-1004 removes the ledger rather than creating one here (`FR-1001:10,116-131`).

The failure record is also useful and must remain. Both live passes agreed, schema rejection was preserved, and the surprising inversions are concrete: the pre-gloss rewrite became YES while the intended positive became NO (`FR-1001:106`). That evidence invalidates the current success claim; it does not invalidate the problem or the three-node design.

## Required revisions

### R-1: Restore the semantic calibration gate

Replace amended AC-13 with the frozen behavior contract from the prior judgement: on the exact tested sample configuration, two complete live passes over `pr-591`, `plain-591`, `pr-591-v2`, and `positive` must each finish without schema rejection and derive `NO/NO/NO/YES`, in that order. Commit all eight raw readings and replay them through deterministic tests that assert the same sequence.

Delete the strict-xfail clause. `REJECTED/NO/YES/NO` is the recorded failed attempt, not an acceptable product oracle: `pr-591-v2` is a false positive against the pre-written expectation, `positive` is a false negative, and rejection is not a verdict. A test that fails when the desired sequence starts passing violates both the Ideal Result and the repository's fail-closed/TDD doctrine (`FR-1001:40-42,81,106`; `.github/copilot-instructions.md:181-193`).

Preserve the existing eight readings unchanged as historical evidence. A corrective run must use new evidence filenames carrying the new run timestamps and source commit; it must not overwrite or relabel the failed readings.

### R-2: Make status and public claims tell the same truth as the evidence

Change the FR Status and implementation table so AC-13 is **NOT MET** until R-1 passes. Remove “P1 resolved,” “met as amended,” and every statement that the current implementation satisfies the live calibration contract (`FR-1001:5,106`).

Keep the Ideal Result and Value Statement unchanged: the demo is valuable only if it separates descriptions that stand alone from those that do not (`FR-1001:24-27,40-42`). Until AC-13 passes, the README and implementation record must describe the tested sample as an experimental configuration with a recorded failed calibration, not as a validated sample. Once it passes, link the new eight-run evidence set and source commit.

### R-3: Forbid calibration by changing the question

The correction may change only the already authorized external sample configuration, graph/prompt/tool behavior, and their focused tests within D-2 through D-5. It must not revise the four fixture bodies, their pre-written `NO/NO/NO/YES` expectations, the `<= 2` retained-item threshold, the four hedge markers, or the rule that malformed/over-cap output fails closed. It must not turn a rejected reading into a verdict or add a fallback that substitutes a plausible report.

If the chosen provider/model cannot satisfy the unchanged fixtures twice, select and record a different human-approved sample configuration under the existing R-5 spend gate; do not weaken the fixtures to fit the model. Prompt or graph edits remain subject to the existing authoring route.

### R-4: Fold raw-reading capture into the evidence contract

Move `OUTSIDER_DUMP_READING` from the implementation deviation into Proposed Solution 6 and the acceptance criteria (`FR-1001:61,81,113`). Freeze it as an evidence-only, opt-in interface:

1. absent in ordinary wrapper/comment runs and producing no extra artifact by default;
2. enabled only with an explicit destination selected by the live-test harness;
3. writing the exact model payload before the stricter boundary so rejected readings remain inspectable;
4. never changing validation, verdict, report, comment, or process-success semantics;
5. surfacing a capture-write failure rather than silently losing required evidence; and
6. covered for valid, rejected, disabled, and write-failure cases.

This is necessary for AC-13's rejected-output evidence but is not authority for general tracing, telemetry, or a second run ledger.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Public MIT repository `sheikkinen/yamlgraph-outsider`, maintained as a sibling clone with its own Git root |
| D-2 | External repo: `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, and executable `yamlgraph-outsider` |
| D-3 | External repo: `.github/skills/outsider-view/{SKILL.md,doctrine.md}` with the provider-API, advisory contract |
| D-4 | External repo: the four frozen fixtures and expectations, immutable failed evidence, a new passing eight-run evidence set, focused reducer/tool/wrapper/live tests, and `docs/evidence/` |
| D-5 | External repo: `README.md`, `LICENSE`, `.env.sample`, `.gitignore`, and `pyproject.toml` with tested minimum YAMLGraph and test commands |
| D-6 | This repo: `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md` and verified `tmp/draft-authoring-report.md` |
| D-7 | This repo: one non-Copilot-route line in `.github/skills/outsider-view/adapters/README.md` |
| D-8 | This repo: revised FR, final human-reviewed judgement/status record, changelog fragment, and one `docs/diary/` reflection |

Not authorized: changes to the four fixture inputs or their expected `NO/NO/NO/YES` labels; a relaxed retained-item threshold or hedge rule; xfail/skip treatment of the live semantic gate; success-shaped fallback after rejection; YAMLGraph runtime, provider factory, or framework normalization changes; changes to this repository's existing outsider graph, prompt, wrapper, skill, doctrine, fixtures, or ledger beyond the single adapter-README link; a demo ledger or general telemetry facility; edits to either historical spike tree or the existing failed live evidence; `ramp/manifest.yaml`; GitHub Actions, hooks, automatic invocation/comments, blocking status, approval, merge behavior, or other enforcement; judge/review/graph-authoring doctrine changes; a new node type; or packaging the demo as a Python distribution.

## Revised acceptance criteria

- [ ] AC-01: The FR cites `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `scripts/author.sh` produces the declared external graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the report records successful lint and a narrow smoke, or the exact credential blocker.
- [ ] AC-02: `gh repo view sheikkinen/yamlgraph-outsider --json visibility,licenseInfo` reports public visibility and an MIT license; the local target is a separate Git root outside this repository; `git check-ignore` proves `.env` and `out/` are ignored and `.env.sample` is tracked.
- [ ] AC-03: Parsed `graph.yaml` contains no configured provider or model at defaults or node level; the entry script accepts no `--provider` or `--model` flag and contains no hard-coded model identifier.
- [ ] AC-04: `.env.sample` contains one active sample provider, an empty key, and one explicit sample model on separate lines. README calls these the tested sample selection, documents alternatives one variable per line, and does not call the selection validated until AC-13 passes.
- [ ] AC-05: Tests cover all four provenance cases. Changing `.env` changes recorded configured values without editing graph, prompt, tool, or wrapper; omitted values are recorded only as `framework-default`.
- [ ] AC-06: The wrapper chooses `out/<label>-<timestamp>.md` before invocation and passes it as `report_path`; no LLM result is needed to construct the path.
- [ ] AC-07: Standalone doctrine and `SKILL.md` contain no Copilot-CLI, pinned-`gpt-5.6-sol`, or ledger claim; they preserve title-and-body-only model input, advisory status, fail-closed handling, three-reader ownership, four top-level sections, one run per PR, and `./yamlgraph-outsider` invocation.
- [ ] AC-08: Pydantic tests exercise every accepted and rejected normalization form, every required field and cap, quote/question parsing, every reducer rule and near miss, reason precedence, stable order, no loss or duplication, retained-only counts, and the three named reducer cases.
- [ ] AC-09: The wrapper contains exactly one `yamlgraph graph run`, no `gh`, and one operational `git` call. Controlled executables prove distinct missing-prerequisite and missing-`.env` failures; the `--var` set is exactly `pr,repo,input_path,comment,report_path`; invalid comment values and `--input --comment` fail before graph invocation.
- [ ] AC-10: Wrapper success requires graph status zero and complete report validation. Tests prove graph status non-zero is preserved despite a valid report, and graph status zero with an absent or invalid report fails.
- [ ] AC-11: With a fake `gh`, `fetch_pr` uses the exact argument-list contract and returns exactly `# <title>\n\n<body>`; `--input` never calls `gh`; `finalize` posts only for strict `comment=true` with a PR source. A failed post returns non-zero and leaves the valid local report without claiming a successful comment.
- [ ] AC-12: Malformed structured output, missing API key, missing `gh`, invalid PR/repository, fetch failure, graph failure, absent report, invalid report, comment failure, and raw-capture write failure follow their declared artifact semantics and never produce wrapper success. Tests prove `OUTSIDER_DUMP_READING` is disabled by default, captures exact valid and rejected payloads when enabled by the live harness, and never changes validation or verdict semantics.
- [ ] AC-13: After the recorded human spend decision, `pytest -m live` runs the four unchanged fixtures twice on the exact `.env.sample` configuration. Both passes complete without schema rejection and derive `NO/NO/NO/YES`. Expectations predate execution; all eight new raw readings are committed with timestamps and source commit; deterministic replay derives the same sequence. Any rejection or different verdict fails normally—no skip or xfail.
- [ ] AC-14: README's pre-publication report is committed under `docs/evidence/` and linked with input SHA-256, item count, configured provider/model, timestamp, and source commit.
- [ ] AC-15: After the public-write decision and AC-13, one explicit `--comment` run on the approved public PR outside `sheikkinen/yamlgraph` leaves the comment on that PR; its URL and evidence report are recorded in the FR; no credential or private PR material is committed.
- [ ] AC-16: `pyproject.toml` declares the exact deterministic and live test commands and tested minimum `yamlgraph`; focused tests pass in a clean environment; the README clone/install/configure/run path succeeds.
- [ ] AC-17: Research and Prior art retain the `is_this_a_graph` answer, substantive solution-class disposition, committed dependencies, and the failed calibration record. FR Status and implementation table mark AC-13 unmet until its passing evidence exists.
- [ ] AC-18: This repository's diff is limited to the authoring brief, one adapter-README line, FR plus final judgement/status record, changelog fragment, and diary entry; spike trees, ramp manifest, existing outsider implementation, and ledger are byte-unchanged.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 and AC-01 through AC-18 into FR-1001 before corrective implementation or merge; the current amended AC-13 grants no authority. | GATE |
| C-2 | Preserve the existing failed eight-run evidence unchanged and label it as a failed calibration; produce a distinct new evidence set for any corrective run. | GATE |
| C-3 | Do not revise fixtures, expectations, threshold, hedge markers, or fail-closed behavior to make the sample pass. | GATE |
| C-4 | Route every external graph or prompt edit through the committed FR-1001 brief and `scripts/author.sh`; verify the report artifact, lint, and smoke rather than an exit code. | GATE |
| C-5 | Parse and validate before deriving, rendering, posting, or reporting success; a rejected model payload is evidence, never a verdict. | GATE |
| C-6 | Obtain and record human approval before any additional provider spend or public comment, including a changed provider/model selection. | GATE |
| C-7 | Keep raw capture opt-in, evidence-only, fail-visible, and semantically inert; do not grow it into a ledger or telemetry subsystem. | GATE |
| C-8 | Do not describe the current sample configuration as validated or AC-13 as met until the exact two-pass gate succeeds normally. | GATE |
| C-9 | Remain within D-1 through D-8 and the explicit not-authorized boundary; framework, automation, enforcement, and historical-artifact changes require separate judged authority. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, correct and re-evidence only the existing standalone contrib/example within D-1 through D-8; the current `REJECTED/NO/YES/NO` implementation is not authorized as satisfying the demo contract.
