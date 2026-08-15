# Judgement: FR-796 Reclassify watcher2 witness demos out of the examples garden

**Prior art:** `examples/2026-07-01-plan-cleanup.md` (Tier 1/Tier 3 disposition of these directories); FR-196 (`.chaplain/` relocation precedent); FR-206 (demo-gate); FR-279/280/281/283/286/287/288/289 (witnessed FRs, all Implemented).

**Verdict:** APPROVED WITH REVISIONS — the garden-curation direction is sound, but authority activates only after the FR corrects the graph-authoring route claim, the content-diff contradiction, and the self-referential commit-SHA criterion.

**Reviewed against:** `feature-requests/FR-796-reclassify-watcher2-witness-demos.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `examples/2026-07-01-plan-cleanup.md`; `feature-requests/FR-196-portable-chaplain.md`; `feature-requests/FR-206-demo-proof-gate.md`; `feature-requests/FR-279-watcher2-ci-resilience.md`; `feature-requests/FR-280-watcher2-red-verification-timestamp-fix.md`; `feature-requests/FR-281-watcher2-remediation-loop-crash-fix.md`; `feature-requests/FR-283-auto-generate-changelog-fragments-watcher2.md`; `feature-requests/FR-286-watcher2-merged-branch-collision-guard.md`; `feature-requests/FR-287-watcher2-deduplication-gate.md`; `feature-requests/FR-288-watcher2-hook-preflight-gate.md`; `feature-requests/FR-289-watcher2-post-merge-inbox-consumption.md`; `examples/README.md`; `examples/demos/README.md`; `examples/dependency-taxonomy.yaml`; `yamlgraph/discovery.py`; cited demo `graph.yaml` files under `examples/demos/{security-cve-ignore,watcher2-*}/`; `capabilities/**/*.yaml` only for the cited-path no-match check.

## What is sound

The problem is real and evidenced. The prior cleanup plan already classified `script-retirement`, `security-cve-ignore`, and `watcher2-red-verification` as delete candidates because they are witness artifacts rather than teaching demos (`examples/2026-07-01-plan-cleanup.md:5-14`), and classified the seven watcher2 directories named by this FR as internal infrastructure to relocate to `.chaplain/demos/` (`examples/2026-07-01-plan-cleanup.md:24-34`). The plan also predicted the MCP effect: default graph discovery includes `examples/demos/*/*.yaml`, so relocated infrastructure demos should disappear from the tool namespace (`examples/2026-07-01-plan-cleanup.md:83-85`; `yamlgraph/discovery.py:22-26`).

The current garden surfaces corroborate drift. `examples/README.md` still lists all ten targets in Utility Demos (`examples/README.md:146-164`), `examples/demos/README.md` still advertises `watcher2-deduplication-gate` as a demo (`examples/demos/README.md:19-52`), and `examples/dependency-taxonomy.yaml` still carries path/entrypoint records for the delete and relocate targets (`examples/dependency-taxonomy.yaml:421-429`, `examples/dependency-taxonomy.yaml:500-539`). The watcher2 precedent FRs cited by FR-796 are implemented (`FR-279:1-7`, `FR-280:1-7`, `FR-281:1-7`, `FR-283:1-7`, `FR-286:1-7`, `FR-287:1-7`, `FR-288:1-7`, `FR-289:1-7`), so the demos are no longer standing in for unimplemented work.

The scope is mostly minimal and single-purpose: FR-796 names exactly three deletions, seven relocations, and live reference updates (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:55-89`), while explicitly excluding the rest of the older mega-plan (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:90-95`). Strategic classification: **Pattern documentation / contrib-garden curation**, not a framework primitive. The change uses existing repository conventions (`.chaplain/` as the infrastructure home from FR-196, `examples/demos/` as the user-facing demo garden, and existing discovery patterns) rather than adding a new abstraction.

## Required revisions

### R-1: Correct the graph-authoring route claim

Replace C-1's assertion that pure `git mv` avoids the authoring-route trigger. FR-796 currently says relocation/deletion is "no authoring-route trigger" because `git mv` preserves content byte-for-byte (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:97-102`). Repo doctrine says the trigger is the artifact class, and that any task creating or materially modifying `graph.yaml` or `prompts/*.yaml`, explicitly including `mv`, must use the graph-authoring route (`.github/copilot-instructions.md:15`). Fold this into the FR as a hard enforcement constraint:

> Moving or deleting governed `graph.yaml` and `prompts/*.yaml` artifacts must be performed through the graph-authoring route/sentinel. The content-preservation goal remains in scope, but it does not bypass the route. If the route fails, enforcement stops and fixes the route rather than moving graph artifacts manually.

### R-2: Reconcile README path updates with the no-content-diff criterion

AC-02 says the seven relocated directories must have "no content diff" (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:119-121`), but the Proposed Solution also requires README run-command path updates inside each relocated demo (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:87`). Replace the broad "no content diff" rule with a precise one:

> `graph.yaml`, `prompts/**`, Python node files, scripts, and existing `demo-output.log` files are byte-for-byte identical after relocation; README files may change only to update old `examples/demos/...` command paths to `.chaplain/demos/...`.

### R-3: Replace the self-referential deleting-commit SHA requirement

AC-01 and C-4 require deleted demos' FRs to record "the deleting commit SHA" (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:109-111`, `feature-requests/FR-796-reclassify-watcher2-witness-demos.md:117-118`). A commit cannot reliably include its own final SHA in files it changes, so this is not a clean mechanical acceptance criterion under the judge rubric's measurability requirement (`.github/skills/judge-fr/doctrine.md:43-44`). Replace it with:

> Deleted demos' governing FRs receive one-line retirement notes naming FR-796, the retired path, and the fact that witness evidence remains in git history; FR-796 implementation notes record the PR URL and, after it exists, the relevant deleting commit or merge commit identifier.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `examples/demos/script-retirement/`, `examples/demos/security-cve-ignore/`, and `examples/demos/watcher2-red-verification/` |
| D-2 | Relocate `watcher2-changelog-gen`, `watcher2-ci-remediation`, `watcher2-deduplication-gate`, `watcher2-hook-preflight-gate`, `watcher2-merged-branch-collision-guard`, `watcher2-post-merge-inbox-consumption`, and `watcher2-remediation` from `examples/demos/` to `.chaplain/demos/` |
| D-3 | Update `examples/README.md`, `examples/demos/README.md`, and `examples/dependency-taxonomy.yaml` so live indexes/taxonomy match the new locations |
| D-4 | Update README run commands inside relocated demos only as needed for the new `.chaplain/demos/...` paths |
| D-5 | Add retirement notes to the governing FRs for deleted witness demos and annotate `examples/2026-07-01-plan-cleanup.md` with this executed slice |
| D-6 | Add required changelog fragment(s), diary reflection, and verification output for one representative relocated demo run |

Not authorized: executing other tiers from `examples/2026-07-01-plan-cleanup.md`; moving `enforcer`, `req-cross-check`, `pipeline_audit`, `run-analyzer`, `system-status`, `forensic-failure-diary`, `hook_classifier`, or `code-analysis`; adding `.chaplain/demos/*/*.yaml` to `DEFAULT_GRAPH_PATTERNS`; weakening `demo-gate`, branch protection, hooks, or MCP discovery; changing graph semantics, prompts, node code, or demo behavior; converting the witnesses into tests; moving these demos to `purgatory/`.

## Revised acceptance criteria

- [ ] AC-01: FR-796 is amended with R-1 through R-3 before enforcement authority is used.
- [ ] AC-02: The three delete-target directories are removed from `examples/demos/`; their governing FR records contain one-line retirement notes naming FR-796, the retired path, and git-history witness retention.
- [ ] AC-03: The seven watcher2 directories exist under `.chaplain/demos/`; `git diff --find-renames` reports them as renames/moves rather than unrelated delete/add churn where Git can detect it.
- [ ] AC-04: For each relocated watcher2 demo, `graph.yaml`, `prompts/**`, node files, scripts, and existing `demo-output.log` files are byte-for-byte preserved; README changes are limited to path updates for runnable commands.
- [ ] AC-05: `yamlgraph graph lint` passes for all seven relocated graphs, and one representative relocated demo run succeeds with output captured under its new `.chaplain/demos/...` directory.
- [ ] AC-06: A tracked-file search for `examples/demos/(watcher2-|script-retirement|security-cve-ignore)` returns no live references outside record artifacts (`feature-requests/**`, `docs/diary/**`, and git history); indexes, taxonomy, relocated READMEs, tests, and CAP registry files are updated or confirmed clean.
- [ ] AC-07: MCP graph/tool discovery no longer lists the deleted or relocated demos, including `Watcher2DeduplicationGateDemo`, `Watcher2HookPreflightGateDemo`, `Watcher2MergedBranchCollisionGuardDemo`, `Watcher2PostMergeInboxConsumptionDemo`, and `Security CVE Ignore Demo`.
- [ ] AC-08: `examples/README.md` removes the ten Utility Demo rows and adds a concise pointer to `.chaplain/demos/` for infrastructure witnesses; `examples/demos/README.md` removes the stale `watcher2-deduplication-gate` row.
- [ ] AC-09: `examples/dependency-taxonomy.yaml` no longer records deleted paths and records relocated watcher2 entrypoints at `.chaplain/demos/...` only if that taxonomy intentionally covers `.chaplain` witnesses; otherwise the entries are removed with rationale in FR-796 implementation notes.
- [ ] AC-10: Full tests pass, and no test file references the retired `examples/demos/...` paths.
- [ ] AC-11: Changelog fragment(s), diary reflection, and an annotation to `examples/2026-07-01-plan-cleanup.md` are included in the implementation diff.
- [ ] AC-12: FR-796 implementation notes record the PR URL and, after available, the deleting or merge commit identifier that preserves deleted witness evidence in git history.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-3 must be folded into FR-796 before implementation begins. | GATE |
| C-2 | Any relocation/deletion of `graph.yaml` or `prompts/*.yaml` artifacts must proceed through the graph-authoring route/sentinel required by repo doctrine. | GATE |
| C-3 | If a relocated graph requires graph, prompt, node-code, or behavior changes to run from `.chaplain/demos/`, stop; those changes are not authorized by this FR. | GATE |
| C-4 | Do not modify `DEFAULT_GRAPH_PATTERNS` to include `.chaplain/demos/`; disappearance from MCP discovery is an intended outcome of relocation. | GATE |
| C-5 | Do not weaken or bypass `demo-gate`, hooks, CI, or branch-protection enforcement. If pure deletes/renames expose a gate defect, file a separate FR or amend this one for human-reviewed enforcement-infrastructure work. | GATE |
| C-6 | Do not execute any other item from the 2026-07-01 cleanup plan under this authority. | GATE |

Authority granted: after R-1 through R-3 are folded into FR-796, enforcement may perform only the frozen delete/relocate/reference-update slice above, with graph artifact movement routed through the governed authoring mechanism and no semantic graph or prompt edits.
