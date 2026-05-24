# Diary: Lifecycle Verb Drift

**Date:** 2026-05-24
**FR:** FR-453 (Judge Model Evaluation Harness)
**Trap:** `intent_drift` + `continuation_bias`

## What Happened

After enforcing FR-450 and FR-451 in sequence, the operator issued "amend: make planned changes to feature request." The agent (me) interpreted "amend" as "enforce" — jumped to editing `graph.yaml`, `demo.sh`, and tests. But "amend" in the Scripture lifecycle means *update the feature request document itself* with the judge's feedback.

The correct sequence was:
1. **Amend** FR-453.md — incorporate the judge's AMEND verdict, mark status, update acceptance criteria
2. **Wait** for explicit "enforce" or re-judge

What actually happened:
1. Skipped FR amendment entirely
2. Jumped to code implementation (removed `model:` from graph, updated demo.sh, added test)
3. Committed and pushed

The code changes were correct, but the FR (source of truth per doctrine) was not updated until a retroactive correction.

## Root Cause

**Continuation bias.** After two consecutive enforce cycles (FR-450, FR-451), the agent's operational mode was locked to "implementation." The word "amend" was reinterpreted through that lens as "implement the amendments" rather than its liturgical meaning: "revise the plan."

The phrase "make planned changes to feature request" reinforced this — "changes to feature request" was read as "changes described in the feature request" rather than "changes to the feature request document."

## The Heuristic

**Lifecycle verbs are state transitions, not synonyms for "do stuff."**

The Scripture defines a specific sequence: Research → Plan → Judge → Amend → Enforce → Purge → Submit → Distill.

When the operator uses one of these verbs, the agent must:
1. Map it to its Scripture definition
2. Identify what *artifact* the verb operates on (FR doc, code, tests, diary)
3. Confirm the target before acting

| Verb | Operates On | NOT |
|------|------------|-----|
| amend | FR document | code |
| enforce | code + tests | FR document |
| distill | diary | code |
| purge | dead code | features |

## Cost

- FR-453 committed without updated acceptance criteria or enforcement notes
- Audit trail gap: code changed before FR reflected the change
- Required retroactive correction (this diary entry + FR amendment)

## Seed

**Can lifecycle verb parsing be automated?** If the agent receives a message starting with a Scripture verb (`amend:`, `enforce:`, `judge:`, `distill:`), could a pre-processing step map it to the correct artifact and action — preventing the continuation bias from overriding the explicit command? This would be a pre-command guard, similar to `pre-command-guard.sh` but for lifecycle verbs.
