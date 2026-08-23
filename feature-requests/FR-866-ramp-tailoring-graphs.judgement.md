# Judgement: FR-866 Target-Tailoring Graph Suite -- Doctrine, RTM, Incidents

**Verdict:** APPROVED WITH REVISIONS -- the graph-shaped child scope is sound and satisfies the parent split in principle, but authority activates only after draft outputs, authoring records, doctrine-subset semantics, `fr_atlas` reuse, and target-independent tests are made mechanically exact.

**Reviewed against:** `feature-requests/FR-866-ramp-tailoring-graphs.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-748-fr-atlas-onboarding-summary.md`; `examples/demos/fr-atlas/graph.yaml`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`; `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`; `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`. No author chat narrative was consumed.

**Prior art:** dispositioned below — FR-864 (parent SPLIT, controlling), FR-748/`fr_atlas` (corpus map + merge + reconciliation precedent; reuse boundary is R-5), FR-863 (the incident corpus `ramp_incidents` reads), FR-865/867/868 (sibling children, non-overlap). FR-207 marked non-overlap: it contains no LLM step. No REJECTED prior art occupies this territory. FR-866 is the subject FR.

## What is sound

FR-866 is the correct child-B extraction from the parent SPLIT. The parent judgement required a target-tailoring graph child for `ramp_doctrine`, `ramp_rtm`, and `ramp_incidents`, with graph paths, prompt paths, draft paths, schemas, validation, smoke inputs, governed authoring evidence, and human review before landing (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:29-33`, `69-77`). FR-866 names exactly those three graphs and excludes the mechanical installer, target application, and `scripture-dev` retirement surfaces handled by siblings (`feature-requests/FR-866-ramp-tailoring-graphs.md:9-23`, `25-31`).

The problem is real and supported by the cited record. FR-866 identifies three target-specific artifacts that copying cannot honestly supply: doctrine, requirements, and incidents (`feature-requests/FR-866-ramp-tailoring-graphs.md:39-54`). FR-863 records the four `deviant-daily` production failures this graph suite is supposed to repatriate (`feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md:8-15`, `44-80`, `82-112`), and the diary record states the target's incident memory is currently filed in yamlgraph rather than in the repo that suffered it (`docs/diary/diary-2026-08-23-process-transfers-by-practice.md:53-71`).

The architecture choice is aligned with YAMLGraph rather than framework cosplay. The local doctrine says graph artifacts must go through the graph-authoring route and be validated with lint/smoke evidence (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:76-107`), while the `is_this_a_graph` question says N-items-times-LLM-call work should use map/reduce graph shapes before scripts or subagents (`.github/copilot-instructions.md:119-133`). FR-866's shared contract is deterministic inventory, map fan-out, merge reconciliation, and draft output (`feature-requests/FR-866-ramp-tailoring-graphs.md:67-82`), which matches the `fr_atlas` precedent's collect -> map -> assemble -> merge -> finalize -> render structure (`examples/demos/fr-atlas/graph.yaml:52-122`) and its count-in == count-out design (`feature-requests/FR-748-fr-atlas-onboarding-summary.md:62-80`).

The prior-art disposition is mostly sufficient. FR-866 reuses FR-748 as the direct precedent rather than duplicating its shape (`feature-requests/FR-866-ramp-tailoring-graphs.md:14-18`), distinguishes FR-207 as distribution rather than derivation (`feature-requests/FR-866-ramp-tailoring-graphs.md:19-20`), separates FR-865's mechanical copy surface (`feature-requests/FR-866-ramp-tailoring-graphs.md:21-22`), and identifies FR-863 as the incident source corpus (`feature-requests/FR-866-ramp-tailoring-graphs.md:22-23`). Strategic classification: **Contrib/example governance graph suite**, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Make every graph write only exact draft paths under `tmp/ramp/`

Replace all destination wording that names final target artifacts with exact draft artifact paths. FR-866's shared runtime says every graph outputs `tmp/ramp/<name>-draft.md` and `tmp/ramp/<name>-draft.json` (`feature-requests/FR-866-ramp-tailoring-graphs.md:69-80`), but the per-graph sections also say `ramp_doctrine` renders an `AGENTS.md` draft and `ramp_incidents` renders `docs/incidents.md` (`feature-requests/FR-866-ramp-tailoring-graphs.md:89-92`, `108-111`). The first event also names `tmp/ramp/doctrine-draft.md`, which does not mechanically identify whether `<name>` is `doctrine` or `ramp_doctrine` (`feature-requests/FR-866-ramp-tailoring-graphs.md:9-12`).

Fold this by naming the six exact output files in the FR: `tmp/ramp/doctrine-draft.md`, `tmp/ramp/doctrine-draft.json`, `tmp/ramp/rtm-draft.md`, `tmp/ramp/rtm-draft.json`, `tmp/ramp/incidents-draft.md`, and `tmp/ramp/incidents-draft.json`. State that generated markdown may be shaped for later human copying into `AGENTS.md`, `capabilities/*.yaml`/RTM docs, or `docs/incidents.md`, but the graphs themselves must not write those final paths.

### R-2: Replace generic authoring-report language with per-graph closed records

Specify one committed task brief and one retained authoring report per graph. The graph-authoring doctrine requires FR-bound task briefs under `feature-requests/authoring-briefs/` and says the adapter returns a parseable `tmp/draft-authoring-report.md` (`.github/skills/graph-authoring/doctrine.md:19-30`, `69-74`, `91-107`). FR-866 currently says "reports retained in `feature-requests/authoring-briefs/` and the enforcement record" without naming the briefs, how three overwritten `tmp/draft-authoring-report.md` files survive, or what proves which report belongs to which graph (`feature-requests/FR-866-ramp-tailoring-graphs.md:119-122`).

Fold this by requiring briefs named `feature-requests/authoring-briefs/fr-866-ramp-doctrine-brief.md`, `feature-requests/authoring-briefs/fr-866-ramp-rtm-brief.md`, and `feature-requests/authoring-briefs/fr-866-ramp-incidents-brief.md`, plus uniquely retained reports or FR implementation-evidence subsections for each adapter run. Each record must name the graph path, prompt paths, optional node/tool paths, precedent used, lint command, smoke command, and whether validation passed or was blocked.

### R-3: Define doctrine tailoring for traps, cures, and questions, not only traps

Align the proposed schema, rendered markdown, and acceptance criteria. The proposed `ramp_doctrine` map covers this repo's Scripture traps, cures, and questions (`feature-requests/FR-866-ramp-tailoring-graphs.md:84-89`), but the merge/render and ACs mechanically constrain only the "trap list" (`feature-requests/FR-866-ramp-tailoring-graphs.md:89-92`, `129-134`). That leaves cures/questions free to be copied wholesale, invented, or carry foreign witness citations while the trap-only test passes.

Fold this by stating that every retained doctrine entry of any kind must be selected from the source doctrine by stable id, must carry target evidence or an explicit `no_target_evidence` rejection/tailoring reason, and must not invent new ids. Revise the foreign-citation assertion to cover the entire generated doctrine draft, including traps, cures, questions, prayers/process text, and local-incident placeholders.

### R-4: Make `ramp_rtm` honest-failure behavior mechanically testable

Resolve the tension between the requirement-candidate floor and the no-padding rule. AC-08 requires the `deviant-daily` smoke to emit at least ten candidates (`feature-requests/FR-866-ramp-tailoring-graphs.md:135-137`), while the risks section says fewer than ten defensible requirements should be reported honestly rather than padded (`feature-requests/FR-866-ramp-tailoring-graphs.md:165-168`). Both instincts are right, but the current AC can pressure the graph into inventing requirements to pass.

Fold this by making the graph's contract two-valued: either it emits at least ten cited `status: proposed` entries for the target, or it emits an explicit insufficiency finding with the test-file count, gap list, and no padded entries. The smoke expectation for `deviant-daily` may remain "expected >= 10", but the acceptance test must fail on uncited/padded entries rather than force the model to satisfy a quota.

### R-5: Decide the `fr_atlas` reuse boundary before graph authoring starts

Move the `ramp_incidents` reuse decision from "before implementation" into the FR itself. The FR says `ramp_incidents` is closest to `fr_atlas` and must justify itself against it rather than re-implement it (`feature-requests/FR-866-ramp-tailoring-graphs.md:14-18`), but later defers the decision to implementation time (`feature-requests/FR-866-ramp-tailoring-graphs.md:108-113`, `147-151`). Scope should be frozen before authoring because graph-authoring inputs are closed by task briefs, not hidden implementation judgement (`.github/skills/graph-authoring/doctrine.md:19-30`).

Fold this by adding one design decision before enforcement: either `ramp_incidents` reuses/adapts named `fr_atlas` collector/reconciliation/render helpers, or it copies only the graph pattern because the corpus and schema differ. If reuse is chosen, name the exact source files/functions. If not, state the one-sentence reason and add an acceptance test that the new merge still enforces count-in == count-out like the precedent.

### R-6: Separate committed fixture tests from local sibling-repo smoke

Remove any requirement that CI or unit tests depend on `/Users/sheikki/Documents/src/deviant-daily` existing. FR-866's first event and several ACs are target-specific (`feature-requests/FR-866-ramp-tailoring-graphs.md:9-12`, `129-146`), but the parent judgement requires preserving repo boundaries in cross-repo work (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:87-89`), and local doctrine warns that workspace visibility is not ownership (`.github/copilot-instructions.md:63-65`, `109-110`, `163-163`).

Fold this by requiring committed fixture target repos/corpora for automated tests, while recording the real `deviant-daily` smoke as local enforcement evidence when the sibling repo is present. The graph CLI may accept an absolute `target`, but tests must not hard-code the operator's machine path. Any live sibling-repo smoke must read only and write only yamlgraph `tmp/ramp/` drafts.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-866-ramp-tailoring-graphs.md` folding R-1 through R-6 |
| D-2 | `examples/demos/ramp_doctrine/graph.yaml`, prompts, optional nodes/tools, committed task brief, retained authoring report, and tests |
| D-3 | `examples/demos/ramp_rtm/graph.yaml`, prompts, optional nodes/tools, committed task brief, retained authoring report, and tests |
| D-4 | `examples/demos/ramp_incidents/graph.yaml`, prompts, optional nodes/tools, committed task brief, retained authoring report, and tests |
| D-5 | Draft outputs only under `tmp/ramp/` during smoke/evidence runs |
| D-6 | FR implementation-status update with raw-output-read evidence and any deviations |

Not authorized: modifying `scripts/ramp.sh` or ramp installer assets; applying any generated draft to `sheikkinen/deviant-daily`; modifying any sibling repository; archiving, deleting, renaming, transferring, or changing settings on `scripture-dev`; changing yamlgraph runtime primitives, node types, providers, graph-authoring/judge/review doctrine, hooks, CI, spike detector, or unenforced-repo warning behavior; writing generated governance artifacts outside `tmp/ramp/`; committing target-repo archives, secrets, token-bearing logs, or ignored generated output trees.

## Revised acceptance criteria

- [ ] AC-01: FR-866 is revised to define exact draft paths, per-graph authoring records, doctrine-entry semantics, `ramp_rtm` honest-failure semantics, the `fr_atlas` reuse decision, and fixture-vs-live-smoke boundaries from R-1 through R-6.
- [ ] AC-02: Each graph is authored through the governed graph-authoring route with a committed task brief and a uniquely retained report naming artifacts, precedent, validation commands, repairs, and blocked validation if any.
- [ ] AC-03: All three graphs pass `yamlgraph graph lint` against their final committed `graph.yaml` files.
- [ ] AC-04: Each graph declares Pydantic output schemas for its map and final JSON output; tests validate representative fixture outputs against those schemas.
- [ ] AC-05: Draft paths are exactly `tmp/ramp/doctrine-draft.{md,json}`, `tmp/ramp/rtm-draft.{md,json}`, and `tmp/ramp/incidents-draft.{md,json}`; tests assert no graph/tool writes outside `tmp/ramp/`.
- [ ] AC-06: Source scans assert no graph, prompt, or tool invokes `git commit`, `git push`, `gh`, or writes into a target repository.
- [ ] AC-07: `ramp_doctrine` fixture tests prove every retained doctrine entry is selected from the source doctrine by stable id, no new doctrine ids are invented, and every retained entry has target evidence or an explicit rejection/tailoring reason.
- [ ] AC-08: `ramp_doctrine` smoke on `deviant-daily`, when that target is available, emits a strict subset of the source doctrine, contains zero foreign witness citations matching `NC-\d+` or `FR-\d+`, and names at least one target-specific boundary.
- [ ] AC-09: `ramp_rtm` fixture tests prove every emitted requirement has `status: proposed`, cites at least one existing test by name, and rejects or flags any cited test name absent from the target inventory.
- [ ] AC-10: `ramp_rtm` reports count-in == count-out over test files, lists tests witnessing no requirement, and either emits at least ten cited candidates for the smoke target or an explicit insufficiency finding without padding.
- [ ] AC-11: `ramp_incidents` fixture tests prove document classification emits either an incident object with `date`, `defect`, `root_cause`, `cure`, `witness`, and resolvable `source_ref`, or `not_an_incident`.
- [ ] AC-12: `ramp_incidents` smoke on `deviant-daily`, when that target is available, emits the four 2026-08-23 failures named by FR-866: vision payload ceiling, DA title cap, degenerate corpus key, and guard-flag hedging.
- [ ] AC-13: `ramp_incidents` count-in == count-out covers every scanned FR/diary document, with non-incidents explicitly classified and no silently dropped files.
- [ ] AC-14: The FR records the `fr_atlas` reuse decision before authoring; implementation follows that decision or records a judged deviation before changing course.
- [ ] AC-15: Before merge tuning for each graph, the FR records at least three raw map-node outputs read end-to-end, each with a concrete surprising detail a generated dump could not supply.
- [ ] AC-16: Tests are added before implementation for the graph behavior above, with RED/GREEN evidence recorded in the FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-866-ramp-tailoring-graphs.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any `graph.yaml` or `prompts/*.yaml` creation/material modification must use the governed graph-authoring route and retain the per-graph authoring record. | GATE |
| C-4 | Generated governance artifacts are drafts only; no graph/tool may write outside `tmp/ramp/` or modify a target repository. | GATE |
| C-5 | Automated tests must use committed fixtures and must not require a sibling repo or the operator's absolute filesystem path. | GATE |
| C-6 | No yamlgraph framework primitive, hook, CI, judge/review doctrine, graph-authoring doctrine, spike-detector, or unenforced-repo-warning behavior may change under this FR. | GATE |
| C-7 | `ramp_rtm` and `ramp_incidents` must fail closed on missing/ambiguous target inventories, unresolved source refs, count mismatch, or schema-invalid LLM output. | GATE |
| C-8 | Real `deviant-daily` smoke runs, if performed, must be read-only with respect to the target and must preserve separate git boundaries. | GATE |

Authority granted: after the required revisions are folded, enforcement may author the three target-tailoring graph demos and their prompts/tools/tests through the governed authoring route, producing review-only drafts under `tmp/ramp/`.
