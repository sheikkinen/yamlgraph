# Feature Request: Harden retirement witnesses — assert tracked absence, not filesystem absence

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-08-30
**First consumer / first event:** any maintainer running the retirement
witnesses in a long-lived working tree — the first event is the next local
`pytest tests/unit/test_fr909_a2a_retirement.py`, which fails today on a
checkout where the retirement is correct.
**Research:** in-body evidence table below (FR-889 style); every row was
produced by the commands shown, on the main checkout at `667dfdb2`.
**`is_this_a_graph`:** No. This is a defect fix in three test modules — no
LLM stage, no multi-item fan-out, no graph or prompt authored or modified.
**Prior art:** FR-909, FR-910, FR-915 (the three witnesses being hardened —
this FR fixes them, it does not reopen their retirements); FR-858 (whose
witness already uses the `git ls-files` form this FR generalises); FR-717
(created the `yamlgraph/a2a` package whose directory is the residue).

## Summary

Three retirement witnesses assert `Path.exists()` where their own acceptance
criteria specified *tracked* absence. Switch them to `git ls-files`, and add
import guards so a retired module cannot resurrect as an empty namespace
package.

## Value Statement

A retirement witness starts answering the question it was written to answer,
and stops passing in CI while failing on every developer's machine.

## Problem

FR-909's **AC-01 reads**: `git ls-files 'yamlgraph/a2a/*' ... prints no
files`. The witness that enforces it reads:

```python
assert not (REPO_ROOT / relative_path).exists()
```

Those are different questions. They agree on a fresh clone and diverge in any
working tree carrying build residue — which is why CI has been green since
`a07477b7` while the test fails locally.

| # | Observation | Command |
|---|---|---|
| E-1 | `test_a2a_surface_files_are_deleted[yamlgraph/a2a]` **FAILS** on main at `667dfdb2` | `pytest 'tests/unit/test_fr909_a2a_retirement.py::test_a2a_surface_files_are_deleted[yamlgraph/a2a]'` |
| E-2 | The retirement is nonetheless correct: **0 tracked files** under that path | `git ls-files yamlgraph/a2a/` |
| E-3 | What survives on disk is one stale `__pycache__/` dated Jul 24 — invisible to `git status` because `__pycache__` is gitignored | `ls -la yamlgraph/a2a/` |
| E-4 | The leftover directory is an **importable namespace package**: `import yamlgraph.a2a` succeeds, returning `<module 'yamlgraph.a2a' (namespace)>` with `__file__: None` | `python -c "import yamlgraph.a2a"` |
| E-5 | All three retirement witnesses share the `.exists()` form; only the package-directory case manifests today (a deleted *file* leaves no directory behind) | `rg -n 'exists\(\)' tests/unit/test_fr9{09,10,15}_*.py` |
| E-6 | The suite state: `1 failed, 21 passed` across the three witness modules | `pytest tests/unit/test_fr909… test_fr910… test_fr915…` |

E-4 is the part that matters. A retired module that still imports — silently,
as an empty namespace — is worse than one that fails loudly: downstream code
guarded by `try: import yamlgraph.a2a` takes the wrong branch.

This is the third instance today of one failure shape: **a check that answers
a question adjacent to the one it was written to answer.** FR-910's C-3
asserted a consumer that had not existed for seven months; FR-915's AC-03
could only be satisfied literally by editing another demo's proof artifact;
this one tests the filesystem where the criterion said the repository.

## Ideal Result

Each retirement witness asks git what is tracked and asks Python what is
importable — the two questions that actually define "retired". Build residue
in a developer's tree is irrelevant to the verdict, and a resurrected
namespace package is caught by name.

## Proposed Solution

1. **Tracked absence** — in `test_fr909_a2a_retirement.py`,
   `test_fr910_mcp_retirement.py`, `test_fr915_mastra_demo_retirement.py`,
   replace `Path.exists()` deletion assertions with a `git ls-files <path>`
   check returning no output. One shared helper per module (these are
   separate test modules by design; a shared conftest helper would couple
   three FRs' witnesses).
2. **Import guard** — assert the retired module paths are not importable:
   `yamlgraph.a2a`, `yamlgraph.a2a.server`, `yamlgraph.a2a.message`,
   `yamlgraph.contrib.a2a_client`, `yamlgraph.cli.a2a_commands`,
   `yamlgraph.export.mcp`. Each must raise `ModuleNotFoundError` — a
   namespace-package hit returns a module object and therefore fails.
3. **Confessions** for the new `subprocess`/`S603` suppressions, following
   CONF-432/433/434 (the FR-858 witness precedent).

**Not in scope:** re-opening any retirement; changing what was deleted;
`.gitignore` policy for `__pycache__`; adding a cleanup hook or CI step that
prunes stale directories; the ADR-001 conftest scoping issue observed
separately.

## Acceptance Criteria

- [ ] AC-01: no retirement witness asserts `Path.exists()` for a deleted path; each uses `git ls-files` and asserts empty output
- [ ] AC-02: `test_fr909_a2a_retirement.py` passes on a working tree containing a stale untracked `yamlgraph/a2a/__pycache__/` (the E-1 reproducer)
- [ ] AC-03: an import guard asserts `ModuleNotFoundError` for each retired module path listed in Proposed Solution item 2; the guard fails while a namespace-package directory exists
- [ ] AC-04: with the stale directory removed, the three witness modules pass — `22 passed`, matching E-6's total
- [ ] AC-05: `python scripts/noqa_coverage.py --strict` passes with confessions for any new suppressions
- [ ] AC-06: full unit suite passes; `python scripts/req_coverage.py --strict` passes
- [ ] AC-07: no production code under `yamlgraph/` is modified — `git diff --name-only` contains only `tests/`, `docs/confessions.md`, `feature-requests/`, and `changelog/`
- [ ] AC-08: changelog fragment under `changelog/unreleased/` with `type: fix` naming FR-924

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| **Harden the witnesses (chosen)** | Fixes the check at the boundary where the question is asked; catches the namespace-package resurrection that `.exists()` and `git ls-files` both miss. |
| Delete the stale directory and leave the tests alone | REFUTED — `downstream_fix`: it repairs one machine and leaves the wrong assertion in place for the next residue. |
| Add `__pycache__` cleanup to a hook or CI | REFUTED — treats a symptom in the developer's tree, adds a gate, and still lets a genuinely resurrected module pass the witness. |
| Move all three witnesses to a shared conftest helper | REFUTED — couples three independently-judged FRs' witnesses; a change to one FR's retirement would ripple into the others' tests. |
| Do nothing; CI is green | REFUTED — CI is green *because* it checks out clean. The witness is supposed to hold on the machines where retirement decay actually happens. |

## Related

- Witnesses fixed: FR-909, FR-910, FR-915
- Form adopted from: FR-858 (`git ls-files` witness), CONF-432/433/434
- Residue origin: `yamlgraph/a2a/__pycache__/` (Jul 24), orphaned by `a07477b7`
- Failure-shape siblings recorded the same day: FR-910 C-3, FR-915 AC-03

## Judgement (pending)

Not yet judged. Route: `scripts/judge.sh feature-requests/FR-924-harden-retirement-witnesses.md`.
