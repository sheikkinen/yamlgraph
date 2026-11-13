# Feature Request: FR-1157 Register FR-1156 in CAP-164 and State the Literal Rule in REQ-YG-712

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**REQ:** REQ-YG-712 (existing, CAP-164)
**Requested:** 2026-11-13
**First consumer / first event:** the FR-1156 PR (branch
`fix/fr-1156-anthropic-2`). Its fast unit run on the committed GREEN
`f69b58c6`, in a clean CI-mirror container, failed exactly one test,
`test_changelog_req_cross_wiring.py::TestChangelogReqIntegrity::test_no_req_collision_across_unrelated_frs`:
`REQ-YG-712 claimed by FR-1156 (fragment) but FR-1156 capability has no capability`.
The PR cannot merge until this is fixed, and PR #768 waits on that merge.
**Research:** in-body dispositioned alternatives table (§ Alternatives Considered).
**Prior art:**
[FR-1156](FR-1156-anthropic-sdk-2-8-floor.md) is the parent change; its
round-3 amendment request was refused by the judge's round cap
("re-file a shorter plan as a new FR file"), which is why this FR exists.
[FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md) is the
precedent: it appended itself to CAP-164 `fr:` for the same REQ.
[FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md) wrote the
REQ-YG-712 text that FR-1156 makes incomplete.

## Summary

FR-1156's changelog fragment declares `req: REQ-YG-712` (its AC-09). The
cross-wiring gate requires every FR that claims a REQ in a fragment to be
listed in the owning capability's `fr:` field, and CAP-164 does not list
FR-1156. Separately, REQ-YG-712's text defines "untyped" as "lacking
type/anyOf/oneOf/allOf/$ref", which is no longer the shipped rule: FR-1156
also accepts a primitive `const` or a non-empty all-primitive `enum`.

## Value Statement

The FR-1156 PR (and with it PR #768) can merge with a green suite, and the
capability registry describes the rule the code enforces.

## Problem

The test is the condemning witness: it fails on `f69b58c6` and is the only
failure in the clean CI-mirror run (1 failed, 7646 passed, 57 skipped).

## Ideal Result

CAP-164 lists every FR that claims REQ-YG-712, and REQ-YG-712's text
states the rule the walker implements.

## Planned Operations

```yaml
probes:
  - "done: clean CI-mirror run on f69b58c6 (FR-1156 Implementation Status)"
branches:
  - "any other failure after the edit → stop, record, new FR"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "CI"
commands:
  - python -m pytest tests/unit/test_changelog_req_cross_wiring.py -q --no-cov
  - python scripts/req_coverage.py --strict
  - docker run --rm -v <repo>:/src:ro python:3.11-slim sh /src/<FR-1156 CI-mirror script>
```

## Proposed Solution

One file, `capabilities/CAP-164-structured-output-fallback.yaml`:

1. `fr: FR-464, FR-998, FR-1121, FR-1123, FR-1125` →
   `fr: FR-464, FR-998, FR-1121, FR-1123, FR-1125, FR-1156`.
2. In REQ-YG-712 `text`, replace
   `untyped (lacking type/anyOf/oneOf/allOf/$ref, FR-1123)` with
   `untyped (lacking type/anyOf/oneOf/allOf/$ref and carrying no primitive
   const or non-empty all-primitive enum, FR-1123/FR-1156)`.

No new REQ, capability, test, or other field. It lands as a commit in the
FR-1156 PR, because that PR cannot pass CI without it.

## Acceptance Criteria

- [ ] AC-01: CAP-164 `fr:` ends with `FR-1156`; no other `fr:` change.
- [ ] AC-02: REQ-YG-712 `text` contains the replacement clause above; no other text change.
- [ ] AC-03: `test_no_req_collision_across_unrelated_frs` passes; `req_coverage.py --strict` passes.
- [ ] AC-04: The unchanged fast-unit command passes in the clean CI-mirror container on the committed candidate; Linux CI is green.
- [ ] AC-05: FR records implementation status; changelog coverage is the FR-1156 fragment (same PR, same REQ); no separate fragment.

## Alternatives Considered

**is_this_a_graph:** no.

| # | Alternative | Disposition |
|---|---|---|
| A | Drop `req:` from the FR-1156 fragment | Rejected: violates FR-1156 AC-09 and hides the REQ the change alters. |
| B | Exempt FR-1156 in the cross-wiring test | Rejected: weakens a gate to pass a change. |
| C | Register only (item 1), leave the REQ text | Rejected: registry would then misstate the rule it owns. |
| D | Register and correct the text (this FR) | Chosen; matches FR-1125's precedent. |
