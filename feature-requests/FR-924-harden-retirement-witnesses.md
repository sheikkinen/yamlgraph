# Feature Request: Harden retirement witnesses — assert tracked absence, not filesystem absence

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded 2026-08-30)
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

A retirement witness must ask **three separate questions** (R-1, R-2), and
today the three modules conflate them:

| Question | Instrument | Passes with stale `__pycache__` residue? |
|---|---|---|
| Is it gone from the **repository**? | `git ls-files <path>` → empty | yes — residue is untracked |
| Is it gone from the **import system**? | `import x` → `ModuleNotFoundError` | **no** — an empty dir is a namespace package |
| Is it gone from the **filesystem**? | `Path.exists()` | no |

FR-909 and FR-915 asked the filesystem question where their criteria said
repository. **FR-910 is different**: its AC-01 explicitly specified
`test ! -e yamlgraph/export/mcp.py && test ! -e .vscode/mcp.json && test ! -e
reference/mcp-server.md` — filesystem absence is its actual contract and
must be preserved, not replaced (R-2, C-2).

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

Revised per judgement (R-1 separates the three questions; R-2 preserves
FR-910's filesystem contract):

1. **Tracked absence** — `test_fr909_a2a_retirement.py` and
   `test_fr915_mastra_demo_retirement.py`: replace `Path.exists()` deletion
   assertions with `git ls-files <path>` returning empty. One local helper
   per module (a shared conftest helper would couple three FRs' witnesses —
   explicitly not authorized).
2. **FR-910 keeps its filesystem checks** — `test_fr910_mcp_retirement.py`
   retains `Path.exists()` absence for `yamlgraph/export/mcp.py`,
   `.vscode/mcp.json`, and `reference/mcp-server.md` because FR-910 AC-01
   specified exactly that; it *adds* an import guard, and adds tracked-file
   checks only where they do not weaken the existing contract.
3. **Import guards** — assert `ModuleNotFoundError` for `yamlgraph.a2a`,
   `yamlgraph.a2a.server`, `yamlgraph.a2a.message`,
   `yamlgraph.contrib.a2a_client`, `yamlgraph.cli.a2a_commands` (FR-909) and
   `yamlgraph.export.mcp` (FR-910). A namespace-package hit returns a module
   object, so the guard fails — which is the point (C-5).
4. **Confessions** for new `S603` suppressions, following CONF-432/433/434.

**Expected behaviour on a tree with stale `yamlgraph/a2a/__pycache__/`**
(R-1's resolution): the tracked-absence *assertion* passes; the FR-909
witness *module* fails, because the import guard correctly reports the
namespace package. Removing the residue makes the module pass. A failing
import guard in that state is not a false failure — it is the hazard this FR
elected to witness (C-5).

**Not in scope:** re-opening any retirement; changing what was deleted;
`.gitignore` policy for `__pycache__`; adding a cleanup hook or CI step that
prunes stale directories; the ADR-001 conftest scoping issue observed
separately.

## Acceptance Criteria

Adopted verbatim from the judgement (R-1..R-3 folded; AC-10 is R-3's exact
file allowlist).

- [ ] AC-01: FR-924 states the three witness questions separately: git tracked absence, Python import absence, and retained FR-910 filesystem absence
- [ ] AC-02: `test_fr909_a2a_retirement.py` uses `git ls-files` for every path in its A2A `DELETED_PATHS`; no `Path.exists()` assertion remains in that tracked-deletion test
- [ ] AC-03: the FR-909 tracked-absence assertion passes with stale untracked `yamlgraph/a2a/__pycache__/` residue, but the FR-909 import guard fails while `import yamlgraph.a2a` succeeds; after the stale directory is removed, `pytest tests/unit/test_fr909_a2a_retirement.py -q --no-cov` passes
- [ ] AC-04: the FR-909 import guard asserts `ModuleNotFoundError` for `yamlgraph.a2a`, `yamlgraph.a2a.server`, `yamlgraph.a2a.message`, `yamlgraph.contrib.a2a_client`, `yamlgraph.cli.a2a_commands`
- [ ] AC-05: `test_fr910_mcp_retirement.py` preserves filesystem-absence checks for `yamlgraph/export/mcp.py`, `.vscode/mcp.json`, `reference/mcp-server.md`, adds non-weakening tracked-file checks for remaining retired paths, and asserts `ModuleNotFoundError` for `yamlgraph.export.mcp`
- [ ] AC-06: `test_fr915_mastra_demo_retirement.py` uses `git ls-files 'examples/demos/mastra-integration/*'`; no `Path.exists()` assertion remains in that witness
- [ ] AC-07: new `S603` suppressions documented in `docs/confessions.md`; `python scripts/noqa_coverage.py --strict` passes
- [ ] AC-08: the three witness modules pass together on a tree with no importable stale retired package directories
- [ ] AC-09: full unit suite passes; `python scripts/req_coverage.py --strict` passes
- [ ] AC-10: `git diff --name-only` contains **only**: the three witness modules, `docs/confessions.md`, `feature-requests/FR-924-harden-retirement-witnesses.md`, `feature-requests/FR-924-harden-retirement-witnesses.judgement.md`, and one FR-924 changelog fragment
- [ ] AC-11: changelog fragment under `changelog/unreleased/` with `type: fix` naming FR-924

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

## Judgement (2026-08-30)

**Verdict:** APPROVED WITH REVISIONS — full judgement:
[FR-924-harden-retirement-witnesses.judgement.md](FR-924-harden-retirement-witnesses.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | AC-02 and AC-03 contradicted each other — the FR-909 module cannot both pass with stale residue and have its import guard fail in that state | Summary now separates the three questions; AC-03 states the resolution: the tracked-absence *assertion* passes, the *module* fails until the residue is gone |
| R-2 | False claim that all three FRs specified tracked absence — FR-910 AC-01 explicitly required `test ! -e` filesystem checks | Summary and Solution item 2: FR-910 keeps filesystem absence, gains an import guard only (C-2) |
| R-3 | AC-07's directory-level allowlist would permit unrelated edits | Replaced by AC-10, an exact file allowlist |

**Conditions:** C-1–C-5 — notably C-2 (never weaken FR-910 AC-01), C-3 (import
guards must exercise the real import system: no `sys.path` monkeypatching, no
deleting residue inside the test, no `sys.modules` mutation), C-5 (a guard
failing on stale residue is a true positive).

**Scope frozen:** deliverables D-1–D-7 per judgement.
