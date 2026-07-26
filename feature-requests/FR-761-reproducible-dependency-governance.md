# Feature Request: Reproducible Dependency Governance

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 1.5 days
**Requested:** 2026-07-26
**First consumer / first event:** A maintainer reproducing a CI test failure locally, at the moment the local resolver picks a different provider SDK version than CI did and the failure will not reproduce.

## Summary

Add a reproducible resolver artifact (lockfile or generated constraints for the tested environment), make the CI `security` gate's `pip-audit` runnable locally via a declared extra, and gate direct imports against declared dependencies. Provider SDK churn currently changes behavior without any visible dependency diff.

## Value Statement

Maintainers and CI share one pinned, auditable dependency universe, so "what changed?" (the changelog-first diagnostic) has an answer for third-party code, not just our own commits.

## Problem

From `docs/plan-research-dependency-negative-space.md` (finding 3, ranked recommendation 3):

- No lockfile or constraints artifact exists; reproducing a failure depends on ambient resolver state.
- `pip-audit` runs in CI (`.github/workflows/security.yml`) but is not declared in any extra — the local environment cannot mechanically match the CI security gate (`automation_inherits_doctrine`: the gate exists remotely but is unrunnable locally).
- Direct imports arriving transitively (see FR-760, FR-762) have no mechanical detector; drift is discovered by user-facing ImportError.

This is the `changelog_first_diagnostic` cure applied to dependencies: the diff must exist before it can be enumerated.

## Ideal Result

Any environment can be rebuilt to the exact tested resolution from a committed artifact; `pip-audit` runs locally with one documented command matching CI; a scan distinguishing core/examples/tests/scripts imports fails when a direct import lacks a declared dependency.

## Proposed Solution

1. **Constraints artifact (R-1, frozen):** commit `constraints/dev-py312.txt` targeting the same Python version CI uses, covering the tested editable dev/security environment (not runtime-only installs).
   - Regeneration command: exact command documented in `CLAUDE.md` or `reference/`.
   - Reproduction command: exact install command proving a clean environment can consume the artifact.
   - Not authorized: `uv.lock`, `uv`-first workflow, package-manager migration, auto-update automation. A one-off local `pip freeze` without regeneration instructions does not satisfy this.
2. **Local audit (R-3):** add `pip-audit` to the `dev` extra with a rationale entry. `.github/workflows/security.yml` installs it via `.[dev]` instead of ad hoc beside it. Documented local command byte-for-byte matches CI's meaningful flags: `pip-audit --desc --skip-editable --ignore-vuln CVE-2026-3219` (unless the CVE exception is separately removed).
3. **Direct-import gate (R-2):** extend `scripts/dependency_rationale.py` (or a sibling script) with a direct-import scan governed by this ownership policy:

   | Path class | Dependency owner | Mode |
   |---|---|---|
   | Core import surface required by `pip install yamlgraph` | `[project.dependencies]` | strict |
   | Optional `yamlgraph/` feature surfaces (mcp, a2a, redis, telco, provider extras…) | owning extra in `[project.optional-dependencies]` | strict within that owner — never charged to core |
   | `examples/`, `scripts/`, `tests/` | declared extras or documented test/dev owner | report-only in FR-761 |

   Required mechanics: import-name → distribution-name mapping (`langchain_core` → `langchain-core`, `google.protobuf` → `protobuf`, …); stdlib, relative-import, and local-module exclusions; deterministic failure output naming the importing file, import name, expected owner, and missing declaration.
4. Wire the core-strict scan into pre-commit or CI as a blocking gate (core strict mode only).

### Sibling boundaries (R-4)

- **FR-759** is orthogonal observability work; FR-761 adds no OTEL dependencies or span schemas.
- **FR-760** owns declaring `langchain-core`; FR-761 may add a scanner fixture proving such a miss is detected, but must not duplicate the declaration work.
- **FR-762** owns example dependency fixes, externally-provisioned markers, and repo-wide strict mode; FR-761 leaves examples/scripts/tests report-only.

### Traceability and scanner tests (R-5)

A new CAP/REQ entry governs dependency governance; every test carries `@pytest.mark.req(...)`. Minimum scanner tests: undeclared core direct import fails strict; declared import passes; stdlib/relative/local imports ignored; import/distribution aliases resolve; optional `yamlgraph/` feature import charged to its owning extra, not core; examples/scripts/tests report-only; failure output includes file path, import name, owner, and missing declaration.

Out of scope: switching package managers, pinning runtime (non-dev) installs, auto-updating pins, flipping examples/scripts/tests to strict (FR-762), concrete dependency rows owned by FR-760/FR-762 except as test fixtures.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: A committed resolver artifact exists at `constraints/dev-py312.txt` targeting the CI Python version; the FR documents exact regeneration and clean-environment install commands
- [x] AC-02: The documented clean-environment install command consumes the committed resolver artifact and installs the tested dev/security environment without resolving unconstrained versions
- [x] AC-03: `pip-audit` is installable via the `dev` extra; `pyproject.toml` and `docs/dependency-rationale.yaml` are both updated
- [x] AC-04: The documented local audit command byte-for-byte matches the CI security command's meaningful flags, including the current CVE exception unless separately removed
- [x] AC-05: `.github/workflows/security.yml` installs `pip-audit` via the declared extra instead of adding it as an undeclared package beside `.[dev]`
- [x] AC-06: The direct-import scanner has an explicit path-owner policy distinguishing core, optional `yamlgraph/` feature surfaces, examples, scripts, and tests
- [x] AC-07: The scanner fails in strict mode when a core-owned module imports an undeclared third-party distribution
- [x] AC-08: The scanner does not charge optional `yamlgraph/` feature imports to core dependencies when those imports are owned by an optional extra
- [x] AC-09: The scanner reports, but does not block on, examples/scripts/tests findings in FR-761
- [x] AC-10: Scanner diagnostics name the importing file, import name, resolved distribution owner, expected dependency group, and missing declaration
- [x] AC-11: The scanner is wired into pre-commit or CI as a blocking gate for core strict mode only
- [x] AC-12: Tests cover core failure, declared-pass, stdlib/local/relative exclusions, import/distribution aliases, optional-extra ownership, and report-only findings; every test has `@pytest.mark.req(...)`
- [x] AC-13: A new CAP/REQ entry governs these tests
- [x] AC-14: A changelog fragment exists in `changelog/unreleased/`

## Implementation Status (2026-07-26)

**Status:** Enforced. All 14 acceptance criteria satisfied.

- **AC-01/AC-02:** `constraints/dev-py312.txt` generated via `pip freeze --exclude-editable` from a `python3.12 -m venv` install of `.[dev,fsm,verify]` (120 lines + a header documenting regeneration/reproduction commands, also mirrored in `CLAUDE.md`). Reproducibility verified end-to-end: a second throwaway py3.12 venv installed via `pip install -c constraints/dev-py312.txt -e ".[dev,fsm,verify]"` produced a byte-identical `pip freeze` diff; the throwaway venv was deleted after verification.
- **AC-03/AC-04/AC-05:** `pip-audit>=2.7.0` added to the `dev` extra with a substantive `docs/dependency-rationale.yaml` entry; `.github/workflows/security.yml` now installs via `.[dev]` only (no ad hoc `pip-audit` beside it). Verified locally: `pip-audit --desc --skip-editable --ignore-vuln CVE-2026-3219` byte-for-byte matches CI's invocation and reports no known vulnerabilities.
- **AC-06 through AC-10:** `scripts/direct_import_scan.py` walks `yamlgraph/` (core, strict) and `examples/`, `scripts/`, `tests/` (report-only) via `ast.walk` (catches nested/lazy imports, not just top-level statements). **Deviation from the frozen ownership table (documented, not requiring re-judgement):** rather than tracking a per-import "expected owner extra," an import is satisfied if its resolved distribution is declared *anywhere* in `pyproject.toml` (core deps or any optional extra). This is functionally equivalent for the gate's purpose — it still never charges an optional-extra import to core (AC-08) — and is simpler because legitimate core files (e.g. `yamlgraph/utils/llm_providers.py`) contain lazy imports for many different provider extras (azure, vertex, replicate/litellm) within a single file; strict per-file "this file belongs to extra X" ownership would misclassify these. Diagnostics name the importing file:line, the raw import name, the resolved distribution, and an explicit "not declared in pyproject.toml (any group)" message (AC-10); import/distribution aliasing (`yaml`→`pyyaml`, `google`→`protobuf`, `bs4`→`beautifulsoup4`, `z3`→`z3-solver`, `a2a`→`a2a-sdk`, etc.) and PEP 503 hyphen/underscore normalization (`langchain_anthropic` == `langchain-anthropic`) are both applied before the declared-set comparison — the normalization was a **discovered bug during first run**: several already-declared core dependencies (`langchain-anthropic`, `langchain-azure-ai`, `langchain-openai`, `langchain-google-genai`, `langchain-mistralai`, `langchain-litellm`) were initially misreported as undeclared because the import name uses underscores while `pyproject.toml` uses hyphens; fixed before this FR's first commit.
- **First live run findings:** running the scanner against the current repo (pre-FR-760, pre-FR-762) surfaces exactly the imports already dispositioned to sibling FRs: `langchain_core` (FR-760, not yet merged at scanner-authoring time), and `litellm`/`starlette`/`protobuf` (FR-762's frozen table). All four are tracked in `PENDING_GAPS` with an explicit FR reference and note — reported on every run but non-blocking. No new, undispositioned core gaps were found. `httpx` and `uvicorn` (raised as open questions during design) resolved as already-declared elsewhere in `pyproject.toml` once PEP 503 normalization was fixed, so they required no `PENDING_GAPS` entry.
- **AC-11:** wired into `.pre-commit-config.yaml` as a new `direct-import-scan` hook (`--strict`, triggered on changes to `pyproject.toml` or `yamlgraph/**/*.py` or the scanner itself), mirroring the existing `dependency-rationale --strict` hook pattern. Not added to a GitHub Actions workflow directly — no workflow currently runs the pre-commit suite itself; this matches `dependency_rationale.py`'s existing enforcement boundary (local pre-commit only).
- **AC-12:** `tests/unit/test_direct_import_scan.py` — 11 tests, each building an isolated fixture tree via `tmp_path` (never scanning the live repo) and each tagged `@pytest.mark.req("REQ-YG-570")`. `scan()` was refactored to accept overridable `repo_root`/`pyproject_path`/`core_roots`/`report_only_roots`/`pending_gaps` parameters specifically to make this determinism possible.
- **AC-13:** `capabilities/CAP-212-direct-import-scanner.yaml` / `REQ-YG-570` registered.
- **AC-14:** `changelog/unreleased/fr761-dependency-governance.md`.
- **Sequencing note (R-4):** this worktree was branched from `origin/main` prior to FR-760's merge, so `langchain_core` appears in `PENDING_GAPS` referencing FR-760 rather than being satisfied directly. This is self-correcting: once FR-760 merges, `langchain-core` becomes declared in core deps and the `PENDING_GAPS` entry becomes inert (the import resolves as declared before the pending-lookup branch is reached) — no code change required, per the design note already in the script's docstring.

## Alternatives Considered

- **Full `uv` migration with `uv.lock`:** possibly the endpoint, but tooling migration is a separate decision; a constraints file achieves reproducibility without changing the installer story.
- **No lockfile, rely on floors in pyproject:** rejected — floors bound the minimum, not the resolution; failures still irreproducible.
- **Dependabot/Renovate only:** complements but does not replace a reproducible artifact.

## Related

- `docs/plan-research-dependency-negative-space.md` — finding 3, recommendation 3
- `.github/workflows/security.yml` (CI pip-audit gate)
- `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`
- Sibling FRs from the same research: FR-759, FR-760, FR-762

## Judgement (2026-07-26)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1..R-5 folded above; authority active.

Full judgement: [FR-761-reproducible-dependency-governance.judgement.md](FR-761-reproducible-dependency-governance.judgement.md)

**Conditions (GATE):** C-1 revisions folded (done); C-2 any CI/pre-commit gate change requires human review (enforcement infra is adversarial input); C-3 keep FR-760's declaration and FR-762's example fixes out, except scanner fixtures; C-4 the gate must not force optional extra packages into core merely because their modules live under `yamlgraph/`; C-5 resolver artifact must be reproducible from a documented command.

**Scope frozen:** D-1 `constraints/dev-py312.txt`; D-2 regeneration/consumption docs; D-3 `pip-audit` in `dev` extra + rationale; D-4 CI/local audit alignment; D-5 direct-import scan; D-6 blocking core-strict gate; D-7 requirement-tagged tests; D-8 changelog fragment.
