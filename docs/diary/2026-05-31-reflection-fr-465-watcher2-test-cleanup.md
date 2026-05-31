# Diary: FR-465 Watcher2 Test Cleanup

## Reflection on FR-465

### The downstream_fix trap — caught by the operator

When 4 CAPs were marked retired, their REQs disappeared from `ALL_REQS`. `test_fr278` referenced REQ-YG-294 (from retired CAP-132), triggering phantom detection. My first instinct was to silence the signal: add a `load_retired_req_ids()` function that excluded retired REQs from phantom detection.

The operator caught it in 5 words: "it breaks the requirement traceability."

The phantom detector was **correct**. An active test referencing a retired REQ is a traceability defect. The fix wasn't to silence the detector — it was to fix the traceability chain:

1. Create CAP-165 (Watcher2 Baseline Dead Code Removal) with REQ-YG-466
2. Re-tag `test_fr278` from REQ-YG-294 → REQ-YG-466
3. Keep CAP-165 **active** (not retired) because the tests prove dead code stays dead — an ongoing concern

### Second trap: reflexive retirement

After creating CAP-165, I initially marked it `status: retired` because it's about watcher2. But the CAP's *feature* (baseline removal) is retired — the CAP's *verification* (tests proving removal) is active. A test that asserts "this file must not exist" is a guardrail, not historical record. Retiring the CAP would have re-created the phantom.

### Heuristic

**Retirement is for features, not for guardrails.** If a test proves something must *stay* deleted/absent, the CAP backing that test must remain active even when the original feature is retired. The absence is the ongoing contract.

This is a refinement of the `downstream_fix` trap: the symptom (phantom REQ) and the root cause (broken traceability) were in different conceptual layers. The symptom was in the detection mechanism; the cause was in the data model (wrong REQ tag + missing CAP).

## Seed:

When a CAP is retired, should `req_coverage.py` emit a warning for any active test still referencing that CAP's REQs? This would have caught the `test_fr278` mis-tagging automatically instead of requiring human insight. The distinction: phantom detection catches REQs that don't exist anywhere; this would catch REQs that exist only in retired CAPs — a "zombie REQ" detector.
