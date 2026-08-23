# Judgement: FR-867 Ramp deviant-daily to Tier 2 + RTM

**Verdict:** APPROVED WITH REVISIONS -- the target application is the right child scope and the need is proven, but authority activates only after dependency provenance, exact tier invocation, human-review handoff, CI-block semantics, RTM identity, and cross-repo safety evidence are made mechanically exact.

**Reviewed against:** `feature-requests/FR-867-ramp-deviant-daily.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`. No author chat narrative was consumed.

**Prior art:** dispositioned below — FR-864 (parent SPLIT, controlling), FR-826 (target repo contracts, unchanged here), FR-862 (partially superseded dispatch surface), FR-863 (the four incidents motivating the ramp), FR-865/866 (dependencies, provenance gated by R-1), FR-868 (non-overlap). No REJECTED prior art occupies this territory. FR-867 is the subject FR.

## What is sound

FR-867 is the correct child-C extraction from the parent SPLIT. The parent judgement required a target-specific child for applying the ramp to `sheikkinen/deviant-daily`, including target ref, tier/RTM decision, target files, CI/test baseline, non-secret witnesses, and hard sibling-repo boundary conditions (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:41-45`, `73-78`). FR-867 stays on that surface: it applies existing sibling outputs to one target repo and explicitly depends on FR-865 and FR-866 rather than re-specifying their tooling (`feature-requests/FR-867-ramp-deviant-daily.md:8-10`, `24-28`, `91-94`).

The problem is real and urgent. FR-867 records that `deviant-daily` had gone live, had zero pre-commit hooks, zero CI jobs running its 145 tests, zero doctrine file, and four production failures in one morning (`feature-requests/FR-867-ramp-deviant-daily.md:35-48`). The incident FR gives concrete failures: vision payload ceiling, confidence-policy loss, DeviantArt title cap, degenerate corpus identity, and guard-flag hedging (`feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md:44-80`, `82-112`). The target repo history is also established by FR-826: the repo exists outside yamlgraph, is public, runs a YAMLGraph daily pipeline, and has pending operational observations around cron/roster/gate paths (`feature-requests/FR-826-deviantart-daily-repo.md:5-11`, `227-235`, `255-263`, `267-277`, `293-315`).

The scope is mostly measurable. FR-867 asks for before/after target refs, dry-run output, hook installation, CI run ids, blocked local and CI witnesses, landed `AGENTS.md`/RTM/incidents artifacts, `req_coverage --strict`, next cron proof, secret scanning, repo-boundary cleanliness, and FR-863 cross-references (`feature-requests/FR-867-ramp-deviant-daily.md:81-124`). Those are concrete operational checks, not aspirational prose.

The architecture alignment is sound if the child boundaries hold. FR-865 owns the mechanical installer and says its first real target remains FR-867 (`feature-requests/FR-865-ramp-installer.judgement.md:91-100`), while FR-866 owns graph-generated drafts only and explicitly forbids writing into a target repo (`feature-requests/FR-866-ramp-tailoring-graphs.judgement.md:91-99`). FR-867 is therefore the right place to perform the final, reviewed handoff into `sheikkinen/deviant-daily`. Strategic classification: **target-repo governance application**, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Gate authority on exact dependency artifacts, not vague readiness

Replace "FR-865 (installer) and FR-866 (graphs) having their own granted authority and working artifacts" with a mechanically checkable activation record. FR-867 currently names the dependency (`feature-requests/FR-867-ramp-deviant-daily.md:8-10`), but both sibling judgements grant authority only after revisions are folded and specific artifacts are produced (`feature-requests/FR-865-ramp-installer.judgement.md:91-100`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md:91-100`).

Fold this by requiring FR-867 to record, before target writes begin: the yamlgraph commit SHA containing the enforced FR-865 installer/manifest assets, the yamlgraph commit SHA containing the enforced FR-866 graph artifacts, the two judgement statuses showing authority active, and the validation evidence that those sibling artifacts are working. "Working artifacts" must name concrete paths and commands, not a prose assertion.

### R-2: Freeze the exact Tier 2 + RTM install command and asset set

Resolve the ambiguity between "Tier 2" and "Tier 3 RTM subset." FR-867 says to install Tier 2 and then "the Tier 3 RTM subset" (`feature-requests/FR-867-ramp-deviant-daily.md:69-77`), while FR-865 defines only tiered installer behavior and lists Tier 3 as the registry shape, `req_coverage.py`, and `--strict` gate (`feature-requests/FR-865-ramp-installer.md:74-80`).

Fold this by stating the exact command sequence the enforcer must run against the target. If the intended operation is `scripts/ramp.sh <target> --tier 3`, say so and define the resulting policy label as "Tier 2 operating governance plus Tier 3 RTM assets." If the intended operation is `--tier 2` plus selected RTM files, list every selected destination path and require the dry-run transcript to prove only those paths are planned. Do not permit undocumented hand-copying of a subset.

### R-3: Make generated-draft landing a recorded human-review handoff

Define what "reviewed drafts" means before generated governance files are copied into the target. FR-867 instructs the enforcer to run FR-866's graphs, review three drafts, and land them as `AGENTS.md`, `capabilities/*.yaml`, and `docs/incidents.md` (`feature-requests/FR-867-ramp-deviant-daily.md:72-75`). FR-866, however, only authorizes draft generation under `tmp/ramp/`; the generated artifacts are drafts until human-reviewed (`feature-requests/FR-866-ramp-tailoring-graphs.judgement.md:63-66`, `91-99`). Repo doctrine also treats agent outputs that modify enforcement infrastructure or doctrine as adversarial input requiring review (`.github/copilot-instructions.md:83-85`; `.github/skills/judge-fr/doctrine.md:96-101`).

Fold this by requiring a per-draft review record in FR-867 before landing: draft path, draft hash, reviewer/date, accepted edits if any, final target path, and a statement that the final target file was compared against the reviewed draft. This record must cover doctrine, RTM/registry, and incidents. A graph output alone is not authority to write target governance.

### R-4: Define CI "blocked" as a real merge gate or rename it to detection

Make AC-06 mechanically true. FR-867's ideal says a bad commit is refused locally and in CI (`feature-requests/FR-867-ramp-deviant-daily.md:50-57`), and AC-06 says a deliberately non-conforming push is "blocked in CI" (`feature-requests/FR-867-ramp-deviant-daily.md:101-104`). A normal GitHub Actions failure after a push detects a defect but does not block the bad commit from entering the branch unless branch protection or a PR-required workflow is in force.

Fold this by choosing one exact witness. Preferred: create a throwaway branch or PR with a deliberately non-conforming change, show the required CI status failing, and show that the PR cannot merge to `main`. If branch protection is intentionally out of scope, revise the criterion to "detected by CI" and add a separate follow-up FR for branch protection. Do not claim "blocked in CI" from a failing run id alone.

### R-5: Freeze the target RTM identity and honest-gap policy

Specify the target requirement namespace and the allowed result when strict coverage cannot honestly pass. FR-867 says to tag existing tests with requirement IDs until `req_coverage --strict` passes or gaps are accepted (`feature-requests/FR-867-ramp-deviant-daily.md:76-77`, `110-113`), but it does not define the target prefix, registry naming convention, or who accepts gaps. The yamlgraph doctrine's `REQ-YG-*` convention is repo-local (`.github/copilot-instructions.md:172-178`); copying it into `deviant-daily` would blur repo identity.

Fold this by naming the target requirement prefix, registry path convention, and exact gap-acceptance record. Every target registry entry must carry `status`, at least one existing witness test, and a target-local requirement id. If `req_coverage --strict` fails, each accepted gap must name the missing requirement/test relation, the reason it is accepted for this ramp, and the human who accepted it.

### R-6: Add a cross-repo execution transcript boundary

Preserve separate repository ownership at every step. FR-867 correctly requires clean and separate git statuses at completion (`feature-requests/FR-867-ramp-deviant-daily.md:120-122`) and recognizes cross-repo index-collision risk (`feature-requests/FR-867-ramp-deviant-daily.md:136-138`), while repo doctrine warns that nested repositories are separate blast radii and require explicit boundary checks (`.github/copilot-instructions.md:63-65`, `87-87`, `163-163`).

Fold this by requiring a non-secret transcript section that records, before and after target modification: yamlgraph repo status, target repo status, target HEAD, branch name, and the exact file list intended for each repo. The transcript must prove no `deviant-daily` tree, archive, submodule, generated image, credential, token-bearing log, or workflow secret was committed into yamlgraph.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-867-ramp-deviant-daily.md` folding R-1 through R-6 |
| D-2 | Target application of the already-enforced FR-865 installer assets to `sheikkinen/deviant-daily` at the recorded target ref |
| D-3 | Reviewed landing of already-produced FR-866 draft outputs into the target as `AGENTS.md`, target requirement registry/RTM artifacts, and `docs/incidents.md` |
| D-4 | Target-local requirement tagging and `req_coverage --strict` evidence or accepted-gap record |
| D-5 | Target-local hook, CI, and deliberate-failure witnesses |
| D-6 | Target scheduled-publish regression witness |
| D-7 | YAMLGraph-side update only to FR-867 implementation status and FR-863 cross-references to the incidents' new target home |

Not authorized: changing yamlgraph core/runtime behavior; modifying FR-865 installer behavior or curated ramp assets; modifying FR-866 graphs, prompts, schemas, or graph-authoring evidence; creating or materially editing any `graph.yaml` or `prompts/*.yaml` artifact; changing yamlgraph live hooks, CI, judge/review/graph-authoring doctrine, spike detector, or unenforced-repo warning behavior; changing `scripture-dev`; modifying any repository other than `sheikkinen/deviant-daily` and the two listed yamlgraph FR files; vendoring, submoduling, archiving, or committing the target repo into yamlgraph; copying secrets, token-bearing logs, generated images, or target repo archives across repositories; weakening the daily publisher's external-side-effect safeguards from FR-826/FR-863.

## Revised acceptance criteria

- [ ] AC-01: FR-867 is revised to define dependency activation evidence, exact install command/asset set, draft-review handoff, CI-block semantics, target RTM identity, and cross-repo transcript requirements from R-1 through R-6.
- [ ] AC-02: Before any target write, FR-867 records the target repo URL/path, branch, exact HEAD, clean target git status, clean yamlgraph git status for relevant files, and the explicit file list expected to change in each repo.
- [ ] AC-03: Before any target write, FR-867 records the yamlgraph commit SHA and validation evidence for the enforced FR-865 installer assets and the enforced FR-866 graph draft artifacts; both sibling judgements' revision gates are satisfied.
- [ ] AC-04: The chosen install path is exact: either `scripts/ramp.sh <target> --tier 3` or `scripts/ramp.sh <target> --tier 2` plus an explicitly listed RTM asset subset. The dry-run transcript is pasted into FR-867 before install and shows the planned target paths.
- [ ] AC-05: The curated ramp manifest and enforcement asset set have a recorded human-review approval before first non-scratch use against `deviant-daily`.
- [ ] AC-06: The installer writes only the approved paths from AC-04; the install transcript records created/skipped/overwritten actions and source commit SHA without secrets.
- [ ] AC-07: After install, `.git/hooks/pre-commit` exists in the target and `pre-commit run --all-files` executes; the target transcript records command, exit status, and non-secret summary.
- [ ] AC-08: The FR-866 graph runs used for this application record source commit SHA, command, draft paths, and draft hashes; no graph/tool writes directly into the target repo.
- [ ] AC-09: Before landing each generated governance artifact, FR-867 records draft path, draft hash, reviewer/date, accepted edits, final target path, and comparison statement. `AGENTS.md` names at least one target-specific boundary and contains zero foreign witness citations.
- [ ] AC-10: `docs/incidents.md` in the target contains all four 2026-08-23 failures from FR-863 -- vision payload ceiling, DA title cap, degenerate corpus key, and guard-flag hedging -- each with root cause, cure, and source reference.
- [ ] AC-11: The target requirement registry uses a target-local requirement prefix, every entry carries `status`, and every witness test name exists in the target.
- [ ] AC-12: Target tests are tagged with target-local requirement IDs until `req_coverage --strict` passes, or every strict gap is recorded with missing relation, reason, and human acceptance.
- [ ] AC-13: The target CI runs its full suite on push, with run id, commit SHA, command summary, and test count reported as at least 145.
- [ ] AC-14: A deliberately non-conforming target commit is blocked locally by pre-commit; the non-secret transcript records the failing hook and proves the deliberate change was not committed to `main`.
- [ ] AC-15: A deliberately non-conforming target change is blocked by a required CI merge gate using a throwaway branch or PR. If only a failing workflow run is available, the criterion is not satisfied unless FR-867 is revised to say "detected by CI" and branch protection is deferred to a separate FR.
- [ ] AC-16: The first scheduled publish after the ramp completes runs green; FR-867 records run id, commit SHA, and ledger row, proving the ramp did not break the daily product.
- [ ] AC-17: No secret, credential, token, token-bearing log, generated image, target repo archive, nested repo, or submodule is copied in either direction; the assertion is backed by a non-secret diff/status scan.
- [ ] AC-18: YAMLGraph's FR-863 gains cross-references from the four incident entries to their new target home, without duplicating target incident prose back into yamlgraph.
- [ ] AC-19: Completion records clean and separate git statuses for yamlgraph and `deviant-daily`, plus the final changed-file list for each repository.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-867-ramp-deviant-daily.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while acting on this judgement. | GATE |
| C-3 | Do not begin target writes until FR-865 and FR-866 have active authority, enforced artifacts, recorded commit SHAs, and validation evidence. | GATE |
| C-4 | Cross-repo work must be one repo at a time with explicit file lists, before/after statuses, and no nested repo, archive, submodule, secret, or token-bearing artifact crossing the boundary. | GATE |
| C-5 | Generated doctrine, RTM, and incident drafts are advisory until reviewed; no graph output may be landed in the target without the review record required by R-3. | GATE |
| C-6 | If applying the ramp requires changing FR-865 assets, FR-866 graph artifacts, yamlgraph hooks, yamlgraph CI, judge/review/graph-authoring doctrine, or spike/unenforced-repo detector behavior, stop for the owning FR or a new judgement. | GATE |
| C-7 | Deliberate failure witnesses must use disposable target branches/changes and must not leave `main` broken or the daily publisher disabled. | GATE |
| C-8 | If the first post-ramp scheduled publish fails, enforcement is incomplete until the failure is diagnosed in the target repo and FR-867 records the outcome. | GATE |

Authority granted: after the required revisions are folded and dependency gates are satisfied, enforcement may apply the already-built ramp and reviewed generated governance drafts to `sheikkinen/deviant-daily`, prove local/CI gates and scheduled publishing, and record yamlgraph-side FR cross-references within the frozen scope above.
