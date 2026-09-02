# Feature Request: FR-950 residuals — faithful no-fork simulation and CAP-198 attribution

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-02
**First consumer / first event:** a contributor on a constraint-pinned `[dev]` mac runs `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on clean main and reads 2 failures that are defects in the FR-950 enforcement itself, not in their change.
**Research:** in-body dispositioned alternatives table below (FR-952 precedent for the in-body route); every row carries a probe result executed 2026-09-02 on this host.
**Prior art:**
- [FR-950 fragment](../changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md) and branch `feat/fr950-cap198-attribution` — the parent. The branch name states the attribution intent; the merged commits changed the test and fragment but never touched `capabilities/CAP-198-persistent-bridge-loop.yaml`, so the intent is recorded but not landed. This FR lands it.
- [FR-713-persistent-bridge-loop.md](FR-713-persistent-bridge-loop.md) — owns CAP-198. REQ-YG-541's description already contains FR-950's no-fork semantics ("where absent (no-fork runtimes such as Windows) no fork setup is performed"), so shared attribution reflects reality, not convenience.
- FR-242 (`tests/unit/test_changelog_req_cross_wiring.py`) — authored the collision test whose multi-FR mechanism (`fr: "FR-A, FR-B"`, `_build_fr_to_reqs`) this FR uses as-is. No test change needed for Defect B.
- [FR-952-optional-extras-must-skip-not-error.md](FR-952-optional-extras-must-skip-not-error.md) / [FR-953-windows-posix-shell-misattribution.md](FR-953-windows-posix-shell-misattribution.md) — sibling residual-class filings from the same 2026-09-02 sweep; they cover the Windows host's failure classes, this FR covers the two failures that survive on a correctly provisioned mac. No overlap: neither touches the fork sim or the registry attribution.

## Summary

Two defects remain on clean main after the FR-951 arc, both belonging to
FR-950's enforcement: (A) the Windows/no-fork simulation in
`test_import_without_register_at_fork_capability` deletes
`os.register_at_fork` but not `os.fork`, which no real runtime exhibits;
(B) the FR-950 changelog fragment claims REQ-YG-541 while no capability
attributes FR-950, failing the FR-242 collision gate.

## Value Statement

A contributor on a pinned `[dev]` install gets a green fast suite on clean
main, and the capabilities registry tells the truth about which FRs shaped
REQ-YG-541.

## Problem

### Defect A — unfaithful no-fork simulation (test defect)

`tests/unit/test_fr713_persistent_bridge.py::TestImportAndForkSafety::test_import_without_register_at_fork_capability`
simulates Windows by deleting only `os.register_at_fork`. Real Windows
lacks **both** `os.fork` and `os.register_at_fork`. The partial deletion
creates a runtime no platform exhibits, and third-party code legitimately
breaks under it: `uuid_utils` 0.17.0 (reached via
`langchain_core.utils.uuid` during `import yamlgraph`) guards its fork
hook on `hasattr(os, "fork")` — true in the sim — then calls the deleted
`os.register_at_fork`:

```
AttributeError mid-import of langchain_core.runnables
→ partial module left in sys.modules
→ surfaced as: ImportError: cannot import name 'RunnableConfig'
  from 'langchain_core.runnables'
```

The misleading terminal error cost most of the diagnosis time; the causal
chain was proven by reproducing the exact subprocess and grepping
site-packages for `register_at_fork` (hit: `uuid_utils/__init__.py:39`,
guard at line 38 `if hasattr(os, "fork")`).

### Defect B — REQ-YG-541 attribution gap (registry defect)

`tests/unit/test_changelog_req_cross_wiring.py::TestChangelogReqIntegrity::test_no_req_collision_across_unrelated_frs`
fails on clean main:

```
REQ-YG-541 claimed by FR-950 (fragment) but FR-950 capability has no capability
```

`changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md`
claims `req: REQ-YG-541`; `capabilities/CAP-198-persistent-bridge-loop.yaml`
says `fr: FR-713` only. The merged FR-950 branch was literally named
`feat/fr950-cap198-attribution` yet never edited the CAP file.

## Proposed Solution

**A.** Make the simulation faithful — delete both attributes in the
subprocess setup:

```python
for attr in ("register_at_fork", "fork"):
    if hasattr(os, attr):
        delattr(os, attr)
```

This matches the real Windows surface, and `uuid_utils`' own guard then
takes its no-fork path exactly as it does on Windows. No production code
changes; `yamlgraph/utils/bridge.py` already handles absence via
`getattr(os, "register_at_fork", None)`.

**B.** Use the existing multi-FR attribution mechanism in the CAP file:

```yaml
fr: FR-713, FR-950
feature_request: FR-713, FR-950
```

`_build_fr_to_reqs` already splits on commas ("A capability may serve
multiple FRs"); no test or fragment change. Restage whatever
`cap-architecture-sync` regenerates.

## Acceptance Criteria

- [ ] AC-01: `pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` green on a pinned `[dev]` venv containing `uuid_utils` ≥ 0.17.0
- [ ] AC-02: the sim subprocess asserts `not hasattr(os, "fork")` before importing yamlgraph (guards the fidelity itself, not just the outcome)
- [ ] AC-03: `pytest tests/unit/test_changelog_req_cross_wiring.py -q --no-cov` green on clean main
- [ ] AC-04: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` reports 0 failures on this host's pinned venv (ramp exception below noted if venv not on PATH)

## Alternatives Considered

| Alternative | Probe executed (2026-09-02) | Disposition |
|---|---|---|
| A: pin/patch `uuid_utils` to guard on `register_at_fork` | `sed -n 38,39p .venv/.../uuid_utils/__init__.py` → guard is `hasattr(os, "fork")`, upstream-correct for every real platform | REJECTED — upstream is right; our sim is the liar. Fixing the sim is normalize-at-the-boundary; patching a vendor is a downstream_fix |
| A: mock `uuid_utils` in the test subprocess | n/a (design inspection) | REJECTED — mock_escape_hatch; the test exists to prove real import behavior on a no-fork runtime |
| A: skip the test when `uuid_utils` present | `.venv/bin/pip show uuid_utils` → 0.17.0 installed by the pinned constraint set, so the skip would fire everywhere | REJECTED — permanent skip = deleted witness |
| B: change CAP-198 to `fr: FR-950` alone | `grep -n "fr:" capabilities/CAP-198-*.yaml` → FR-713 is the origin FR of the whole capability | REJECTED — steals FR-713's origin attribution to fix FR-950's |
| B: drop `req:` from the FR-950 fragment | fragment read → `req: REQ-YG-541` is the fragment's only traceability link | REJECTED — severs ADR-001 traceability instead of completing it |
| B: exempt REQ-YG-541 in the collision test | test read → collision list is the gate's entire point | REJECTED — detection_without_enforcement in reverse: gate stays, registry lies |

## Out of Scope

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
- `capabilities/CAP-198-persistent-bridge-loop.yaml`
- `changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md`
- `tests/unit/test_changelog_req_cross_wiring.py`
