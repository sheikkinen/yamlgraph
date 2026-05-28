# Diary: Schema Compliance as Pre-flight Check

**Date:** 2026-05-28
**FR:** FR-460 (CAP Architecture Auto-Sync)
**Trap:** `gate_checks_shape_not_substance` → `downstream_fix`

## Observation

During FR-460 enforcement, the CAP-160 YAML file I created was missing two required fields (`fr`, requirement-level `modules`). The existing `validate-capabilities` pre-commit hook caught this — but only after the full test suite ran and one test failed with a clear error message.

The cognitive trap: I copied the top-level structure from CAP-159 but truncated it, omitting fields that the schema validator requires. The error was trivial to fix, but the iteration cost was a full parallel pytest run (~50 seconds) before discovering a schema-level issue that could have been caught in under 1 second.

## Heuristic

**Pre-flight before full suite**: When creating registry artifacts (CAP YAML, changelog fragments, FR files), run the specific validator script *before* the full test suite. The validator is 100x faster than pytest and catches structural errors immediately.

```bash
# Before committing a new CAP:
python scripts/validate_capabilities.py   # <1 second
# Only then:
pytest tests/unit/ -q --no-cov -m "not slow" -n auto  # ~50 seconds
```

This is a specific instance of the general principle: validate at the boundary where the artifact is created, not downstream where a test happens to assert on it.

## The Auto-Sync Pattern

FR-460 itself was a clean enforcement: one pre-commit hook, nine tests, one CAP file. The `ruff-format` auto-fix pattern (modify file → pre-commit detects unstaged change → developer stages) proved correct — the hook ran and passed during the commit that introduced it.

The hook closes the `detection_without_enforcement` gap that caused silent ARCHITECTURE.md drift during FR-452.

## Seed

Pre-commit hooks now span two behavioral patterns: **gates** (exit 1 to block) and **regenerators** (modify file, let pre-commit detect change). Should these be formally catalogued? A hook registry YAML that declares each hook's pattern type would make the pre-commit config self-documenting and help new hooks follow the right pattern.
