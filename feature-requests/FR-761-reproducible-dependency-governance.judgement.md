# Judgement: FR-761 Reproducible Dependency Governance

**Verdict:** APPROVED WITH REVISIONS — the dependency-governance direction is sound, but authority activates only after the FR fixes resolver-artifact ambiguity, narrows the direct-import gate so optional `yamlgraph/` surfaces are not misclassified as core, and explicitly dispositions sibling FR boundaries.

**Reviewed against:** `feature-requests/FR-761-reproducible-dependency-governance.md`; cited evidence `docs/plan-research-dependency-negative-space.md`, `.github/workflows/security.yml`, `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `feature-requests/FR-759-otel-observability-boundary.md`, `feature-requests/FR-760-declare-langchain-core-dependency.md`, `feature-requests/FR-762-example-dependency-taxonomy.md`; dependency declarations `pyproject.toml`; enforcement surfaces `.pre-commit-config.yaml`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `ARCHITECTURE.md`, `CLAUDE.md`.

## What is sound

The problem is real and evidenced. The research record states there is no lockfile or constraints artifact, no local security-audit command matching CI, and no explicit identity for direct imports that arrive transitively (`docs/plan-research-dependency-negative-space.md:88-107`). CI currently installs `pip-audit` ad hoc beside `.[dev]` (`.github/workflows/security.yml:28-42`), while `pyproject.toml`'s `dev` extra does not include it (`pyproject.toml:38-50`). The existing dependency-rationale script only compares declared packages to rationale entries and stale module paths; it does not scan direct imports (`scripts/dependency_rationale.py:24-49`, `scripts/dependency_rationale.py:149-180`, `scripts/dependency_rationale.py:229-341`). The FR's first consumer is concrete and matches the Scripture's changelog-first diagnostic: dependency drift must leave a diff before it can be investigated (`feature-requests/FR-761-reproducible-dependency-governance.md:8-16`, `.github/copilot-instructions.md:106`, `.github/copilot-instructions.md:257`).

The proposal also preserves useful sequencing. FR-760 owns the immediate `langchain-core` declaration (`feature-requests/FR-760-declare-langchain-core-dependency.md:30-37`), and FR-762 owns example taxonomy and flipping example scans strict (`feature-requests/FR-762-example-dependency-taxonomy.md:36-53`). FR-761 can therefore be the governance mechanism rather than the dependency-fix omnibus.

## Required revisions

### R-1: Freeze one resolver artifact contract

Replace the open-ended "lockfile or generated constraints" choice with one mechanically checkable artifact contract for this FR. The FR currently leaves `uv.lock` versus constraints as an enforce-time choice (`feature-requests/FR-761-reproducible-dependency-governance.md:34`), while also declaring package-manager switching out of scope (`feature-requests/FR-761-reproducible-dependency-governance.md:39`). Fold in an explicit artifact path, Python version target, included extras, regeneration command, and reproduction command.

Minimum foldable shape:

- Artifact: `constraints/dev-py312.txt` for the same Python version CI uses (`.github/workflows/security.yml:23-31`).
- Contents: the tested editable dev/security environment, not runtime-only installs.
- Regeneration command: exact command documented in `CLAUDE.md` or `reference/`.
- Reproduction command: exact install command proving a clean environment can consume the artifact.
- Not authorized: `uv.lock`, `uv`-first workflow, package-manager migration, or auto-update automation unless a later FR explicitly grants that scope.

### R-2: Define the direct-import scanner's ownership model before gating it

Amend the FR so "strict for core" cannot be implemented as "every import under `yamlgraph/` must be in `[project.dependencies]`." `pyproject.toml` declares multiple optional feature extras whose code lives under `yamlgraph/` (`mcp`, `a2a`, `redis-simple`, `redis`, `telco`, and provider extras at `pyproject.toml:69-127`). A naive `yamlgraph/` strict scan would either force optional packages into core or fail valid optional feature modules.

Fold in a scanner policy table with these columns: path prefix, dependency owner, mode, and rationale. At minimum:

| Path class | Dependency owner | Mode |
|---|---|---|
| Core import surface required by `pip install yamlgraph` | `[project.dependencies]` | strict |
| Optional `yamlgraph/` feature surfaces | owning extra in `[project.optional-dependencies]` | strict only within that feature owner, not core |
| `examples/`, `scripts/`, `tests/` | declared extras or documented test/dev dependency owner | report-only in FR-761 |

Also require an import-name to distribution-name mapping mechanism (`langchain_core` -> `langchain-core`, `google.protobuf` -> `protobuf`, etc.), stdlib/local-module exclusions, relative-import exclusions, and deterministic failure output that names the importing file, import name, expected owner, and missing declaration.

### R-3: Make the local audit contract match CI by declaration, not prose

Choose one declared extra for `pip-audit` and require CI to install it instead of installing `pip-audit` as a separate ad hoc package. The FR currently allows either `dev` or `security` (`feature-requests/FR-761-reproducible-dependency-governance.md:35`), while CI uses `pip install -e ".[dev]" pip-audit` (`.github/workflows/security.yml:28-31`). The revised FR must name the extra and the exact local command, including `--desc --skip-editable --ignore-vuln CVE-2026-3219` unless the CVE exception is separately removed (`.github/workflows/security.yml:39-42`).

### R-4: Disposition sibling FR boundaries explicitly

Add a "Prior art / sibling boundary" subsection. It must state:

**Prior art:**
- FR-759 is orthogonal observability work; FR-761 does not add OTEL dependencies or span schemas (`feature-requests/FR-759-otel-observability-boundary.md:32-55`).
- FR-760 owns declaring `langchain-core`; FR-761 may add a scanner fixture proving such a miss is detected but must not duplicate the dependency declaration work (`feature-requests/FR-760-declare-langchain-core-dependency.md:30-37`).
- FR-762 owns example dependency fixes, externally-provisioned markers, and repo-wide strict mode; FR-761 leaves examples/scripts/tests report-only (`feature-requests/FR-762-example-dependency-taxonomy.md:40-53`).

This satisfies the judge doctrine's prior-art disposition rule before authority is granted (`.github/skills/judge-fr/doctrine.md:112-117`, `.github/copilot-instructions.md:228-231`).

### R-5: Add traceability and scanner test specifics

The FR says tests must be tagged with `@pytest.mark.req(...)` (`feature-requests/FR-761-reproducible-dependency-governance.md:47`), but it does not identify whether a new capability/REQ is required. Amend the FR to either name the existing REQ that governs dependency governance or require a new CAP/REQ entry, because repo doctrine requires every test function to link to a requirement and new capabilities to add a CAP file (`.github/copilot-instructions.md:171-174`).

Fold in the minimum scanner tests:

- undeclared direct import in core strict mode fails;
- declared direct import passes;
- stdlib, relative, and local package imports are ignored;
- import/distribution aliases resolve correctly;
- optional `yamlgraph/` feature import is charged to its owning extra, not core;
- examples/scripts/tests produce report-only findings in FR-761;
- failure output includes file path, import name, owner, and missing declaration.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One committed resolver artifact, preferably `constraints/dev-py312.txt` after R-1 is folded |
| D-2 | Documentation for regenerating and consuming the resolver artifact in `CLAUDE.md` or `reference/` |
| D-3 | Declared local audit extra for `pip-audit` in `pyproject.toml` plus rationale entry in `docs/dependency-rationale.yaml` |
| D-4 | CI/local audit command alignment in `.github/workflows/security.yml` and documentation |
| D-5 | Direct-import scan implemented in `scripts/dependency_rationale.py` or a sibling script |
| D-6 | Blocking gate for the core strict scan in pre-commit or CI |
| D-7 | Unit tests for scanner policy and resolver/audit command documentation, all requirement-tagged |
| D-8 | Changelog fragment in `changelog/unreleased/` |

Not authorized: package-manager migration; runtime dependency pinning for normal users; Dependabot/Renovate or auto-update automation; adding or fixing the concrete missing dependency rows owned by FR-760 or FR-762 except as test fixtures; OTEL dependencies or observability work owned by FR-759; flipping examples/scripts/tests to strict before FR-762; broad CI/hook rewrites beyond adding the one dependency-governance gate.

## Revised acceptance criteria

- [ ] AC-01: A committed resolver artifact exists at the path named in the revised FR and targets the CI Python version; the FR documents exact regeneration and clean-environment install commands.
- [ ] AC-02: The documented clean-environment install command consumes the committed resolver artifact and installs the tested dev/security environment without resolving unconstrained versions.
- [ ] AC-03: `pip-audit` is installable via the declared extra named in the revised FR; `pyproject.toml` and `docs/dependency-rationale.yaml` are both updated.
- [ ] AC-04: The documented local audit command byte-for-byte matches the CI security command's meaningful flags, including the current CVE exception unless separately removed.
- [ ] AC-05: `.github/workflows/security.yml` installs the declared extra for `pip-audit` instead of adding `pip-audit` as an undeclared package beside `.[dev]`.
- [ ] AC-06: The direct-import scanner has an explicit path-owner policy distinguishing core, optional `yamlgraph/` feature surfaces, examples, scripts, and tests.
- [ ] AC-07: The scanner fails in strict mode when a core-owned module imports an undeclared third-party distribution.
- [ ] AC-08: The scanner does not charge optional `yamlgraph/` feature imports to core dependencies when those imports are owned by an optional extra.
- [ ] AC-09: The scanner reports, but does not block on, examples/scripts/tests findings in FR-761.
- [ ] AC-10: Scanner diagnostics name the importing file, import name, resolved distribution owner, expected dependency group, and missing declaration.
- [ ] AC-11: The scanner is wired into pre-commit or CI as a blocking gate for core strict mode only.
- [ ] AC-12: Tests cover core failure, declared-pass, stdlib/local/relative exclusions, import/distribution aliases, optional-extra ownership, and report-only findings; every test has `@pytest.mark.req(...)`.
- [ ] AC-13: The FR names the existing REQ for these tests or adds a new CAP/REQ entry.
- [ ] AC-14: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-5 are folded into `feature-requests/FR-761-reproducible-dependency-governance.md`. | GATE |
| C-2 | Any CI or pre-commit gate change must receive human review because enforcement-infrastructure changes are adversarial input under judge doctrine. | GATE |
| C-3 | The enforcer must keep FR-760's concrete `langchain-core` declaration and FR-762's example dependency fixes out of this implementation, except for scanner fixtures. | GATE |
| C-4 | The direct-import gate must not require optional extra packages to become core dependencies merely because their modules live under `yamlgraph/`. | GATE |
| C-5 | The resolver artifact must be reproducible from a documented command; a one-off local `pip freeze` without regeneration instructions does not satisfy AC-01. | GATE |

Authority granted: after the required revisions are folded, build one dependency-governance increment: a reproducible dev/security resolver artifact, local/CI `pip-audit` declaration parity, and a core-strict direct-import scanner with report-only non-core findings.
