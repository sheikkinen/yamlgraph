# Reflection: FR-425 Hook Classification Daemon — Phase A Enforcement

**Date:** 2026-05-20
**FR:** FR-425
**Phase:** A (demo-only)

## Cognitive Process

The task was to enforce a pre-judged FR through the full rite: implementation, tests, demo, infrastructure (CAP, ARCHITECTURE, changelog). The FR had been through 3 plan-judge cycles, so the contract was frozen and clear. The enforcement itself was largely mechanical — translate spec to code.

## Traps Encountered

### 1. Jinja2 Auto-Detection (Boundary Trap)

The prompt YAML mixed simple `{tool_name}` substitution with Jinja2 `{% if session_history %}` blocks. YAMLGraph's auto-detection saw `{%` and switched to Jinja2 mode, turning `{tool_name}` into a literal string. Fix: use `{{ tool_name }}` throughout.

**Pattern:** This is a *boundary normalization* failure — the template engine boundary should reject mixed syntax rather than silently degrading. The `{` vs `{{` distinction is a classic "gate checks shape not substance" trap.

### 2. SnapshotParams Positional Args (API Surface Drift)

Tests built `SnapshotParams` with keyword args but missed `phase` and `payload_keys` — fields added in a later FR. The error was clear (`TypeError: missing 2 required positional arguments`), but it highlights that positional-only constructors in data classes are fragile across versions.

**Pattern:** `recent_changes_blindness` — I assumed I knew the constructor shape without checking the current source.

### 3. Timestamp Eviction (Test vs Production Time)

Test hardcoded `"2026-05-20T09:15:00+00:00"` as "recent" history, but `evict_history()` uses a 30-minute window from `datetime.now()`. By the time tests ran, the hardcoded timestamp was stale. Fix: use `datetime.now(timezone.utc)` in test fixtures.

**Pattern:** `plausible_wrong_answer` — the test looked correct (timestamp was "today") but was semantically wrong (not within the eviction window).

### 4. Hyphenated Directory (Module Structure Boundary)

`hook-classifier` directory cannot be a Python package. Caught by import failure in tests. Renamed to `hook_classifier` with `__init__.py` files.

**Pattern:** `module_structure` boundary — Python import contracts demand underscore naming. The kebab-case was inherited from the FSM config naming convention.

## Insight

**Enforcement is where boundary violations surface.** The plan-judge cycle caught structural issues (scope, contracts, acceptance criteria), but the boundary traps — Jinja2 syntax, import paths, timestamp semantics — only appeared during enforcement. This validates the doctrine: "What survives the fire may merge."

## Heuristic

When a YAML prompt uses *any* Jinja2 syntax (`{% %}` or `{{ }}`), convert *all* variable references to Jinja2 double-brace syntax. Mixed `{var}` and `{{ var }}` in the same file is always a bug.

## Seed:

**Can YAMLGraph detect and warn about mixed template syntax at lint time?** A graph lint rule that flags `{word}` (simple substitution) co-occurring with `{{` or `{%` (Jinja2) in the same prompt file would catch this class of bugs before runtime. This could be a CAP: "prompt syntax consistency lint."
