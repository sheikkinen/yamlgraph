# FR-954: Faithful no-fork import simulation

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS; R-1–R-4 folded 2026-09-02; enforcement gated on human review of the judgement (C-2)
**Effort:** 0.25 days
**Requested:** 2026-09-02
**First consumer / first event:** a contributor reads `test_import_without_register_at_fork_capability` on clean main (green since `82111177`) and finds a witness that pre-imports the dependency chain (`asyncio`, `random`, `langgraph.checkpoint.base`) before deleting `os.register_at_fork` — it proves yamlgraph's local guard but overclaims Windows/no-fork import fidelity: the ordinary cold dependency chain is never exercised under the no-fork surface.
**Research:** in-body dispositioned alternatives table below (FR-952 precedent for the in-body route), restricted to the remaining Defect A decision; probe status is stated per row.
**Prior art:**
- [FR-950 fragment](../changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md) — the parent defect class (unconditional `os.register_at_fork` at import).
- [FR-713-persistent-bridge-loop.md](FR-713-persistent-bridge-loop.md) — owns CAP-198 and the witness under repair; REQ-YG-541's description already contains the no-fork semantics this witness must prove.
- [FR-952-optional-extras-must-skip-not-error.md](FR-952-optional-extras-must-skip-not-error.md) / [FR-953-windows-posix-shell-misattribution.md](FR-953-windows-posix-shell-misattribution.md) — sibling residual-class filings from the same 2026-09-02 sweep; neither touches the fork sim.

## Implementation history

This FR originally carried two defects. **Defect B** (CAP-198 attributed
only FR-713 while the FR-950 fragment claimed REQ-YG-541) was
independently diagnosed by a parallel session and shipped in PR #555
(`82111177`) byte-identically to this FR's proposal — CAP-198 now reads
`fr: FR-713, FR-950`, and the FR-242 collision gate is green on clean
main. #555 also partially cured **Defect A** by pre-importing the
dependency chain before the deletion, which unblocked the suite. Defect B
and the suite-green criteria are complete and out of active scope; only
the Defect A fidelity repair below remains.

## Summary

The Windows/no-fork import witness in
`test_import_without_register_at_fork_capability` is unfaithful twice
over: it deletes `os.register_at_fork` but not `os.fork` (a runtime no
platform exhibits), and since #555 it pre-imports the dependency chain so
the cold import path never runs under the simulated surface. Delete both
attributes, assert their absence before importing yamlgraph, and remove
the pre-import scaffold — the ordinary dependency chain becomes the seam
again.

## Value Statement

The REQ-YG-541 no-fork import guarantee ("import still succeeds where
`os.register_at_fork` is absent") is proven against the
Windows-equivalent OS capability surface through the real cold import
chain, instead of being overclaimed by a witness that bypasses it.

## Problem

`tests/unit/test_fr713_persistent_bridge.py::TestImportAndForkSafety::test_import_without_register_at_fork_capability`
simulates a no-fork runtime by deleting only `os.register_at_fork`. Real
Windows lacks **both** `os.fork` and `os.register_at_fork`. The partial
deletion creates a runtime no platform exhibits, and third-party code
legitimately breaks under it: `uuid_utils` 0.17.0 (reached via
`langchain_core.utils.uuid` during `import yamlgraph`) guards its fork
hook on `hasattr(os, "fork")` — true in the sim — then calls the deleted
`os.register_at_fork`:

```
AttributeError mid-import of langchain_core.runnables
→ partial module left in sys.modules
→ surfaced as: ImportError: cannot import name 'RunnableConfig'
  from 'langchain_core.runnables'
```

The same class exists in the 3.14 stdlib: `random` and `asyncio` register
fork hooks at import behind `os.fork` guards. #555's workaround
pre-imports those modules before the deletion, which makes the suite green
but removes the cold dependency chain from the simulated surface — the
witness no longer tests what REQ-YG-541 claims.

The misleading terminal error cost most of the diagnosis time; the causal
chain was proven by reproducing the exact subprocess and grepping
site-packages for `register_at_fork` (hit: `uuid_utils/__init__.py:39`,
guard at line 38 `if hasattr(os, "fork")`).

## Ideal Result

The import witness exercises the Windows-equivalent OS capability surface
— neither `os.fork` nor `os.register_at_fork` exists — while importing
YAMLGraph through its ordinary cold dependency chain and proving that no
bridge loop starts; production behavior and registry attribution remain
unchanged. ("Windows-equivalent OS capability surface", not a claim that
deleting two POSIX attributes simulates every property of Windows.)

## Proposed Solution

Make the simulation faithful — delete both attributes in the subprocess
setup, assert their absence, and drop the pre-import scaffold:

```python
import os
for attr in ("register_at_fork", "fork"):
    if hasattr(os, attr):
        delattr(os, attr)
assert not hasattr(os, "fork") and not hasattr(os, "register_at_fork")
import yamlgraph, yamlgraph.utils.bridge
import threading
```

This matches the real no-fork capability surface: every fork-hook consumer
in the chain (`uuid_utils`, stdlib `random`/`asyncio`) guards on
`hasattr(os, "fork")` and takes its genuine no-fork path exactly as on
Windows. No production code changes; `yamlgraph/utils/bridge.py` already
handles absence via `getattr(os, "register_at_fork", None)`.

## Acceptance Criteria

- [ ] AC-01: In `test_import_without_register_at_fork_capability`, the subprocess imports only `os` before setup; removes both `fork` and `register_at_fork` when present; asserts `not hasattr(os, "fork")` and `not hasattr(os, "register_at_fork")`; only then imports `yamlgraph`, `yamlgraph.utils.bridge`, and `threading`; and asserts that `yamlgraph-bridge-loop` did not start.
- [ ] AC-02: The subprocess contains no pre-import of `asyncio`, `random`, or `langgraph.checkpoint.base`, so the ordinary cold YAMLGraph dependency chain remains the seam under test.
- [ ] AC-03: On CPython 3.14 in the pinned `[dev]` environment with `uuid_utils >= 0.17.0`, `pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` exits zero. The validation record includes a `python` preflight that mechanically reports the Python and `uuid_utils` versions.
- [ ] AC-04: Git history contains separate RED and GREEN commits: RED adds the missing `os.fork`-absence assertion to the current one-attribute setup and records its failure; GREEN removes both attributes, removes the pre-import scaffold, and makes the targeted test file green.
- [ ] AC-05: The implementation diff contains no production, CAP, ARCHITECTURE, dependency, constraint, collision-test, or FR-950-fragment change; the FR records implementation status, a `type: fix` FR-954 changelog fragment exists without a new CAP/REQ allocation, and the final diary entry contains `Seed:`.

## Alternatives Considered

Restricted to the remaining Defect A decision. Four solution classes:

| Alternative | Probe status (2026-09-02) | Disposition |
|---|---|---|
| Two-attribute capability simulation (chosen): delete both `os.fork` and `os.register_at_fork`, assert absence, cold import chain | executed — `sed -n 38,39p .venv/.../uuid_utils/__init__.py` shows the guard `hasattr(os, "fork")`; stdlib `random`/`asyncio` fork hooks carry the same guard | ACCEPTED — every consumer takes its genuine no-fork path; the witness tests what REQ-YG-541 claims |
| Pin/patch `uuid_utils` to guard on `register_at_fork` | executed — same probe: upstream guard is correct for every real platform | REJECTED — upstream is right; our sim is the liar. Fixing the sim is normalize-at-the-boundary; patching a vendor is a downstream_fix |
| Mock `uuid_utils` (and stdlib registrants) in the test subprocess | not executed — design inspection only; no probe exists that could make a mock exercise the real import chain | REJECTED — mock_escape_hatch; the test exists to prove real import behavior on a no-fork runtime |
| Skip the test when `uuid_utils` present | executed — `.venv/bin/pip show uuid_utils` → 0.17.0 installed by the pinned constraint set, so the skip would fire everywhere | REJECTED — permanent skip = deleted witness |

**Strongest dissent** (best rejected alternative — the mock): "a mocked
`uuid_utils` isolates the seam to yamlgraph's own guard, exactly what a
unit test should do, and #555's pre-import scaffold is already a de facto
mock of the chain." Resolved: the witness exists because FR-950's defect
was an *import-chain* failure on a no-fork runtime — the phenomenon under
test IS the chain's behavior under the absent capability
(`mock_escape_hatch`: if the feature exists because of a physical
phenomenon, the test must exercise the real phenomenon). The evidence is
the defect's own history: yamlgraph's guard was green under #555's
scaffold while the chain's no-fork behavior remained unproven; only the
two-attribute simulation makes every guard in the chain
(`uuid_utils/__init__.py:38`, stdlib `random`/`asyncio`) take the path
Windows actually takes.

**`is_this_a_graph`?** No. This is one deterministic subprocess witness
edit; it has no model stage, multi-stage LLM pipeline, or fan-out.

## Out of Scope

- Not authorized (judgement C-3): changes to `yamlgraph/utils/bridge.py`;
  dependency or constraint changes; vendor patches; mocks or skips;
  changes to CAP-198, ARCHITECTURE, the FR-950 fragments, or
  `tests/unit/test_changelog_req_cross_wiring.py`; reopening Defect B;
  FR-952/FR-953 work; ramp-installer work; broader Windows simulation
  claims; unrelated refactoring.
- `test_ramp_installer::test_wrapper_delegates` — fails only when the venv
  is not on the invoking shell's PATH (`scripts/ramp.sh` `exec python3`
  resolves the homebrew interpreter, no PyYAML). Environment fact of the
  invoking shell, not a defect class; revisit only if it appears in CI.
- The 11 environment-staleness failures resolved during diagnosis (retired-
  module `__pycache__` phantoms, missing `pypsrp`, constraint drift, retired
  mastra demo's `node_modules` leftover) — no code change required.
- FR-952/FR-953 territory (optional-extras skip policy, POSIX-shell
  misattribution on the Windows host).

## Related

- `tests/unit/test_fr713_persistent_bridge.py`
- [FR-954 judgement](FR-954-fr950-residuals-fork-sim-and-cap198-attribution.judgement.md)
- `changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md`
