# Feature Request: Windows-safe bridge fork registration

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-01
**Traceability:** Existing REQ-YG-541 persistent bridge contract; no new capability or requirement allocation
**First consumer / first event:** a Windows contributor imports `yamlgraph`, runs any `yamlgraph` CLI command, or starts pytest; package initialization completes instead of raising before argument parsing or test collection.
**Research:** [FR-950.research.md](FR-950.research.md) (five personas, 2026-09-01; all converged on local runtime-capability detection)
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

Add a subprocess witness that removes `os.register_at_fork` when present,
imports YAMLGraph and the bridge, and asserts that no bridge thread starts.
This exercises the absent-capability path on every CI OS rather than depending
on access to a Windows runner. Keep the existing real `os.fork` witness as the
functional proof that the callback path still resets a warmed bridge in the
child.

No platform-name branch, fake `os` API, fallback callback, new abstraction,
dependency, graph artifact, capability, or requirement is needed.

## Acceptance Criteria

- [ ] AC-01 Importing `yamlgraph` and `yamlgraph.utils.bridge` succeeds when the runtime does not expose `os.register_at_fork`.
- [ ] AC-02 The absent-capability witness runs in a fresh subprocess, can execute on every supported CI OS, and asserts that import starts no `yamlgraph-bridge-loop` thread.
- [ ] AC-03 On runtimes that expose `os.register_at_fork`, the existing `_reset_after_fork` callback remains registered and the real fork-after-warmup witness remains green.
- [ ] AC-04 No process-wide shim adds or replaces attributes on the `os` module, and no branch keys behavior from a platform-name string.
- [ ] AC-05 `.venv/Scripts/yamlgraph.exe graph lint examples/demos/hello/graph.yaml` succeeds on Windows without an invocation workaround.
- [ ] AC-06 `.venv/Scripts/python.exe -m pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` passes on Windows, with only the real-fork witness skipped there.
- [ ] AC-07 The fast non-slow unit suite reaches collection and no longer fails from bridge module initialization on Windows.
- [ ] AC-08 Every new test carries `@pytest.mark.req("REQ-YG-541")`; strict requirement coverage remains green; no CAP/REQ allocation is added.
- [ ] AC-09 Changelog fragment, implementation status, verification record, and diary reflection are completed during enforcement.

## Alternatives Considered

- **Runtime capability detection at the callsite:** chosen. It follows Python's feature model and changes only the invalid assumption.
- **Check `sys.platform` or `platform.system()`:** rejected. Platform identity is a weaker proxy than asking whether the required API exists and is harder to exercise portably.
- **Catch `AttributeError` around registration:** rejected. A broad exception boundary could hide defects raised while registering a present API; absence can be decided before invocation.
- **Add a fake `os.register_at_fork` on Windows:** rejected. Diagnosis proved that standard-library modules use the same feature detection and may enter invalid POSIX branches when the process-global module is modified.
- **Delete fork reset entirely:** rejected. It violates FR-713 F3 by leaving copied loop, thread, lock, and cached-client state stale in a forked child.
- **Register lazily when the bridge loop starts:** rejected. It enlarges the state machine, risks repeated registration, and provides no benefit over one capability-guarded import-time registration.
- **Do nothing and document Windows wrappers:** rejected. The package declares Python 3.13 support and already contains Windows-specific tests; requiring every entry point to bypass package initialization leaves the product defect intact.

## Related

- `yamlgraph/utils/bridge.py`
- `tests/unit/test_fr713_persistent_bridge.py`
- `pyproject.toml`
- Research brief: `feature-requests/research-briefs/fr-950-windows-bridge-import-brief.md`
