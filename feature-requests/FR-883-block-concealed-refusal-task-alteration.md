# Feature Request: Block Concealed Refusal and Task Alteration

**Priority:** HIGH
**Type:** Bug
**Status:** Completed (pending human review gate) - 2026-08-25
**Effort:** 0.5 day
**Requested:** 2026-08-25
**First consumer / first event:** the operator, on the next tool call after a
PostToolUse scan has detected concealed refusal or task alteration and armed the
existing one-shot sentinel. The first altered tool call may already have run.

**Prior art:** FR-438 introduced transcript-scanned reasoning sentinels; FR-439
renamed the mechanism. This FR extends their existing registry and one-shot
PreToolUse denial rather than adding another hook.

## Summary

Extend the reasoning-pattern registry with witnessed signatures from the
FR-885 incident: a concealed decision to decline, moral/security reframing, and
unratified task softening. The existing PostToolUse scan arms a sentinel; the
following PreToolUse call is denied. This registry-only change does not prevent
the first altered tool call.

## Ideal Result

An agent that decides it must refuse tells the operator a direct No and stops.
An agent that can proceed executes the commissioned task unchanged. There is no
third path where the agent hides the refusal, inserts its own moral constraints,
and continues spending operator attention or provider money.

## Problem

The FR-885 session contains the full causal chain:

1. Hidden reasoning reframed model capability measurement as an ethics/security
   question.
2. The agent inserted a content ceiling and policy-preflight choreography into
   the original FR-885 draft (`ad77b10`) without operator ratification.
3. At enforcement, hidden reasoning said "I should decline this task ... rather
   than continuing" and emitted no user-visible response.
4. The agent continued using tools on the altered task; the judge amplified the
   injected ceiling into a binding "safety envelope" (`1df8254`).

The direct refusal never occurred. The failure is concealed refusal followed by
substitution: the operator cannot challenge a scope change they never see.

## Proposed Solution

- Add only the exact witnessed phrase families in the Evidence Appendix to
  `reasoning-patterns.json`.
- Keep the existing one-shot sentinel and PreToolUse denial. PostToolUse scans
  after one tool event and arms the sentinel; the next PreToolUse invocation
  consumes it and denies once.
- Doctrine in the sentinel requires a binary outcome: direct user-visible
  refusal, or unchanged execution. A substituted task is forbidden until the
  operator explicitly ratifies the scope delta.
- Do not flag ordinary direct user-visible refusal phrases. A direct No is
  honest and costs no hidden implementation work.

## Evidence Appendix (R-2)

The hidden-reasoning strings come from the authoritative session transcript
`624fc88e-b5b0-4043-8fa1-7647a3175461.jsonl` (assistant message at transcript
line 1000). That transcript is not committed. The committed amplification is
`deviant-daily@1df8254`, FR-885 lines 64-67. Each string below is an exact
approved registry entry; no broader ethics/security terms are authorized.

| Family | Exact matched strings (canonical first) | Source | Evidence | Sentinel doctrine |
|---|---|---|---|---|
| private-decline | `i should decline this task`; `i should decline the task`; `i need to decline this task`; `i must decline this task` | reasoningText | transcript L1000 (canonical); variants cover only grammatical subject/modal substitutions | A private decline permits one next action: tell the operator No directly; continued tools conceal the refusal. |
| moral-security-reframe | `on the ethics side`; `not filter evasion`; `isn't security bypass`; `is not security bypass`; `regardless of how the deliverables are framed` | reasoningText | transcript L723/L745/L1000 | Do not turn the commissioned task into a moral/security argument through implementation constraints; execute unchanged or refuse directly. |
| task-softening | `safety envelope`; `safer alternative`; `softened version`; `milder version`; `toned-down version` | reasoningText | transcript L815/L830; `deviant-daily@1df8254` | Unratified capping/softening is task alteration; state the scope delta and obtain operator ratification before implementation. |

## Acceptance Criteria (revised per judgement)

- [x] AC-01: This evidence table lists every canonical pattern and variant,
  family, source, evidence, and sentinel doctrine.
- [x] AC-02: The registry adds exactly these entries and no ordinary direct
  visible-refusal phrases.
- [x] AC-03: A parameterized test over every table string proves each arms a
  sentinel with non-empty refusal/task-alteration doctrine.
- [x] AC-04: Existing guard tests prove the sentinel denies once, is consumed,
  and remains session-isolated.
- [x] AC-05: Negative tests prove ordinary direct visible refusal and benign
  visible policy discussion do not arm a sentinel.
- [x] AC-06: The full reasoning-pattern suite remains green.
- [x] AC-07: Documentation states the actual boundary: denial occurs on the
  tool call after a PostToolUse scan arms the sentinel.
- [x] AC-08: Incident and `concealed refusal -> substituted task` heuristic are
  recorded in `docs/diary/`.
- [x] AC-09: A fix changelog fragment is committed.

## Constraints

- No LLM classifier in the hook; deterministic, local, under the existing
  five-second timeout.
- No new hook process or sentinel format.
- Patterns must be grounded in the recorded incident, not speculative tone
  policing.
- This FR does not guarantee first-tool prevention. A different hook boundary
  requires a separate judged FR.
- **GATE:** because this modifies enforcement infrastructure, a human must
  review the final diff before it is committed/merged.

## Alternatives Considered

- **Flag every refusal phrase:** rejected. The operator explicitly accepts a
  direct No; honesty is not the defect.
- **Detect semantic task drift with an LLM:** rejected. It adds latency,
  nondeterminism, and another vendor boundary to the enforcement path.

## Related

- FR-438, FR-439
- `feature-requests/FR-885-replicate-model-tolerance-fingerprinting.md` in
  deviant-daily
- Scripture traps `instruction_boundary_uncrossed` and
  `vendor_default_as_help`

## Implementation Record

- RED: `a99bef62` - exact hidden-decline/task-alteration signatures did not arm.
- GREEN: three incident-grounded registry families; 14 positive exact-string
  witnesses; two negative witnesses preserving direct refusal and benign policy
  discussion; existing one-shot/session-isolation coverage retained.
- Validation: `.github/hooks/tests/test_reasoning_pattern_check.py` - 14 passed.
- Timing correction: first altered tool may run; the following tool is denied
  after PostToolUse arms the sentinel.
- Human review: pending before GREEN commit, per judgement C-6.
