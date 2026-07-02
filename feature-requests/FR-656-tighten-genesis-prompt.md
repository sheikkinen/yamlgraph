# Feature Request: FR-656 — Tighten Genesis Prompt to Match Canon Schema

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-02

## Judgement

**Verdict: Granted with 3 amendments.**

### A1: AC-5/AC-6 are verification, not acceptance criteria
Re-running genesis and checking tests is the enforcement method, not the
acceptance criterion. ACs should specify what the prompt must contain.
AC-5/AC-6 become verification steps during enforcement.

### A2: Drop valence enum — use examples, not closed set
`Relationship.valence` is `str` in the Pydantic model; the enum lives only
in `retrieve_window`'s filter. Hardcoding filter expectations in the prompt
creates a second source of truth. Instruct with examples ("e.g. enmity,
trust, fear"), not a closed set.

### A3: User template is in scope too
The user template (lines 43–55) duplicates field names from the system
message. Both halves must be tightened — e.g. `consequences` should say
`list[str]` in the user template too.

## Summary

The `structure_world.yaml` prompt produces canon output that fails Pydantic
validation in five specific ways. Each required a manual edit after genesis ran
for Floodmark. The prompt must be tightened so the LLM output passes
`validate_page()` without post-hoc fixup.

## Problem

FR-655 genesis pipeline ran successfully but produced structurally invalid
canon. Five gaps between prompt instructions and `schema/canon.py`:

| Field | Prompt says | Schema expects | Manual fix applied |
|-------|------------|----------------|-------------------|
| `Event.consequences` | (implicit: string) | `list[str]` | Converted all 7 events |
| `Character.triggers` | "triggers" (no count guidance) | `list[str]` | Split comma-list into separate items |
| `Relationship.valence` | Not mentioned | `str` — tested for `enmity`/`caution`/`fear`/`distrust` by `retrieve_window` | Set `valence: enmity` |
| `Character.references` | "list ids of related entities" | Must include referenced rule IDs | Added `blood_feud_rule` |
| `Synopsis.references` | "list ids of related entities" | Must include premise ID | Added `the_floodmark_saga_premise` |

## Root Cause

The prompt was written from the perspective of "what fields exist" without
cross-checking the Pydantic model's type annotations or the downstream
`retrieve_window` function's filtering logic. The prompt is the contract;
the schema is the enforcer; the two disagreed.

## Acceptance Criteria (amended)

1. **AC-1**: `consequences` explicitly described as `list[str]` in both system and user template.
2. **AC-2**: `triggers`, `fears`, `goals` described as "list — one item per distinct entry, not comma-separated".
3. **AC-3**: `relationships` documented with `{to, kind, valence}` structure; `valence` described with examples (e.g. enmity, trust, fear), not a closed enum. *(A2)*
4. **AC-4**: Cross-reference rules: "Every character must reference any rules that govern them. Synopsis must reference the premise."
5. **AC-5**: User template field descriptions match system message type annotations. *(A3)*

## Verification (enforcement)

- Re-run genesis on Floodmark premise; all 30 canon files pass `validate_page()` without manual edits. ✅
- 14 tests pass (4477 total, 0 failures). ✅
- Jinja2 template collision discovered and fixed: bare `{to, kind, valence}` parsed as Jinja2 set; replaced with "objects with keys: to, kind, valence" notation.
- Tests updated to match new genesis IDs (`hilde` not `hilde_aschenwulf`, `the_great_flood` not `the_great_flood_event`, etc.).

## Implementation Approach

1. Update `examples/novel_fandom/prompts/structure_world.yaml`:
   - System message: add type annotations for list-typed fields, add valence with examples, add cross-reference rules, add "one item per entry" instruction.
   - User template: tighten field descriptions to match (consequences as list[str], relationships with valence, etc.). *(A3)*

2. Re-run genesis on the Floodmark premise.

3. Run `test_all_seed_pages_validate` + full 13-test suite.

## Constraints

- Prompt changes only — no schema or test changes.
- The prompt already carries a W026 warning for inline schema size (accepted per FR-655 judgement). Additional system text must stay proportional.
- Do not add a validation step to the pipeline itself (that would be a separate FR for a post-genesis gate).

## Risks

- LLMs may still produce comma-separated items despite instruction. Mitigation: test with DeepSeek (current provider) and verify.
- Adding valence enum to the prompt increases token cost per call (~50 tokens). Acceptable for a one-shot genesis pipeline.

## Related

- [FR-655](FR-655-genesis-graph.md) — Genesis pipeline (parent)
- [diary-2026-07-02-the-allowlist-is-the-coupling.md](../docs/diary/diary-2026-07-02-the-allowlist-is-the-coupling.md) — Discovery context
