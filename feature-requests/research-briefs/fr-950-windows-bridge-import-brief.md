# Problem brief: bridge import fails when fork registration is unavailable

**Prior art:** `feature-requests/FR-713-persistent-bridge-loop.md` owns the
persistent sync-to-async bridge and requires child-process reset after a POSIX
fork. This brief concerns the unhandled platform boundary at module import,
not a replacement for the persistent bridge or a relaxation of its fork-safety
contract. `feature-requests/FR-294-precommit-venv-path-isolation.md` and
`feature-requests/FR-793-hook-ruff-venv-fallback-and-error-surfacing.md` concern
environment and hook interpreter selection, not runtime API availability.

## Problem statement

Importing `yamlgraph` on Windows raises `AttributeError` before any CLI command
or test can collect. The import chain reaches `yamlgraph/utils/bridge.py`, whose
module initialization unconditionally calls `os.register_at_fork`. Python does
not expose that function on Windows because Windows starts child interpreters
rather than implementing POSIX `fork` semantics.

FR-713 requires the bridge to clear inherited event-loop, thread, lock, and LLM
client state in a child created after the parent bridge has warmed up. That
requirement is valid on runtimes that support `fork`. On a runtime without
`os.register_at_fork`, however, there is no inherited fork state to repair and
the unconditional registration makes the whole package unimportable.

The failure occurs during `tests/conftest.py` import, before pytest can collect
the existing bridge witnesses. It also occurs before `yamlgraph graph lint` or
`yamlgraph graph run` can parse arguments, so even graph operations unrelated
to race or router-race nodes are unavailable.

The existing FR-713 import witness launches a subprocess and asserts that an
import starts no bridge thread. Its separate fork-after-warmup witness is
correctly skipped on Windows because `os.fork` is POSIX-only, but there is no
explicit cross-platform witness for importing the bridge when fork
registration itself is absent.

During diagnosis, adding a process-wide fake `os.register_at_fork` before
imports caused Python's own `concurrent.futures.thread` module to enter its
POSIX-only registration branch and fail while evaluating a Windows lock. That
secondary `ThreadPoolExecutor` error disappeared when the standard executor was
imported normally and is diagnostic evidence about unsafe global shimming, not
an independent product defect.

The open question this brief poses: what is the smallest platform-boundary
contract that preserves FR-713 fork hygiene where the runtime supports it while
keeping package import and ordinary CLI operations available where it does not?

## Classification

enforcement/latency-critical

## Constraints

- FR-713's child reset remains mandatory on runtimes that expose
  `os.register_at_fork`; the correction cannot weaken or remove the existing
  fork-after-warmup behavior.
- Importing YAMLGraph must remain side-effect-light: no bridge event-loop thread
  may start during package or bridge import.
- No process-wide shim may add a fake API to Python's `os` module; other
  standard-library and dependency modules use feature detection on that module.
- The defect is in runtime capability detection, not Python version selection.
  The witnessed interpreter is CPython 3.13.15, and `pyproject.toml` declares
  Python 3.13 support.
- The change belongs at the external platform boundary where the optional OS
  capability enters the bridge module.
- Existing POSIX fork witnesses must remain green, and a witness that does not
  require access to a Windows CI host must make absence of the API testable.
- This is a correction to the existing bridge capability under REQ-YG-541, not
  a new user-facing graph capability unless research proves otherwise.
- Scope excludes the diagnostic-only `ThreadPoolExecutor` failure caused by the
  temporary global shim.

## Witnessed incidents

- On Windows with CPython 3.13.15,
  `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto`
  failed while loading `tests/conftest.py`; no tests were collected. The root
  exception was `AttributeError: module 'os' has no attribute
  'register_at_fork'` at `yamlgraph/utils/bridge.py` module initialization.
- On the same environment, `.venv/Scripts/yamlgraph.exe graph lint
  examples/demos/hello/graph.yaml` failed through the same import chain before
  linting began.
- With a process-local diagnostic workaround applied after preloading
  `ThreadPoolExecutor`, the hello graph passed lint and completed a real
  DeepSeek invocation. This isolates the unavailable fork-registration call as
  the blocker rather than the graph, provider credentials, or broader Windows
  execution.
- FR-713 AC-06 records successful lazy import and POSIX fork reset behavior, but
  its implementation and witnesses do not cover a runtime where
  `os.register_at_fork` is absent.
