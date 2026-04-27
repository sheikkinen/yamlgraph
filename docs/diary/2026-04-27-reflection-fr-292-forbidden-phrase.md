---

## 2026-04-27: FR-292 — The Forbidden Phrase and Event Loop Ownership

**Context:** Enforcing FR-292 (pipeline path alignment) — fixing 9 graph path references, removing 2 phantom states, converting changelog_gen to bash. TDD cycle: 14 RED tests committed, all GREEN after 18 config changes + 3 test file updates. The config work was mechanical. The real lesson came from the test suite.

**Trap:** **"pre-existing failure"** — Six async tests in `test_fr291` (BashContextAction, PrecommitAction) failed when run in the full suite but passed in isolation. The immediate instinct was to label them "pre-existing" and move on. The Scripture forbids this phrase explicitly: *"A red test suite belongs to the current change author."* The reasoning was sound: our diff only changed a state count assertion, not the async code. But the doctrine doesn't care about diff scopes — it cares about the suite being green when you push.

**Root cause:** Test pollution. An earlier module in the collection order closes or replaces the asyncio event loop. The FR-291 tests used `asyncio.get_event_loop().run_until_complete()`, which depends on a global event loop existing in the thread. After pollution, `get_event_loop()` raises `RuntimeError: There is no current event loop`. The fix: replace with `asyncio.run()`, which creates a fresh loop per call.

**Secondary trap:** **downstream_fix** manifested twice. First, blaming the test runner for not isolating event loops (downstream) instead of fixing the test to not depend on global state (boundary). Second, the worktree's `.venv` wasn't symlinked, causing `statemachine-lint` and pre-commit's `diary-rotate` hook to fail with "executable not found." The symptom appeared as test failures, but the boundary was the worktree setup.

**Heuristic:** **`asyncio.run()` over `get_event_loop().run_until_complete()` in tests — always.** The deprecated pattern creates invisible coupling to global event loop state. `asyncio.run()` is self-contained. This applies everywhere a sync test needs to call an async function.

**Evidence chain:**
- Baseline full suite: 6 async failures + 14 FR-292 RED = 20 failed
- With GREEN config: 6 async failures + 0 FR-292 = 6 failed
- After `asyncio.run()` fix: 0 failures, 3804 passed
- Pre-commit: all 30+ hooks pass, including full pytest

**Seed:** Worktrees that share `.venv` via symlink are fragile — pre-commit hooks that reference `.venv/bin/python` hardcoded won't find it. Should worktree creation in the Chaplain automatically symlink `.venv`? Or should all hook entry points use `python -m` instead of direct `.venv/bin/python` paths?
