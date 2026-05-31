# Diary: Traceability as Architecture, Not Bookkeeping

**Date:** 2026-05-31
**Context:** Explaining the CAP/REQ/test traceability structure to a new observer
**Trap:** `architecture_as_diagram`

## Observation

When asked to explain the capabilities and requirements structure, the act of articulating it revealed something: this is not a documentation system — it is an architectural enforcement mechanism with four interlocking pieces:

1. **CAP YAML** defines what the system claims to do
2. **REQ-YG-XXX** decomposes each claim into testable assertions
3. **`@pytest.mark.req`** binds tests to claims
4. **`req_coverage.py --strict`** + CI gate makes unbacked claims fatal

The chain is closed: you cannot add a capability without a requirement, cannot merge without a test covering it, and cannot reference a phantom requirement without the gate catching it. 163 capabilities, 281 requirements, 4541 tagged tests — 100% coverage enforced mechanically.

## Insight

The power is not in the numbers but in the **closure**. Most traceability systems are open-loop: someone writes a requirement, someone else writes a test, and a human auditor occasionally checks alignment. Here the loop is closed by CI — the `changelog-req-gate` validates that changelog fragments reference real REQ IDs, and `req_coverage.py --strict` validates that every declared REQ has at least one test. The system cannot drift without breaking the build.

This is `detection_without_enforcement` turned inside out: every detection point has a corresponding enforcement gate.

## Heuristic

**Traceability is only as strong as its weakest gate.** The moment any link in the chain becomes advisory (logged but not blocking), the entire structure degrades to documentation — which is to say, it degrades to aspiration. The value of 281/281 green is not the number; it is that 280/281 would be red.

## Seed

Could the same closed-loop traceability pattern be applied to the diary entries themselves? Currently the `diary-gate` checks existence but not substance (`gate_checks_shape_not_substance`). What would a substantive diary gate look like — requiring a Trap, Heuristic, and Seed section, not just a non-empty file?
