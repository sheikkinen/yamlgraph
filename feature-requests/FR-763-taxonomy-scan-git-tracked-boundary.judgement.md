# Judgement: FR-763 Example taxonomy scanner must scope discovery to git-tracked files

**Verdict:** APPROVED WITH REVISIONS — the tracked-tree boundary fix is sound, but authority activates only after the FR removes the unsupported hook claim, drops the unrelated direct-import cleanup rider, and updates the CAP-213 contract it is changing.

**Prior art:** The noun-overlap hits (FR-759 `otel-observability-boundary`, matching on *scan/boundary*) are not substantive — FR-759 governs the OTel per-node export boundary, an unrelated subsystem. The governing prior art is FR-762 (CAP-213), which this FR fixes, plus FR-760/FR-761 as cited context (all reviewed against, above). No prior FR, approved or rejected, has proposed scoping example-root discovery to the git-tracked tree; the territory is new.

**Reviewed against:** `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/diary/diary-2026-07-27-sixteen-not-approveds-forensic.md`; `feature-requests/FR-762-example-dependency-taxonomy.md`; `feature-requests/FR-762-example-dependency-taxonomy.judgement.md`; `capabilities/CAP-213-example-dependency-taxonomy.yaml`; `ARCHITECTURE.md`; `scripts/example_taxonomy_scan.py`; `scripts/direct_import_scan.py`; `tests/unit/test_example_taxonomy_scan.py`; `tests/unit/test_direct_import_scan.py`; `.pre-commit-config.yaml`; direct repository search for `example-taxonomy-check`, `example_taxonomy_scan.py --check`, `dependency-taxonomy`, `FR-763`, and `PENDING_GAPS`.

## What is sound

The problem is real and correctly located at the boundary. The FR says `scripts/example_taxonomy_scan.py` walks the raw filesystem under `examples/` and therefore admits gitignored generator output roots (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:16-23`). The implementation confirms that discovery is an `os.walk(examples_root)` over directories, followed by filesystem marker checks (`scripts/example_taxonomy_scan.py:161-181`), while graph YAML, Python entrypoint, and README checks read from globbed filesystem files (`scripts/example_taxonomy_scan.py:97-158`). The cited forensic independently records the same residual: ignored `examples/yamlgraph_gen/outputs/*` directories are counted as roots, causing local false-stale failures while CI stays green on clean checkouts (`docs/diary/diary-2026-07-27-sixteen-not-approveds-forensic.md:70-79`).

The proposed normalization target is architecturally aligned. Repo doctrine names the one law as normalizing where external data enters (`.github/copilot-instructions.md:47-50`) and names `workspace_is_not_boundary` as the trap where editor/workspace visibility is mistaken for ownership (`.github/copilot-instructions.md:84-85`). FR-763 applies that directly: filesystem data enters at root discovery, so discovery should be scoped to git-tracked paths before classification (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:63-77`).

The change is feasible with existing surfaces. `build_taxonomy()` and `classify_root()` already accept overridable roots (`scripts/example_taxonomy_scan.py:403-421`), and CAP-213 explicitly requires tests to exercise isolated fixture trees rather than the live repo (`capabilities/CAP-213-example-dependency-taxonomy.yaml:47-50`). Existing tests already cover discovery and classification through `tmp_path` fixtures (`tests/unit/test_example_taxonomy_scan.py:38-478`), so a tmp git repo regression can be added without introducing new infrastructure.

The strategic classification is a contrib/example bug fix, not a framework primitive. It changes the generator for CAP-213's example dependency taxonomy (`capabilities/CAP-213-example-dependency-taxonomy.yaml:6-24`) and preserves the taxonomy schema/content contract (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:79-80`). The acceptance criteria are mostly mechanical: ignored roots, untracked roots, byte-identical regeneration, fallback warning, requirement tags, and changelog are all directly testable (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:82-100`).

## Required revisions

### R-1: Correct the unsupported pre-commit hook claim

Replace the first-consumer wording that names an `example-taxonomy-check` pre-commit hook (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:8-12`) with a committed, evidenced surface: developers running `python scripts/example_taxonomy_scan.py --check` or any existing wrapper that is actually present in the repository. Direct repository search found no committed `example-taxonomy-check` hook, and `.pre-commit-config.yaml` contains no taxonomy hook entry; the adjacent dependency hook is `direct-import-scan --strict` only (`.pre-commit-config.yaml:108-116`). If a new pre-commit hook is desired, it is enforcement infrastructure and must be a separate human-reviewed scope, not implied by this bug fix.

### R-2: Remove or split the direct-import `PENDING_GAPS` cleanup rider

Delete the cleanup rider from FR-763's Related section (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:121-124`) or move it to a separate FR. The tracked-boundary defect lives in `scripts/example_taxonomy_scan.py` root discovery; removing the FR-760 `langchain_core` `PENDING_GAPS` entry lives in `scripts/direct_import_scan.py` (`scripts/direct_import_scan.py:126-159`) and does not help ignored generator outputs stop becoming taxonomy roots. Under the single-responsibility criterion, this FR may mention the cleanup as adjacent context, but it must not authorize touching `scripts/direct_import_scan.py`.

### R-3: Fold the git-tracked boundary into CAP-213's requirement contract

Add an acceptance criterion and scope item requiring `capabilities/CAP-213-example-dependency-taxonomy.yaml` to be updated so REQ-YG-571 states that root discovery and marker evaluation are scoped to git-tracked files when running in a git work tree. If the repository convention regenerates `ARCHITECTURE.md` from capability files, include the generated `ARCHITECTURE.md` change as part of the same deliverable. CAP-213 currently describes filesystem root discovery with only noise/hidden pruning (`capabilities/CAP-213-example-dependency-taxonomy.yaml:7-24`, `capabilities/CAP-213-example-dependency-taxonomy.yaml:30-50`; `ARCHITECTURE.md:2639-2647`), so changing behavior without changing the governing requirement would leave tests and doctrine out of sync.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/example_taxonomy_scan.py`: root discovery and marker evaluation normalize candidates to git-tracked files before classification. |
| D-2 | `tests/unit/test_example_taxonomy_scan.py`: regression coverage using an isolated tmp git repo for ignored and untracked roots, plus fallback behavior outside a git work tree. |
| D-3 | `capabilities/CAP-213-example-dependency-taxonomy.yaml`: REQ-YG-571 updated to include the tracked-tree boundary. |
| D-4 | `ARCHITECTURE.md`: regenerated capability text only if required by the existing capability aggregation workflow. |
| D-5 | `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md`: implementation status/decisions after enforcement. |
| D-6 | `changelog/unreleased/`: one changelog fragment for the bug fix. |

Not authorized: adding or modifying pre-commit hooks, CI workflows, branch protection, judge/review doctrine, or hook infrastructure; changing `scripts/direct_import_scan.py` or its `PENDING_GAPS`; changing the taxonomy schema; adding dependency declarations; adding a second taxonomy/dependency scanner; parsing `.gitignore` manually instead of asking git; committing phantom `examples/dependency-taxonomy.yaml` rows from ignored or untracked files.

## Revised acceptance criteria

- [ ] AC-01: In a git work tree, root discovery obtains the tracked path set under `examples/` once via git and never treats ignored or untracked files as discovery input.
- [ ] AC-02: Root markers are evaluated against tracked files only: an ignored or untracked `graph.yaml`, Python main entrypoint, or README usage command cannot create a taxonomy row even when the directory contains other filesystem artifacts.
- [ ] AC-03: A tmp git repo regression proves a gitignored directory under `examples/yamlgraph_gen/outputs/` containing `graph.yaml` produces no taxonomy row.
- [ ] AC-04: `example_taxonomy_scan.py --check` (or the checked code path with monkeypatched module constants) passes in a fixture checkout that contains the ignored output directory from AC-03 and a matching committed `examples/dependency-taxonomy.yaml`.
- [ ] AC-05: Regeneration in a checkout with ignored generator outputs is byte-identical to regeneration from the same tracked tree without those outputs.
- [ ] AC-06: An untracked-but-not-ignored example root does not create a taxonomy row; after that same file is `git add`ed, it is eligible for discovery and taxonomy drift becomes visible.
- [ ] AC-07: Outside a git work tree, the scanner emits a warning and preserves the current filesystem-walk behavior so exported archives and existing non-git fixture tests remain usable.
- [ ] AC-08: CAP-213 / REQ-YG-571 is updated to state the git-tracked discovery boundary, and every new or changed test is tagged with `@pytest.mark.req("REQ-YG-571")`.
- [ ] AC-09: No changes are made to `scripts/direct_import_scan.py`, `PENDING_GAPS`, pre-commit hooks, CI workflows, or taxonomy schema under this FR.
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Normalize at root discovery. Do not implement this as post-classification row filtering or as a hard-coded prune for `yamlgraph_gen/outputs`; the bug class is filesystem scope, not that one directory name. | GATE |
| C-2 | Use git as the source of truth for tracked paths. Do not reimplement `.gitignore` matching semantics in Python. | GATE |
| C-3 | Fallback is allowed only when git is unavailable or the target tree is not a git work tree; unexpected git errors inside a work tree must fail loudly rather than silently falling back to filesystem discovery. | GATE |
| C-4 | Do not add or modify enforcement infrastructure under this FR. A new `example-taxonomy-check` hook or CI gate requires separate human-reviewed authority. | GATE |
| C-5 | Do not change `scripts/direct_import_scan.py` or remove `PENDING_GAPS` entries under this FR; that cleanup is orthogonal and must be split if desired. | GATE |
| C-6 | `examples/dependency-taxonomy.yaml` should remain byte-identical for the current tracked tree; any content change must be justified by a tracked-file discovery difference, not by ignored or untracked local artifacts. | GATE |

Authority granted: after R-1 through R-3 are folded into the FR, the enforcer may implement the git-tracked discovery boundary for the example taxonomy scanner, update CAP-213's requirement text, add the specified regression tests, and add the changelog fragment within the frozen surfaces above.
