# Judgement: FR-865 Ramp Installer -- Generic Asset Copier with Tiers

**Verdict:** APPROVED WITH REVISIONS -- the amended installer remains the right child scope, but authority activates only after the consumer registry is made generic and the curated-asset drift contract is made mechanically checkable without changing yamlgraph's live enforcement infrastructure.

**Reviewed against:** `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-748-fr-atlas-onboarding-summary.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`. No author chat narrative was consumed, and no judge route was invoked.

**Prior art:** `feature-requests/FR-865-ramp-installer.judgement.md` is the controlling original judgement — this amendment judgement extends it for A-1/A-2 only and reverses none of its R-1…R-6; FR-864 (parent SPLIT) and FR-207 (superseded template mechanism) are dispositioned in the body; FR-866/867/868 are sibling children, non-overlap except the R-1 decoupling ruled here. No REJECTED prior art occupies this territory.

## What is sound

The parent split is now respected. FR-864 split the original ramp into child A for "generic ramp installer + copyable asset manifest" and separated target tailoring, deviant-daily application, and scripture-dev retirement (`feature-requests/FR-864-ramp-spike-to-governed.md:17-22`). FR-865's current summary stays in that lane: a mechanical installer, no LLM, no target-specific content, and no repo it does not own (`feature-requests/FR-865-ramp-installer.md:27-30`). The previous FR-865 judgement's non-authorized list also keeps sibling repos, graphs, live hook/CI doctrine, detector work, and scripture-dev settings out of this child (`feature-requests/FR-865-ramp-installer.judgement.md:57-69`, `89-102`).

The core defects from the prior judgement were folded substantially. The FR now narrows Tier 1 to Python repos with `pyproject.toml`, pytest, and ruff, refusing other shapes with no writes (`feature-requests/FR-865-ramp-installer.md:61-71`); moves source assets into a curated `ramp/assets/tier{1,2,3}` tree and forbids directory/live-root manifest entries unless justified (`feature-requests/FR-865-ramp-installer.md:72-95`); defines manifest validation against traversal, directories, missing sources, symlinks, generated paths, and duplicate destinations (`feature-requests/FR-865-ramp-installer.md:96-103`); and resolves force/rollback semantics with `created`, `skipped_exists`, and `overwritten` action records plus restore/refusal behavior (`feature-requests/FR-865-ramp-installer.md:130-137`).

Amendment A-1 fixes the central strategic trap exposed by FR-207. FR-207's template-repo mechanism was explicitly a standalone extraction with `scripture.yaml` and `render.sh` substitution (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:48-65`, `108-142`), and the cited diary explains why a distributor that does not consume its own process decays while a practicing repo stays current (`docs/diary/diary-2026-08-23-process-transfers-by-practice.md:49-52`, `86-95`). Requiring yamlgraph to run the curated Tier-1 pre-commit config against a fixture and to fail on unexplained drift (`feature-requests/FR-865-ramp-installer.md:147-159`, `218-219`) is the right correction.

The proposal is measurable and testable after revisions. AC-02 through AC-15 already define direct assertions for manifest schema, monotonic tier expansion, dry-run behavior, idempotency, overwrite/rollback, refusal cases, source scans, CI/stub behavior, human review, and RED/GREEN evidence (`feature-requests/FR-865-ramp-installer.md:203-217`). AC-16 and AC-17 add recurrence guards for curated assets (`feature-requests/FR-865-ramp-installer.md:218-219`). Strategic classification remains **contrib/governance tooling**, not a YAMLGraph framework primitive: it packages governance assets around existing repo practice and does not alter YAMLGraph runtime semantics.

## Required revisions

### R-1: Make the consumer registry generic and remove FR-867 as an FR-865 acceptance dependency

Revise A-2 so `ramp/consumers.md` is a generic source-repo registry maintained by the ramp installer, not a target-specific success criterion for FR-867. Replace the current statement that "FR-867's install must append its row" (`feature-requests/FR-865-ramp-installer.md:220`) with a checkable FR-865 criterion:

`scripts/ramp.sh <target> --tier N --record-consumer owner/repo` appends or idempotently updates exactly one `ramp/consumers.md` row after a successful non-dry-run install; `--dry-run` prints the would-be row and writes nothing; scratch tests may omit `--record-consumer`; row identity is `(target, tier, manifest hash)`; the target field is a repository slug, never an absolute local path or URL with credentials.

FR-867 may later provide the first real row, but FR-865 enforcement must not depend on modifying or successfully ramping `sheikkinen/deviant-daily`. The parent judgement made deviant-daily application a separate child (`feature-requests/FR-864-ramp-spike-to-governed.md:17-22`), and the prior FR-865 judgement kept the first real target application in FR-867 while allowing only scratch-repo proof here (`feature-requests/FR-865-ramp-installer.judgement.md:95-100`).

### R-2: Specify the curated-asset drift evidence format and keep it inside the existing test path

Revise A-1 so the drift contract is mechanically inspectable. Add fields to `ramp/manifest.yaml` or a dedicated `ramp/curation-diffs.md` that, for every curated asset mirroring a live root counterpart, records one of two states: `mirror_exact: <live path>` or `curation_diff: <record path>`. Each curation diff must name the live source, curated destination, removed/changed lines or semantic sections, and the reason each removal is domain-specific. AC-17 must fail if a mirrored asset has neither exact equality nor a recorded curation diff.

Implement "this repo's CI runs the curated Tier-1 `.pre-commit-config.yaml`" (`feature-requests/FR-865-ramp-installer.md:153-159`, `218`) as tests executed by the existing test workflow, not as a change to yamlgraph's live hook/CI enforcement policy unless a separate enforcement-infrastructure FR authorizes that policy change. The judge doctrine requires enforcement-infrastructure changes to be treated as adversarial input (`.github/skills/judge-fr/doctrine.md:96-101`), and the prior FR-865 judgement explicitly forbids changing yamlgraph's live hook, CI, judge/review, graph-authoring, detector, or warning behavior under this FR (`feature-requests/FR-865-ramp-installer.judgement.md:97-99`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-865-ramp-installer.md` folding R-1 and R-2 |
| D-2 | `scripts/ramp.sh` mechanical installer |
| D-3 | `ramp/manifest.yaml` schema and curated `ramp/assets/tier{1,2,3}/` source tree |
| D-4 | `ramp/consumers.md` registry with documented schema and idempotent update behavior |
| D-5 | Curation-drift evidence in `ramp/manifest.yaml` or `ramp/curation-diffs.md` |
| D-6 | Unit/integration tests using scratch git repositories and committed fixture scratch repos only |
| D-7 | Rollback documentation and tests for the exact manifest action model |
| D-8 | FR implementation-status update with source commit SHA and non-secret validation evidence |

Not authorized: applying the ramp to `sheikkinen/deviant-daily`; making FR-867 success a prerequisite for FR-865 completion; modifying any sibling repository; creating or editing `graph.yaml` or `prompts/*.yaml` artifacts; authoring FR-866 graph outputs; generating or landing target-specific doctrine/RTM/incidents; archiving, deleting, renaming, transferring, or changing settings on `scripture-dev`; changing yamlgraph's live `.github/hooks/`, CI enforcement policy, judge/review/graph-authoring doctrine, spike detector, or unenforced-repo warning behavior; copying hook logs, pycache, audit trails, credentials, token-bearing logs, absolute local paths, or target repo archives into committed ramp assets or registry rows.

## Revised acceptance criteria

- [ ] AC-01: FR-865 is revised to define the supported target contract, curated asset source tree, exact manifest schema, overwrite/rollback model, git-root detection contract, human-review gate, curated-asset drift evidence format, and consumer-registry contract from R-1 and R-2.
- [ ] AC-02: `ramp/manifest.yaml` schema validation runs in tests, and every entry has relative normalized `source`, relative normalized `destination`, `tier`, executable-mode metadata where needed, and an overwrite policy whose values match the implemented behavior.
- [ ] AC-03: Manifest validation rejects absolute paths, `..` traversal, directory sources, missing source files, symlink sources unless explicitly allowed, generated/cache/log paths, and duplicate destinations.
- [ ] AC-04: Tier expansion is mechanical and monotonic: Tier 2 installs Tier 1 plus Tier 2, Tier 3 installs Tier 1 plus Tier 2 plus Tier 3; tests assert set containment from the manifest rather than hardcoded lists.
- [ ] AC-05: `--tier {1,2,3} --dry-run` each prints every action it would take from the manifest, including `create`, `skip exists`, or `overwrite` status as applicable, writes zero files, prints any would-be consumer row when `--record-consumer` is provided, and exits 0.
- [ ] AC-06: A Tier-1 install into a scratch supported repo creates all Tier-1 destinations from curated ramp sources; installed files match those curated sources byte-for-byte except documented templated/stub fields such as the `AGENTS.md` stub.
- [ ] AC-07: A second identical run changes no file content or mtime and reports every already-present destination as skipped; if `--record-consumer` is used, `ramp/consumers.md` is idempotently updated rather than duplicated.
- [ ] AC-08: A pre-existing `AGENTS.md` with sentinel content survives without `--force`; the with-`--force` behavior is tested according to the revised backup/restore/refusal contract.
- [ ] AC-09: `docs/ramp-manifest.md` records every destination, source path, action taken, source commit SHA, and source/installed hashes; a test parses it and verifies it is sufficient for the documented rollback behavior.
- [ ] AC-10: Rollback is documented and tested against a scratch repo: it deletes only files created by the installer and either restores forced-overwrite backups or refuses forced overwrite when restoration is not supported.
- [ ] AC-11: The installer refuses a non-repo path, this repository, an unsupported target shape, and any target path that would escape the repo root; each refusal exits non-zero and writes nothing.
- [ ] AC-12: Source scans assert the installer and curated assets contain no LLM call, no network call, no target-repo mutating `git` command, no secret material, no hook logs, no pycache, and no unresolved yamlgraph-only assumptions outside the explicitly reviewed contract.
- [ ] AC-13: If a CI workflow is installed into targets, fixture tests prove the exact supported target suite command and ruff command run as documented; otherwise the workflow is an explicit setup stub and is not described as an active gate.
- [ ] AC-14: The manifest and curated enforcement assets are human-reviewed before first non-scratch use; the FR records the reviewed source commit SHA and any approved deviations.
- [ ] AC-15: Tests are added before implementation for the installer behavior above, with RED/GREEN evidence recorded in the FR.
- [ ] AC-16: Existing yamlgraph test/CI execution runs the curated Tier-1 `.pre-commit-config.yaml` against a committed fixture scratch repo; a failing curated config is a red build without changing yamlgraph's live hook or CI enforcement policy.
- [ ] AC-17: A drift test asserts every curated asset mirroring a live root counterpart either matches it exactly or carries a recorded curation diff naming the live source, curated destination, removed/changed material, and reason; unexplained drift fails.
- [ ] AC-18: `ramp/consumers.md` exists with a documented row schema: target repository slug, install date, tier, source SHA, manifest hash, and optional reviewed-source SHA; tests validate the format, reject absolute paths/credential-bearing URLs, and prove idempotent append/update behavior using scratch metadata only.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 and R-2 are folded into `feature-requests/FR-865-ramp-installer.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | No target repository may be modified during FR-865 enforcement except disposable scratch repos created by tests. | GATE |
| C-4 | No `graph.yaml` or `prompts/*.yaml` artifact may be created or materially modified under FR-865; graph work belongs to FR-866 and its governed authoring route. | GATE |
| C-5 | Do not archive, delete, rename, transfer, or change settings on `scripture-dev`; salvage/retirement belongs to FR-868. | GATE |
| C-6 | Do not change yamlgraph's live hook, CI enforcement policy, judge/review, graph-authoring, spike-detector, or unenforced-repo-warning behavior under this FR; only curated copied assets, manifest validation, registry behavior, and installer tests are in scope. | GATE |
| C-7 | The installer must fail closed on path ambiguity, manifest validation failure, unsupported target shape, unsafe registry identity, and rollback-unsafe overwrite behavior. | GATE |
| C-8 | The first real target application remains FR-867; FR-865 may prove behavior only with scratch repos, fixture repos, and recorded dry-run output. | GATE |
| C-9 | Consumer registry rows must never contain absolute local filesystem paths, credential-bearing URLs, secrets, tokens, hook logs, audit logs, or target-repo archives. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the mechanical `scripts/ramp.sh` installer, curated ramp asset manifest/source tree, consumer registry, scratch-repo and fixture tests, drift checks, and rollback documentation within the frozen scope above.
