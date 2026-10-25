# Feature Request: FR-1150 Split llm_providers.py under the size gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-10-25
**First consumer / first event:** the next `.py` commit that touches
`yamlgraph/utils/llm_providers.py` (FR-1148's owed tests and the effort
setting, the two PRs queued after this one), which today rides on the
temporary `llm_providers.py: 473` BASELINE entry of FR-1149.
**Research:** in-body Alternatives Considered table (FR-889 style); no
`research.sh` run, the change is a move of existing code with no behaviour
change.
**Prior art:** [FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md)
— added the thinking-off rule that pushed the file to 473 lines and owes
this split (AC-08, R-6); this FR does that split only, not FR-1148's owed
tests and docs;
[FR-1149-size-gate-windows-paths.md](FR-1149-size-gate-windows-paths.md)
— added the temporary entry this FR removes, and parked the tautology this
FR repairs;
[FR-263-azure-openai-provider.md](FR-263-azure-openai-provider.md) — whose
change extracted `llm_providers.py` from `llm_factory.py` for the same gate
(the module docstring), the same kind of move;
[FR-998-anthropic-constrained-structured-output.md](FR-998-anthropic-constrained-structured-output.md) — owns the capability
classification block moved here, unchanged.
No rejected FR covers this territory.

## Summary

`yamlgraph/utils/llm_providers.py` is 473 lines against the 450-line gate,
held only by FR-1149's temporary BASELINE entry. This FR moves two
self-contained Anthropic blocks into modules of their own, with no change in
behaviour, names or messages, removes the temporary entry, and repairs the
size-gate test so a stale entry like it can never stay unnoticed.

## Value Statement

Maintainers of `llm_providers.py` get the file back under the gate without
an exception, and the gate's own test catches a BASELINE entry that outlives
its reason.

## Problem

1. `wc -l yamlgraph/utils/llm_providers.py` is 473; `LIMIT` is 450.
2. `scripts/size_gate.py` holds it with `"yamlgraph/utils/llm_providers.py": 473`,
   a temporary entry (FR-1149, operator decision of 2026-10-25) that this
   split must remove.
3. `test_baseline_is_shrink_only_and_honest` would not notice if the entry
   stayed after the split. Its last clause,
   `assert actual > size_gate.LIMIT or allowed >= actual`, is always true
   once `actual <= allowed` has passed (FR-1149's parked note). A 410-line
   `llm_providers.py` with its 473 entry left in place passes the test.

## Ideal Result

`llm_providers.py` is under 450 lines with no BASELINE entry; every name and
message importable from it today is still importable from it and behaves the
same; and `test_baseline_is_shrink_only_and_honest` fails for any BASELINE
entry whose file is at or under `LIMIT`.

## Planned Operations

```yaml
probes:
  - "wc -l of the three modules after the move"
  - "the repaired honesty test with the 473 entry left in place, after the split — must fail (RED witness)"
  - "pytest on the tests that import the moved names, before and after"
branches:
  - "a moved name is imported from llm_providers somewhere not listed here → keep it importable there"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits:
  - "judge"
  - "CI"
  - "producer's reviewer, then merge"
commands:
  - JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-1150-llm-providers-split.md
  - pytest -q --no-cov tests/unit/test_thinking_budget.py tests/unit/test_fr998_structured_output.py .github/hooks/tests/test_size_gate.py
  - PYTHONUTF8=1 python scripts/size_gate.py
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

Two moves and one repair. No logic, docstring meaning, name or message
changes.

1. **`yamlgraph/utils/anthropic_thinking.py`** (FR-1148 R-6 names this
   module): `_ANTHROPIC_THINKING_ALWAYS_ON` and `_anthropic_thinking_off`,
   moved verbatim. The error text stays
   `"thinking_budget=0: thinking cannot be turned off on {model}; omit thinking_budget for this model"`.
   `llm_providers.py` imports both names back, so
   `from yamlgraph.utils.llm_providers import _anthropic_thinking_off, _ANTHROPIC_THINKING_ALWAYS_ON`
   still works. FR-1148 R-6 also proposed the name
   `_THINKING_OFF_UNSUPPORTED`; renaming is not part of a pure move, so it is
   left to FR-1148's owed work, which may add it as an alias.
2. **`yamlgraph/utils/anthropic_capability.py`**: the FR-998 block (the three
   term tuples, `is_anthropic_chat_model`, `_structured_error_message`,
   `is_anthropic_unsupported_structured_output`), moved verbatim.
   `llm_providers.py` re-exports the two public functions
   (`from ... import x as x`, ruff's explicit re-export form, no `noqa`), so
   `structured_output.py` and `test_fr998_structured_output.py`, which import
   them from `llm_providers`, are unchanged.
3. **`scripts/size_gate.py`**: the temporary entry and its comment removed.
   **`.github/hooks/tests/test_size_gate.py`**: the tautological clause
   becomes `assert actual > size_gate.LIMIT, f"stale baseline entry: {rel} is {actual} lines, not over LIMIT"`.
   Every other entry is above `LIMIT` today (checked: the smallest is
   `scripts/migrate_capabilities.py` at 501).

The thinking move alone leaves the file at about 456 lines, so the second
move is needed. `llm_providers.py`'s module docstring is updated to say where
the two blocks now live.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Move only the thinking rule | Rejected: about 456 lines, still over 450 |
| Move only the FR-998 block | Rejected: under 450, but FR-1148 AC-08/R-6 asks for the thinking rule in its own module |
| Rename to `_THINKING_OFF_UNSUPPORTED` now | Rejected: not a pure move; left to FR-1148's owed work |
| Point `structured_output.py` and the test at the new module, no re-export | Rejected: changes import sites in a pure move |
| Leave the honesty test as it is | Rejected: it cannot catch the stale entry this FR removes |

## Acceptance Criteria

- [ ] AC-01: `llm_providers.py` is at most 450 lines and has no BASELINE
  entry; `PYTHONUTF8=1 python scripts/size_gate.py` exits 0.
- [ ] AC-02: `_anthropic_thinking_off`, `_ANTHROPIC_THINKING_ALWAYS_ON`,
  `is_anthropic_chat_model` and `is_anthropic_unsupported_structured_output`
  import from `yamlgraph.utils.llm_providers` and are the same objects as in
  their new modules.
- [ ] AC-03: `_anthropic_thinking_off("claude-opus-5-5")` raises a
  `ValueError` whose message ends `omit thinking_budget for this model`.
- [ ] AC-04: `git diff` of the moved bodies shows only the move (no logic
  change); `test_thinking_budget.py` and `test_fr998_structured_output.py`
  pass unchanged.
- [ ] AC-05: RED witness: with the 473 entry left in place after the split,
  the repaired `test_baseline_is_shrink_only_and_honest` fails naming
  `llm_providers.py`; with it removed, it passes.
- [ ] AC-06: no new `noqa`; no `--no-verify`; no `Co-authored-by` trailer;
  any `SKIP=pytest` is recorded with its commit and reason in the PR body.
- [ ] AC-07: a `docs/diary/` reflection with a **Seed:**.
