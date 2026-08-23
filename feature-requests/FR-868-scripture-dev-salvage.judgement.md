# Judgement: FR-868 scripture-dev Salvage and Retirement

**Verdict:** APPROVED WITH REVISIONS -- the child-D salvage/retirement scope is the right split and the problem is real, but authority activates only after the source ref/artifact population, graph artifacts, lift destinations, validation tests, and human-approval boundary are made mechanically exact.

**Reviewed against:** `feature-requests/FR-868-scripture-dev-salvage.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `reference/getting-started.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md`; `feature-requests/FR-858-retire-committed-fr-board.md`; `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`. No author chat narrative was consumed.

**Prior art:** dispositioned below — FR-864 (parent SPLIT, controlling), FR-207 (the FR being closed out; its judgement is not reversed), FR-858 (retirement-FR precedent), FR-865 (lift destination, decoupled by R-3), FR-866/867 (non-overlap). No REJECTED prior art occupies this territory. FR-868 is the subject FR.

## What is sound

FR-868 is the correct child-D extraction from the parent SPLIT. The parent judgement required a separate child for "`scripture-dev` salvage and retirement" and barred `scripture-dev` state changes from the parent scope (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:35-39`, `57-68`). FR-868 confines itself to classification, possible lift into yamlgraph, FR-207 closeout, consumer checks, and archive approval (`feature-requests/FR-868-scripture-dev-salvage.md:24-30`, `83-90`), so this is one retirement workflow rather than another bundle.

The problem is real and supported by the cited record. FR-207's original goal was to extract the governance methodology into `sheikkinen/scripture-dev` (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:46-65`) using `scripture.yaml` plus `render.sh` parameterisation (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:108-142`). The cited diary explains why that mechanism decayed: `scripture-dev` shipped artifacts but did not consume the practice, while a practicing peer repo stayed current and contributed doctrine back (`docs/diary/diary-2026-08-23-process-transfers-by-practice.md:11-27`, `39-52`). FR-868 preserves that distinction by promising archive, not deletion, after salvage (`feature-requests/FR-868-scripture-dev-salvage.md:59-65`, `117-118`).

The proposed classification shape fits YAMLGraph doctrine. FR-868 describes a deterministic enumeration followed by a map over artifacts and a merge to `tmp/ramp/salvage-disposition.{md,json}` with count-in == count-out (`feature-requests/FR-868-scripture-dev-salvage.md:69-79`). That is the exact N-items-times-LLM-call map/reduce shape the local Scripture says should look for a graph before scripts or subagents (`.github/copilot-instructions.md:119-133`), and it aligns with YAMLGraph's documented map node and Python-tool separation (`reference/getting-started.md:84-101`; `ARCHITECTURE.md:55-69`).

The safety instincts are sound. The FR requires raw reading before lift decisions (`feature-requests/FR-868-scripture-dev-salvage.md:106-108`), keeps generated output in drafts with no commits (`feature-requests/FR-868-scripture-dev-salvage.md:77-81`), requires human approval before GitHub archive state changes (`feature-requests/FR-868-scripture-dev-salvage.md:90-90`, `115-118`), and includes a no-secrets lift criterion (`feature-requests/FR-868-scripture-dev-salvage.md:122-123`). Strategic classification: **Contrib/governance graph plus retirement workflow**, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Freeze the `scripture-dev` input ref and artifact population before authority activates

Replace the deferred source definition with an exact input closure. The parent judgement required child D to freeze the source ref and full artifact population count (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:35-39`, `69-77`), but FR-868 currently says the count is "determined by the run" and only records the SHA before the run (`feature-requests/FR-868-scripture-dev-salvage.md:71-72`, `96-99`). That lets implementation begin before the surface being judged is known.

Fold this by adding, before enforcement starts, the exact `scripture-dev` repository URL, commit SHA, enumeration command or API contract, and the resulting tracked-file count. If the file list is too long for the FR body, commit a manifest path such as `feature-requests/evidence/fr-868-scripture-dev-files.txt` or `.json` and cite it from the FR. The manifest must be the population that `salvage_classify` consumes; no unlisted files may be silently added or dropped.

### R-2: Specify the governed graph artifacts, schemas, and retained authoring records

Name the exact graph, prompt, node/tool, task-brief, and authoring-report artifacts. FR-868 proposes `salvage_classify` and correctly says it must be authored through the governed route (`feature-requests/FR-868-scripture-dev-salvage.md:69-81`, `98-99`), but it does not freeze graph paths, prompt paths, output schemas, smoke inputs, or how the overwritten `tmp/draft-authoring-report.md` will be retained. Local doctrine makes graph artifact creation governed by artifact class, with lint/smoke evidence required (`.github/copilot-instructions.md:15`).

Fold this by adding paths such as `examples/demos/salvage_classify/graph.yaml`, `examples/demos/salvage_classify/prompts/*.yaml`, and any `examples/demos/salvage_classify/nodes/*.py`; a task brief path such as `feature-requests/authoring-briefs/fr-868-salvage-classify-brief.md`; and a retained report path or FR evidence section. Define the map output schema and final JSON schema fields exactly: `path`, `category`, `verdict`, `rationale`, `yamlgraph_equivalent`, `target_path`, and any confidence/error fields. The graph must write only `tmp/ramp/salvage-disposition.md` and `tmp/ramp/salvage-disposition.json`.

### R-3: Make lift destinations independent of sibling implementation state

Replace the ambiguous "FR-865's manifest" dependency with a concrete destination contract. FR-868 says lift items are merged into this repo's ramp assets "with attribution in the commit message" (`feature-requests/FR-868-scripture-dev-salvage.md:85-90`), while FR-865's own judgement has not granted unconditional authority and requires revisions before its `ramp/manifest.yaml` and asset tree are trustworthy (`feature-requests/FR-865-ramp-installer.judgement.md:17-54`, `87-100`). FR-868 cannot depend on a sibling's unfinalized manifest shape without freezing its own behavior.

Fold this by stating the allowed lift destinations now. Either require all lifted assets to land under a concrete curated ramp tree owned by FR-865 after FR-865's R-1 through R-6 are folded, or create a FR-868-owned holding path such as `ramp/salvage/scripture-dev/<sha>/` pending a later manifest integration. For every `lift` verdict, require a destination path, rationale for why the asset is still correct, source SHA attribution recorded in the FR implementation section, and a test or review check proving the destination is in the authorized namespace.

### R-4: Make validation executable without depending on a sibling checkout

Separate committed tests from live `scripture-dev` evidence. FR-868's criteria require validating every duplicate equivalent, every lift destination, count-in == count-out, consumer checks, and archive verification (`feature-requests/FR-868-scripture-dev-salvage.md:100-123`), but the FR does not say whether CI must have a live `scripture-dev` checkout or GitHub access. Repo doctrine warns that workspace visibility is not ownership and cross-repo boundaries are separate blast radii (`.github/copilot-instructions.md:63-65`, `87-88`, `109-110`), and the parent judgement requires explicit target refs and separate repo boundaries (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:87-89`).

Fold this by requiring automated tests to use committed fixtures for enumeration, classification schema validation, duplicate-path validation, lift-destination validation, no-write-outside-`tmp/`, and count reconciliation. The real `scripture-dev` run may be recorded as local enforcement evidence, but tests must not require `/Users/...` paths, a sibling checkout, mutable GitHub state, or network access. Any command that reads the live repo must be read-only until the explicit archive step.

### R-5: Turn human approval and consumer impact into a hard archive gate

Revise AC-12 so archive does not "still proceed" by default after a consumer-impact finding. FR-868 correctly requires recorded human approval before archive (`feature-requests/FR-868-scripture-dev-salvage.md:115-118`), but AC-12 says if `my-minesweeper` or `my-minesweeper2` would break, the archive "still proceeds" because archive is read-only (`feature-requests/FR-868-scripture-dev-salvage.md:119-121`). That absorbs a human/product decision into the FR and weakens the approval gate required for external repository state changes.

Fold this by making the approval line include the reviewed consumer-impact result. If either known consumer would break or if the check cannot be completed, the FR must record that fact and require a fresh human approval line after the impact is known. The archive action remains authorized only after that approval; it must be performed as GitHub archive, not deletion, transfer, rename, or branch rewrite.

### R-6: Replace the secret-scan criterion with a named mechanical check

Make "no secrets or token-bearing content are lifted" mechanically checkable. AC-13 currently says "the diff is scanned" without naming the scanner, target paths, failure condition, or where the result is recorded (`feature-requests/FR-868-scripture-dev-salvage.md:122-123`). Judge doctrine requires measurable acceptance criteria (`.github/skills/judge-fr/doctrine.md:43-46`), and repo doctrine requires exposing errors rather than relying on silent or aspirational checks (`.github/copilot-instructions.md:220-225`).

Fold this by naming the exact command(s) or repo hook(s) used to scan lifted files and the final diff, and by requiring non-zero failure on private keys, tokens, API keys, or credential-looking material. At minimum, the FR must state the scan scope, the accepted false-positive handling process, and the evidence location in the FR implementation section.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-868-scripture-dev-salvage.md` folding R-1 through R-6 |
| D-2 | `salvage_classify` graph demo, prompts, optional nodes/tools, committed task brief, retained authoring report, lint/smoke evidence |
| D-3 | `tmp/ramp/salvage-disposition.md` and `tmp/ramp/salvage-disposition.json` draft outputs |
| D-4 | Source-ref/file-population evidence for the exact `scripture-dev` commit classified |
| D-5 | Tests/fixtures for enumeration, schema validation, count reconciliation, duplicate equivalents, lift destinations, and no writes outside `tmp/` |
| D-6 | Lifted assets, if any, only into the revised authorized ramp namespace, with source SHA attribution and secret-scan evidence |
| D-7 | FR-207 outcome update recording implemented/superseded status and the mechanism diagnosis |
| D-8 | Consumer-impact record and explicit human approval before GitHub archive state change |

Not authorized: applying any ramp to `sheikkinen/deviant-daily` or another target repo; implementing or modifying `scripts/ramp.sh` outside the lift-destination integration explicitly authorized after FR-865 revisions; authoring `ramp_doctrine`, `ramp_rtm`, or `ramp_incidents`; modifying `my-minesweeper` or `my-minesweeper2`; deleting, transferring, renaming, rewriting history, changing visibility, or otherwise administrating `scripture-dev` beyond GitHub archive after recorded approval; changing yamlgraph runtime primitives, live hooks, CI enforcement, judge/review doctrine, graph-authoring doctrine, spike detector, or unenforced-repo warning behavior; committing `tmp/` outputs, sibling-repo working trees, archives, secrets, token-bearing logs, or generated external-repo state.

## Revised acceptance criteria

- [ ] AC-01: FR-868 is revised to define the exact `scripture-dev` repository URL, commit SHA, enumeration mechanism, tracked-file count, artifact-population evidence path, graph artifact paths, schemas, authoring-record paths, lift namespace, archive approval gate, and secret-scan command from R-1 through R-6.
- [ ] AC-02: The source artifact manifest for the classified `scripture-dev` commit exists as committed evidence or an FR section; the manifest count equals the enumerator's count and is the complete population consumed by `salvage_classify`.
- [ ] AC-03: `salvage_classify` is authored through the governed graph-authoring route with a committed task brief and a retained report naming artifacts, precedent, lint command, smoke command, repairs, and blocked validation if any.
- [ ] AC-04: `salvage_classify` passes `yamlgraph graph lint` against its final committed `graph.yaml`.
- [ ] AC-05: The graph declares Pydantic schemas for per-artifact classifications and final disposition JSON; tests validate representative fixture outputs against those schemas.
- [ ] AC-06: Draft paths are exactly `tmp/ramp/salvage-disposition.md` and `tmp/ramp/salvage-disposition.json`; tests assert the graph/tool writes no file outside `tmp/ramp/`.
- [ ] AC-07: Classification reports count-in == count-out over the source artifact manifest, emits zero `unknown` verdicts, and explicitly classifies every item as `duplicate`, `lift`, or `obsolete`.
- [ ] AC-08: Every `duplicate` verdict names a `yamlgraph_equivalent` path that exists in this repo and passes a test over the generated disposition JSON.
- [ ] AC-09: Every `lift` verdict names an authorized destination path, source SHA, and rationale; tests reject destinations outside the revised lift namespace.
- [ ] AC-10: Before any lift is committed, the FR records a raw-output read of at least three disposition entries, each quoted with a concrete detail and the human decision made from it.
- [ ] AC-11: If the lift list is empty, the FR records that explicitly with rationale; an empty lift list is a valid finding only after the raw-output read.
- [ ] AC-12: Lifted assets, if any, are committed here with attribution to `scripture-dev` and the classified SHA recorded in the FR implementation section and commit evidence.
- [ ] AC-13: The named secret-scan command(s) run over every lifted file and final diff; the FR records the command, result, and any reviewed false-positive disposition.
- [ ] AC-14: FR-207 is updated with the outcome, the `asset_source_must_be_a_consumer` mechanism diagnosis, the classified SHA, and a pointer to the FR-864 child family.
- [ ] AC-15: `my-minesweeper` and `my-minesweeper2` dependence checks are recorded before archive approval; if either would break or the check cannot complete, a fresh human approval line after that finding is required.
- [ ] AC-16: `scripture-dev` is archived only after explicit recorded human approval and is verified afterward as archived/read-only, not deleted.
- [ ] AC-17: Tests are added before implementation for the graph behavior and validation checks above, with RED/GREEN evidence recorded in the FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-868-scripture-dev-salvage.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any `graph.yaml` or `prompts/*.yaml` creation/material modification must use the governed graph-authoring route and retain the FR-868 authoring record. | GATE |
| C-4 | Live `scripture-dev` access before archive must be read-only and pinned to the recorded source SHA; no external repo state change is authorized before the explicit archive approval line. | GATE |
| C-5 | No tests may require a sibling checkout, operator-local absolute path, network access, or mutable GitHub state; committed fixtures must cover automated behavior. | GATE |
| C-6 | No lifted file may be committed until duplicate/lift/obsolete disposition has been raw-read, the destination is authorized, and the named secret scan passes or has a recorded reviewed false-positive disposition. | GATE |
| C-7 | Archive is the only authorized GitHub state change for `scripture-dev`; deletion, transfer, rename, visibility changes, branch rewrites, issue/PR mutation, or hook/CI changes in that repo are out of scope. | GATE |
| C-8 | If known consumer impact is non-empty or unknown, archive requires a fresh human approval line after that impact is recorded. | GATE |
| C-9 | No yamlgraph framework primitive, live hook, CI enforcement, judge/review doctrine, graph-authoring doctrine, spike-detector, unenforced-repo-warning behavior, FR-865 installer behavior, or FR-866 tailoring graph may change under this FR except for explicitly authorized lift-destination integration after sibling revisions are folded. | GATE |

Authority granted: after the required revisions are folded, enforcement may author and validate the `salvage_classify` graph through the governed route, produce review-only disposition drafts under `tmp/ramp/`, lift approved missing artifacts into the authorized ramp namespace with attribution, update FR-207, and archive `scripture-dev` only after recorded human approval.
