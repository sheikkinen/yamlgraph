# Feature Request: Graduate `infrastructure_self_exempt` Trap to Scripture

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-12

## Summary

Add `infrastructure_self_exempt` as a new trap entry in the Scripture's Knowledge Graph. The pattern has been independently confirmed in 3 diary entries (audits 94, 95, 97), meeting the graduation threshold defined in the `process.graduation` rule.

## Value Statement

All agents benefit from an explicit Scripture entry that names the cognitive blind spot where infrastructure tooling exempts itself from the quality gates it enforces, preventing recurring audit violations on meta-tooling.

## Problem

When work involves building or maintaining infrastructure that enforces quality (pre-commit hooks, validation scripts, ID registries, traceability tooling), there is a consistent cognitive exemption: "the tool that guards quality doesn't need guarding itself." This leads to:

- Production scripts shipped without tests (Commandment 7 violation)
- Traceability features without their own traceability (no CHANGELOG, no REQ, no diary)
- Audit cycles that detect absence without triggering remediation (`audit_as_ritual` compounding)

The pattern is currently unnamed in Scripture despite 3 confirmed occurrences, which means agents have no compressed signal to recognize and interrupt the trap in real time.

### Evidence — 3 Confirmed Occurrences

| Diary Entry | Domain | Self-Exemption (trap) | Finding |
|---|---|---|---|
| `2026-03-10-inquisitor-audit-94.md` | Traceability sprint (FR-177/178/180) | 2,304+ new lines of infrastructure with zero CHANGELOG, zero diary, zero tests for `aggregate_capabilities.py` | "Infrastructure-for-infrastructure creates a blind spot" |
| `2026-03-10-inquisitor-audit-95.md` | Capability registry (FR-178) | 511-line migration script + 243-line validator with zero tests; registered in `.pre-commit-config.yaml` as production gate | "Scripts in .pre-commit-config.yaml are production code — classifying them as 'tooling' exempts them from TDD" |
| `2026-03-10-inquisitor-audit-97.md` | Traceability feature (FR-180) | 628 lines with no CHANGELOG, no ARCHITECTURE.md row, tests tagged with wrong requirement | "A traceability feature that isn't itself traceable is the framework_costume trap inverted" |

All three share the same root cause: meta-tooling classified as "not real code" and therefore exempt from the gates it implements.

## Proposed Solution

Add a new `infrastructure_self_exempt` entry to the `traps:` section in `.github/copilot-instructions.md` (after line 63):

```yaml
# Before (traps section ends at line 63)
  working_system_inertia: "'It works' blocks seeing it clearly → inventory fit, not function"

# After (new entry appended)
  working_system_inertia: "'It works' blocks seeing it clearly → inventory fit, not function"
  infrastructure_self_exempt: "Meta-tooling exempted from gates it enforces → apply same rules to the guardrail as to what it guards"
```

This description:
- **Names the trigger**: "Meta-tooling exempted from gates it enforces" — describes what the agent catches itself doing (classifying infrastructure as exempt)
- **Points to the cure**: "apply same rules to the guardrail as to what it guards" — directly actionable
- **Generalizes across domains**: applies to pre-commit scripts, traceability tooling, validation infrastructure, and CI gates alike

No other Scripture changes are needed. The existing `audit_as_ritual` trap and `audit_gate` process entry remain complementary — `infrastructure_self_exempt` names the *cause* (cognitive exemption), while `audit_as_ritual` names the *consequence* (repeated findings without fix).

## Acceptance Criteria

- [ ] New `infrastructure_self_exempt` entry added to `traps:` section in `.github/copilot-instructions.md`
- [ ] Exact text: `infrastructure_self_exempt: "Meta-tooling exempted from gates it enforces → apply same rules to the guardrail as to what it guards"`
- [ ] No other traps, cures, or process descriptions changed
- [ ] Pre-commit hooks pass
- [ ] Changelog fragment added to `changelog/unreleased/`
- [ ] Diary reflection added to `docs/diary/`

## Alternatives Considered

1. **Add as a cure instead of a trap.** Rejected — the pattern names a cognitive hazard (the blind spot), not a prevention technique. The cure is embedded in the description's second clause ("apply same rules...") following the established `trap → redirect` convention.

2. **Expand `audit_as_ritual` to cover this case.** Rejected — `audit_as_ritual` names the symptom (repeated audits without fix); `infrastructure_self_exempt` names the root cause (why the fix never happens). They are complementary, not duplicative.

3. **Add a blocking CI gate for meta-tooling tests.** Out of scope for this FR. The diary seeds in audits 95 and 97 suggest pre-commit enforcement (refusing to register scripts without tests). That deserves its own FR if the pattern continues. This FR is strictly about graduating the heuristic to Scripture.

4. **No change (leave unnamed).** Rejected — the pattern has met the graduation threshold (3 independent occurrences, `process.graduation` rule). Leaving it unnamed means agents must rediscover it from diary entries rather than having a compressed signal in their working context.

## Related

- **Diary evidence:**
  - `docs/diary/2026-03-10-inquisitor-audit-94.md`
  - `docs/diary/2026-03-10-inquisitor-audit-95.md`
  - `docs/diary/2026-03-10-inquisitor-audit-97.md`
- **Scripture location:** `.github/copilot-instructions.md`, `traps:` section (after line 63)
- **Complementary entries:** `audit_as_ritual` (trap), `audit_gate` (process)
- **Graduation precedent:** FR-189 (graduated `downstream_fix` refinement)
- **Graduation rule:** `process.graduation` — "Heuristic appears twice → create FR; confirmed recurrence → graduate to Scripture"
