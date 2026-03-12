# Feature Request: Graduate `plausible_wrong_answer` Trap Description

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-12

## Summary

Refine the `plausible_wrong_answer` trap description in the Scripture's Knowledge Graph based on evidence from 4 diary entries that confirm the pattern is broader than the current description suggests. The current wording focuses on one variant (silent fallback) while the trap manifests across multiple domains.

## Value Statement

All agents benefit from a trap description that captures the full pattern — output that passes validation but is semantically wrong — so they recognize the hazard whether it appears as a silent fallback, a type-correct-but-wrong LLM output, or a non-deterministic stand-in for a deterministic check.

## Problem

The `plausible_wrong_answer` trap in `.github/copilot-instructions.md` currently reads:

```yaml
plausible_wrong_answer: "Silent fallback harder to catch than crash"
```

This description has two issues:

1. **It names only one variant.** "Silent fallback" captures the `on_error: skip` pattern (FR-165), but the 4 diary entries show the trap is broader: it fires whenever output looks correct but is semantically wrong — whether from silent fallback, type-valid-but-wrong LLM output, data structure costume, or LLM-based deterministic matching.

2. **It lacks the trigger → redirect format.** Contrast with `quick_confidence: "When I feel certain → Judge instead"` which names a trigger (feeling certain) and a redirect (Judge). The current description states a fact ("harder to catch") but doesn't tell the agent what to watch for or what to do instead.

### Evidence — 4 Confirmed Occurrences

| Diary Entry | Domain | Plausible Wrong Answer | What Was Missing |
|---|---|---|---|
| `2026-03-08-reflection-fr-165.md` | Error handling | `on_error: skip` silently omits failed outputs | Lint rule to flag silent fallbacks |
| `2026-03-08-reflection-fr-164.md` | LLM outputs | Passes type validation but content is wrong | Prediction/assertion layer beyond type checks |
| `2026-03-11-reflection-fr-184.md` | Scripture dedup | LLM says "no duplicates" but matching is wrong | Deterministic parsing instead of LLM |
| `2026-03-12-philosopher-fr185.md` | Data structures | PipelineError looks raiseable but is BaseModel | Boundary normalization (type honesty) |

All four share the same root: **the output satisfied the shape contract (type, schema, no error raised) while violating the semantic contract (wrong content, missing data, false negative).** The fix in every case was adding a semantic assertion layer — a check that goes beyond "right type" to "right meaning."

## Proposed Solution

Update the `plausible_wrong_answer` entry in the `traps:` section of `.github/copilot-instructions.md`:

```yaml
# Before
plausible_wrong_answer: "Silent fallback harder to catch than crash"

# After
plausible_wrong_answer: "Output passes shape check but is semantically wrong → add assertion beyond type validation"
```

This revised description:
- **Names the trigger**: "Output passes shape check but is semantically wrong" — describes what the agent catches itself seeing
- **Points to the cure**: "add assertion beyond type validation" — a concrete redirect
- **Generalizes across domains**: applies to silent fallbacks, LLM outputs, data structure costumes, and deterministic-vs-non-deterministic matching alike
- **Follows the convention**: `trigger → redirect` format matching other traps

The complementary reference in Commandment 6 ("A plausible wrong answer is harder to catch than a crash") remains unchanged — it is a principle statement, not a trap description.

## Acceptance Criteria

- [x] `plausible_wrong_answer` description in `.github/copilot-instructions.md` updated to: `"Output passes shape check but is semantically wrong → add assertion beyond type validation"`
- [x] No other traps or cures descriptions changed
- [x] Pre-commit hooks pass
- [x] Changelog fragment added to `changelog/unreleased/`

## Alternatives Considered

1. **Add sub-variants as separate traps.** Rejected — the 4 instances share a single root pattern (shape-valid, semantically-wrong). Splitting would create false distinctions and bloat the Knowledge Graph.

2. **Keep the current description and add a cure instead.** Rejected — the trap already lacks a cure entry, but the primary issue is that the description itself is too narrow. Adding a cure without fixing the description compounds the mismatch.

3. **No change (leave as-is).** Rejected — the current description captures only 1 of 4 confirmed variants. Agents encountering the FR-164, FR-184, or FR-185 variants would not recognize the trap from "Silent fallback harder to catch than crash" alone.

## Related

- **Diary evidence:**
  - `docs/diary/2026-03-08-reflection-fr-165.md` — silent `on_error: skip`
  - `docs/diary/2026-03-08-reflection-fr-164.md` — type-valid but content-wrong LLM output
  - `docs/diary/2026-03-11-reflection-fr-184.md` — LLM-based deterministic matching
  - `docs/diary/2026-03-12-philosopher-fr185.md` — BaseModel masquerading as Exception
- **Scripture location:** `.github/copilot-instructions.md`, line 61
- **Commandment 6:** "A plausible wrong answer is harder to catch than a crash" (unchanged)
- **Precedent:** FR-189 (graduated `downstream_fix` trap via same refinement process)
