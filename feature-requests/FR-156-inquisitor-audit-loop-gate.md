# Feature Request: Inquisitor audit-loop gate — fix SHA extraction and duplicate-range detection

**Priority:** HIGH
**Type:** Bug
**Status:** ✅ Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08
**Judged:** 2026-03-08

## Summary

Fix the commit-delta gate (FR-131) SHA extraction regex that silently fails on the actual diary format, and add duplicate-range detection as a second defence layer against audit-loop repetition.

## Value Statement

The Inquisitor stops producing redundant audit entries (XXXIV–XXXVII covered the identical commit range) because the gate's SHA extraction regex now matches the diary format the copilot actually writes.

## Problem

Audits XXXIV through XXXVII all covered the identical commit range (`1c65de2..01b75e7`), producing near-duplicate findings across 4 entries. The commit-delta gate (FR-131) should have suppressed audits when no new `feat:`/`fix:` commits existed, but it silently passed every time.

**Root cause — regex mismatch:**

The gate's `sed` regex expects individually backticked SHAs:

```
`abc1234`..`def5678`
```

But the copilot agent consistently writes a single backtick pair wrapping the entire range:

```
`abc1234..def5678`
```

The regex in `inquisitor.sh` line 37:
```bash
sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p'
```

This never matches, so `LAST_SHA=""`, which hits the graceful-degradation path (no SHA → gate skipped → audit proceeds). The gate has been structurally broken since the copilot began writing diary entries in this format.

**Secondary issue — inconsistent range direction:**

Audit XXXIV writes `1c65de2..01b75e7` while audit XXXVI writes `01b75e7..1c65de2` (reversed). Even with a fixed regex, extracting the "HEAD SHA" as the second element is unreliable when the copilot doesn't guarantee direction.

## Proposed Solution

### Fix 1: Broaden SHA extraction regex

Replace the current regex with one that tolerates both formats:

```bash
# Matches both `SHA`..`SHA` and `SHA..SHA` (single or double backtick wrapping)
LAST_SHA=$(sed -nE 's/.*`?([a-f0-9]{7,})`?\.\.`?([a-f0-9]{7,})`?.*/\2/p' "$LATEST_AUDIT" | head -1)
```

Or more robustly, extract both SHAs and resolve which is newer:

```bash
# Extract both SHAs from the commit range (any backtick format)
RANGE_SHAS=$(sed -nE 's/.*\(?`?([a-f0-9]{7,})\.\.([a-f0-9]{7,})`?\)?.*/\1 \2/p' "$LATEST_AUDIT" | head -1)
SHA_A=$(echo "$RANGE_SHAS" | awk '{print $1}')
SHA_B=$(echo "$RANGE_SHAS" | awk '{print $2}')

# Resolve the newer SHA (the one reachable from the other)
if [[ -n "$SHA_A" && -n "$SHA_B" ]]; then
    if git merge-base --is-ancestor "$SHA_A" "$SHA_B" 2>/dev/null; then
        LAST_SHA="$SHA_B"
    else
        LAST_SHA="$SHA_A"
    fi
fi
```

### Fix 2: Duplicate-range detection (second layer)

Before running the audit, hash the current commit window and compare against the last audit's range. If identical, abort — regardless of whether new commits exist.

```bash
# --- Duplicate-range detection (FR-156) ---
if [[ -n "$SHA_A" && -n "$SHA_B" && -z "$FORCE" ]]; then
    CURRENT_RANGE_START=$(git log --oneline -5 HEAD | tail -1 | awk '{print $1}')
    CURRENT_RANGE_END=$(git rev-parse --short HEAD)
    # If both SHAs from the last audit appear in the current 5-commit window, it's a duplicate
    if git log --oneline "${SHA_A}^..${SHA_B}" 2>/dev/null | grep -q . && \
       [[ "$CURRENT_RANGE_END" == "$SHA_B"* || "$CURRENT_RANGE_END" == "$SHA_A"* ]]; then
        echo "⏭️  Inquisitor: Current commit range already covered by $(basename "$LATEST_AUDIT"). Skipping."
        echo "   Use --force to override."
        exit 0
    fi
fi
```

### Fix 3: Mirror SHA extraction in test suite

Update `_SHA_EXTRACT_SCRIPT` in `tests/unit/test_inquisitor_gate.py` to match the fixed regex, and add test cases for both backtick formats and reversed ranges.

### Implementation scope

| Change | File | Lines |
|--------|------|-------|
| Fix SHA regex | `.chaplain/inquisitor.sh` | ~5 lines changed |
| Add duplicate-range check | `.chaplain/inquisitor.sh` | ~10 lines added |
| Fix test SHA regex | `tests/unit/test_inquisitor_gate.py` | ~5 lines changed |
| Add test: single-backtick format | `tests/unit/test_inquisitor_gate.py` | ~15 lines |
| Add test: reversed range | `tests/unit/test_inquisitor_gate.py` | ~15 lines |
| Add test: duplicate range suppressed | `tests/unit/test_inquisitor_gate.py` | ~20 lines |

## Acceptance Criteria

- [ ] SHA extraction succeeds on diary entries using `\`SHA..SHA\`` format (single backtick pair)
- [ ] SHA extraction succeeds on diary entries using `\`SHA\`..\`SHA\`` format (individual backtick pairs)
- [ ] Gate correctly identifies the newer SHA when the range is written in reversed order
- [ ] Duplicate-range detection blocks audit when the current commit window matches the last audit's range
- [ ] `--force` bypasses both the commit-delta gate and the duplicate-range check
- [ ] Graceful degradation preserved: missing diary, no SHAs parseable, first audit all proceed
- [ ] Test: two consecutive gate invocations on the same commit range — second is suppressed
- [ ] Test: diary entry with single-backtick range format → SHA extracted correctly
- [ ] Test: diary entry with reversed range → newer SHA identified
- [ ] `_SHA_EXTRACT_SCRIPT` in test suite matches production regex

## Alternatives Considered

1. **Fix copilot prompt to enforce backtick-per-SHA format:** Rejected — LLM output format is non-deterministic. The gate must tolerate format variance, not rely on prompt engineering for structural correctness. This is the `tolerant_matching` cure from the Knowledge Graph.

2. **Marker file (`.last-audit-range`):** Considered — simpler than diary parsing, but FR-131's Judgement already rejected this approach. The diary-as-source-of-truth principle is sound; the regex just needs to match reality.

3. **Restrict to `--force` only (disable automatic gate):** Rejected — defeats the purpose of FR-131. The gate is valuable; it just has a parsing bug.

4. **Add `chore:` and `docs:` to actionable commit types:** Rejected — these don't introduce behaviour changes that the 6-point checklist evaluates. The real problem is the regex, not the commit-type filter.

## Related

- **FR-131** (`feature-requests/FR-131-inquisitor-commit-delta-gate.md`): Original gate implementation — this FR fixes its regex
- **FR-076** (`feature-requests/FR-076-chaplain-inquisitor.md`): Inquisitor design
- **Audit XXXVI** (`docs/diary/2026-03-08-inquisitor-audit-xxxvi.md`): Flagged repeated range
- **Audit XXXVII** (`docs/diary/2026-03-08-inquisitor-audit-xxxvii.md`): Flagged gate bypass
- **Knowledge Graph**: `tolerant_matching` cure ("prefix/contains/regex, not exact equality for LLM"), `audit_as_ritual` trap

## Judgement

**Verdict: APPROVED** — Scope frozen. Authority granted to implement.

**Evidence review (data-confirmed):**

1. **Root cause confirmed.** All diary entries from audit XXXI onward use the single-backtick format `` `SHA..SHA` ``. The regex only matches the double-backtick format `` `SHA`..`SHA` `` (used in audits I–XXIII). The gate has been structurally broken since the format shifted.

2. **Duplicate range confirmed — worse than stated.** The FR claims 4 duplicate audits (XXXIV–XXXVII). Actual count is **6**: audits XXXIV, XXXVII, XXXVIII, XXXIX, XL, XLI all cover `1c65de2..01b75e7`. Audit XXXVI covers a different range.

3. **Reversed range confirmed.** Audit XXXVI writes `(01b75e7..1c65de2)` — reversed direction, parenthesized, no backticks. This is a **third format variant** the FR's regex must also handle.

**Corrections for implementor:**

- **Factual:** "Audits XXXIV through XXXVII" should read "XXXIV, XXXVII–XLI" (6 duplicates, not 4). XXXVI has a different range in reversed order.
- **Missing format:** XXXVI uses `(SHA..SHA)` — parentheses without backticks. The proposed regex in Fix 1's robust variant already handles this (optional parens `\(?`/`\)?`), but tests must cover this third format.
- **Fix 2 sketch:** The proposed duplicate-range detection code has a logical gap (computes `CURRENT_RANGE_START` but never uses it; prefix matching with `*` is fragile for short SHAs). Refine during Enforce — the concept is sound, the sketch needs tightening.

**What is approved:**
- Fix 1: Broaden SHA extraction to tolerate all three observed formats
- Fix 2: Duplicate-range detection as a second defence layer
- Fix 3: Mirror production regex in test suite, with cases for all three formats plus reversed ranges
- Scope boundary: changes limited to `.chaplain/inquisitor.sh` and `tests/unit/test_inquisitor_gate.py`
