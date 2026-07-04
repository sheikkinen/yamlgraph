# Feature Request: Replace fixed module-map line budget with a format-density contract

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-04
**Supersedes:** the original FR-681 plan ("reorganize modules to restore 250")

## Summary

The FR-335 module-map budget (≤250 lines) has silently become a **module-count
cap**, not a compression gate. The compressed format is fixed at 2 lines per
module plus a 9-line header: 121 modules × 2 + 9 = 251. The only way to
satisfy ≤250 today is to delete or merge a module — the assertion
mathematically forbids the 121st module regardless of code quality. Replace
the fixed constant with a format-density contract that scales with module
count, and revert FR-677's temporary 260 bump.

## Value Statement

The entropy gates stop fighting each other: the 450-line file cap can keep
forcing healthy splits (Commandment 8) without the map budget punishing every
split with a demand to merge unrelated small modules.

## Problem

### The proxy has inverted (Goodhart)

FR-335's real problem was **format bloat**: the generated map was 1511 lines
of dependency noise, so agents skipped it. The fix was compression to a fixed
2-lines-per-module format. "≤250" was simply 2 × ~115 modules *at the time* —
a snapshot of module count frozen into a constant, not a chosen invariant.

Two years of doctrine-compliant growth later, the constant now measures the
wrong thing:

1. **FR-677 demonstrated the contradiction.** Extracting `node_timeout.py`
   from `node_compiler.py` (440/450 lines) was *mandatory* under the file
   cap — and it is exactly what broke the map budget. Gate A forces the
   move; gate B condemns it.
2. **"Paying back the debt" would increase entropy.** The available merge
   candidates are clean single-purpose modules: `graph_cache.py` (31 lines),
   `models/streaming.py` (29), `utils/content.py` (36). Merging any of them
   to reclaim 2 map lines trades real cohesion for a proxy number. Modules
   should be small; a gate that penalizes small modules is defective.
3. **The gate no longer measures compression at all.** The format is
   emitted by our own generator — it cannot regress to 1511-line verbosity
   unless the generator changes. A fixed total-line assertion detects
   module count, which is governed by architecture and the file cap, not by
   the map.

This is the `gate_checks_shape_not_substance` trap in mirror image: the gate
checks a number whose substance has drifted out from under it.

### What FR-335 actually wanted, still worth keeping

- The map stays **agent-readable**: compact per-module format, no
  dependency noise, deterministic ordering.
- Regeneration is committed and current.

Both are format properties, count-invariant.

## Proposed Solution

1. **Replace the fixed budget with a density contract** in
   `tests/unit/test_fr335_module_map_compression.py`:

   ```python
   # Map must stay in compressed form: header + at most 2 lines per module.
   module_count = _extract_module_count(module_map)   # from metadata line
   max_allowed = HEADER_ALLOWANCE + 2 * module_count  # HEADER_ALLOWANCE = 12
   assert line_count <= max_allowed, (
       f"module-map format regressed: {line_count} lines for "
       f"{module_count} modules (max {max_allowed})"
   )
   ```

   This fails on the failure FR-335 actually fixed (verbose multi-line
   entries, dependency noise) and is neutral to doctrine-compliant splits.

2. **Remove the FR-677 temporary bump** (250 → 260) and its comment — the
   density contract subsumes it.

3. **Keep an advisory, not a gate, on module count** — if module-count
   growth itself is worth watching, that signal belongs in the code-analysis
   agent / structural-drift reporting (Commandment 8 measurement), not in a
   blocking assertion that punishes correct splits. No count gate is added
   in this FR.

4. **Regenerate and commit `reference/module-map.md`** (currently 2 lines
   stale at 252 vs 254 generated).

## Constraints

- No changes to `scripts/generate_module_map.py` output format — this FR
  fixes the assertion, not the artifact.
- The density contract must still fail if someone reverts the FR-335
  compression (regression test: feed the test a synthetic verbose map).
- `REQ-YG-263` (structural drift) tagging preserved on amended tests.

## Acceptance Criteria

- [ ] Budget assertion derives `max_allowed` from module count (header
  allowance + 2×N); fixed constants 250/260 removed
- [ ] Synthetic-verbose-map regression test proves the density contract
  still catches FR-335-style format bloat
- [ ] FR-677 temporary-bump comment removed
- [ ] `reference/module-map.md` regenerated and committed; map test green
- [ ] No module merges, no module reorganization — grep diff confirms zero
  `yamlgraph/` source moves
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

1. **Original FR-681 plan: merge/reorganize modules to fit 250** —
   rejected: mathematically requires deleting a module (121×2+9=251);
   punishes the small-module doctrine to satisfy a stale constant.
2. **Bump the constant again (260 → 280 → …)** — rejected: a ratcheting
   constant is the `audit_as_ritual` failure mode; each bump normalizes the
   next.
3. **Hard module-count cap chosen deliberately (e.g. ≤150)** — rejected for
   now: no evidence module *count* is a problem; the file cap and
   import-linter already govern structure. Revisit if the code-analysis
   agent shows count-driven degradation.
4. **Byte-size budget instead of lines** — rejected: same Goodhart failure,
   different unit.

## Related

- FR-335 — introduced compression + the 250 constant (intent honored,
  constant retired)
- FR-677 — took the temporary 260 bump; this FR removes it
- FR-674 — module splits that will keep increasing module count, correctly
- Scripture: Commandment 8 (measure structural drift, not only passing
  checks), `gate_checks_shape_not_substance`, `audit_as_ritual`,
  `growth_as_default` (inverse: pruning a stale gate is the subtractive
  commit)
