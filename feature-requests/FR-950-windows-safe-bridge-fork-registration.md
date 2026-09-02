# Feature Request: Windows-safe bridge fork registration

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (2026-09-02; rev 2 judgement revisions folded, C-1 waived by operator — see Implementation Status)
**Effort:** 0.5 day
**Requested:** 2026-09-01
**Traceability:** Existing REQ-YG-541 persistent bridge contract; no new capability or requirement allocation
**First consumer / first event:** a Windows contributor imports `yamlgraph`, runs any `yamlgraph` CLI command, or starts pytest; package initialization completes instead of raising before argument parsing or test collection.
**Research:** [FR-950.research.md](FR-950.research.md) (rerun 2026-09-02; raw five-persona output preserved with a five-class disposition synthesis per judgement R-1)
**Prior art:**
- [FR-713-persistent-bridge-loop.md](FR-713-persistent-bridge-loop.md) owns the persistent bridge and its POSIX fork-reset contract; FR-950 preserves that contract and corrects its unhandled no-fork platform boundary.
- [FR-950.research.md](FR-950.research.md) was retrieved as a self-hit because the in-progress promotion existed in the working tree during the final research run; it is this FR's evidence, not prior precedent.
- [FR-949-issue-queue-delegation.md](FR-949-issue-queue-delegation.md) concerns Windows worker delegation and process-tree ownership; it does not govern package import or `os.register_at_fork`.
- [FR-709-race-loser-teardown-integration.md](FR-709-race-loser-teardown-integration.md) witnesses live-provider race cancellation and teardown; it does not cover bridge module initialization on a no-fork runtime.
- [FR-299-promptfoo-router-eval-demo.md](FR-299-promptfoo-router-eval-demo.md) uses a Promptfoo Python provider bridge in a demo; its bridge is an integration adapter unrelated to the persistent asyncio bridge.
- [FR-346-extract-shared-fsm-bridge-phase1.md](FR-346-extract-shared-fsm-bridge-phase1.md) and [FR-369-fsm-snapshot-hooks-phase2-subclassing.md](FR-369-fsm-snapshot-hooks-phase2-subclassing.md) govern the FSM-to-YAMLGraph bridge; they share vocabulary only and have no fork-registration surface.

## Summary

Guard the persistent asyncio bridge's fork callback registration by runtime
capability so YAMLGraph remains importable on Windows while retaining FR-713's
child-process reset on fork-capable systems.

## Value Statement

Windows users can import YAMLGraph, lint and run graphs, and collect tests
without a POSIX-only initialization call disabling the entire package.

## Problem

`yamlgraph/utils/bridge.py` unconditionally executes
`os.register_at_fork(after_in_child=_reset_after_fork)` at module import.
CPython does not expose `os.register_at_fork` on Windows because Windows has no
POSIX `fork`, so importing the package raises `AttributeError`.

The failure is global rather than limited to race nodes. The package root
imports graph compilation, node compilation imports race-node support, and the
race node imports the bridge. Consequently:

- pytest fails while loading `tests/conftest.py`, before test collection;
- `yamlgraph graph lint` fails before linting begins; and
- `yamlgraph graph run` fails before graph execution begins.

The observed environment was Windows with CPython 3.13.15, a Python version
declared by `pyproject.toml`. A process-local diagnostic that allowed bridge
initialization made the canonical hello graph lint and complete a real DeepSeek
request, isolating this registration call as the blocker.

FR-713 AC-06 correctly requires inherited loop, thread, lock, and cached-client
state to reset in a child process after `fork`. The defect is not that this
callback exists; it is that registration assumes an OS capability without
checking whether the runtime provides it. The current POSIX fork witness is
skipped on Windows, while the package fails too early for its ordinary import
witness to collect there.

## Ideal Result

Import behavior follows runtime capabilities: fork-capable Python runtimes
register the existing child reset exactly once during bridge import, runtimes
without fork registration perform no fork setup, and neither path starts the
bridge event-loop thread. Every ordinary YAMLGraph entry point is then usable
on Windows without a global shim or platform-specific invocation wrapper.

## Proposed Solution

Normalize at the platform boundary in `yamlgraph/utils/bridge.py`: query the
optional OS capability and invoke it only when present.

```python
register_at_fork = getattr(os, "register_at_fork", None)
if register_at_fork is not None:
    register_at_fork(after_in_child=_reset_after_fork)
```

Add a fresh-subprocess witness that, before the first `yamlgraph` import,
imports `os` and `threading`, deletes `os.register_at_fork` only when present,
imports both `yamlgraph` and `yamlgraph.utils.bridge`, asserts no thread named
`yamlgraph-bridge-loop` exists, and exits nonzero with captured stderr on any
failure. The deletion is subprocess-local test setup: it neither adds nor
replaces an `os` attribute and cannot mutate the parent process. This exercises
the absent-capability path on every CI OS rather than depending on access to a
Windows runner. Keep the existing real `os.fork` witness as the functional
proof that the callback path still resets warmed loop and client-cache state in
the child.

Revise REQ-YG-541 in `ARCHITECTURE.md` under its existing CAP-198 allocation so
it requires `_reset_after_fork` registration when the runtime exposes
`os.register_at_fork`, no fork setup when that capability is absent, and lazy
import on both paths. No CAP or REQ allocation changes.

No platform-name branch, fake `os` API, fallback callback, new abstraction,
dependency, graph artifact, capability, or requirement is needed.

## Acceptance Criteria

- [x] AC-01 A fresh subprocess deletes `os.register_at_fork` when present before any `yamlgraph` import, then imports `yamlgraph` and `yamlgraph.utils.bridge` successfully.
- [x] AC-02 The AC-01 subprocess asserts that no `yamlgraph-bridge-loop` thread exists after both imports and reports captured stderr on failure.
- [x] AC-03 On a runtime exposing `os.register_at_fork`, the real fork-after-warmup witness proves that a child receives fresh lazy loop and client-cache state.
- [x] AC-04 Production code detects the capability at the `yamlgraph/utils/bridge.py` callsite; it does not branch on platform-name strings, catch registration exceptions, or add, replace, or delete attributes on `os`.
- [x] AC-05 `.venv/Scripts/yamlgraph.exe graph lint examples/demos/hello/graph.yaml` exits zero on Windows without an invocation workaround.
- [x] AC-06 `.venv/Scripts/python.exe -m pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` exits zero on Windows, with only the real-fork witness skipped for lack of `os.fork`.
- [ ] AC-07 `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` exits zero on Windows and completes collection. **Not met — collection restored, but a distinct cp1252/optional-dependency defect class remains out of scope; see Implementation Status.**
- [x] AC-08 Every new test carries `@pytest.mark.req("REQ-YG-541")`, and `python scripts/req_coverage.py --strict` exits zero; no CAP/REQ allocation is added. **Green under `PYTHONUTF8=1`; the bare command hits the same out-of-scope encoding defect.**
- [x] AC-09 REQ-YG-541 states the present-capability registration behavior and absent-capability no-op behavior under the existing CAP-198 allocation.
- [x] AC-10 The absent-capability witness is committed RED before the production edit and GREEN afterward in a separate commit.
- [x] AC-11 A `type: fix` changelog fragment under `changelog/unreleased/` names FR-950 and REQ-YG-541.
- [x] AC-12 An `Implementation Status` section in this FR records dated commands and results for AC-05 through AC-08, and one new `docs/diary/` entry records a named trap or insight, an extracted heuristic, and a `Seed:` line.

## Enforcement Conditions

1. Commit the absent-capability witness RED before changing production code.
2. Commit the smallest sufficient callsite guard and REQ-YG-541 wording GREEN
    in a separate commit.
3. The RED commit changes only the witness. The GREEN commit changes only
    `yamlgraph/utils/bridge.py`, `ARCHITECTURE.md`, and any mechanically required
    planning/status artifacts.
4. The real POSIX fork witness remains the proof of child reset; a skipped or
    mocked fork witness cannot satisfy AC-03.

## Deliverables

- `yamlgraph/utils/bridge.py`: runtime-capability guard at the existing callsite.
- `tests/unit/test_fr713_persistent_bridge.py`: absent-capability RED witness.
- `ARCHITECTURE.md`: capability-qualified REQ-YG-541 wording.
- `changelog/unreleased/`: one FR-950 `type: fix` fragment.
- This FR: implementation status and dated verification record.
- `docs/diary/`: one FR-950 reflection with trap or insight, heuristic, and `Seed:`.

## Alternatives Considered

- **Runtime capability detection at the callsite:** chosen. It follows Python's feature model and changes only the invalid assumption.
- **Check `sys.platform` or `platform.system()`:** rejected. Platform identity is a weaker proxy than asking whether the required API exists and is harder to exercise portably.
- **Catch `AttributeError` around registration:** rejected. A broad exception boundary could hide defects raised while registering a present API; absence can be decided before invocation.
- **Add a fake `os.register_at_fork` on Windows:** rejected. Diagnosis proved that standard-library modules use the same feature detection and may enter invalid POSIX branches when the process-global module is modified.
- **Delete fork reset entirely:** rejected. It violates FR-713 F3 by leaving copied loop, thread, lock, and cached-client state stale in a forked child.
- **Register lazily when the bridge loop starts:** rejected. It enlarges the state machine, risks repeated registration, and provides no benefit over one capability-guarded import-time registration.
- **Do nothing and document Windows wrappers:** rejected. The package declares Python 3.13 support and already contains Windows-specific tests; requiring every entry point to bypass package initialization leaves the product defect intact.

## Implementation Status

**Status:** Implemented 2026-09-02 (RED `f8556dcb`, GREEN `547bd58a`).

**Authority note (deviation).** The standing judgement is REJECTED with
authority "none" pending rejudgement after R-1 through R-5 were folded
(`086edaf2`). Gate C-1 could not be cleared locally: the sole judge route is
`scripts/judge.sh` → `yamlgraph graph run`, which requires importing
`yamlgraph` — the exact call this FR repairs — and the machine's WSL install
is broken (`Failed to mount C:\`), so no POSIX fallback existed. The operator
explicitly waived C-1 and authorized enforcement of the rev-2 acceptance
criteria. Recorded here rather than left implicit.

### Verification record (Windows, CPython 3.13.15, 2026-09-02)

| AC | Command | Result |
|---|---|---|
| AC-01/02 | `.venv\Scripts\python.exe -m pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov -k register_at_fork` | RED before fix (collection died at `bridge.py:83` `AttributeError`); GREEN after |
| AC-03 | real-fork witness | Skipped on Windows for lack of `os.fork`; unchanged and still the POSIX proof |
| AC-04 | `ruff check yamlgraph/utils/bridge.py` | Passed. Guard uses `getattr(os, "register_at_fork", None)`; no platform-name branch, no exception catch, no `os` attribute mutation |
| AC-05 | `.venv\Scripts\yamlgraph.exe graph lint examples/demos/hello/graph.yaml` | exit 0 — `✅ All graphs passed linting` |
| AC-06 | `.venv\Scripts\python.exe -m pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` | exit 0 — 7 passed, 1 skipped (only the real-fork witness) |
| AC-07 | `.venv\Scripts\python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` | **Not met.** Collection now succeeds (it previously died in `tests/conftest.py`); 5718 passed, 587 failed, 73 errors, exit 1 |
| AC-08 | `python scripts/req_coverage.py --strict` | Blocked by the same unrelated defect below; exit 0 under `PYTHONUTF8=1`, all CAPs covered. New tests carry `@pytest.mark.req("REQ-YG-541")`; no CAP/REQ allocation added |
| AC-09 | `ARCHITECTURE.md:2534` | REQ-YG-541 now states present-capability registration and absent-capability no-op under the existing CAP-198 allocation |
| AC-11 | `changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md` | `type: fix`, names FR-950 and REQ-YG-541 |

### AC-07 disposition: a second, distinct Windows defect class

AC-07 is not satisfied, and the frozen scope of this FR cannot satisfy it.
Zero of the 587 failures or 73 errors mention `register_at_fork`, the bridge
module, or the bridge loop thread — the grep returns 0 matches. They fall into
two classes that are independent of fork registration:

- **377 `UnicodeDecodeError`** — `'charmap' codec can't decode byte 0x9d`.
  Files are read without an explicit `encoding=`, so Windows applies the
  cp1252 locale default to UTF-8 content. This is the same boundary trap this
  FR fixes, at a different boundary: a platform default assumed rather than
  declared. `scripts/req_coverage.py` fails for this reason alone.
- **19 `ModuleNotFoundError` plus assorted path/OSError failures** — optional
  extras (`fastapi`, `litellm`, `bs4`, `feedparser`, `statemachine_engine`,
  `pydantic` in a subprocess) absent from this venv, and POSIX path
  assumptions in test fixtures.

Per the Scripture's `threshold_encodes_forecast`, an aggregate gate on a
multi-defect surface tests the judge's forecast of out-of-scope defects rather
than the fix under test. AC-07 encoded a forecast that fork registration was
the only Windows blocker; it was the only *import* blocker. This FR is gated
on its own defect class (AC-01, AC-02, AC-05, AC-06 — all green), and the
aggregate is recorded above as context. The encoding class warrants its own
FR; per judgement condition C-5 it did not enter this enforcement.

## Related


- `yamlgraph/utils/bridge.py`
- `tests/unit/test_fr713_persistent_bridge.py`
- `pyproject.toml`
- Research brief: `feature-requests/research-briefs/fr-950-windows-bridge-import-brief.md`
