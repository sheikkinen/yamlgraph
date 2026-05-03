# Feature Request: FR-317 watcher2 sanity-check diary filename from fr_path

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 days
**Requested:** 2026-05-03

## Summary

Fix `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` so the diary filename is derived from the current `fr_path` instead of the hardcoded `fr-316` stem.

## Value Statement

Watcher2 runs produce diary files that correctly match the active feature request, preserving audit traceability and preventing cross-FR diary pollution.

## Problem

GitHub issue #295 reports that the sanity-check prompt currently instructs:

- `docs/diary/YYYY-MM-DD-reflection-fr-316-watcher2-sanity-check-state.md`

This is hardcoded to FR-316. As a result, every pipeline run targets the same diary filename even when reviewing another FR (for example FR-317). The prompt already receives `{{ fr_path }}`, but the diary instruction does not use it.

## Objectives

1. Make sanity-check diary filename instructions dynamic per run, using `fr_path`.
2. Preserve current diary contract (`docs/diary/`, reflection naming, required `Seed:` section).
3. Keep scope minimal: prompt contract + acceptance tests only.

## Constraints

- Limit changes to watcher2 sanity-check prompt/test artifacts under `.chaplain/graphs/watcher-enforce/` and `tests/unit/`.
- Do not change watcher FSM transitions, validate/precommit contracts, or non-related prompts.
- Do not introduce new pipeline variables if `fr_path` is sufficient.

## Research Findings

### Existing patterns and prior art

1. **Dynamic FR-based naming already exists in watcher prompts:**
   `.chaplain/graphs/enforce/prompts/enforce-critique-and-distill.yaml` uses `{{ fr_num }}` in diary/changelog filename instructions.
2. **FR metadata extraction from path is established in shell tooling:**
   `.chaplain/lib/finalize_lib.sh` extracts `FR-[0-9]+` from `fr_path` basename.
3. **Sanity-check prompt currently has required context but does not use it:**
   `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` includes `Feature request: {{ fr_path }}` and still hardcodes `reflection-fr-316-...`.
4. **Current tests miss this boundary:**
   `tests/unit/test_fr316_watcher2_sanity_check_state.py` validates presence of `docs/diary/` but does not assert dynamic filename derivation from `fr_path`.

### Scope impact from research

- No runtime or graph wiring changes are necessary for this fix.
- Prompt contract clarification plus targeted acceptance tests is sufficient.

## Proposed Solution

Update step 6 in `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml`:

1. Remove hardcoded `reflection-fr-316-watcher2-sanity-check-state`.
2. Instruct the reviewer to derive the FR stem from `{{ fr_path }}` (basename without `.md`, normalized to lowercase/kebab-case).
3. Require diary output path format:
   - `docs/diary/YYYY-MM-DD-reflection-<derived-fr-stem>.md`
4. Include an explicit derivation example in the prompt, e.g.:
   - `feature-requests/FR-317-reference-docs-review.md` → `docs/diary/YYYY-MM-DD-reflection-fr-317-reference-docs-review.md`

## Acceptance Criteria

- [x] **AC-01:** `sanity-check-session.yaml` no longer contains hardcoded `reflection-fr-316-watcher2-sanity-check-state`.
- [x] **AC-02:** Prompt explicitly states that diary filename must be derived from `{{ fr_path }}`.
- [x] **AC-03:** Prompt defines the output pattern `docs/diary/YYYY-MM-DD-reflection-<derived-fr-stem>.md`.
- [x] **AC-04:** Prompt includes one concrete derivation example from an `FR-<num>-<slug>.md` path.
- [x] **AC-05:** Prompt still requires the `Seed:` section in diary content.
- [x] **AC-06:** RED acceptance tests are added and fail before implementation, then pass after implementation.

## Implementation Notes

- Updated `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` step 6 to derive the diary filename stem from `fr_path`, define the required output pattern, and include an explicit FR path derivation example.
- Added `tests/unit/test_fr317_watcher_sanity_check_diary_filename_from_fr_path.py` with five `REQ-YG-316` acceptance tests covering AC-01..AC-05.
- Executed RED (`pytest tests/unit/test_fr317_watcher_sanity_check_diary_filename_from_fr_path.py -q --no-cov`) before prompt changes, then GREEN with the same test plus full unit suite (`pytest tests/unit/ -q --no-cov -x`).

## Failing Acceptance Tests (RED)

Add `tests/unit/test_fr317_watcher_sanity_check_diary_filename_from_fr_path.py`:

1. `test_ac01_no_hardcoded_fr316_diary_filename`
2. `test_ac02_diary_filename_is_derived_from_fr_path_variable`
3. `test_ac03_prompt_defines_reflection_derived_fr_stem_path_pattern`
4. `test_ac04_prompt_includes_concrete_fr_path_to_diary_example`
5. `test_ac05_prompt_still_requires_seed_section`

Suggested marker: `@pytest.mark.req("REQ-YG-316")` (same watcher-sanity boundary already used by FR-316 tests).

RED command:

```bash
pytest tests/unit/test_fr317_watcher_sanity_check_diary_filename_from_fr_path.py -q --no-cov
```

## Alternatives Considered

1. **Pass new `fr_num` / `fr_slug` variables into sanity-check graph state**
   Rejected: broader wiring changes are unnecessary because `fr_path` is already present.
2. **Keep hardcoded filename and rely on manual correction**
   Rejected: repeats operator work and preserves incorrect-by-default behavior.
3. **Post-process diary filename in later pipeline step**
   Rejected: fixes symptom downstream instead of correcting the boundary instruction where filename is authored.

## Related

- Topic source requested: `.chaplain/processing/gh-295.md` (not present in this worktree)
- Canonical source used: GitHub issue #295 — <https://github.com/sheikkinen/yamlgraph/issues/295>
- `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml`
- `tests/unit/test_fr316_watcher2_sanity_check_state.py`
- `feature-requests/FR-316-watcher2-sanity-check-state.md`
