# Judgement: FR-865 Ramp Installer -- Generic Asset Copier with Tiers

**Verdict:** APPROVED WITH REVISIONS -- the child scope is the right split and the mechanical installer is worth building, but authority activates only after the FR replaces ambiguous source assets with a curated manifest, narrows the target contract, and makes overwrite/rollback semantics mechanically true.

**Reviewed against:** `feature-requests/FR-865-ramp-installer.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-748-fr-atlas-onboarding-summary.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.judgement.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-867-ramp-deviant-daily.md`; `feature-requests/FR-868-scripture-dev-salvage.md`; `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`; `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`; `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`; `.pre-commit-config.yaml`; `.github/hooks/README.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/workflows/workflow.yml`; targeted repository searches over `feature-requests/` for ramp/installer/scripture-dev/rejected prior art. No author chat narrative was consumed.

**Prior art:** dispositioned below — FR-864 (parent SPLIT, controlling), FR-207 (superseded template mechanism, diagnosed not repeated), FR-866/867/868 (sibling children, non-overlap enforced by C-3..C-5). FR-748/`fr_atlas` marked non-overlap: this FR contains no LLM step. No REJECTED prior art occupies this territory. FR-865 is the subject FR.

## What is sound

FR-865 correctly implements the parent split's child A surface. The parent judgement required a child FR for "generic ramp installer and copyable asset manifest" only, explicitly excluding target application, graph authoring, and `scripture-dev` archival (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:23-27`, `57-68`). FR-865 keeps that boundary in its summary: mechanical copier, no LLM, no target-specific content, no repo it does not own (`feature-requests/FR-865-ramp-installer.md:24-29`), and says its acceptance criteria do not depend on FR-866/867/868 (`feature-requests/FR-865-ramp-installer.md:94-97`).

The first consumer is concrete enough for a generic tool: the first event is a scratch-repo dry run in this repo's own test suite, with the first real target deferred to FR-867 (`feature-requests/FR-865-ramp-installer.md:9-11`). That avoids building a tool with no named use, while preserving the sibling-repo boundary required by the parent judgement (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:87-89`).

The prior-art disposition is directionally correct. FR-207 really was a standalone template-repo extraction of governance assets (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:48-65`) using `scripture.yaml` plus `render.sh` substitution (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:108-142`), and the cited diary records why a non-consuming distributor decayed while a practicing repo stayed live (`docs/diary/diary-2026-08-23-process-transfers-by-practice.md:11-27`, `49-52`). FR-748 is non-overlap for this child because it is a corpus map/merge graph (`feature-requests/FR-748-fr-atlas-onboarding-summary.md:45-80`), while FR-865 explicitly contains no LLM step (`feature-requests/FR-865-ramp-installer.md:26-29`). FR-826/862/863 are target-repo history and incident context, not generic installer implementation authority (`feature-requests/FR-826-deviantart-daily-repo.md:36-44`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md:53-61`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md:28-34`).

The requested behavior is mostly measurable: dry run writes nothing, missing-file copy, skip-on-existing, manifest contents, source-path validation, no LLM/network calls, and non-repo/self-repo refusal are all directly testable (`feature-requests/FR-865-ramp-installer.md:82-119`). Strategic classification: **Contrib/governance tooling**, not a YAMLGraph framework primitive. It ships repo-governance assets around existing project practice and should not modify YAMLGraph runtime semantics.

## Required revisions

### R-1: Replace root-file copying with a curated ramp asset source

Revise the manifest design so every installed source is a curated ramp asset, not an ambiguous pointer at this repo's live root files. FR-865 currently says the manifest entries include source path/destination path/tier and then names `.pre-commit-config.yaml`, `.github/hooks/`, and `.github/workflows/tests.yml` as Tier-1 assets (`feature-requests/FR-865-ramp-installer.md:59-72`). But the current root `.pre-commit-config.yaml` is not "basics only": it includes yamlgraph-specific authoring proof, requirement/capability validation, inline LLM, radon against `yamlgraph/`, bandit against `yamlgraph/`, hedging over `yamlgraph scripts`, demo proof, prior-art gates, FR board, and unit pytest hooks (`.pre-commit-config.yaml:29-35`, `60-75`, `128-146`, `150-162`, `208-216`, `227-307`). AC-02's byte-for-byte source match would therefore install a yamlgraph-specific config while the FR promises domain-free basics (`feature-requests/FR-865-ramp-installer.md:63-72`, `101-103`).

Fold this mechanically by requiring a dedicated source tree such as `ramp/assets/tier*/...` plus `ramp/manifest.yaml`. The manifest must enumerate exact files, not directories, and tests must assert the shipped `.pre-commit-config.yaml` is the curated ramp file, not this repo's root config. If an asset is copied from a live root file, the FR must state why that exact file is domain-free and add a source scan proving it contains no yamlgraph-only paths, `REQ-YG`, capability-registry assumptions, graph-authoring guards, local `.venv/bin` commands, or project-specific test paths.

### R-2: Enumerate the hook and workflow asset population exactly

Revise the Tier-1 hook/workflow entries from directory labels into a closed file list. `.github/hooks/README.md` shows the current hook tree includes runtime JSON, scripts, tests, logs, and `audit.jsonl` (`.github/hooks/README.md:9-35`). The actual `pre-command-guard.sh` includes yamlgraph graph-authoring enforcement for `examples/**/graph.yaml`, `graphs/*.yaml`, and `.chaplain/graphs/*.yaml` (`.github/hooks/scripts/pre-command-guard.sh:169-198`, `288-294`). Those may be useful in a governed repo, but they are not automatically "domain-free" for every Tier-1 target.

Fold this by requiring `ramp/manifest.yaml` to name each hook JSON/script/check file to install and to exclude `logs/`, `audit.jsonl`, `tests/`, `__pycache__/`, generated state, and any path whose behavior is not meant to run in the target. Add acceptance criteria that parse the manifest and fail if it contains a directory source, a generated/cache/log path, or a source file with unresolved yamlgraph-only assumptions unless that assumption is explicitly part of the target contract.

### R-3: Narrow the supported target contract or make CI truly generic

Replace the "any path" promise with a testable target contract. The Ideal Result says the command works "against any path" (`feature-requests/FR-865-ramp-installer.md:49-55`), while Tier 1 includes a workflow that "runs the target's suite + ruff" (`feature-requests/FR-865-ramp-installer.md:70-70`). A generic copier cannot know every repo's package manager, test command, dependency installation command, or whether `ruff` is relevant. The current yamlgraph CI is also not a generic source for that claim: it installs yamlgraph extras and runs `pytest tests/unit` plus `ruff check yamlgraph/` (`.github/workflows/workflow.yml:30-40`, `56-68`), and no consumed workflow file named `.github/workflows/tests.yml` exists in the current workflow set.

Fold this by stating the supported Tier-1 target shape precisely, e.g. "Python repos with pytest and ruff configured by `pyproject.toml`" or by making the CI asset a deliberately inert stub that prints required operator steps and is not counted as a running test gate. If the intended first class is Python repos, add fixture scratch repos covering a passing suite, missing tests, and missing ruff configuration, with explicit non-zero refusal or explicit documented skip behavior. Do not claim "runs the target's suite" unless the workflow source and tests prove the exact command path.

### R-4: Reconcile `overwrite: never`, `--force`, and rollback semantics

Make overwrite and rollback behavior internally consistent. FR-865 says every manifest entry has `overwrite: never` (`feature-requests/FR-865-ramp-installer.md:59-62`), but also allows `--force` to overwrite (`feature-requests/FR-865-ramp-installer.md:84-88`). It calls the installer reversible (`feature-requests/FR-865-ramp-installer.md:26-28`) and requires rollback to delete exactly what was installed (`feature-requests/FR-865-ramp-installer.md:118-119`), but a forced overwrite cannot be reversed by deletion alone without losing the target's original file. AC-05 also has a mechanical wording defect: it says a pre-existing `AGENTS.md` "survives a run without `--force`, and is replaced with it" (`feature-requests/FR-865-ramp-installer.md:108-109`), where "with it" has no unambiguous referent.

Fold this by defining manifest action records: `created`, `skipped_exists`, and, if `--force` remains authorized, `overwritten` with before/after hashes and either a backup path sufficient to restore or an explicit statement that forced overwrites are not covered by rollback. Revise AC-05 to say exactly: without `--force`, sentinel content survives; with `--force`, it is replaced by the installer stub and the prior content is either backed up and restorable or the action is refused. Revise AC-10 so rollback tests prove the chosen contract, not just deletion.

### R-5: Resolve the git-in-target contradiction

Define how the installer proves a target is a git repo root without violating its own "no git invocation in the target" rule. FR-865 requires refusal when `<target>` is not a git repo root or is this repo (`feature-requests/FR-865-ramp-installer.md:90-93`), while AC-08 says the installer contains no `git` invocation in the target (`feature-requests/FR-865-ramp-installer.md:114-115`). Those can coexist only if root detection is filesystem-based and deliberately limited, or if the prohibition is narrowed to mutating git commands.

Fold this mechanically by choosing one contract: either inspect `<target>/.git` and path identity only, with documented limitations for worktrees, or allow read-only `git -C <target> rev-parse --show-toplevel` while forbidding mutating target git commands. Add tests for normal repo, non-repo directory, worktree if supported, nested subdirectory if refused, and self-repo refusal.

### R-6: Add an explicit human-review gate for shipped enforcement infrastructure

Treat the copied hooks, CI, commit gates, judge/review scripts, and skill directories as enforcement infrastructure. Judge doctrine requires enforcement-infrastructure changes to be treated as adversarial input and gated for human review (`.github/skills/judge-fr/doctrine.md:96-101`), and repo doctrine likewise treats agent/vendor instruction and enforcement surfaces as untrusted boundaries (`.github/copilot-instructions.md:81-85`, `229-236`). FR-865 currently installs those surfaces mechanically, but has no acceptance criterion that the exact curated asset set was reviewed before it becomes a distributor.

Fold this by adding a gate that the manifest and rendered asset tree are human-reviewed before first non-scratch use, with the reviewed source commit SHA recorded in `docs/ramp-manifest.md`. This does not authorize changing `.github/hooks/`, CI behavior, judge/review doctrine, graph-authoring doctrine, or spike/unenforced-repo detector behavior in yamlgraph itself; it authorizes only adding a curated installer asset set and tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-865-ramp-installer.md` folding R-1 through R-6 |
| D-2 | `scripts/ramp.sh` mechanical installer |
| D-3 | `ramp/manifest.yaml` schema and curated ramp asset source tree |
| D-4 | Curated Tier-1, Tier-2, and Tier-3 asset files named by the manifest |
| D-5 | Unit/integration tests using scratch git repositories only |
| D-6 | Rollback documentation and tests for the exact manifest action model |
| D-7 | FR implementation-status update with source commit SHA and non-secret validation evidence |

Not authorized: applying the ramp to `sheikkinen/deviant-daily`; modifying any sibling repository; creating or editing `graph.yaml` or `prompts/*.yaml` artifacts; authoring FR-866 graph outputs; generating or landing target-specific doctrine/RTM/incidents; archiving, deleting, renaming, transferring, or changing settings on `scripture-dev`; changing yamlgraph's live `.github/hooks/`, CI enforcement, judge/review/graph-authoring doctrine, spike detector, or unenforced-repo warning behavior; copying hook logs, pycache, audit trails, credentials, token-bearing logs, or target repo archives into committed ramp assets.

## Revised acceptance criteria

- [ ] AC-01: FR-865 is revised to define the supported target contract, curated asset source tree, exact manifest schema, overwrite/rollback model, git-root detection contract, and human-review gate from R-1 through R-6.
- [ ] AC-02: `ramp/manifest.yaml` schema validation runs in CI/test, and every entry has relative normalized `source`, relative normalized `destination`, `tier`, executable-mode metadata where needed, and an overwrite policy whose values match the implemented behavior.
- [ ] AC-03: Manifest validation rejects absolute paths, `..` traversal, directory sources, missing source files, symlink sources unless explicitly allowed, generated/cache/log paths, and duplicate destinations.
- [ ] AC-04: Tier expansion is mechanical and monotonic: Tier 2 installs Tier 1 plus Tier 2, Tier 3 installs Tier 1 plus Tier 2 plus Tier 3; tests assert set containment from the manifest rather than hardcoded lists.
- [ ] AC-05: `--tier {1,2,3} --dry-run` each prints every action it would take from the manifest, including `create`, `skip exists`, or `overwrite` status as applicable, writes zero files, and exits 0.
- [ ] AC-06: A Tier-1 install into a scratch supported repo creates all Tier-1 destinations from curated ramp sources; installed files match those curated sources byte-for-byte except documented templated/stub fields such as the `AGENTS.md` stub.
- [ ] AC-07: A second identical run changes no file content or mtime and reports every already-present destination as skipped; exit 0.
- [ ] AC-08: A pre-existing `AGENTS.md` with sentinel content survives without `--force`; the with-`--force` behavior is tested according to the revised backup/restore/refusal contract.
- [ ] AC-09: `docs/ramp-manifest.md` records every destination, source path, action taken, source commit SHA, and source/installed hashes; a test parses it and verifies it is sufficient for the documented rollback behavior.
- [ ] AC-10: Rollback is documented and tested against a scratch repo: it deletes only files created by the installer and either restores forced-overwrite backups or refuses forced overwrite when restoration is not supported.
- [ ] AC-11: The installer refuses a non-repo path, this repository, an unsupported target shape, and any target path that would escape the repo root; each refusal exits non-zero and writes nothing.
- [ ] AC-12: Source scans assert the installer and curated assets contain no LLM call, no network call, no target-repo mutating `git` command, no secret material, no hook logs, no pycache, and no unresolved yamlgraph-only assumptions outside the explicitly reviewed contract.
- [ ] AC-13: If a CI workflow is installed, fixture tests prove the exact supported target suite command and ruff command run as documented; otherwise the workflow is an explicit setup stub and is not described as an active gate.
- [ ] AC-14: The manifest and curated enforcement assets are human-reviewed before first non-scratch use; the FR records the reviewed source commit SHA and any approved deviations.
- [ ] AC-15: Tests are added before implementation for the installer behavior above, with RED/GREEN evidence recorded in the FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-865-ramp-installer.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | No target repository may be modified during FR-865 enforcement except disposable scratch repos created by tests. | GATE |
| C-4 | No `graph.yaml` or `prompts/*.yaml` artifact may be created or materially modified under FR-865; graph work belongs to FR-866 and its governed authoring route. | GATE |
| C-5 | Do not archive, delete, rename, transfer, or change settings on `scripture-dev`; salvage/retirement belongs to FR-868. | GATE |
| C-6 | Do not change yamlgraph's live hook, CI, judge/review, graph-authoring, spike-detector, or unenforced-repo-warning behavior under this FR; only curated copied assets and installer tests are in scope. | GATE |
| C-7 | The installer must fail closed on path ambiguity, manifest validation failure, unsupported target shape, and rollback-unsafe overwrite behavior. | GATE |
| C-8 | The first real target application remains FR-867; FR-865 may prove behavior only with scratch repos and recorded dry-run output. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the mechanical `scripts/ramp.sh` installer, curated ramp asset manifest/source tree, scratch-repo tests, and rollback documentation within the frozen scope above.
