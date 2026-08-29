# Judgement: FR-900 Release yamlgraph so tool slots reach PyPI consumers

**Prior art:** inherits the disposition in
`FR-900-release-tool-slots-to-pypi.md` — FR-901/FR-902 are same-arc
siblings; FR-187, FR-127, and FR-196 govern CI gates that run during a
release, not the decision to cut one, and remain in force unchanged.

**Verdict:** APPROVED WITH REVISIONS — the release need is real and minimal, but authority activates only after the FR replaces the ambiguous release snippet with the canonical release command and pins the clean-venv slot smoke to an exact non-checkout procedure.

**Reviewed against:** feature-requests/FR-900-release-tool-slots-to-pypi.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-902-daily-digest-slot-bound-refactor.md; feature-requests/FR-768-tool-manifest-declaration-reuse.md; reference/release-checklist.md; scripts/release.sh; pyproject.toml; yamlgraph/__init__.py; .github/workflows/workflow.yml; .github/workflows/commitlint.yml; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; repo doctrine in project instructions; git metadata for v0.5.22 and 06d1dfe4.

## What is sound

The problem is concrete and externally observable. FR-900 names the first consumer and exact failing event: `yamlgraph-daily-digest` will run `pip install yamlgraph` and then invoke `yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml` (feature-requests/FR-900-release-tool-slots-to-pypi.md:8-10). FR-902 independently confirms the dependency: Phase 2 requires FR-900, and every published yamlgraph lacks FR-892 `--tool` (feature-requests/FR-902-daily-digest-slot-bound-refactor.md:125-154, 188-192).

The release target is tied to an already-implemented framework primitive rather than a speculative feature. FR-892 is completed (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:5), defines the invocation-time slot contract (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-79), and names `--tool SLOT=path` as the CLI binding surface (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:71, 148-150). FR-768 has already delivered manifest expansion for existing tool runtimes (feature-requests/FR-768-tool-manifest-declaration-reuse.md:5, 78-105), so this FR does not need a new runtime or graph mechanism.

Scope is appropriately small: FR-900 proposes following the existing release checklist and explicitly says "No new mechanism" (feature-requests/FR-900-release-tool-slots-to-pypi.md:74-76). The repository has a canonical release script that validates unreleased fragments, freezes them, bumps versions, regenerates the changelog, commits, and creates the tag (reference/release-checklist.md:5-20; scripts/release.sh:5-29). The tag-triggered workflow builds, checks, publishes to PyPI, and creates a GitHub release ( .github/workflows/workflow.yml:95-124, 126-145), and release hygiene checks that `changelog/<version>/` exists with no orphaned unreleased fragments ( .github/workflows/commitlint.yml:197-215).

The research and prior-art gates are satisfied for a routine release. FR-900 points its `Research:` field at an in-body alternatives table (feature-requests/FR-900-release-tool-slots-to-pypi.md:12-13), then dispositions git installs, vendoring, dropping slots, packaging examples, and doing nothing (feature-requests/FR-900-release-tool-slots-to-pypi.md:112-120). It also dispositions related FRs and explains why FR-187, FR-127, and FR-196 do not govern the release decision (feature-requests/FR-900-release-tool-slots-to-pypi.md:14-24).

Strategic classification: **operational release of an existing framework primitive**, not a new framework primitive, contrib/example, or pattern-documentation feature. The value is distribution of already-merged slot support to PyPI consumers (feature-requests/FR-900-release-tool-slots-to-pypi.md:28-36), not new product surface.

## Required revisions

### R-1: Replace the partial manual release snippet with the canonical release path

Revise `## Proposed Solution` so the executable path is:

```bash
scripts/release.sh <version>
git push && git push --tags
```

State that `<version>` must be the next unclaimed version above the current source version and PyPI version. If the FR keeps a manual fallback, it must explicitly include every state change handled by `scripts/release.sh`: freezing `changelog/unreleased/`, bumping both `pyproject.toml` and `yamlgraph/__init__.py`, regenerating `CHANGELOG.md`, committing those exact files, and creating `v<version>` (reference/release-checklist.md:5-20; scripts/release.sh:17-29; pyproject.toml:7; yamlgraph/__init__.py:6).

### R-2: Make the clean-venv slot smoke mechanically runnable outside the checkout

Replace the current "fixture pair is the smoke" wording with an exact procedure. The smoke must install `yamlgraph==<version>` in a fresh venv, copy `examples/demos/corpus_census/` to a temporary directory outside any yamlgraph checkout, run from that copied directory, and bind the fixture manifests with relative paths:

```bash
python -m venv /tmp/yamlgraph-relcheck
/tmp/yamlgraph-relcheck/bin/pip install "yamlgraph==<version>"
tmpdir="$(mktemp -d)"
cp -R examples/demos/corpus_census "$tmpdir/corpus_census"
cd "$tmpdir/corpus_census"
/tmp/yamlgraph-relcheck/bin/yamlgraph graph run graph.yaml \
  --tool discover=fixtures/discover.tool.yaml \
  --tool extract=fixtures/extract.tool.yaml \
  --var source=fixtures/corpus \
  --var rubric="classify each document's main topic in one word" \
  --var output_path="$tmpdir/corpus-census-ledger.md" \
  --var brief_path="$tmpdir/census-brief.md" \
  --var brief_rubric="What does this corpus cover overall?"
```

This closes the measurability gap caused by `examples*` being excluded from the wheel (pyproject.toml:173-175) while preserving FR-900's decision not to change packaging policy (feature-requests/FR-900-release-tool-slots-to-pypi.md:58-64, 118-120, 129-132).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-900-release-tool-slots-to-pypi.md` revisions folding R-1 and R-2 |
| D-2 | Release commit produced by `scripts/release.sh <version>` changing only release-owned artifacts: `changelog/<version>/`, `CHANGELOG.md`, `pyproject.toml`, and `yamlgraph/__init__.py` |
| D-3 | Git tag `v<version>` on the release commit, with `06d1dfe4` as an ancestor |
| D-4 | PyPI artifact `yamlgraph==<version>` published by the existing tag workflow |
| D-5 | Verification transcript or recorded Implementation Status proving the help-surface and slot-bound corpus-census smoke from a clean non-checkout venv |

Not authorized: packaging `examples/` or `examples/shared/` into the wheel; changing FR-892 slot semantics; changing FR-768 manifest semantics; editing `.github/workflows/`, hooks, release credentials, or trusted-publishing infrastructure; refactoring `yamlgraph-daily-digest`; adding the SMTP tool from FR-901; deleting or force-moving existing release tags; introducing a new release mechanism.

## Revised acceptance criteria

- [ ] AC-01: The FR is revised to fold R-1 and R-2 before enforcement starts.
- [ ] AC-02: `scripts/release.sh <version>` runs with `<version>` greater than the current source version and not already present on PyPI or as a local/remote git tag.
- [ ] AC-03: The release commit changes only the release-owned surfaces: `changelog/<version>/`, `CHANGELOG.md`, `pyproject.toml`, and `yamlgraph/__init__.py`.
- [ ] AC-04: `pyproject.toml` and `yamlgraph/__init__.py` both contain `<version>`, and `changelog/unreleased/` contains no `.md` fragments except `.gitkeep`.
- [ ] AC-05: Tag `v<version>` exists on the release commit, and `git merge-base --is-ancestor 06d1dfe4 v<version>` exits 0.
- [ ] AC-06: The existing tag workflow publishes `yamlgraph==<version>` to PyPI, or enforcement records the failed workflow URL and stops without bypassing release infrastructure.
- [ ] AC-07: In a fresh venv outside the repository, `pip install "yamlgraph==<version>"` succeeds and `yamlgraph graph run --help | grep -- '--tool'` exits 0.
- [ ] AC-08: From a copied `examples/demos/corpus_census/` directory outside any yamlgraph checkout, the exact R-2 smoke command exits 0 and writes both the ledger and brief artifacts.
- [ ] AC-09: The `examples*` wheel-exclusion finding remains recorded in the FR Related section, and no packaging-policy code change is made in this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 and R-2 into the FR before running release commands. | GATE |
| C-2 | Use the next unclaimed version if `0.5.23` is already published or tagged; do not overwrite, delete, or force-move an existing tag. | GATE |
| C-3 | Use the existing release script and tag workflow; do not edit release CI, hooks, credentials, or publishing configuration under this FR. | GATE |
| C-4 | Verify the PyPI artifact from an installed wheel in a fresh venv outside the checkout; editable installs and in-repo imports do not satisfy the release proof. | GATE |
| C-5 | If PyPI publishing, CI, or trusted publishing fails, stop with the failure recorded in the FR instead of bypassing the workflow manually. | GATE |
| C-6 | Keep `examples*` packaging out of scope; open a separate FR if shared examples/manifests should become public package artifacts. | GATE |

Authority granted: after R-1 and R-2 are folded, the enforcer may cut exactly one yamlgraph release that publishes existing FR-892 `--tool` slot support to PyPI and records the specified verification evidence.
