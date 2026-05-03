# Feature Request: FR-316 watcher2 post-validate sanity_check diary state

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 0.5-1 day
**Requested:** 2026-05-03

## Summary

Add a non-blocking `sanity_check` state between `validate` and `precommit_check` in `watcher-pipeline-v2` so watcher2 can automatically perform the current manual quality review and write a structured diary entry from pipeline artifacts.

## Value Statement

Watcher2 operators get consistent, context-rich post-validate review output (scope proportionality, test quality, FR/code alignment) without repeating manual checklist work after each cycle.

## Problem

GitHub issue #290 requests automation for a manual post-run sanity review currently done by humans after watcher2 pipeline execution.

Today:

1. `.chaplain/config/watcher-pipeline-v2.yaml` routes `validate -> precommit_check` directly.
2. `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` still asks the enforce agent to write the diary entry itself.
3. There is no independent post-validate reviewer that inspects issue intent vs FR vs produced diff before pre-commit gate.

This couples implementation and reflection in one agent boundary and leaves proportionality/test-quality checks as ad-hoc manual work.

## Objectives

1. Insert a dedicated post-validate `sanity_check` reviewer boundary in watcher FSM v2.
2. Produce a diary-style reflection artifact from concrete pipeline evidence.
3. Keep sanity findings non-blocking for pre-commit gate flow (`warn` continues).
4. Move diary quality-review ownership out of enforce-session prompt.

## Constraints

- Scope is limited to watcher2 FSM/config/prompt/test artifacts under `.chaplain/` and `tests/unit/`.
- Do not change YAMLGraph runtime primitives or core CLI behavior.
- Do not turn sanity warnings into hard pipeline blockers.
- Keep existing `validate` and `precommit_check` contracts intact outside the inserted boundary.

## Research Findings

### Existing abstractions and prior art

- **Post-enforce quality split already exists:** FR-310 introduced `validate` + `precommit_check` boundaries in `.chaplain/config/watcher-pipeline-v2.yaml`.
- **Diary generation pattern exists in dedicated reviewer flows:** FR-285 forensic path uses a separate graph/prompt (`.chaplain/graphs/watcher-forensic/`) to analyze artifacts and write diary entries, proving this belongs in its own review boundary.
- **Current enforcement prompt still owns diary writing:** `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` includes explicit diary-generation instructions, which conflicts with independent review intent.
- **Pipeline evidence sources are available in-repo:** dispatcher writes `logs/fsm-pipeline-*.log`; enforce/validate stages already have FR path, topic path, and worktree context that can be inspected by a reviewer prompt with tool access.

### Gap check

- No `sanity_check` state exists in watcher FSM v2.
- No dedicated sanity-check graph/prompt exists for successful cycles.
- No tests enforce the non-blocking warn-to-precommit contract for a sanity reviewer state.

## Proposed Solution

Add a dedicated `sanity_check` state to watcher pipeline v2:

```text
enforce_session -> validate -> sanity_check -> precommit_check -> done
                             └────────warn───────────────┘
```

### 1. FSM insertion in `.chaplain/config/watcher-pipeline-v2.yaml`

- Add state: `sanity_check`.
- Replace direct transition:
  - `validate --validate_done--> precommit_check`
- With:
  - `validate --validate_done--> sanity_check`
  - `sanity_check --pass--> precommit_check`
  - `sanity_check --warn--> precommit_check` (non-blocking warnings)
- Keep hard failures explicit:
  - `sanity_check --error--> failed`

### 2. Dedicated sanity-check graph/prompt

Add:

- `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml`

Prompt responsibilities:

1. Read topic intent (issue/body), FR, and changed code/tests.
2. Inspect diff proportionality (`git diff --stat main..HEAD`, `git diff main..HEAD`).
3. Inspect pipeline execution evidence (transition/timing log where available).
4. Evaluate FR-to-code and test-quality alignment.
5. Write a diary reflection in `docs/diary/` including a required **Seed:** question.
6. Return `PASS` or `WARN` for FSM event routing (`warn` remains non-blocking).

### 3. Enforce prompt boundary cleanup

Update `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` to remove diary ownership so enforce stays implementation-focused while sanity_check performs independent review.

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` defines a `sanity_check` state.
- [x] **AC-02:** `validate` no longer transitions directly to `precommit_check`.
- [x] **AC-03:** FSM path includes `validate -> sanity_check -> precommit_check`.
- [x] **AC-04:** `sanity_check` has non-blocking `warn` routing to `precommit_check`.
- [x] **AC-05:** `sanity_check` uses `type: yamlgraph_async` and calls `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml`.
- [x] **AC-06:** Sanity-check graph and prompt files exist under `.chaplain/graphs/watcher-enforce/`.
- [x] **AC-07:** Sanity-check prompt explicitly evaluates proportionality, test quality, FR/code alignment, and writes a diary entry with `Seed:`.
- [x] **AC-08:** Enforce-session prompt no longer contains diary-generation ownership instructions.
- [x] **AC-09:** Acceptance tests in `tests/unit/test_fr316_watcher2_sanity_check_state.py` fail on current implementation and pass after implementation.

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr316_watcher2_sanity_check_state.py` with:

1. `test_ac01_adds_sanity_check_state`
2. `test_ac02_removes_direct_validate_to_precommit_transition`
3. `test_ac03_ac04_routes_validate_to_sanity_then_precommit_with_warn_non_blocking`
4. `test_ac05_sanity_check_state_uses_yamlgraph_async_action`
5. `test_ac06_sanity_check_graph_and_prompt_exist`
6. `test_ac07_sanity_prompt_covers_review_dimensions_and_diary_seed`
7. `test_ac08_enforce_prompt_no_longer_owns_diary_generation`

RED command:

```bash
pytest tests/unit/test_fr316_watcher2_sanity_check_state.py -q --no-cov
```

## Alternatives Considered

1. **Keep diary generation inside enforce session**
   Rejected: implementation and review remain coupled; no independent sanity boundary.
2. **Run sanity checks only as manual operator checklist**
   Rejected: repeats cognitive work and produces inconsistent review quality.
3. **Make sanity warnings blocking**
   Rejected: conflicts with requested non-blocking review design and could stall healthy cycles.

## Related

- Topic source requested: `.chaplain/processing/gh-290.md` (not present in this worktree)
- Canonical source used: GitHub issue #290 — <https://github.com/sheikkinen/yamlgraph/issues/290>
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`
- `feature-requests/FR-310-watcher2-validate-precommit-states.md`
- `feature-requests/FR-285-watcher2-forensic-failure-diary.md`
