# Feature Request: FR-1162 Upgrade the sole-route adapter model pins to gpt-6.1-sol

**Priority:** HIGH
**Type:** Fix
**Status:** Proposed (operator directive 2026-11-14: "upgrade all to 6.1-sol. pr. outsider. merge")
**Requested:** 2026-11-14
**First consumer / first event:** the next `scripts/review.sh` run (PR #771's
review is waiting). Today it fails before producing a report because its pinned
model is no longer served. The outsider read of PR #773 failed the same way on
2026-11-13.
**Prior art:** FR-931 (moved the judge and review pins `gpt-5.5` →
`gpt-5.6-sol`; this FR repeats that move and keeps its witness design).
FR-995 (the outsider adapter pinned `gpt-5.6-sol` literally and echoed it in
`scripts/outsider.sh`). FR-765/FR-767 (the authoring adapter; FR-931 left it
outside the pin invariant on purpose, and this FR keeps it outside). FR-960
(the judge's opt-in Claude node; its `claude-opus-5` pin is not a GPT pin and
is out of scope). None of these is rejected; none proposes this model.

## Summary

Change the Copilot-CLI model pin from `gpt-5.6-sol` (judge, review, outsider)
and `gpt-5.5` (authoring) to `gpt-6.1-sol` in the four adapter graphs and in
`scripts/outsider.sh`. Update the tests that assert the pin, and the docs that
state the current pin.

## Problem

The Copilot CLI no longer serves either old model. A one-line probe on
2026-11-14:

| Model | `copilot -p "Reply OK." --model <m>` |
|---|---|
| `gpt-5.5` | exit 1, `Execution failed` |
| `gpt-5.6-sol` | exit 1, `Model "gpt-5.6-sol" is not available.` |
| `gpt-6.1-sol` | exit 0 |

So `scripts/judge.sh`, `scripts/review.sh`, `scripts/outsider.sh` and
`scripts/author.sh` cannot run from a clean checkout of `main`. The FR-1161
demo was authored only because the authoring pin was edited locally and left
uncommitted. Uncommitted pins are invisible drift: the exact thing FR-931's
witness exists to prevent.

## Ideal Result

Every governed adapter route runs from a clean `main` on a served model, and
the model it runs on is visible in the diff.

## Proposed Solution

1. `cli_flags.model: gpt-6.1-sol` in
   `.github/skills/{judge-fr,review-pr,outsider-view,graph-authoring}/adapters/graph.yaml`.
2. `MODEL="gpt-6.1-sol"` in `scripts/outsider.sh` (the observation marker must
   match the adapter).
3. Tests that assert the pin: `PINNED_MODEL` in
   `tests/unit/test_fr931_sole_route_model_pin.py`; the judge pin assertions in
   `test_fr960_claude_judge_variant.py` and `test_fr1049_opencode_judge_variant.py`;
   the outsider pin assertions in `test_fr995_outsider_wrapper.py`. Fixture
   strings that only pass a model value through (`test_fr995_outsider_reader.py`)
   stay unchanged.
4. Docs that state the current pin: REQ-YG-632 and REQ-YG-663 in
   `ARCHITECTURE.md`, `capabilities/CAP-211` and `CAP-263`, the judge-fr adapter
   README, and the outsider-view skill, doctrine, adapter README and fixture
   expectations. Historic records (spikes, research notes, recaps, released
   changelog, diary) stay unchanged.

Out of scope: the judge's Claude node pin (`claude-opus-5`). The Claude CLI
login has expired on this host, so a replacement cannot be checked.

## Acceptance Criteria

- [ ] AC-01: No adapter graph or adapter wrapper script on the branch names
  `gpt-5.5` or `gpt-5.6-sol`.
- [ ] AC-02: The FR-931 witness pins `gpt-6.1-sol` and passes; it failed
  against the old adapters before the change (RED commit).
- [ ] AC-03: The route runs live on the new pin. `scripts/judge.sh` renders a
  judgement of this FR, and `scripts/outsider.sh` produces a valid report for
  this FR's PR.
- [ ] AC-04: The unit suite passes in the CI-mirror container and in CI.

## Implementation Status

Not started.

## Related

- [FR-931](FR-931-judge-review-model-pin-gpt56sol.md): previous pin move, witness design.
- [FR-995](FR-995-outsider-reader.md): outsider adapter and wrapper.
